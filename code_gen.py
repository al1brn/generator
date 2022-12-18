#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 17:41:59 2022

@author: alain
"""

# ====================================================================================================
# Class hierarchy

CLASSES = {
    
    # Geometry

    'Geometry'      : ('data', 'geosocks.Geometry'),

    'Mesh'          : ('data', 'Geometry'),
    'Curve'         : ('data', 'Geometry'),
    'Points'        : ('data', 'Geometry'),
    'Instances'     : ('data', 'Geometry'),
    'Volume'        : ('data', 'Geometry'),
    
    # Base

    'Boolean'       : ('data', 'geosocks.Boolean'),
    'Integer'       : ('data', 'geosocks.Integer'),
    'Float'         : ('data', 'geosocks.Float'),
    'Vector'        : ('data', 'geosocks.Vector'),
    'Color'         : ('data', 'geosocks.Color'),
    'String'        : ('data', 'geosocks.String'),
    'Rotation'      : ('data', 'Vector'),
    
    # Blender

    'Collection'    : ('data', 'geosocks.DataSocket'),
    'Object'        : ('data', 'geosocks.DataSocket'),
    'Material'      : ('data', 'geosocks.DataSocket'),
    'Texture'       : ('data', 'geosocks.DataSocket'),
    'Image'         : ('data', 'geosocks.DataSocket'),
    
    # Domains
    
    'Domain'        : ('domain', 'geodom.Domain'),

    'Vertex'        : ('domain', 'Domain'),
    'Edge'          : ('domain', 'Domain'),
    'Face'          : ('domain', 'Domain'),
    'Corner'        : ('domain', 'Domain'),
    'ControlPoint'  : ('domain', 'Domain'),
    'Spline'        : ('domain', 'Domain'),
    'CloudPoint'    : ('domain', 'Domain'),
    'Instance'      : ('domain', 'Domain'),
    }


# ====================================================================================================
# Source code generator

class Generator:
    
    INDENT = "    "
    
    def __init__(self, **kwargs):
        
        self.indent_      = Generator.INDENT    # Indentation
        self.decorator    = None                # if setter: generate @{fname}.setter
        self.fname_       = None                # function or method name
        self.first_arg    = None                # cls, self or None
        
        self.node_wrapper = None                # function to call with node as an argument. Used for stack and attribute 
        
        self.header       = None                # replace the header generation by user source code
        self.body         = None                # replace the body generation by user source code
        
        self.ret_socket   = None                # socket to return, returns node if None. Can be a tuple
        self.ret_class    = None                # type of the return socket. Ignore if socket is None. must be a tuple if ret_socket is tuple.
        self.cache        = False               # use a cache for the node
        self.dtype        = None                # (data_type, value) implements: data_type = self.value_data_type(argument, data_type)
        
        self.is_domain    = False               # domain method
        
        self.kwargs       = {}                  # node argument values
        
        self.com_descr    = None                # Description string
        self.com_args     = None                # Args comments
        self.com_ret      = None                # Return description
        
        # ----------------------------------------------------------------------------------------------------
        # Key word arguments either initialize attributes or are Node arguments
        
        for k, v in kwargs.items():
            if k in ['fname', 'indent']:
                k += '_'
                
            if k in dir(self):
                setattr(self, k, v)
            else:
                self.kwargs[k] = v
                
        # ----------------------------------------------------------------------------------------------------
        # For domain methods:
        # - we replace socket=self by socket = self.data_socket
        # - we add selection=self.selection if no value is given for selection argument
        
        if self.is_domain:
            ok_selection = False
            ok_domain    = False
            ok_data_type = False
            self_key     = None
            for k, v in self.kwargs.items():
                if k == 'selection':
                    ok_selection = True
                if k == 'domain':
                    ok_domain = True
                if v == 'self':
                    self_key = k
                    
            if not ok_selection:
                self.kwargs['selection'] = 'self.selection'
                
            if not ok_selection:
                self.kwargs['domain'] = 'self.domain'
                
            if self_key is not None:
                self.kwargs[self_key] = 'self.data_socket'
                
            if self.node_wrapper == 'stack':
                self.node_wrapper = 'socket_stack'
                
    # ----------------------------------------------------------------------------------------------------
    # Indentation
        
    def indent(self, n):
        return self.indent_ + Generator.INDENT*n

    # ----------------------------------------------------------------------------------------------------
    # fname is either fixed or provided by the node
    
    def fname(self, node):
        return node.function_name if self.fname_ is None else self.fname_

    # ----------------------------------------------------------------------------------------------------
    # Source code to create the name:
    # - nodes.NODE_NAME(keyword=value,...)
    # The value is read from the dictionary when the keyword entry exists,
    # Default value is used otherwise
    
    def node_call_str(self, node):
        args = node.get_node_arguments()
        return f"nodes.{node.node_name}({args.method_call_arguments(**self.kwargs)})"
    
    # ----------------------------------------------------------------------------------------------------
    # Generate the source code
        
    def gen_source(self, node):

        # ----- Hide data_type if exists
        
        if self.dtype is not None:
            default_data_type = None
            for arg in node.get_node_arguments():
                if arg.name == self.dtype[0]:
                    default_data_type = arg.value
                    self.kwargs[self.dtype[0]] = default_data_type
                    break
                    
        # ----- Global

        fname = self.fname(node)
        args  = node.get_node_arguments().method_header(**self.kwargs)
        
        # ----------------------------------------------------------------------------------------------------
        # Header
        #
        # @decorator
        # def fname(...):


        # ----- Decorator
        
        if self.decorator is not None:
            if self.decorator == 'setter':
                yield self.indent(0) + f"@{fname}.setter\n"
                self.header = f"def {fname}(self, attr_value):"
                
            else:
                yield self.indent(0) + self.decorator + "\n"
            
        # ----- Header
            
        if self.header is None:
            if self.first_arg is not None:
                args.insert(0, self.first_arg)
                
            s = ", ".join(args)
            
            yield self.indent(0) + f"def {fname}({s}):\n"
            
        else:
            yield self.indent(0) + self.header + "\n"
            
        # ----------------------------------------------------------------------------------------------------
        # Documentation
        
        # ----- Header
        
        yield self.indent(1) + f'""" Node {node.node_name}.\n\n'
        yield self.indent(1) + f"Node reference [{node.bnode.name}]({node.blender_ref})\n"
        yield self.indent(1) + f"Developer reference [{node.bl_idname}]({node.blender_python_ref})\n\n"
        
        if self.com_descr is not None:
            for line in self.com_descr.split('\n'):
                yield self.indent(1) + line + "\n"
            yield "\n"

        # ----- Arguments
            
        if self.com_args is None:
            ok_arg = False
            for arg in node.get_node_arguments():
                if not arg.name in self.kwargs.keys():
                    if not ok_arg:
                        yield self.indent(1) + f"Args:\n"
                        ok_arg = True
                    yield self.indent(2) + f"{arg.scomment(**self.kwargs)}\n"
    
            if ok_arg:
                yield "\n"
                
        else:
            if len(self.com_args):
                yield self.indent(1) + f"Args:\n"
                for line in self.com_args:
                    yield self.indent(2) + line + "\n"
                yield "\n"
                
        # ----- Returns
        
        if self.com_ret is None:
            if self.decorator != 'setter':
                yield self.indent(1) + f"Returns:\n"
                if self.ret_socket is None:
                    yield self.indent(2) + f"node with sockets {list(node.outputs.unames.keys())}\n"
                elif isinstance(self.ret_socket, tuple):
                    yield self.indent(2) + f"tuple {self.ret_socket}\n"
                else:
                    yield self.indent(2) + f"socket '{self.ret_socket}'"
                    if self.ret_class is None or self.ret_class == 'cls':
                        yield "\n"
                    else:
                        yield f" of class {self.ret_class}\n"
        else:
            if self.com_ret != "":
                yield self.indent(1) + f"Returns:\n"
                for line in self.com_ret.split('\n'):
                    yield self.indent(1) + line + "\n"
                    
        # ----- Done
                    
        yield self.indent(1) + '"""\n'

            
        # ----------------------------------------------------------------------------------------------------
        # Body
            
        # ----- Body if exists
            
        if self.body is not None:
            for line in self.body.split("\n"):
                yield self.indent(1) + line + "\n"
            
            yield "\n"

            return
        
        # ----- data_type
 
        if self.dtype is not None:
            yield self.indent(1) + f"{self.dtype[0]}_ = self.value_data_type({self.dtype[1]}, {default_data_type})\n"
            self.kwargs[self.dtype[0]] = f"{self.dtype[0]}_"
        
        # ----- Node creation string

        s = f"{self.node_call_str(node)}"
        if self.node_wrapper is not None:
            s = f"self.{self.node_wrapper}({s})"
            
        # ----- Cache mechanism
        # node = ...
            
        if self.cache:
            fname = self.fname(node)
            yield self.indent(1) + f"if not hasattr(self, '_c_{fname}'):\n"
            yield self.indent(2) + f"self._c_{fname} = {s}\n"
            snode = f"self._c_{fname}"
        else:
            snode = s

        # ----- Return node, a socket or a tuple of sockets
        
        def check_output_socket(name):
            if name not in node.outputs.unames.keys():
                raise Exception(f"Node {node.bl_idname}: '{name}' is not a valid output socket name in {list(node.outputs.unames.keys())}")
        
        if self.ret_socket is None:
            s = snode
            
        elif isinstance(self.ret_socket, tuple):
            yield self.indent(1) + f"node = {snode}\n"
            vals = []
            ret_class = (None,) * len(self.ret_socket) if self.ret_class is None else self.ret_class
            for rs, rc in zip(self.ret_socket, ret_class):
                check_output_socket(rs)
                if rc is None:
                    vals.append(f"node.{rs}")
                else:
                    vals.append(f"{rc}(node.{rs})")
                    
            s = ", ".join(vals)
                
        else:
            check_output_socket(self.ret_socket)
            s = f"{snode}.{self.ret_socket}"

            if self.ret_class is not None:
                s = f"{self.ret_class}({s})"
                
        # ----- No return if property setter
        
        if self.decorator == 'setter':
            return_ = ""
        else:
            return_ = "return "
            
        # ----- Done
            
        yield self.indent(1) + f"{return_}{s}\n\n"
        
# ----------------------------------------------------------------------------------------------------
# Method 

class Static(Generator):
    def __init__(self, **kwargs):
        super().__init__(decorator='@staticmethod', **kwargs)
            
class Method(Generator):
    def __init__(self, **kwargs):
        if 'first_arg' in kwargs.keys():
            super().__init__(**kwargs)
        else:
            super().__init__(first_arg='self', **kwargs)
        
class DomMethod(Method):
    def __init__(self, **kwargs):
        super().__init__(is_domain=True, **kwargs)

# ----------------------------------------------------------------------------------------------------
# Property
        
class Property(Method):
    def __init__(self, **kwargs):
        super().__init__(decorator="@property", **kwargs)
        
        self.com_descr = "Node implemented as property."
        self.com_args = []
        
class DomProperty(Property):
    def __init__(self, **kwargs):
        super().__init__(is_domain=True, **kwargs)        

class Setter(Method):
    def __init__(self, stack=True, **kwargs):
        node_wrapper = 'stack' if stack else None
        super().__init__(decorator="setter", node_wrapper=node_wrapper, **kwargs)
        self.com_descr = "Node implemented as property setter."
        
        for k, v in self.kwargs.items():
            if v == 'attr_value':
                self.com_args  = [f"attr_value: {k}"]
                break
        self.com_ret = ""
        
class DomSetter(Setter):
    def __init__(self, stack=True, **kwargs):
        super().__init__(is_domain=True, stack=stack, **kwargs)        

# ----------------------------------------------------------------------------------------------------
# Stack method
        
class StackMethod(Method):
    def __init__(self, **kwargs):
        super().__init__(node_wrapper='stack', **kwargs)

class DomStackMethod(StackMethod):
    def __init__(self, **kwargs):
        super().__init__(is_domain=True, **kwargs)
    
# ----------------------------------------------------------------------------------------------------
# Attribute method
        
class Attribute(Method):
    def __init__(self, **kwargs):
        super().__init__(node_wrapper='as_attribute', **kwargs)
        
class PropAttribute(Attribute):
    def __init__(self, **kwargs):
        super().__init__(decorator="@property", **kwargs)
        
class DomAttribute(Method):
    def __init__(self, **kwargs):
        super().__init__(is_domain=True, node_wrapper='attribute_node', **kwargs)
        
class DomPropAttribute(DomAttribute):
    def __init__(self, **kwargs):
        super().__init__(decorator="@property", **kwargs)
        
        
        
# ----------------------------------------------------------------------------------------------------
# Constructor
    
class Constructor(Generator):
    def __init__(self, **kwargs):
        super().__init__(first_arg='cls', ret_class='cls', decorator='@classmethod', **kwargs)
        
# ----------------------------------------------------------------------------------------------------
# Function
        
class Function(Generator):
    def __init__(self, **kwargs):
        super().__init__(indent="", **kwargs)
        
# ----------------------------------------------------------------------------------------------------
# Source code
        
class Source(Generator):
    pass

# ----------------------------------------------------------------------------------------------------
# Property read error
#
# Used for properties which are only write only
    
class PropReadError(Generator):
    def __init__(self, fname, class_name):
        super().__init__(
                decorator ="@property",
                header    = f"def {fname}(self):",
                body      = f"raise Exception(\"Error: '{fname}' is a write only property of class {class_name}!\")",
                com_descr = f"'{fname}' is a write only property.\nRaise an exception if attempt to read.",
                com_args  = [],
                com_ret   = "",
                )
        
# ====================================================================================================
# Class generator

class ClassGenerator(dict):
    
    def __init__(self, wnodes):
        super().__init__()
        self.wnodes = wnodes
        
    # ----------------------------------------------------------------------------------------------------
    # Add a dictionary of generators
        
    def add_generators(self, gens):
        
        for blid, classes in gens.items():
            
            wnode = self.wnodes.get(blid)
            
            if wnode is None:
                raise Exception(f"ERROR: node {blid} not found")
                
            for cnames, generators in classes.items():
                
                # ----- cnames can be class name or tuple of class names
                
                if isinstance(cnames, tuple):
                    class_names = cnames
                else:
                    class_names = (cnames,)
                    
                for class_name in class_names:
                    
                    if class_name not in self.keys():
                        self[class_name] = {}
                        
                    if blid not in self[class_name]:
                        self[class_name][blid] = []
                    
                    if isinstance(generators, list):
                        self[class_name][blid].extend(generators)
                    else:
                        self[class_name][blid].append(generators)
                        
    # ----------------------------------------------------------------------------------------------------
    # Mehods of a class
    # Returns sorted array of triplets:
    # - methode name
    # - generator
    # - wnode
    
    def class_methods(self, class_name):
        
        methods = []
        for blid, gens in self[class_name].items():
            wnode = self.wnodes.get(blid)
            for gen in gens:
                fname = gen.fname(wnode)
                if gen.decorator == 'setter':
                    fname += " setter"
                
                methods.append((fname, gen, wnode))
                
        return sorted(methods, key=lambda a: a[0])
    
    # ----------------------------------------------------------------------------------------------------
    # Generate the functions to import in __init__
                        
    def gen_classes_import(self):

        # ----- Data classes
        
        for class_name in sorted(self.keys()):
            if class_name != 'function':
                yield f"from geonodes.nodes.classes import {class_name}\n"
                
        yield "\n"
        
        # ----- Global functions
        
        methods = self.class_methods('function')
        
        s = None
        for f, _, _ in methods:
            if s is None:
                s = f"from geonodes.nodes.classes import {f}"
            else:
                s += f", {f}"
            if len(s) > 140:
                yield s + "\n"
                s = None
        
        if s is not None:
            yield s + "\n"
            
        yield "\n"
        
    # ----------------------------------------------------------------------------------------------------
    # Generate a class
                    
    def gen_class(self, class_name):
        
        if class_name != 'function':
            if class_name not in CLASSES:
                raise Exception(f"{class_name} not in CLASSES!")
                
            root = CLASSES[class_name][1]
            if root != "":
                root = f"({root})"
            yield f"class {class_name}{root}:\n"
        
        # ----- Mehods
        
        methods = self.class_methods(class_name)
        
        # ----- Generate the methods
        
        for _, gen, wnode in methods:
            for line in gen.gen_source(wnode):
                yield line
            yield "\n"
            
    # ----------------------------------------------------------------------------------------------------
    # Create one file per class
                
    def create_files(self, fpath, select=None):
        
        for class_name in self.keys():
            if select is None or class_name in select:
                with open(fpath + f"{class_name.lower()}.py", 'w') as f:
                    for line in self.gen_class(class_name):
                        f.write(line)
                    f.write("\n\n")
                    
    # ----------------------------------------------------------------------------------------------------
    # Create one big file with all classes
        
    def create_one_file(self, file_name, select=None):
        
        with open(file_name, 'w') as f:
            
            f.write("import geonodes.core.datasockets as geosocks\n")
            f.write("import geonodes.core.domain as geodom\n")
            f.write("\n")
            
            if False:
                f.write("# Imports to copy in __init__.py\n")
                f.write('"""\n')

                for line in self.gen_classes_import():
                    f.write(line)
                f.write('"""\n')
            
            for class_name in self.keys():
                if select is None or class_name in select:
                    for line in self.gen_class(class_name):
                        f.write(line)
                    f.write("\n\n")
                    
    # ----------------------------------------------------------------------------------------------------
    # Create the __init__.py file
    
    def create_init_file(self, file_name, version):
        
        with open(file_name, 'w') as f:
            
            import bpy
            
            f.write("# geonodes init file\n\n")
            
            f.write(f"version = {version}\n")
            f.write(f"blender_version={bpy.app.version}\n\n")
            
            f.write("pi = 3.141592653589793\n\n")
            
            f.write("from geonodes.core.node import Node, GroupInput, GroupOutput, Frame, Viewer, SceneTime\n")
            f.write("from geonodes.core.tree import Tree, Groups\n\n")
            
            for line in self.gen_classes_import():
                f.write(line)
                
            f.write("\n")
                    
        
        
        
# ====================================================================================================
# Attribute Menu

ATTRIBUTE = {
    'GeometryNodeAttributeStatistic': {
        'Geometry': Method(geometry='self', dtype=('data_type', 'attribute')),
        'Domain'  : [
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute')),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_mean',   ret_socket='mean'),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_median', ret_socket='median'),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_sum',    ret_socket='sum'),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_min',    ret_socket='min'),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_max',    ret_socket='max'),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_range',  ret_socket='range'),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_std',    ret_socket='standard_deviation'),
            DomMethod(cache=True, geometry='self', dtype=('data_type', 'attribute'), fname='attribute_var',    ret_socket='variance'),
            ],
        },
    'GeometryNodeCaptureAttribute': {
        'Geometry': StackMethod(ret_socket='attribute',    dtype=('data_type', 'attribute'), geometry='self'),
        'Domain':   DomStackMethod(ret_socket='attribute', dtype=('data_type', 'attribute'), geometry='self'),
        },
    'GeometryNodeAttributeDomainSize': {
        'Geometry' : Property(cache=True, geometry='self'),
        
        'Mesh'     : [
            Property(cache=True, geometry='self', component="'MESH'"),
            Property(cache=True, geometry='self', component="'MESH'", fname='point_count',  ret_socket='point_count'),
            Property(cache=True, geometry='self', component="'MESH'", fname='face_count',   ret_socket='face_count'),
            Property(cache=True, geometry='self', component="'MESH'", fname='edge_count',   ret_socket='edge_count'),
            Property(cache=True, geometry='self', component="'MESH'", fname='corner_count', ret_socket='face_corner_count'),
            ],
        'Curve'    : [
            Property(cache=True, geometry='self', component="'CURVE'"),
            Property(cache=True, geometry='self', component="'CURVE'", fname='point_count',  ret_socket='point_count'),
            Property(cache=True, geometry='self', component="'CURVE'", fname='spline_count',  ret_socket='spline_count'),
            ],
        'Points'   : Property(cache=True, geometry='self', component="'POINTCLOUD'", ret_socket='point_count'),
        'Instances': Property(cache=True, geometry='self', component="'INSTANCES'",  ret_socket='instance_count'),
        
        'Vertex'   : Source(header="def __len__(self):", body="return self.data_socket.point_count"),
        'Face'     : Source(header="def __len__(self):", body="return self.data_socket.face_count"),
        'Edge'     : Source(header="def __len__(self):", body="return self.data_socket.edge_count"),
        'Corner'   : Source(header="def __len__(self):", body="return self.data_socket.face_corner_count"),
        
        'Spline'   : Source(header="def __len__(self):", body="return self.data_socket.spline_count"),
        'ControlPoint' : Source(header="def __len__(self):", body="return self.data_socket.point_count"),
        
        'CloudPoint'   : Source(header="def __len__(self):", body="return self.data_socket.point_count"),
        'Instance'     : Source(header="def __len__(self):", body="return self.sata_socker.instance_count"),
        
        },
    'GeometryNodeStoreNamedAttribute': {
        'Geometry': StackMethod(geometry='self',    dtype=('data_type', 'attribute')),
        'Domain'  : DomStackMethod(geometry='self', dtype=('data_type', 'attribute')),
        },
    'GeometryNodeRemoveAttribute': {
        'Geometry': StackMethod(geometry='self'),
        'Domain'  : DomStackMethod(geometry='self'),
        },
}

COLOR = {
    'ShaderNodeValToRGB': {
        'function': Function(),
        'Float': Property(fac='self'),
    },
    'FunctionNodeCombineColor': {
        'function': [
            Function(fname='combine_rgb', ret_socket='color', mode="'RGB'"),
            Function(fname='combine_hsv', ret_socket='color', mode="'HSV'", arg_rename={'red': 'hue', 'green': 'saturation', 'blue': 'value'}),
            Function(fname='combine_hsl', ret_socket='color', mode="'HSL'", arg_rename={'red': 'hue', 'green': 'saturation', 'blue': 'lightness'}),
            ],
        'Color': [
            Constructor(fname='RGB', ret_socket='color', mode="'RGB'"),
            Constructor(fname='HSV', ret_socket='color', mode="'HSV'", arg_rename={'red': 'hue', 'green': 'saturation', 'blue': 'value'}),
            Constructor(fname='HSL', ret_socket='color', mode="'HSV'", arg_rename={'red': 'hue', 'green': 'saturation', 'blue': 'lightness'}),
            ]
    },
    'ShaderNodeMix': {
        'function': [
            Function(fname='float_mix', ret_socket='result', data_type="'FLOAT'", blend_type='MIX', clamp_result=False, factor_mode="'UNIFORM'"),
            Function(fname='vector_mix', ret_socket='result', data_type="'VECTOR'", blend_type='MIX', clamp_result=False),
            
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_mix',              ),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_darken',       blend_type="'DARKEN'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_multiply',     blend_type="'MULTIPLY'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_burn',         blend_type="'BURN'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_lighten',      blend_type="'LIGHTEN'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_screen',       blend_type="'SCREEN'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_dodge',        blend_type="'DODGE'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_add',          blend_type="'ADD'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_overlay',      blend_type="'OVERLAY'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_soft_light',   blend_type="'SOFT_LIGHT'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_linear_light', blend_type="'LINEAR_LIGHT'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_difference',   blend_type="'DIFFERENCE'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_subtract',     blend_type="'SUBTRACT'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_divide',       blend_type="'DIVIDE'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_hue',          blend_type="'HUE'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_saturation',   blend_type="'SATURATION'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_color',        blend_type="'COLOR'"),
            Function(ret_socket='result', data_type="'COLOR'", factor_mode="'UNIFORM'", fname='color_value',        blend_type="'VALUE'"),
            ],
        'Color': [
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix',              ),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_darken',       blend_type="'DARKEN'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_multiply',     blend_type="'MULTIPLY'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_burn',         blend_type="'BURN'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_lighten',      blend_type="'LIGHTEN'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_screen',       blend_type="'SCREEN'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_dodge',        blend_type="'DODGE'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_add',          blend_type="'ADD'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_overlay',      blend_type="'OVERLAY'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_soft_light',   blend_type="'SOFT_LIGHT'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_linear_light', blend_type="'LINEAR_LIGHT'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_difference',   blend_type="'DIFFERENCE'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_subtract',     blend_type="'SUBTRACT'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_divide',       blend_type="'DIVIDE'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_hue',          blend_type="'HUE'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_saturation',   blend_type="'SATURATION'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_color',        blend_type="'COLOR'"),
            Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_value',        blend_type="'VALUE'"),
            ],
        'Float': Method(ret_socket='result', a='self', data_type="'FLOAT'", blend_type='MIX', arg_rename={'b': 'value'}, clamp_result=False, factor_mode="'UNIFORM'"),
        'Vector': [
            Method(ret_socket='result', a='self', data_type="'VECTOR'", blend_type='MIX', arg_rename={'b': 'vector'}, clamp_result=False),
            Method(ret_socket='result', a='self', data_type="'VECTOR'", blend_type='MIX', arg_rename={'b': 'vector'}, clamp_result=False, fname='mix_uniform', factor_mode="'UNIFORM'", factor=None),
            Method(ret_socket='result', a='self', data_type="'VECTOR'", blend_type='MIX', arg_rename={'b': 'vector'}, clamp_result=False, fname='mix_non_uniform', factor_mode="'NON_UNIFORM'"),
            ]
    },
    'ShaderNodeRGBCurve': {
        'function': Function(),
        'Color': Property(color='self'),
    },
    'FunctionNodeSeparateColor': {
        'function': [
            Function(fname='separate_rgb', ret_socket=('red', 'green', 'blue', 'alpha'), mode="'RGB'"),
            Function(fname='separate_hsv', ret_socket=('red', 'green', 'blue', 'alpha'), mode="'HSV'"),
            Function(fname='separate_hsl', ret_socket=('red', 'green', 'blue', 'alpha'), mode="'HSL'"),
                     ],
        'Color'   : [
            Property(fname='rgb', ret_socket=('red', 'green', 'blue', 'alpha'), color='self', mode="'RGB'"),
            Property(fname='hsv', ret_socket=('red', 'green', 'blue', 'alpha'), color='self', mode="'HSV'"),
            Property(fname='hsl', ret_socket=('red', 'green', 'blue', 'alpha'), color='self', mode="'HSL'"),
            ],
    },
}


CURVE1 = {
    'GeometryNodeCurveLength': {
        'Curve': Property(fname='length', ret_socket='length', curve='self'),
    },
    'GeometryNodeCurveToMesh': {
        'Curve': Method(fname='to_mesh', ret_socket='mesh', ret_class='Mesh', curve='self'),
    },
    'GeometryNodeCurveToPoints': {
        'Curve': [
            Method(fname='to_points', ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None), curve='self'),
            Method(fname='to_points_count',     ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None), mode="'COUNT'",     curve='self', length=.1),
            Method(fname='to_points_length',    ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None), mode="'LENGTH'",    curve='self', count=10),
            Method(fname='to_points_evaluated', ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None), mode="'EVALUATED'", curve='self', count=10, length=.1),
            ],
    },
    'GeometryNodeDeformCurvesOnSurface': {
        'Curve': StackMethod(fname='deform_on_surface', curves='self'),
    },
    'GeometryNodeFillCurve': {
        'Curve': [
            Method(fname='fill',           ret_socket='mesh', ret_class='Mesh'),
            Method(fname='fill_triangles', ret_socket='mesh', ret_class='Mesh', mode="'TRIANGLES'"),
            Method(fname='fill_ngons',     ret_socket='mesh', ret_class='Mesh', mode="'NGONS'"),
            ]
    },
    'GeometryNodeFilletCurve': {
        'Curve': [
            StackMethod(fname='fillet',        curve='self'),
            StackMethod(fname='fillet_bezier', curve='self', mode="'BEZIER'", count=1),
            StackMethod(fname='fillet_poly',   curve='self', mode = "'POLY'"),
            ],
    },
    'GeometryNodeResampleCurve': {
        'Curve': [
            StackMethod(fname='resample',           curve='self'),
            StackMethod(fname='resample_count',     curve='self', mode="'COUNT'",     length=.1),
            StackMethod(fname='resample_length',    curve='self', mode="'LENGTH'",    count=10),
            StackMethod(fname='resample_evaluated', curve='self', mode="'EVALUATED'", count=10, length=.1),
            ],
        'Spline': [
            DomStackMethod(fname='resample',           curve='self'),
            DomStackMethod(fname='resample_count',     curve='self', mode="'COUNT'", length=.1),
            DomStackMethod(fname='resample_length',    curve='self', mode="'LENGTH'", count=10),
            DomStackMethod(fname='resample_evaluated', curve='self', mode="'EVALUATED'", count=10, length=.1),
            ],
    },
    'GeometryNodeReverseCurve': {
        'Curve':  StackMethod(fname='reverse', curve='self'),
    },
    'GeometryNodeSampleCurve': {
        'Curve':  StackMethod(fname='sample', curves='self'),
    },
    'GeometryNodeSubdivideCurve': {
        'Curve':  StackMethod(fname='subdivide', curve='self'),
    },
    'GeometryNodeTrimCurve': {
        'Curve':  [
            StackMethod(fname='trim', header="def trim(self, start=None, end=None, mode='FACTOR'):", curve='self', start0='start', end0='start', start1='start', end1='end'),
            StackMethod(fname='trim_factor', curve='self', arg_rename={'start0': 'start', 'end0': 'end'}, start1=None, end1=None),
            StackMethod(fname='trim_length', curve='self', arg_rename={'start1': 'start', 'end1': 'end'}, start0=None, end0=None),
            ],
    },
}

CURVE2 = {
    'GeometryNodeInputCurveHandlePositions': {
        'Spline': [
            Attribute(fname='handle_positions'),
            DomPropAttribute(fname='left_handle_positions', ret_socket='left', relative=None),
            DomPropAttribute(fname='right_handle_positions', ret_socket='right', relative=None),
            ],
    },
    'GeometryNodeInputTangent': {
        'Spline': DomPropAttribute(fname='tangent', ret_socket='tangent'),
    },
    'GeometryNodeInputCurveTilt': {
        'Spline': DomPropAttribute(fname='tilt', ret_socket='tilt'),
    },
    'GeometryNodeCurveEndpointSelection': {
        'Spline': DomAttribute(fname='endpoint_selection', ret_socket='selection'),
    },
    'GeometryNodeCurveHandleTypeSelection': {
        'Spline': [
            DomAttribute(fname='handle_type_selection_node', ret_socket='selection'),
            Source(
                header="def handle_type_selection(self, left=True, right=True, handle_type='AUTO'):",
                body  ="mode={'LEFT'} if left else {}\nif right: mode.add('RIGHT')\nreturn self.handle_type_selection_node(handle_type=handle_type, mode=mode)"
                ),
            Source(
                header="def handle_type_selection_free(self, left=True, right=True):",
                body  ="return self.handle_type_selection(left=left, right=right, handle_type='FREE')"
                ),
            Source(
                header="def handle_type_selection_auto(self, left=True, right=True):",
                body  ="return self.handle_type_selection(left=left, right=right, handle_type='AUTO')"
                ),
            Source(
                header="def handle_type_selection_vector(self, left=True, right=True):",
                body  ="return self.handle_type_selection(left=left, right=right, handle_type='VECTOR')"
                ),
            Source(
                header="def handle_type_selection_align(self, left=True, right=True):",
                body  ="return self.handle_type_selection(left=left, right=right, handle_type='ALIGN')"
                ),
            ],
    },
    'GeometryNodeInputSplineCyclic': {
        'Spline': PropAttribute(fname='cyclic', ret_socket='cyclic'),
    },
    'GeometryNodeSplineLength': {
        'Spline': DomPropAttribute(fname='length', ret_socket=('length', 'point_count')),
    },
    'GeometryNodeSplineParameter': {
        'Spline': DomPropAttribute(fname='parameter', ret_socket=('factor', 'length', 'index')),
    },
    'GeometryNodeInputSplineResolution': {
        'Spline': DomPropAttribute(fname='resolution', ret_socket='resolution'),
    },
    
    'GeometryNodeSetCurveNormal': {
        'Spline': [
            DomStackMethod(fname='set_normal', curve='self'),
            DomSetter(fname='normal', stack=True, curve='self', mode='attr_value'),
            ],
    },
    'GeometryNodeSetCurveRadius': {
        'Spline': [
            DomStackMethod(fname='set_radius', curve='self'),
            DomSetter(fname='radius', stack=True, curve='self', radius='attr_value'),
            ],
    },
    'GeometryNodeSetCurveTilt': {
        'Spline': [
            DomStackMethod(fname='set_tilt', curve='self'),
            DomSetter(fname='tilt', stack=True, curve='self', tilt='attr_value'),
            ],
    },
    'GeometryNodeSetCurveHandlePositions': {
        'Spline': [
            DomStackMethod(fname='set_handle_positions', curve='self'),
            DomStackMethod(fname='set_handle_positions_left',  mode="'LEFT'"),
            DomStackMethod(fname='set_handle_positions_right', mode="'RIGHT'"),
            DomSetter(fname='left_handle_positions', stack=True, position='attr_value', mode="'LEFT'"),
            DomSetter(fname='right_handle_positions', stack=True, position='attr_value', mode="'RIGHT'"),
            ],
    },
    'GeometryNodeCurveSetHandles': {
        'Spline': [
            DomStackMethod(fname='set_handle_type_node', curve='self'),
            Source(
                header="def set_handle_type(self, left=True, right=True, handle_type=""'AUTO'""):",
                body  ="mode={'LEFT'} if left else {}\nif right: mode.add('RIGHT')\nreturn self.set_handle_type_node(handle_type=handle_type, mode=mode)"
                )
            ],
    },
    'GeometryNodeSetSplineCyclic': {
        'Spline': [
            DomStackMethod(fname='set_cyclic', geometry='self'),
            DomSetter(fname='cyclic', stack=True, geometry='self', cyclic='attr_value'),
            ],
    },
    'GeometryNodeSetSplineResolution': {
        'Spline': [
            DomStackMethod(fname='set_resolution', geometry='self'),
            DomSetter(fname='resolution', stack=True, geometry='self', resolution='attr_value'),
            ],
    },
    'GeometryNodeCurveSplineType': {
        'Spline': [
            DomStackMethod(fname='set_type', curve='self'),
            PropReadError(fname='type', class_name='Curve'),
            DomSetter(fname='type', stack=True, curve='self', spline_type='attr_value'),
            ],
    },
}

CURVE_PRIMITIVES = {
    'GeometryNodeCurveArc': {
        'Curve': [
            #Constructor(fname="ArcPrimitive"),
            Constructor(fname='Arc', ret_socket='curve', mode="'RADIUS'", start=None, middle=None, end=None, offset_angle=None),
            Constructor(fname='ArcFromPoints', mode='POINT', radius=None, start_angle=None, sweep_angle=None),
        ],
    },
    'GeometryNodeCurvePrimitiveBezierSegment': {
        'Curve': Constructor(fname='bezier_segment', ret_socket='curve'),
    },
    'GeometryNodeCurvePrimitiveCircle': {
        'Curve': [
            Constructor(fname='Circle', ret_socket='curve', mode="'RADIUS'", point_1=None, point_2=None, point_3=None),
            Constructor(fname='CircleFromPoints', mode='POINT', radius=None),
            ],
    },
    'GeometryNodeCurvePrimitiveLine': {
        'Curve': [
            Constructor(fname='Line', ret_socket='curve', mode="'POINT'", direction=None, length=None),
            Constructor(fname='LineDirection', ret_socket='curve', mode="'DIRECTION'", end=None),
            ],
    },
    'GeometryNodeCurveSpiral': {
        'Curve': Constructor(fname='Spiral', ret_socket='curve'),
    },
    'GeometryNodeCurveQuadraticBezier': {
        'Curve': Constructor(fname='QuadraticBezier', ret_socket='curve'),
    },
    'GeometryNodeCurvePrimitiveQuadrilateral': {
        'Curve': Constructor(fname='Quadrilateral', ret_socket='curve'),
    },
    'GeometryNodeCurveStar': {
        'Curve': Constructor(fname='Star'),
    },    
}

CURVE_TOPOLOGY = {
    'GeometryNodeOffsetPointInCurve': {
        'Curve': Attribute(fname='offset_point',     ret_socket=('is_valid_offset', 'point_index')),
        'ControlPoint': DomAttribute(fname='offset', ret_socket=('is_valid_offset', 'point_index'), point_index='self.selection_index'),
    },
    'GeometryNodeCurveOfPoint': {
        'Curve': Attribute(fname='curve_of_point',  ret_socket=('curve_index', 'index_in_curve')),
        'ControlPoint': DomAttribute(fname='curve', ret_socket=('curve_index', 'index_in_curve'), point_index='self.selection_index'),
    },
    'GeometryNodePointsOfCurve': {
        'Curve': Attribute(fname='points_of_curve', ret_socket=('point_index', 'total')),
        'Spline': DomAttribute(fname='points',      ret_socket=('point_index', 'total'), curve_index='self.selection_index'),
    },
}

GEOMETRY = {
    'GeometryNodeBoundBox': {
        'Geometry': [
            Property(fname='bounding_box', cache=True, ret_socket='bounding_box', ret_class='Mesh', geometry='self'),
            Property(fname='bounding_box_min', cache=True, ret_socket='min', geometry='self'),
            Property(fname='bounding_box_min', cache=True, ret_socket='max', geometry='self'),
            ],
    },
    'GeometryNodeConvexHull': {
        'Geometry': Property(fname='convex_hull', ret_socket='convex_hull', ret_class='Mesh', geometry='self'),
    },
    'GeometryNodeDeleteGeometry': {
        'Geometry': StackMethod(fname='delete', geometry='self'),
        'Mesh'    : [
            StackMethod(fname='delete_all',   geometry='self', mode="'ALL'"),
            StackMethod(fname='delete_edges', geometry='self', mode="'EDGE_FACE'"),
            StackMethod(fname='delete_faces', geometry='self', mode="'ONLY_FACE'"),
            ],
        'Domain'  : DomStackMethod(fname='delete', geometry='self'),
        'Vertex'  : [
            DomStackMethod(fname='delete_all',   geometry='self', mode="'ALL'"),
            DomStackMethod(fname='delete_edges', geometry='self', mode="'EDGE_FACE'"),
            DomStackMethod(fname='delete_faces', geometry='self', mode="'ONLY_FACE'"),
            ],
        'Edge'  : [
            DomStackMethod(fname='delete_all',   geometry='self', mode="'ALL'"),
            DomStackMethod(fname='delete_edges', geometry='self', mode="'EDGE_FACE'"),
            DomStackMethod(fname='delete_faces', geometry='self', mode="'ONLY_FACE'"),
            ],
        'Face'  : [
            DomStackMethod(fname='delete_all',   geometry='self', mode="'ALL'"),
            DomStackMethod(fname='delete_edges', geometry='self', mode="'EDGE_FACE'"),
            DomStackMethod(fname='delete_faces', geometry='self', mode="'ONLY_FACE'"),
            ],
    },
    'GeometryNodeDuplicateElements': {
        'Geometry' : StackMethod(fname='duplicate',    ret_socket='duplicate_index', geometry='self'),
        'Domain'   : DomStackMethod(fname='duplicate', ret_socket='duplicate_index', geometry='self'),
    },
    'GeometryNodeProximity': {
        'Geometry' : [
            Attribute(fname='proximity',        ret_socket='distance'),
            Attribute(fname='proximity_points', ret_socket='distance', target_element="'POINTS'"),
            Attribute(fname='proximity_edges',  ret_socket='distance', target_element="'EDGES'"),
            Attribute(fname='proximity_facess', ret_socket='distance', target_element="'FACES'"),
            ],
    },
    'GeometryNodeGeometryToInstance': {
        'function': Function(ret_socket='instances', ret_class='Instances'),
        'Geometry': Method(fname='to_instance', first_arg=None, ret_socket='instances', ret_class='Instances'),
    },
    'GeometryNodeJoinGeometry': {
        'function': Function(ret_socket='geometry'),
        'Geometry': StackMethod(fname='join', first_arg=None),
    },
    'GeometryNodeMergeByDistance': {
        'Geometry': StackMethod(geometry='self'),
        'Vertex'  : DomStackMethod(geometry='self'),
    },
    'GeometryNodeRaycast': {
        'Geometry' : [
            Attribute(dtype=('data_type', 'attribute')),
            Attribute(fname='raycast_interpolated', dtype=('data_type', 'attribute'), mapping="'INTERPOLATED'"),
            Attribute(fname='raycast_nearest',      dtype=('data_type', 'attribute'), mapping="'NEAREST'"),
            ],
    },
    'GeometryNodeSampleIndex': {
        'Geometry': Method(dtype=('data_type', 'value'), ret_socket='value', geometry='self'),
        'Domain'  : DomMethod(dtype=('data_type', 'value'), ret_socket='value', geometry='self'),
    },
    'GeometryNodeSampleNearest': {
        'Geometry': Method(ret_socket='index', geometry='self'),
        'Domain'  : DomMethod(ret_socket='index', geometry='self'),
    },
    'GeometryNodeSeparateComponents': {
        'Geometry': [
            Property(geometry='self', cache=True),
            Property(geometry='self', cache=True, fname='separate_mesh',      ret_socket='mesh',        ret_class='Mesh'),
            Property(geometry='self', cache=True, fname='separate_curve',     ret_socket='curve',       ret_class='Curve'),
            Property(geometry='self', cache=True, fname='separate_points',    ret_socket='point_cloud', ret_class='Points'),
            Property(geometry='self', cache=True, fname='separate_volume',    ret_socket='volume',      ret_class='Volume'),
            Property(geometry='self', cache=True, fname='separate_instances', ret_socket='instances',   ret_class='Instances'),
            ],
    },
    'GeometryNodeSeparateGeometry': {
        'Geometry': Method(fname='separate', geometr='self', ret_socket=('selection', 'inverted')),
        'Domain'  : DomMethod(fname='separate', geometr='self', ret_socket=('selection', 'inverted')),
    },
    'GeometryNodeTransform': {
        'Geometry': StackMethod(geometry='self'),
    },
    'GeometryNodeSetID': {
        'Geometry': StackMethod(geometry='self'),
        'Domain'  : [
            DomStackMethod(geometry='self'),
            DomSetter(fname='ID', geometry='self', ID='attr_value'),
            ],
    },
    'GeometryNodeSetPosition': {
        'Geometry': StackMethod(geometry='self'),
        'Domain'  : [
            DomStackMethod(geometry='self'),
            DomSetter(fname='position', geometry='self', position='attr_value', offset=None),
            ],
    },
}

INPUT = {
    'FunctionNodeInputBool': {
        'Boolean': Constructor(fname='Boolean', ret_socket='boolean'),
    },
    'GeometryNodeCollectionInfo': {
        'Geometry': Constructor(fname='Collection', ret_socket='geometry'),
    },
    'FunctionNodeInputColor': {
        'Color': Constructor(fname='Color', ret_socket='color'),
    },
    'FunctionNodeInputInt': {
        'Integer': Constructor(fname='Integer', ret_socket='integer'),
    },
    'GeometryNodeIsViewport': {
        'Geometry': PropAttribute(ret_socket='is_viewport'),
    },
    'GeometryNodeInputMaterial': {
        'Material': Constructor(fname='Material', ret_socket='material'),
    },
    'GeometryNodeObjectInfo': {
        'Object': Method(fname='info'),
    },
    'GeometryNodeSelfObject': {
        'Object': Constructor(fname='Self', ret_socket='self_object'),
    },
    'FunctionNodeInputString': {
        'String': Constructor(fname='String', ret_socket='string'),
    },
    'ShaderNodeValue': {
        'Float': Constructor(fname='Value', ret_socket='value'),
    },
    'FunctionNodeInputVector': {
        'Vector': Constructor(fname='Vector', ret_socket='vector'),
    },
    'GeometryNodeInputID': {
        'Geometry': PropAttribute(fname='ID', ret_socket='ID'),
        'Domain'  : DomPropAttribute(fname='ID', ret_socket='ID'),
    },
    'GeometryNodeInputIndex': {
        'Geometry': PropAttribute(fname='index', ret_socket='index'),
        'Domain'  : DomPropAttribute(fname='index', ret_socket='index'),
    },
    'GeometryNodeInputNamedAttribute': {
        'Geometry': [
            Attribute(fname='named_attribute',         ret_socket='attribute'),
            Attribute(fname='named_attribute_float',   ret_socket='attribute', data_type="'FLOAT'"),
            Attribute(fname='named_attribute_integer', ret_socket='attribute', data_type="'INT'"),
            Attribute(fname='named_attribute_vector',  ret_socket='attribute', data_type="'FLOAT_VECTOR'"),
            Attribute(fname='named_attribute_color',   ret_socket='attribute', data_type="'FLOAT_COLOR'"),
            Attribute(fname='named_attribute_boolean', ret_socket='attribute', data_type="'BOOLEAN'"),
            ],
        'Domain': [
            DomAttribute(fname='named_attribute',         ret_socket='attribute'),
            DomAttribute(fname='named_attribute_float',   ret_socket='attribute', data_type="'FLOAT'"),
            DomAttribute(fname='named_attribute_integer', ret_socket='attribute', data_type="'INT'"),
            DomAttribute(fname='named_attribute_vector',  ret_socket='attribute', data_type="'FLOAT_VECTOR'"),
            DomAttribute(fname='named_attribute_color',   ret_socket='attribute', data_type="'FLOAT_COLOR'"),
            DomAttribute(fname='named_attribute_boolean', ret_socket='attribute', data_type="'BOOLEAN'"),
            ],
    },
    'GeometryNodeInputNormal': {
        'Geometry': PropAttribute(fname='normal', ret_socket='normal'),
        'Domain'  : DomPropAttribute(fname='normal', ret_socket='normal'),
        'Spline'  : DomPropAttribute(fname='normal', ret_socket='normal'),
    },
    'GeometryNodeInputPosition': {
        'Geometry': PropAttribute(fname='position', ret_socket='position'),
        'Domain'  : DomPropAttribute(fname='position', ret_socket='position'),
    },
    'GeometryNodeInputRadius': {
        'Geometry'   : PropAttribute(fname='radius', ret_socket='radius'),
        'Domain'     : DomPropAttribute(fname='radius', ret_socket='radius'),
        'Spline'     : DomPropAttribute(fname='radius', ret_socket='radius'),
        'CloudPoint' : DomPropAttribute(fname='radius', ret_socket='radius'),
    },
    'GeometryNodeInputSceneTime': {
        'Float': [
            Constructor(fname='Seconds', ret_socket='seconds'),
            Constructor(fname='Frame', ret_socket='frame'),
            ]
    },

}

INSTANCES = {
    'GeometryNodeInstanceOnPoints': {
        'Instances'     : [
            Constructor(fname='InstanceOnPoints', ret_socket='instances'),
            Method(fname='on_points', ret_socket='instances', ret_classes='Instances', instance='self.data_socket'),
            ],
        'Vertex'        : DomMethod(ret_socket='instances', ret_class='Instances', points='self'),
        'ControlPoint'  : DomMethod(ret_socket='instances', ret_class='Instances', points='self'),
        'CloudPoint'    : DomMethod(ret_socket='instances', ret_class='Instances', points='self'),
    },
    'GeometryNodeInstancesToPoints': {
        'Instances': Method(fname='to_points', ret_socket='points', ret_class='Points', instances='self'),
        'Instance':  DomMethod(fname='to_points', ret_socket='points', ret_class='Points', instances='self'),
        
    },
    'GeometryNodeRealizeInstances': {
        'Instances': Method(fname='realize', ret_socket='geometry'),
    },
    'GeometryNodeRotateInstances': {
        'Instances': StackMethod(fname='rotate', instances='self'),
        'Instance':  DomStackMethod(fname='rotate', instances='self'),
    },
    'GeometryNodeScaleInstances': {
        'Instances': StackMethod(fname='set_scale', instances='self'),
        'Instance':  DomStackMethod(fname='set_scale', instances='self'),
    },
    'GeometryNodeTranslateInstances': {
        'Instances': StackMethod(fname='translate', instances='self'),
        'Instance':  DomStackMethod(fname='translate', instances='self'),
    },
    'GeometryNodeInputInstanceScale': {
        'Instances': PropAttribute(fname='scale',    ret_socket='scale'),
        'Instance':  DomPropAttribute(fname='scale', ret_socket='scale'),
    },
    'GeometryNodeInputInstanceRotation': {
        'Instances': PropAttribute(fname='rotation',    ret_socket='rotation'),
        'Instance':  DomPropAttribute(fname='rotation', ret_socket='rotation'),
    },    
}

MATERIAL = {
    'GeometryNodeReplaceMaterial': {
        'Geometry': StackMethod(geometry='self'),
    },
    'GeometryNodeInputMaterialIndex': {
        'Geometry': PropAttribute(ret_socket='material_index'),
        'Domain':   DomPropAttribute(ret_socket='material_index'),
    },
    'GeometryNodeMaterialSelection': {
        'Geometry': Attribute(ret_socket='selection'),
        'Domain':   DomAttribute(ret_socket='selection'),
    },
    'GeometryNodeSetMaterial': {
        'Geometry': StackMethod(geometry='self'),
        'Domain':   DomPropAttribute(fname='material', geometry='self', material='attr_value'),
    },
    'GeometryNodeSetMaterialIndex': {
        'Geometry': StackMethod(geometry='self'),
        'Domain':   DomStackMethod(geometry='self'),
    },
}

MESH = {
    'GeometryNodeDualMesh': {
        'Mesh': Method(ret_socket='dual_mesh', ret_class='Mesh'),
    },
    'GeometryNodeEdgePathsToCurves': {
        'Mesh': Attribute(   mesh='self', ret_socket='curves', ret_class='Curve'),
        'Edge': DomAttribute(mesh='self', ret_socket='curves', ret_class='Curve'),
    },
    'GeometryNodeEdgePathsToSelection': {
        'Mesh': Method(mesh='self', ret_socket='selection'),
    },
    'GeometryNodeExtrudeMesh': {
        'Mesh':   StackMethod(fname='extrude', mesh='self', ret_socket=('top', 'side')),
        'Face':   DomStackMethod(fname='extrude', mesh='self', ret_socket=('top', 'side'), mode="'FACES'"),
        'Edge':   DomStackMethod(fname='extrude', mesh='self', ret_socket=('top', 'side'), mode="'EDGES'"),
        'Vertex': DomStackMethod(fname='extrude', mesh='self', ret_socket=('top', 'side'), mode="'VERTICES'"),
    },
    'GeometryNodeFlipFaces': {
        'Mesh':   StackMethod(mesh='self'),
        'Face':   DomStackMethod(fname='flip', mesh='self'),
    },
    'GeometryNodeMeshBoolean': {
        'Mesh':   [
            StackMethod(mesh='self', fname='boolean_intersect',  ret_socket='intersecting_edges', operation="'INTERSECT'", first_arg=None, mesh_1=None),
            StackMethod(mesh='self', fname='boolean_union',      ret_socket='intersecting_edges', operation="'UNION'",     first_arg=None, mesh_1=None),
            StackMethod(mesh='self', fname='boolean_difference', ret_socket='intersecting_edges', operation="'DIFFERENCE'", mesh_1='self'),
            ],
    },
    'GeometryNodeMeshToCurve': {
        'Mesh': Method(   fname='to_curve', mesh='self', ret_socket='curve', ret_class='Curve'),
        'Edge': DomMethod(fname='to_curve', mesh='self', ret_socket='curve', ret_class='Curve'),
    },
    'GeometryNodeMeshToPoints': {
        'Mesh':   Method(   fname='to_points', mesh='self', ret_socket='points', ret_class='Points'),
        'Vertex': DomMethod(fname='to_points', mesh='self', ret_socket='points', ret_class='Points'),
    },
    'GeometryNodeMeshToVolume': {
        'Mesh':   Method(   fname='to_volume', mesh='self', ret_socket='volume', ret_class='Volume'),
        'Vertex': DomMethod(fname='to_volume', mesh='self', ret_socket='volume', ret_class='Volume'),
    },
    'GeometryNodeSampleNearestSurface': {
        'Mesh':   Method(mesh='self', ret_socket='value', dtype=('data_type', 'value')),
    },
    'GeometryNodeSampleUVSurface': {
        'Mesh':   Method(mesh='self', ret_socket=('value', 'is_valid'), dtype=('data_type', 'value')),
    },
    'GeometryNodeScaleElements': {
        'Mesh':   [
            StackMethod(geometry='self'),
            StackMethod(geometry='self',    fname='scale_uniform',     scale_mode="'UNIFORM'", axis=None),
            StackMethod(geometry='self',    fname='scale_single_axis', scale_mode="'SINGLE_AXIS'"),
            ],
        'Face': [
            DomStackMethod(geometry='self', fname='scale_uniform',     scale_mode="'UNIFORM'", axis=None),
            DomStackMethod(geometry='self', fname='scale_single_axis', scale_mode="'SINGLE_AXIS'"),
            ],
        'Edge': [
            DomStackMethod(geometry='self', fname='scale_uniform',     scale_mode="'UNIFORM'", axis=None),
            DomStackMethod(geometry='self', fname='scale_single_axis', scale_mode="'SINGLE_AXIS'"),
            ],
    },
    'GeometryNodeSplitEdges': {
        'Mesh': StackMethod(   mesh='self'),
        'Edge': DomStackMethod(mesh='self', fname='split'),
    },
    'GeometryNodeSubdivideMesh': {
        'Mesh': StackMethod(mesh='self', fname='subdivide'),
    },
    'GeometryNodeSubdivisionSurface': {
        'Mesh': StackMethod(mesh='self'),
    },
    'GeometryNodeTriangulate': {
        'Mesh': StackMethod(mesh='self'),
        'Face': DomStackMethod(mesh='self'),
    },
    'GeometryNodeInputMeshEdgeAngle': {
        'Edge': [
            DomPropAttribute(fname='angle', cache=True),
            DomPropAttribute(fname='unisgned_angle', cache=True, ret_socket='unsigned_angle'),
            DomPropAttribute(fname='signed_angle', cache=True, ret_socket='signed_angle'),
            ],
    },
    'GeometryNodeInputMeshEdgeNeighbors': {
        'Edge': DomPropAttribute(fname='neighbors', ret_socket='face_count'),
    },
    'GeometryNodeInputMeshEdgeVertices': {
        'Edge': [
            DomPropAttribute(fname='vertices',          cache=True),
            DomPropAttribute(fname='vertices_index',    cache=True, ret_socket=('vertex_index_1', 'vertex_index_2')),
            DomPropAttribute(fname='vertices_position', cache=True, ret_socket=('position_1', 'position_2')),
            ],
    },
    'GeometryNodeInputMeshFaceArea': {
        'Face': DomPropAttribute(fname='area'),
    },
    'GeometryNodeInputMeshFaceNeighbors': {
        'Face': [
            DomPropAttribute(fname='neighbors',               cache=True),
            DomPropAttribute(fname='neighbors_vertex_count',  cache=True, ret_socket='vertex_count'),
            DomPropAttribute(fname='neighbors_face_count',    cache=True, ret_socket='face_count'),
            ],
    },
    'GeometryNodeMeshFaceSetBoundaries': {
        'Mesh': Attribute(ret_socket='boundary_edges'),
        'Face': DomAttribute(face_set='self.selection_index', ret_socket='boundary_edges'),
    },
    'GeometryNodeInputMeshFaceIsPlanar': {
        'Mesh': Attribute(ret_socket='planar'),
        'Face': DomAttribute(fname='is_planar', ret_socket='planar'),
    },
    'GeometryNodeInputShadeSmooth': {
        'Mesh': Attribute(ret_socket='smooth'),
        'Face': DomPropAttribute(fname='shade_smooth', ret_socket='smooth'),
    },
    'GeometryNodeInputMeshIsland': {
        'Mesh': [
            PropAttribute(fname='island', cache=True),
            PropAttribute(fname='island_index', cache=True, ret_socket='island_index'),
            PropAttribute(fname='island_count', cache=True, ret_socket='island_count'),
            ],
    },
    'GeometryNodeInputShortestEdgePaths': {
        'Mesh': Attribute(ret_socket=('next_vertex_index', 'total_cost')),
    },
    'GeometryNodeInputMeshVertexNeighbors': {
        'Vertex': [
            DomPropAttribute(fname='neighbors',               cache=True),
            DomPropAttribute(fname='neighbors_vertex_count',  cache=True, ret_socket='vertex_count'),
            DomPropAttribute(fname='neighbors_face_count',    cache=True, ret_socket='face_count'),
            ],
    },
    'GeometryNodeSetShadeSmooth': {
        'Mesh': StackMethod(geometry='self'),
        'Face': [
            DomStackMethod(geometry='self'),
            DomSetter(fname='shade_smooth', geometry='self'),
            ],
    },
}

MESH_PRIMITIVES = {
    'GeometryNodeMeshCone': {
        'Mesh': Static(fname='Cone', ret_socket=('mesh', 'top', 'bottom', 'side'), ret_class=('Mesh', None, None, None))
    },
    'GeometryNodeMeshCube': {
        'Mesh': Constructor(fname='Cube', ret_socket='mesh')
    },
    'GeometryNodeMeshCylinder': {
        'Mesh': Static(fname='Cylinder', ret_socket=('mesh', 'top', 'bottom', 'side'), ret_class=('Mesh', None, None, None))
    },
    'GeometryNodeMeshGrid': {
        'Mesh': Constructor(fname='Grid', ret_socket='mesh')
    },
    'GeometryNodeMeshIcoSphere': {
        'Mesh': Constructor(fname='IcoSphere', ret_socket='mesh')
    },
    'GeometryNodeMeshCircle': {
        'Mesh': Constructor(fname='Circle', ret_socket='mesh')
    },
    'GeometryNodeMeshLine': {
        'Mesh': [
            Constructor(fname='Line',                    ret_socket='mesh'),
            Constructor(fname='LineEndPoints',           ret_socket='mesh', mode='END_POINTS', count_mode="'TOTAL'",      resolution=None,
                        arg_rename={'offset': 'end_location'}),
            Constructor(fname='LineOffset',              ret_socket='mesh', mode='OFFSET',     count_mode="'TOTAL'",      resolution=None),
            Constructor(fname='LineEndPointsResolution', ret_socket='mesh', mode='END_POINTS', count_mode="'RESOLUTION'", count=None,
                        arg_rename={'offset': 'end_location'}),
            Constructor(fname='LineOffsetResolution',    ret_socket='mesh', mode='OFFSET',     count_mode="'RESOLUTION'", count=None),
            ],
    },
    'GeometryNodeMeshUVSphere': {
        'Mesh': Constructor(fname='Circle', ret_socket='mesh'),
    },
}

POINT = {
    'GeometryNodeDistributePointsInVolume': {
        'Volume': [
            Method(volume='self', ret_socket='points', ret_class='Points', fname='distribute_points',),
            Method(volume='self', ret_socket='points', ret_class='Points', fname='distribute_points_random', mode="'DENSITY_RANDOM'", spacing=None, threshold=None),
            Method(volume='self', ret_socket='points', ret_class='Points', fname='distribute_points_grid',   mode="'DENSITY_GRID'", density=None, seed=None),
            ],
    },
    'GeometryNodeDistributePointsOnFaces': {
        'Mesh': Method(mesh='self', ret_socket=('points', 'normal', 'rotation'), ret_class=('Points', None, None), fname='distribute_points_on_faces',),
        'Face': [
            DomMethod(mesh='self', ret_socket=('points', 'normal', 'rotation'), ret_class=('Points', None, None),
                fname='distribute_points_random', distribute_method="'RANDOM'", distance_min=None, density_max=None, density_factor=None),
            DomMethod(mesh='self', ret_socket=('points', 'normal', 'rotation'), ret_class=('Points', None, None),
                fname='distribute_points_poisson', distribute_method="'POISSON'", density=None),
            ]
    },
    'GeometryNodePoints': {
        'Points': Constructor(fname='Points', ret_socket='geometry'),
    },
    'GeometryNodePointsToVertices': {
        'Points':     Method(fname='to_vertices', ret_socket='mesh', ret_class='Mesh'),
        'CloudPoint': DomMethod(fname='to_vertices', ret_socket='mesh', ret_class='Mesh'),
    },
    'GeometryNodePointsToVolume': {
        'Points':  [
            Method(fname='to_volume',        points='self', ret_socket='volume', ret_class='Volume'),
            Method(fname='to_volume_size',   points='self', ret_socket='volume', ret_class='Volume', resolution_mode="'VOXEL_SIZE'", voxel_amount=None),
            Method(fname='to_volume_amount', points='self', ret_socket='volume', ret_class='Volume', resolution_mode="'VOXEL_AMOUNT'", voxel_size=None),
            ]
    },
    'GeometryNodeSetPointRadius': {
        'Points': StackMethod(points='self'),
        'CloudPoint': DomSetter(fname='radius', points='self', radius='attr_value'),
        
    },
}

STRING = {
    'GeometryNodeStringJoin': {
        'function': Function(ret_socket='string'),
        'String':   Method(fname='join', first_arg=None, ret_socket='string'),
    },
    'FunctionNodeReplaceString': {
        'function': Function(ret_socket='string'),
        'String':   Method(fname='replace', string='self', ret_socket='string'),
    },
    'FunctionNodeSliceString': {
        'function': Function(ret_socket='string'),
        'String':   Method(fname='slice', string='self', ret_socket='string'),
    },
    'FunctionNodeStringLength': {
        'function': Function(ret_socket='length'),
        'String':   Property(fname='length', string='self', ret_socket='length'),
    },
    'GeometryNodeStringToCurves': {
        'function': Function(ret_socket=('curve_instances', 'line', 'pivot_point'), ret_class=('Instances', None, None)),
        'String':   Method(fname='to_curves', ret_socket=('curve_instances', 'line', 'pivot_point'), ret_class=('Instances', None, None)),
    },
    'FunctionNodeValueToString': {
        'function' : Function(ret_socket='string'),
        'Float'    : Method(fname='to_string', value='self', ret_socket='string'),
        'Integer'  : Method(fname='to_string', value='self', ret_socket='string', decimals=0),
    },
    'FunctionNodeInputSpecialCharacters': {
        'String': [
            Static(fname='LineBreak', ret_socket='line_break'),
            Static(fname='Tab', ret_socket='tab'),
            ],
    },
}

TEXTURE = {
    'ShaderNodeTexBrick': {
        'Texture': Static(fname='brick', ret_socket=('color', 'fac')),
    },
    'ShaderNodeTexChecker': {
        'Texture': Static(fname='checker', ret_socket=('color', 'fac')),
    },
    'ShaderNodeTexGradient': {
        'Texture': [
            Static(fname='gradient',                  ret_socket=('color', 'fac')),
            Static(fname='gradient_linear',           ret_socket=('color', 'fac'), gradient_type="'LINEAR'"),
            Static(fname='gradient_quadratic',        ret_socket=('color', 'fac'), gradient_type="'QUADRATIC'"),
            Static(fname='gradient_easing',           ret_socket=('color', 'fac'), gradient_type="'EASING'"),
            Static(fname='gradient_diagonal',         ret_socket=('color', 'fac'), gradient_type="'DIAGONAL'"),
            Static(fname='gradient_spherical',        ret_socket=('color', 'fac'), gradient_type="'SPHERICAL'"),
            Static(fname='gradient_quadratic_sphere', ret_socket=('color', 'fac'), gradient_type="'QUADRATIC_SPHERE'"),
            Static(fname='gradient_radial',           ret_socket=('color', 'fac'), gradient_type="'RADIAL'"),
            ],
    },
    'GeometryNodeImageTexture': {
        'Texture': Static(fname='image', ret_socket=('color', 'alpha')),
        'Image'  : Method(fname='texture', image='self', ret_socket=('color', 'alpha')),
    },
    'ShaderNodeTexMagic': {
        'Texture': Static(fname='magic', ret_socket=('color', 'fac')),
    },
    'ShaderNodeTexMusgrave': {
        'Texture': Static(fname='musgrave', ret_socket='fac'),
    },
    'ShaderNodeTexNoise': {
        'Texture': [
            Static(fname='noise',    ret_socket=('color', 'fac')),
            Static(fname='noise_1D', ret_socket=('color', 'fac'), noise_dimensions="'1D'", vector=None),
            Static(fname='noise_2D', ret_socket=('color', 'fac'), noise_dimensions="'2D'", w=None),
            Static(fname='noise_3D', ret_socket=('color', 'fac'), noise_dimensions="'3D'", w=None),
            Static(fname='noise_4D', ret_socket=('color', 'fac'), noise_dimensions="'4D'"),
            ],
    },
    'ShaderNodeTexVoronoi': {
        'Texture': [
            Static(fname='voronoi',    ret_socket=('distance', 'color', 'position', 'w')),
            Static(fname='voronoi_1D', ret_socket=('distance', 'color', 'w'),             vector=None),
            Static(fname='voronoi_2D', ret_socket=('distance', 'color', 'position'),      w=None),
            Static(fname='voronoi_3D', ret_socket=('distance', 'color', 'position'),      w=None),
            Static(fname='voronoi_4D', ret_socket=('distance', 'color', 'position', 'w')),
            ],
    },
    'ShaderNodeTexWave': {
        'Texture': [
            Static(fname='wave', ret_socket=('color', 'fac')),
            Static(fname='wave_bands', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction=None,
                          arg_rename={'bands_direction': 'direction'}),
            Static(fname='wave_rings', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction=None,
                          arg_rename={'rings_direction': 'direction'}),
        
            Static(fname='wave_bands_sine', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction=None, wave_profile="'SIN'",
                          arg_rename={'bands_direction': 'direction'}),
            Static(fname='wave_bands_saw', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction=None, wave_profile="'SAW'",
                          arg_rename={'bands_direction': 'direction'}),
            Static(fname='wave_bands_triangle', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction=None, wave_profile="'TRIANGLE'",
                          arg_rename={'bands_direction': 'direction'}),

            Static(fname='wave_rings_sine', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction=None, wave_profile="'SIN'",
                          arg_rename={'rings_direction': 'direction'}),
            Static(fname='wave_rings_saw', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction=None, wave_profile="'SAW'",
                          arg_rename={'rings_direction': 'direction'}),
            Static(fname='wave_rings_triangle', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction=None, wave_profile="'TRIANGLE'",
                          arg_rename={'rings_direction': 'direction'}),
            ],
    },
    'ShaderNodeTexWhiteNoise': {
        'Texture': [
            Static(fname='white_noise',    ret_socket=('value', 'color')),
            Static(fname='white_noise_1D', ret_socket=('value', 'color'), noise_dimensions = "'1D'", vector=None),
            Static(fname='white_noise_2D', ret_socket=('value', 'color'), noise_dimensions = "'2D'", w=None),
            Static(fname='white_noise_3D', ret_socket=('value', 'color'), noise_dimensions = "'3D'", w=None),
            Static(fname='white_noise_4D', ret_socket=('value', 'color'), noise_dimensions = "'3D'"),
            ],
    },
}

UTILITIES = {
    'GeometryNodeAccumulateField': {
        'Domain': DomAttribute(ret_socket=('leading', 'trailing', 'total'), dtype=('data_type', 'value')),
    },
    'FunctionNodeAlignEulerToVector': {
        'function': Function(ret_socket='rotation'),
        'Vector': StackMethod(rotation='self'),
    },
    'FunctionNodeBooleanMath': {
        'function': [
            Function(fname='b_and', ret_socket='boolean', operation='AND'),
            Function(fname='b_or',  ret_socket='boolean', operation='OR'),
            Function(fname='b_not', ret_socket='boolean', operation='NOT', boolean1=None),
            Function(fname='nand',  ret_socket='boolean', operation='NAND'),
            Function(fname='nor',   ret_socket='boolean', operation='NOR'),
            Function(fname='xnor',  ret_socket='boolean', operation='XNOR'),
            Function(fname='xor',   ret_socket='boolean', operation='XOR'),
            Function(fname='imply', ret_socket='boolean', operation='IMPLY'),
            Function(fname='nimply',ret_socket='boolean', operation='NIMPLY'),
            ],
        'Boolean': [
            Method(fname='b_and',   boolean0='self', ret_socket='boolean', operation='AND'),
            Method(fname='b_or',    boolean0='self', ret_socket='boolean', operation='OR'),
            Method(fname='b_not',   boolean0='self', ret_socket='boolean', operation='NOT', boolean1=None),
            Method(fname='nand',    boolean0='self', ret_socket='boolean', operation='NAND'),
            Method(fname='nor',     boolean0='self', ret_socket='boolean', operation='NOR'),
            Method(fname='xnor',    boolean0='self', ret_socket='boolean', operation='XNOR'),
            Method(fname='xor',     boolean0='self', ret_socket='boolean', operation='XOR'),
            Method(fname='imply',   boolean0='self', ret_socket='boolean', operation='IMPLY'),
            Method(fname='nimply',  boolean0='self', ret_socket='boolean', operation='NIMPLY'),
            ],
    },
    'ShaderNodeClamp': {
        'function': [
            Function(ret_socket='result'),
            Function(ret_socket='result', fname='clamp_min_max', clamp_type="'MINMAX'"),
            Function(ret_socket='result', fname='clamp_range',   clamp_type="'RANGE'"),
            ],
        'Float': [
            Method(ret_socket='result', value='self'),
            Method(ret_socket='result', value='self', fname='clamp_min_max', clamp_type="'MINMAX'"),
            Method(ret_socket='result', value='self', fname='clamp_range',   clamp_type="'RANGE'"),
            ],
    },
    'FunctionNodeCompare': {
        'function': Function(ret_socket='result'),
        'Float': [
            Method(a='self', ret_socket='result', data_type="'FLOAT'", c=None, angle=None, mode="'ELEMENT'"),
            Method(a='self', ret_socket='result', data_type="'FLOAT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'FLOAT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'FLOAT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'FLOAT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'FLOAT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'FLOAT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='not_equal', operation="'NOT_EQUAL'"),
            ],
        'Integer': [
            Method(a='self', ret_socket='result', data_type="'INTEGER'", c=None, angle=None, mode="'ELEMENT'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INTEGER'", c=None, angle=None, mode="'ELEMENT'",
                   fname='less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INTEGER'", c=None, angle=None, mode="'ELEMENT'",
                   fname='less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INTEGER'", c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INTEGER'", c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INTEGER'", c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INTEGER'", c=None, angle=None, mode="'ELEMENT'",
                   fname='not_equal', operation="'NOT_EQUAL'", epsilon=None),
            ],
        'String': [
            Method(a='self', ret_socket='result', data_type="'STRING'", c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'STRING'", c=None, angle=None, mode="'ELEMENT'",
                   fname='not_equal', operation="'NOT_EQUAL'", epsilon=None),
            ],
        'Vector': [
            Method(a='self', ret_socket='result', data_type="'VECTOR'"),

            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_not_equal', operation="'NOT_EQUAL'"),

            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'LENGTH'",
                   fname='length_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'LENGTH'",
                   fname='length_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'LENGTH'",
                   fname='length_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'LENGTH'",
                   fname='length_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'LENGTH'",
                   fname='length_equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'LENGTH'",
                   fname='length_not_equal', operation="'NOT_EQUAL'"),

            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'AVERAGE'",
                   fname='average_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'AVERAGE'",
                   fname='average_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'AVERAGE'",
                   fname='average_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'AVERAGE'",
                   fname='average_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'AVERAGE'",
                   fname='average_equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, angle=None, mode="'AVERAGE'",
                   fname='average_not_equal', operation="'NOT_EQUAL'"),
            
            Method(a='self', ret_socket='result', data_type="'VECTOR'", angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_not_equal', operation="'NOT_EQUAL'"),
            
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, mode="'DIRECTION'",
                   fname='direction_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, mode="'DIRECTION'",
                   fname='direction_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, mode="'DIRECTION'",
                   fname='direction_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, mode="'DIRECTION'",
                   fname='direction_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, mode="'DIRECTION'",
                   fname='direction_equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'VECTOR'", c=None, mode="'DIRECTION'",
                   fname='direction_not_equal', operation="'NOT_EQUAL'"),
            ],
        
        'Color': [
            Method(a='self', ret_socket='result', data_type="'COLOR'", c=None, angle=None, mode="'ELEMENT'"),
            Method(a='self', ret_socket='result', data_type="'COLOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='darker', operation="'DARKER'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'COLOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='brighter', operation="'BRIGHTER'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'COLOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'COLOR'", c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'"),
            ],
    },
    'GeometryNodeFieldAtIndex': {
        'Geometry': Attribute(ret_socket='value', dtype=('data_type', 'value')),
        'Domain'  : DomAttribute(ret_socket='value', dtype=('data_type', 'value')),
    },
    'ShaderNodeFloatCurve': {
        'Float' : Method(value='self', ret_socket='value'),
    },
    'FunctionNodeFloatToInt': {
        'Float' : [
            Method(float='self', ret_socket='integer', fname='to_integer'),
            Method(float='self', ret_socket='integer', fname='round',    rounding_mode="'ROUND'"),
            Method(float='self', ret_socket='integer', fname='floor',    rounding_mode="'FLOOR'"),
            Method(float='self', ret_socket='integer', fname='ceiling',  rounding_mode="'CEILING'"),
            Method(float='self', ret_socket='integer', fname='truncate', rounding_mode="'TRUNCATE'"),
            ],
    },
    'ShaderNodeMapRange': {
        'Float': [
            Method(value='self', ret_socket='result', vector=None, data_type="'FLOAT'"),
            Method(value='self', ret_socket='result', vector=None, data_type="'FLOAT'", fname='map_range_linear',   interpolation_type="'LINEAR'", steps=None),
            Method(value='self', ret_socket='result', vector=None, data_type="'FLOAT'", fname='map_range_stepped',  interpolation_type="'STEPPED'"),
            Method(value='self', ret_socket='result', vector=None, data_type="'FLOAT'", fname='map_range_smooth',   interpolation_type="'SMOOTHSTEP'", steps=None),
            Method(value='self', ret_socket='result', vector=None, data_type="'FLOAT'", fname='map_range_smoother', interpolation_type="'SMOOTHERSTEP'", steps=None),
            ],
        'Vector': [
            Method(vector='self', ret_socket='vector', value=None, data_type="'FLOAT_VECTOR'"),
            Method(vector='self', ret_socket='vector', value=None, data_type="'FLOAT_VECTOR'", fname='map_range_linear',   interpolation_type="'LINEAR'", steps=None),
            Method(vector='self', ret_socket='vector', value=None, data_type="'FLOAT_VECTOR'", fname='map_range_stepped',  interpolation_type="'STEPPED'"),
            Method(vector='self', ret_socket='vector', value=None, data_type="'FLOAT_VECTOR'", fname='map_range_smooth',   interpolation_type="'SMOOTHSTEP'", steps=None),
            Method(vector='self', ret_socket='vector', value=None, data_type="'FLOAT_VECTOR'", fname='map_range_smoother', interpolation_type="'SMOOTHERSTEP'", steps=None),
            ],
    },
    'ShaderNodeMath': {
        'function': [
            Function(ret_socket='value'),
            
            Function(ret_socket='value', fname='add',             operation="'ADD'",          value2=None),
            Function(ret_socket='value', fname='subtract',        operation="'SUBTRACT'",     value2=None),
            Function(ret_socket='value', fname='sub',             operation="'SUBTRACT'",     value2=None),
            Function(ret_socket='value', fname='multiply',        operation="'MULTIPLY'",     value2=None),
            Function(ret_socket='value', fname='mul',             operation="'MULTIPLY'",     value2=None),
            Function(ret_socket='value', fname='divide',          operation="'DIVIDE'",       value2=None),
            Function(ret_socket='value', fname='div',             operation="'DIVIDE'",       value2=None),
            Function(ret_socket='value', fname='multiply_add',    operation="'MULTIPLY_ADD'", arg_rename={'value0': 'value', 'value1': 'multiplier', 'value2': 'addend'}),
            Function(ret_socket='value', fname='mul_add',         operation="'MULTIPLY_ADD'", arg_rename={'value0': 'value', 'value1': 'multiplier', 'value2': 'addend'}),

            Function(ret_socket='value', fname='power',           operation="'POWER'",        arg_rename={'value0': 'base', 'value1': 'exponent'}, value2=None),
            Function(ret_socket='value', fname='logarithm',       operation="'LOGARITHM'",    arg_rename={'value0': 'value', 'value1': 'base'}, value2=None),
            Function(ret_socket='value', fname='log',             operation="'LOGARITHM'",    arg_rename={'value0': 'value', 'value1': 'base'}, value2=None),
            Function(ret_socket='value', fname='sqrt',            operation="'SQRT'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='inverse_sqrt',    operation="'INVERSE_SQRT'", arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='absolute',        operation="'ABSOLUTE'",     arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='abs',             operation="'ABSOLUTE'",     arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='exponent',        operation="'EXPONENT'",     arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='exp',             operation="'EXPONENT'",     arg_rename={'value0': 'value'}, value1=None, value2=None),

            Function(ret_socket='value', fname='minimum',         operation="'MINIMUM'",      value2=None),
            Function(ret_socket='value', fname='min',             operation="'MINIMUM'",      value2=None),
            Function(ret_socket='value', fname='maximum',         operation="'MAXIMUM'",      value2=None),
            Function(ret_socket='value', fname='max',             operation="'MAXIMUM'",      value2=None),
            Function(ret_socket='value', fname='math_less_than',    operation="'LESS_THAN'",    arg_rename={'value0': 'value', 'value1': 'threshold'}, value2=None),
            Function(ret_socket='value', fname='math_greater_than', operation="'GREATER_THAN'", arg_rename={'value0': 'value', 'value1': 'threshold'}, value2=None),
            Function(ret_socket='value', fname='sign',            operation="'SIGN'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='math_compare',    operation="'COMPARE'",      arg_rename={'value2': 'epsilon'}),
            Function(ret_socket='value', fname='smooth_minimum',  operation="'SMOOTH_MIN'",   arg_rename={'value2': 'distance'}),
            Function(ret_socket='value', fname='smooth_maximum',  operation="'SMOOTH_MAX'",   arg_rename={'value2': 'distance'}),
            
            Function(ret_socket='value', fname='math_round',      operation="'ROUND'",        arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='math_floor',      operation="'FLOOR'",        arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='math_ceil',       operation="'CEIL'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='math_truncate',   operation="'TRUNC'",        arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='math_trun',       operation="'TRUNC'",        arg_rename={'value0': 'value'}, value1=None, value2=None),
            
            Function(ret_socket='value', fname='fraction',        operation="'FRACT'",        arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='modulo',          operation="'MODULO'",       value2=None),

            Function(ret_socket='value', fname='wrap',            operation="'WRAP'",         arg_rename={'value0': 'value', 'value1': 'max', 'value2': 'min'}),
            Function(ret_socket='value', fname='snap',            operation="'SNAP'",         arg_rename={'value0': 'value', 'value1': 'increment'}, value2=None),
            Function(ret_socket='value', fname='ping_pong',       operation="'PINGPONG'",     arg_rename={'value0': 'value', 'value1': 'scale'}, value2=None),

            Function(ret_socket='value', fname='sine',            operation="'SINE'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='sin',             operation="'SINE'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='cosine',          operation="'COSINE'",       arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='cos',             operation="'COSINE'",       arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='tangent',         operation="'TANGENT'",      arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='tan',             operation="'TANGENT'",      arg_rename={'value0': 'value'}, value1=None, value2=None),

            Function(ret_socket='value', fname='arcsine',         operation="'ARCSINE'",      arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='arcsin',          operation="'ARCSINE'",      arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='arccosine',       operation="'ARCCOSINE'",    arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='arccos',          operation="'ARCCOSINE'",    arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='arctangent',      operation="'ARCTANGENT'",   arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='arctan',          operation="'ARCTANGENT'",   arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='arctan2',         operation="'ARCTAN2'",      value2=None),
            
            Function(ret_socket='value', fname='sinh',            operation="'SINH'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='cosh',            operation="'COSH'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='tanh',            operation="'TANH'",         arg_rename={'value0': 'value'}, value1=None, value2=None),
            
            Function(ret_socket='value', fname='to_radians',      operation="'RADIANS'",      arg_rename={'value0': 'value'}, value1=None, value2=None),
            Function(ret_socket='value', fname='to_degrees',      operation="'DEGREES'",      arg_rename={'value0': 'value'}, value1=None, value2=None),
            ],            
        
        ('Integer', 'Float') : [
            Method(ret_socket='value', fname='add',             operation="'ADD'",          value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='subtract',        operation="'SUBTRACT'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='sub',             operation="'SUBTRACT'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='multiply',        operation="'MULTIPLY'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='mul',             operation="'MULTIPLY'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='divide',          operation="'DIVIDE'",       value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='div',             operation="'DIVIDE'",       value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='multiply_add',    operation="'MULTIPLY_ADD'", value0='self', arg_rename={'value1': 'multiplier', 'value2': 'addend'}),
            Method(ret_socket='value', fname='mul_add',         operation="'MULTIPLY_ADD'", value0='self', arg_rename={'value1': 'multiplier', 'value2': 'addend'}),

            Method(ret_socket='value', fname='power',           operation="'POWER'",        value0='self', arg_rename={'value1': 'exponent'}, value2=None),
            Method(ret_socket='value', fname='logarithm',       operation="'LOGARITHM'",    value0='self', arg_rename={'value1': 'base'}, value2=None),
            Method(ret_socket='value', fname='log',             operation="'LOGARITHM'",    value0='self', arg_rename={'value1': 'base'}, value2=None),
            Method(ret_socket='value', fname='sqrt',            operation="'SQRT'",         value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='inverse_sqrt',    operation="'INVERSE_SQRT'", value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='absolute',        operation="'ABSOLUTE'",     value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='abs',             operation="'ABSOLUTE'",     value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='exponent',        operation="'EXPONENT'",     value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='exp',             operation="'EXPONENT'",     value0='self', value1=None, value2=None),

            Method(ret_socket='value', fname='minimum',         operation="'MINIMUM'",      value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='min',             operation="'MINIMUM'",      value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='maximum',         operation="'MAXIMUM'",      value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='max',             operation="'MAXIMUM'",      value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='math_less_than',    operation="'LESS_THAN'",    value0='self', arg_rename={'value1': 'threshold'}, value2=None),
            Method(ret_socket='value', fname='math_greater_than', operation="'GREATER_THAN'", value0='self', arg_rename={'value1': 'threshold'}, value2=None),
            Method(ret_socket='value', fname='sign',            operation="'SIGN'",         value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='math_compare',    operation="'COMPARE'",      value0='self', arg_rename={'value1': 'value', 'value2': 'epsilon'}),
            Method(ret_socket='value', fname='smooth_minimum',  operation="'SMOOTH_MIN'",   value0='self', arg_rename={'value1': 'value', 'value2': 'distance'}),
            Method(ret_socket='value', fname='smooth_maximum',  operation="'SMOOTH_MAX'",   value0='self', arg_rename={'value1': 'value', 'value2': 'distance'}),
            
            Method(ret_socket='value', fname='math_round',      operation="'ROUND'",        value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='math_floor',      operation="'FLOOR'",        value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='math_ceil',       operation="'CEIL'",         value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='math_truncate',   operation="'TRUNC'",        value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='math_trunc',      operation="'TRUNC'",        value0='self', value1=None, value2=None),
            
            Method(ret_socket='value', fname='fraction',        operation="'FRACT'",        value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='fact',            operation="'FRACT'",        value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='modulo',          operation="'MODULO'",       value0='self', arg_rename={'value1': 'value'}, value2=None),

            Method(ret_socket='value', fname='wrap',            operation="'WRAP'",         value0='self', arg_rename={'value1': 'max', 'value2': 'min'}),
            Method(ret_socket='value', fname='snap',            operation="'SNAP'",         value0='self', arg_rename={'value1': 'increment'}, value2=None),
            Method(ret_socket='value', fname='ping_pong',       operation="'PINGPONG'",     value0='self', arg_rename={'value1': 'scale'}, value2=None),

            Method(ret_socket='value', fname='sine',            operation="'SINE'",         value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='sin',             operation="'SINE'",         value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='cosine',          operation="'COSINE'",       value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='cos',             operation="'COSINE'",       value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='tangent',         operation="'TANGENT'",      value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='tan',             operation="'TANGENT'",      value0='self', arg_rename={'value1': 'value'}, value2=None),

            Method(ret_socket='value', fname='arcsine',         operation="'ARCSINE'",      value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arcsin',          operation="'ARCSINE'",      value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arccosine',       operation="'ARCCOSINE'",    value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arccos',          operation="'ARCCOSINE'",    value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arctangent',      operation="'ARCTANGENT'",   value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arctan',          operation="'ARCTANGENT'",   value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arctan2',         operation="'ARCTAN2'",      value0='self', value2=None),
            
            Method(ret_socket='value', fname='sinh',            operation="'SINH'",         value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='cosh',            operation="'COSH'",         value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='tanh',            operation="'TANH'",         value0='self', arg_rename={'value1': 'value'}, value2=None),
            
            Method(ret_socket='value', fname='to_radians',      operation="'RADIANS'",      value0='self', value1=None, value2=None),
            Method(ret_socket='value', fname='to_degrees',      operation="'DEGREES'",      value0='self', value1=None, value2=None),
            ],
    },
    'FunctionNodeRandomValue': {
        'function': [
            Function(ret_socket='value', fname='random_float',   data_type="'FLOAT'",        probability=None),
            Function(ret_socket='value', fname='random_integer', data_type="'INT'",          probability=None),
            Function(ret_socket='value', fname='random_vector',  data_type="'FLOAT_VECTOR'", probability=None),
            Function(ret_socket='value', fname='random_boolean', data_type="'BOOLEAN'",      min=None, max=None),
            ],
        'Geometry': [
            Attribute(ret_socket='value', fname='random_float',   data_type="'FLOAT'",        probability=None),
            Attribute(ret_socket='value', fname='random_integer', data_type="'INT'",          probability=None),
            Attribute(ret_socket='value', fname='random_vector',  data_type="'FLOAT_VECTOR'", probability=None),
            Attribute(ret_socket='value', fname='random_boolean', data_type="'BOOLEAN'",      min=None, max=None),
            ],
        'Domain': [
            DomAttribute(ret_socket='value', fname='random_float',   data_type="'FLOAT'",        probability=None),
            DomAttribute(ret_socket='value', fname='random_integer', data_type="'INT'",          probability=None),
            DomAttribute(ret_socket='value', fname='random_vector',  data_type="'FLOAT_VECTOR'", probability=None),
            DomAttribute(ret_socket='value', fname='random_boolean', data_type="'BOOLEAN'",      min=None, max=None),
            ],
        
    },
    'FunctionNodeRotateEuler': {
        'function': [
            Function(fname='rotate_euler',      ret_socket='rotation', type='EULER', axis=None, angle=None),
            Function(fname='rotate_axis_angle', ret_socket='rotation', type='AXIS_ANGLE', rotate_by=None),
            ],
        'Rotation': [
            Constructor(fname='Euler',     ret_socket='rotation', type='EULER',      axis=None, angle=None),
            Constructor(fname='AxisAngle', ret_socket='rotation', type='AXIS_ANGLE', rotate_by=None),
            Method(fname='rotate_euler',      ret_socket='rotation', rotation='self', type='EULER', axis=None, angle=None),
            Method(fname='rotate_axis_angle', ret_socket='rotation', rotation='self', type='AXIS_ANGLE', rotate_by=None),
            ],
    },
    'GeometryNodeSwitch': {
        'function': [
            Function(ret_socket='output'),
            Function(ret_socket='output', fname='switch_float',      input_type="'FLOAT'"),
            Function(ret_socket='output', fname='switch_integer',    input_type="'INT'"),
            Function(ret_socket='output', fname='switch_boolean',    input_type="'BOOLEAN'"),
            Function(ret_socket='output', fname='switch_vector',     input_type="'VECTOR'"),
            Function(ret_socket='output', fname='switch_string',     input_type="'STRING'"),
            Function(ret_socket='output', fname='switch_color',      input_type="'RGBA'"),
            Function(ret_socket='output', fname='switch_object',     input_type="'OBJECT'"),
            Function(ret_socket='output', fname='switch_image',      input_type="'IMAGE'"),
            Function(ret_socket='output', fname='switch_geometry',   input_type="'GEOMETRY'"),
            Function(ret_socket='output', fname='switch_collection', input_type="'COLLECTION'"),
            Function(ret_socket='output', fname='switch_texture',    input_type="'TEXTURE'"),
            Function(ret_socket='output', fname='switch_material',   input_type="'MATERIAL'"),
            ],
        'Float':      Method(false='self', ret_socket='output', input_type="'FLOAT'"),
        'Integer':    Method(false='self', ret_socket='output', input_type="'INT'"),
        'Boolean':    Method(false='self', ret_socket='output', input_type="'BOOLEAN'"),
        'Vector':     Method(false='self', ret_socket='output', input_type="'VECTOR'"),
        'String':     Method(false='self', ret_socket='output', input_type="'STRING'"),
        'Color':      Method(false='self', ret_socket='output', input_type="'RGBA'"),
        'Object':     Method(false='self', ret_socket='output', input_type="'OBJECT'"),
        'Image':      Method(false='self', ret_socket='output', input_type="'IMAGE'"),
        'Geometry':   Method(false='self', ret_socket='output', input_type="'GEOMETRY'"),
        'Collection': Method(false='self', ret_socket='output', input_type="'COLLECTION'"),
        'Texture':    Method(false='self', ret_socket='output', input_type="'TEXTURE'"),
        'Material':   Method(false='self', ret_socket='output', input_type="'MATERIAL'"),
    },
}

UV= {
    'GeometryNodeUVPackIslands': {
        'Mesh': Attribute(ret_socket='uv'),
        'Face': DomAttribute(ret_socket='uv'),
    },
    'GeometryNodeUVUnwrap': {
        'Mesh': Attribute(ret_socket='uv'),
        'Face': DomAttribute(ret_socket='uv'),
    },
}

VECTOR = {
    'ShaderNodeCombineXYZ': {
        'Vector': Constructor(fname='Combine', ret_socket='vector'),
    },
    'ShaderNodeSeparateXYZ': {
        'Vector': [
            Method(fname='separate', cache=True, vector='self'),
            Property(fname='x', cache=True, vector='self', ret_socket='x'),
            Property(fname='y', cache=True, vector='self', ret_socket='y'),
            Property(fname='z', cache=True, vector='self', ret_socket='z'),
            ],
    },
    'ShaderNodeVectorCurve': {
        'Vector': Method(fname='curves', ret_socket='vector', vector='self'),
    },
    'ShaderNodeVectorMath': {
        'Vector': [
            Method(ret_socket='vector', fname='add',             operation="'ADD'",           vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='subtract',        operation="'SUBTRACT'",      vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='sub',             operation="'SUBTRACT'",      vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='multiply',        operation="'MULTIPLY'",      vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='mul',             operation="'MULTIPLY'",      vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='divide',          operation="'DIVIDE'",        vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='div',             operation="'DIVIDE'",        vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='multiply_add',    operation="'MULTIPLY_ADD'",  vector0='self', arg_rename={'vector1': 'multiplier', 'vector2':'addend'}, scale=None),
            Method(ret_socket='vector', fname='mul_add',         operation="'MULTIPLY_ADD'",  vector0='self', arg_rename={'vector1': 'multiplier', 'vector2':'addend'}, scale=None),

            Method(ret_socket='vector', fname='cross_product',   operation="'CROSS_PRODUCT'", vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='cross',           operation="'CROSS_PRODUCT'", vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='project',         operation="'PROJECT'",       vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='reflect',         operation="'REFLECT'",       vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='refract',         operation="'REFRACT'",       vector0='self', arg_rename={'vector1': 'vector', 'scale':'ior'}, vector2=None),
            Method(ret_socket='vector', fname='face_forward',    operation="'FACEFORWARD'",   vector0='self', arg_rename={'vector1': 'incident', 'vector2':'reference'}, scale=None),
            Method(ret_socket='value',  fname='dot_product',     operation="'DOT_PRODUCT'",   vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='value',  fname='dot',             operation="'DOT_PRODUCT'",   vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            
            Method(ret_socket='value',  fname='distance',        operation="'DISTANCE'",      vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Property(ret_socket='value',  fname='length',        operation="'LENGTH'",        vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='scale',           operation="'SCALE'",         vector0='self', vector1=None, vector2=None),
            
            Method(ret_socket='vector', fname='normalize',       operation="'NORMALIZE'",     vector0='self', vector1=None, vector2=None, scale=None),
            
            Method(ret_socket='vector', fname='absolute',        operation="'ABSOLUTE'",      vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='abs',             operation="'ABSOLUTE'",      vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='minimum',         operation="'MINIMUM'",       vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='min',             operation="'MINIMUM'",       vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='maximum',         operation="'MAXIMUM'",       vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='max',             operation="'MAXIMUM'",       vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='floor',           operation="'FLOOR'",         vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='ceil',            operation="'CEIL'",          vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='fraction',        operation="'FRACTION'",      vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='fract',           operation="'FRACTION'",      vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='modulo',          operation="'MODULO'",        vector0='self', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='wrap',            operation="'WRAP'",          vector0='self', arg_rename={'vector1': 'max', 'vector2':'min'}, scale=None),
            Method(ret_socket='vector', fname='snap',            operation="'SNAP'",          vector0='self', arg_rename={'vector1': 'increment'}, vector2=None, scale=None),
            
            Method(ret_socket='vector', fname='sine',            operation="'SINE'",          vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='sin',             operation="'SINE'",          vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='cosine',          operation="'COSINE'",        vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='cos',             operation="'COSINE'",        vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='tangent',         operation="'TANGENT'",       vector0='self', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='tan',             operation="'TANGENT'",       vector0='self', vector1=None, vector2=None, scale=None),            
            ],
    },
    'ShaderNodeVectorRotate': {
        'Vector' : [
            #rotation_type (str): 'AXIS_ANGLE' in [AXIS_ANGLE, X_AXIS, Y_AXIS, Z_AXIS, EULER_XYZ]
            Method(ret_socket='vector', vector='self', fname='rotate_euler',     rotation_type= "'EULER_XYZ'",  axis=None, angle=None),
            Method(ret_socket='vector', vector='self', fname='rotate_axis_angle', rotation_type="'AXIS_ANGLE'", rotation=None),
            Method(ret_socket='vector', vector='self', fname='rotate_x',          rotation_type="'X_AXIS'",     rotation=None, axis=None),
            Method(ret_socket='vector', vector='self', fname='rotate_y',          rotation_type="'Y_AXIS'",     rotation=None, axis=None),
            Method(ret_socket='vector', vector='self', fname='rotate_z',          rotation_type="'Z_AXIS'",     rotation=None, axis=None),
            ],
    },
}

VOLUME = {
    'GeometryNodeVolumeCube': {
        'Volume': Constructor(fname='Cube', ret_socket='volume'),
    },    
    'GeometryNodeVolumeToMesh': {
        'Volume': Method(volume='self', fname='to_mesh', ret_socket='mesh', ret_class='Mesh'),
    },
}


# ----------------------------------------------------------------------------------------------------
# All the generators

ALL = {
       **ATTRIBUTE, 
       **COLOR, 
       **CURVE1, 
       **CURVE2, 
       **CURVE_PRIMITIVES, 
       **CURVE_TOPOLOGY, 
       **GEOMETRY,
       **INPUT,
       **INSTANCES,
       **MATERIAL,
       **MESH,
       **MESH_PRIMITIVES,
       #**MESH_TOPOLOGY,
       **POINT,
       **STRING,
       **TEXTURE,
       **UTILITIES,
       **UV,
       **VECTOR,
       **VOLUME,
       }

def get_class_generators(wnodes):
    cg = ClassGenerator(wnodes)
    cg.add_generators(ALL)
    
    return cg
    
    cg.add_generators(ATTRIBUTE)
    cg.add_generators(COLOR)
    cg.add_generators(CURVE1)
    cg.add_generators(CURVE2)
    cg.add_generators(CURVE_PRIMITIVES)
    cg.add_generators(CURVE_TOPOLOGY)
    cg.add_generators(GEOMETRY)
    cg.add_generators(INPUT)
    cg.add_generators(INSTANCES)
    cg.add_generators(MATERIAL)
    cg.add_generators(MESH)
    cg.add_generators(MESH_PRIMITIVES)
    cg.add_generators(POINT)
    cg.add_generators(STRING)
    cg.add_generators(TEXTURE)
    cg.add_generators(UTILITIES)
    cg.add_generators(UV)
    cg.add_generators(VECTOR)
    cg.add_generators(VOLUME)
    
    return cg









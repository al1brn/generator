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
                    yield self.indent(2) + f"{arg.scomment}\n"
    
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
        
    def add_generators(self, gens):
        
        for blid, classes in gens.items():
            
            wnode = self.wnodes.get(blid)
            
            if wnode is None:
                raise Exception(f"ERROR: node {blid} not found")
            
            for class_name, generators in classes.items():
                
                if class_name not in self.keys():
                    self[class_name] = {}
                    
                if blid not in self[class_name]:
                    self[class_name][blid] = []
                
                if isinstance(generators, list):
                    self[class_name][blid].extend(generators)
                else:
                    self[class_name][blid].append(generators)
                    
    def gen_class(self, class_name, no_setter=False):
        
        if class_name != 'function':
            if class_name not in CLASSES:
                raise Exception(f"{class_name} not in CLASSES!")
            root = CLASSES[class_name][1]
            if root != "":
                root = f"({root})"
            yield f"class {class_name}{root}:\n"
        
        # ----- Sort the methods
        
        methods = []
        for blid, gens in self[class_name].items():
            wnode = self.wnodes.get(blid)
            for gen in gens:
                fname = gen.fname(wnode)
                if gen.decorator == 'setter':
                    if no_setter:
                        continue
                    fname += " setter"
                
                methods.append((fname, gen, wnode))
                
        methods = sorted(methods, key=lambda a: a[0])
        
        for _, gen, wnode in methods:
            for line in gen.gen_source(wnode):
                yield line
            yield "\n"
            
        """
        for blid, codes in self[class_name].items():
            wnode = self.wnodes.get(blid)
            for code in codes:
                for line in code.gen_source(wnode):
                    yield line
                yield "\n"
        """
                
    def create_files(self, fpath, select=None):
        
        for class_name in self.keys():
            if select is None or class_name in select:
                with open(fpath + f"{class_name.lower()}.py", 'w') as f:
                    for line in self.gen_class(class_name):
                        f.write(line)
                    f.write("\n\n")
        
    def create_one_file(self, file_name, no_setter=False, select=None):
        
        with open(file_name, 'w') as f:
            
            f.write("import geonodes.core.datasockets as geosocks\n")
            f.write("import geonodes.core.domain as geodom\n")
            f.write("\n")
            
            for class_name in self.keys():
                if select is None or class_name in select:
                    for line in self.gen_class(class_name, no_setter=no_setter):
                        f.write(line)
                    f.write("\n\n")
        
        
        
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
            Source(
                header="def combine_hsv(hue=None, saturation=None, value=None, alpha=None):",
                body  ="return nodes.CombineColor(red=hue, green=saturation, blue=value, alpha=alpha, mode='HSV').color",
                indent=""),
            Source(
                header="def combine_hsl(hue=None, saturation=None, lightness=None, alpha=None):",
                body  ="return nodes.CombineColor(red=hue, green=saturation, blue=lightness, alpha=alpha, mode='HSL').color",
                indent=""),
            ],
        'Color': [
            Constructor(fname='RGB', ret_socket='color', mode="'RGB'"),
            Constructor(
                header="def HSV(cls, hue=None, saturation=None, valye=None, alpha=None):",
                body  ="return cls(nodes.CombineColor(red=hue, green=saturation, blue=value, alpha=alpha, mode='HSL').color)",
                        ),
            Constructor(
                header="def HSL(cls, hue=None, saturation=None, lightness=None, alpha=None):",
                body  ="return cls(nodes.CombineColor(red=hue, green=saturation, blue=lightness, alpha=alpha, mode='HSL').color)",
                        ),
            ]
    },
    'ShaderNodeMix': {
        'function': [
            Function(fname='float_mix', ret_socket='result', data_type="'FLOAT'", blend_type='MIX', clamp_result=False, factor_mode="'UNIFORM'"),
            Function(fname='vector_mix', ret_socket='result', data_type="'VECTOR'", blend_type='MIX', clamp_result=False),
            ],
        'Color': [Method(ret_socket='result', a='self', data_type="'COLOR'", factor_mode="'UNIFORM'"),],
        'Float': Method(ret_socket='result', a='self', data_type="'FLOAT'", blend_type='MIX', clamp_result=False, factor_mode="'UNIFORM'"),
        'Vector': Method(ret_socket='result', a='self', data_type="'VECTOR'", blend_type='MIX', clamp_result=False),
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
            Source(header="def trim_factor(self, start=None, end=None):", body="return self.trim(start=start, end=end, mode='FACTOR')"),
            Source(header="def trim_length(self, start=None, end=None):", body="return self.trim(start=start, end=end, mode='LENGTH')"),
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


# ----------------------------------------------------------------------------------------------------
# Mix color functions and methods

mix_functions = []
mix_methods   = []
for mode in ('MIX', 'DARKEN', 'MULTIPLY', 'BURN', 'LIGHTEN', 'SCREEN', 'DODGE', 'ADD', 'OVERLAY', 'SOFT_LIGHT', 'LINEAR_LIGHT', 'DIFFERENCE', 'SUBTRACT', 'DIVIDE', 'HUE', 'SATURATION', 'COLOR', 'VALUE'):

    fname = f"mix_{mode.lower()}"
    
    # ----- Color

    mix_methods.append(
        Method(fname=fname, ret_socket='result', a='self', blend_type=f"'{mode}'", data_type="'COLOR'", factor_mode="'UNIFORM'")
        )
    
    # ----- Function
    # - mix_mix --> replaced par mix with blend_type accesible

    if fname == 'mix_mix':
        mix_functions.append(
            Function(fname='mix', ret_socket="result", data_type="'COLOR'", factor_mode="'UNIFORM'")
            )
    else:
        mix_functions.append(
            Function(fname=fname, ret_socket="result", blend_type=f"'{mode}'", data_type="'COLOR'", factor_mode="'UNIFORM'")
            )
    
COLOR['ShaderNodeMix']['function'].extend(mix_functions)
COLOR['ShaderNodeMix']['Color'].extend(mix_methods)





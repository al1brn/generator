#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 17:41:59 2022

@author: alain
"""

# ====================================================================================================
# Class hierarchy

CLASSES = {
    
    'function'      : ('functions', None),
    
    # Geometry

    'Geometry'      : ('classes', 'geosocks.Geometry'),

    'Mesh'          : ('classes', 'Geometry'),
    'Curve'         : ('classes', 'Geometry'),
    'Points'        : ('classes', 'Geometry'),
    'Instances'     : ('classes', 'Geometry'),
    'Volume'        : ('classes', 'Geometry'),
    
    # Base

    'Boolean'       : ('classes', 'geosocks.Boolean'),
    'Integer'       : ('classes', 'geosocks.Integer'),
    'Float'         : ('classes', 'geosocks.Float'),
    'Vector'        : ('classes', 'geosocks.Vector'),
    'Color'         : ('classes', 'geosocks.Color'),
    'String'        : ('classes', 'geosocks.String'),
    #'Rotation'      : ('classes', 'Vector'),
    
    # Blender

    'Collection'    : ('classes', 'geosocks.Collection'),
    'Object'        : ('classes', 'geosocks.Object'),
    'Material'      : ('classes', 'geosocks.Material'),
    'Texture'       : ('classes', 'geosocks.Texture'),
    'Image'         : ('classes', 'geosocks.Image'),
    
    # Domains
    
    'Domain'        : ('domains', 'geodom.Domain'),

    'Vertex'        : ('domains', 'Domain'),
    'Edge'          : ('domains', 'Domain'),
    'Face'          : ('domains', 'Domain'),
    'Corner'        : ('domains', 'Domain'),
    'ControlPoint'  : ('domains', 'Domain'),
    'Spline'        : ('domains', 'Domain'),
    'CloudPoint'    : ('domains', 'Domain'),
    'Instance'      : ('domains', 'Domain'),
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
        
        self.stack        = False               # call self.stack
        self.attribute    = False               # call self.attribute
        
        self.header       = None                # replace the header generation by user source code
        self.body         = None                # replace the body generation by user source code
        self.body_start   = None                # first lines of code
        
        self.ret_socket   = None                # socket to return, returns node if None. Can be a tuple
        self.ret_class    = None                # type of the return socket. Ignore if socket is None. must be a tuple if ret_socket is tuple.
        self.cache        = False               # use a cache for the node
        self.dtype        = None                # (data_type, value, color_domain) implements: data_type = self.value_data_type(argument, data_type, color_domain)
        
        self.is_domain    = False               # domain method
        
        self.kwargs       = {}                  # node argument values
        
        self.com_descr    = None                # Description string
        self.com_args     = None                # Args comments
        self.com_ret      = None                # Return description
        
        self.no_code      = False               # Do net generate source code (comments only)
        self.node_blid    = None                # Node bl_idname 
        
        self.for_test     = None                # Test code
        
        
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
                
            if not ok_domain:
                self.kwargs['domain'] = 'self.domain'
                
            if self_key is not None:
                self.kwargs[self_key] = 'self.data_socket'
                
    # ----------------------------------------------------------------------------------------------------
    # Indentation
        
    def indent(self, n):
        return self.indent_ + Generator.INDENT*n

    # ----------------------------------------------------------------------------------------------------
    # fname is either fixed or provided by the node
    
    def fname(self, node):
        return node.function_name if self.fname_ is None else self.fname_
    
    # ----------------------------------------------------------------------------------------------------
    # decorator
    
    def get_decorator(self, node):

        if self.decorator is None:
            return None
        
        elif self.decorator == 'setter':
            return f"@{self.fname(node)}.setter\n"
        
        else:
            return self.decorator
    

    # ----------------------------------------------------------------------------------------------------
    # Source code to create the name:
    # - nodes.NODE_NAME(keyword=value,...)
    # The value is read from the dictionary when the keyword entry exists,
    # Default value is used otherwise
    
    def node_call_str(self, node):
        args = node.get_node_arguments()
        return f"nodes.{node.node_name}({args.method_call_arguments(**self.kwargs)})"
    
    # ----------------------------------------------------------------------------------------------------
    # The call string
    
    def call_string(self, node):
        
        if self.header is None:
            args  = node.get_node_arguments().method_header(**self.kwargs)
            
            if self.first_arg is not None:
                args.insert(0, self.first_arg)
                
            s = ", ".join(args)
            
            return f"def {self.fname(node)}({s}):"
            
        else:
            return self.header
    
    
    # ----------------------------------------------------------------------------------------------------
    # Generate the source code
        
    def gen_source(self, node):
        
        if self.no_code:
            return
        
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
        
        yield self.indent(0) + self.call_string(node) + "\n"
            
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
                    yield self.indent(2) + f"socket `{self.ret_socket}`"
                    if self.ret_class is None or self.ret_class == 'cls':
                        yield "\n"
                    else:
                        yield f" [{self.ret_class}]({self.ret_class}.md)\n"
                        
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
        
        # ----- Import class name if required
        
        s_gn = ""
        if self.ret_class is not None and self.ret_class != 'cls':
            yield self.indent(1) + "import geonodes as gn\n"
            s_gn = "gn."

        # ----- body start
        
        if self.body_start is not None:
            for line in self.body_start.split("\n"):
                yield self.indent(1) + line + "\n"
            
            yield "\n"
            
        # ----- Function calls
        
        attribute_func = None
        if self.attribute:
            if self.is_domain:
                attribute_func = "attribute_node"
            else:
                attribute_func = "attribute_node"
        
        stack_func = None
        if self.stack:
            if self.is_domain:
                stack_func = "socket_stack"
            else:
                stack_func = "stack"
        
        # ----- data_type
 
        if self.dtype is not None:
            if len(self.dtype) > 2:
                scolor = f", color_domain={self.dtype[2]}"
            else:
                scolor = ""
            yield self.indent(1) + f"{self.dtype[0]}_ = self.value_data_type({self.dtype[1]}, {default_data_type}{scolor})\n"
            self.kwargs[self.dtype[0]] = f"{self.dtype[0]}_"
        
        # ----- Node creation string

        snode = f"{self.node_call_str(node)}"
        ssock = None
        
        # ----- Attribute
        # attribute function returns a node

        snode = f"{self.node_call_str(node)}"
        if attribute_func is not None:
            snode = f"self.{attribute_func}({snode})"
            
        # ----- Cache mechanism
        # node = ...
            
        if self.cache:
            cache_name = node.bl_idname.lower()
            yield self.indent(1) + f"if not hasattr(self, '_c_{cache_name}'):\n"
            yield self.indent(2) + f"self._c_{cache_name} = {snode}\n"
            snode = f"self._c_{cache_name}"
            
        # ----- Stack
        # stack function returns a socket
            
        if stack_func is not None:
            ssock = f"self.{stack_func}({snode})"
            snode = ssock + ".node"

        # ----- Return node, a socket or a tuple of sockets
        
        def check_output_socket(name):
            if name not in node.outputs.unames.keys():
                raise Exception(f"Node {node.bl_idname}: '{name}' is not a valid output socket name in {list(node.outputs.unames.keys())}")
        
        if self.ret_socket is None:
            sret = snode if ssock is None else ssock
            
        elif isinstance(self.ret_socket, tuple):
            yield self.indent(1) + f"node = {snode}\n"
            vals = []
            ret_class = (None,) * len(self.ret_socket) if self.ret_class is None else self.ret_class
            for rs, rc in zip(self.ret_socket, ret_class):
                check_output_socket(rs)
                if rc is None:
                    vals.append(f"node.{rs}")
                else:
                    vals.append(f"{s_gn}{rc}(node.{rs})")
                    
            sret = ", ".join(vals)
                
        else:
            check_output_socket(self.ret_socket)
            sret = f"{snode}.{self.ret_socket}"

            if self.ret_class is not None:
                sret = f"{s_gn}{self.ret_class}({sret})"
                
        # ----- No return if property setter
        
        if self.decorator == 'setter':
            return_ = ""
        else:
            return_ = "return "
            
        # ----- Done
            
        yield self.indent(1) + f"{return_}{sret}\n\n"
        
    # ----------------------------------------------------------------------------------------------------
    # Generate test code
    
    def test_code(self, class_name, node):
        
        dom_insts = {
                'Vertex':       'mesh.verts',
                'Edge':         'mesh.edges',
                'Face':         'mesh.faces',
                'Corner':       'mesh.corners',
                'ControlPoint': 'curve.points',
                'Spline':       'curve.splines',
                'Instance':     'instances.insts',
                'CloudPoint':   'points.points',
            }
        
        if self.for_test is not None:
            for line in self.for_test.split("\n"):
                yield line
            return
        
        if CLASSES[class_name][0] == 'classes':
            inst_names = [class_name.lower()]
            
        elif CLASSES[class_name][0] == 'domains':
            if class_name == 'Domain':
                inst_names = list(dom_insts.values())
            else:
                inst_names = [dom_insts[class_name]]
                
        else:
            inst_names = ['global']
            
        for inst_name in inst_names:
            if self.decorator is None:
                if class_name == 'function':
                    yield f"gn.{self.fname(node)}()"
                else:
                    fname = self.fname(node)
                    if fname == 'len':
                        yield f"var = len({inst_name})"
                    else:
                        yield f"{inst_name}.{fname}()"
            
            elif self.decorator in ['@classmethod', '@staticmethod']:
                yield f"var = gn.{class_name}.{self.fname(node)}()"
            
            elif self.decorator == 'setter':
                yield f"{inst_name}.{self.fname(node)} = None"
            
            elif self.decorator == '@property':
                yield f"var = {inst_name}.{self.fname(node)}"
            
            else:
                raise Exception("Strange")
        
        
    # ----------------------------------------------------------------------------------------------------
    # Generate api documentation
    
    def anchor(self, node):
        s = self.fname(node)
        if self.decorator is not None:
            if self.decorator != "setter":
                s += f"-{self.decorator[1:]}"
        return s
    
    def gen_api_doc(self, node):
        
        s = self.fname(node)
        if self.decorator is not None:
            if self.decorator == 'setter':
                yield
            s += f' <sub>*{self.decorator[1:]}*</sub>'
        
        yield f"## {s}\n\n"
        
        yield "```python\n"
        yield f"{self.call_string(node)}\n\n"
        yield "```\n"
        
        if node is not None:
            yield f"> Node: [{node.bnode.name}]({node.bl_idname}.md) - [Blender reference]({node.blender_ref}) - [api reference]({node.blender_python_ref})\n\n"
        
        if self.com_descr is not None:
            yield self.com_descr + "\n\n"

        # ----- Arguments
            
        if self.com_args is None:
            ok_arg = False
            for arg in node.get_node_arguments():
                if not arg.name in self.kwargs.keys():
                    if not ok_arg:
                        yield f"#### Args:\n"
                        ok_arg = True
                    yield f"- {arg.scomment(**self.kwargs)}\n"
    
            if ok_arg:
                yield "\n"
                
        else:
            if len(self.com_args):
                yield f"#### Args:\n"
                for line in self.com_args:
                    yield f"- {line }\n"
                yield "\n"
                
        # ----- Returns
        
        if isinstance(self.ret_socket, tuple):
            yield f"![Node Image]({node.node_image_ref})\n\n"
        
        if self.com_ret is None:
            if self.decorator != 'setter':
                yield f"#### Returns:\n"
                if self.ret_socket is None:
                    if self.stack:
                        yield "- self\n"
                    else:
                        yield f"- node with sockets {list(node.outputs.unames.keys())}\n"
                    
                elif isinstance(self.ret_socket, tuple):
                    sr = tuple([f"`{rs}`" for rs in self.ret_socket])
                    yield f"- tuple {sr}\n"
                    
                else:
                    yield f"- socket `{self.ret_socket}`"
                    if self.ret_class is None or self.ret_class == 'cls':
                        yield "\n"
                    else:
                        yield f" of class {self.ret_class}\n"
        else:
            if self.com_ret != "":
                yield f"#### Returns:\n"
                for line in self.com_ret.split('\n'):
                    yield f"- {line}\n"    
                    
        yield "\n"
        
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
        
        self.com_args = []
        
class DomProperty(Property):
    def __init__(self, **kwargs):
        super().__init__(is_domain=True, **kwargs)        

class Setter(Method):
    def __init__(self, stack=True, **kwargs):
        super().__init__(decorator="setter", stack=stack, **kwargs)
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
        super().__init__(stack=True, **kwargs)

class DomStackMethod(StackMethod):
    def __init__(self, **kwargs):
        super().__init__(is_domain=True, **kwargs)
    
# ----------------------------------------------------------------------------------------------------
# Attribute method
        
class Attribute(Method):
    def __init__(self, **kwargs):
        super().__init__(attribute=True, **kwargs)
        
class PropAttribute(Attribute):
    def __init__(self, **kwargs):
        super().__init__(decorator="@property", **kwargs)
        
class DomAttribute(Method):
    def __init__(self, **kwargs):
        super().__init__(is_domain=True, attribute=True, **kwargs)
        
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
                fname     = fname,
                header    = f"def {fname}(self):",
                body      = f"raise Exception(\"Error: '{fname}' is a write only property of class {class_name}!\")",
                com_descr = f"'{fname}' is a write only property.\nRaise an exception if attempt to read.",
                com_args  = [],
                com_ret   = "",
                for_test  = "",
                )
        
# ----------------------------------------------------------------------------------------------------
# Node code, just for documentaticon
# Used for methods which are implemented manually
        
class Comment(Generator):
    def __init__(self, **kwargs):
        super().__init__(no_code=True, **kwargs)

        
# ====================================================================================================
# Class generator

class ClassGenerator(dict):
    
    def __init__(self, wnodes):
        super().__init__()
        self.wnodes = wnodes
        
        # ----- Add the comments generator
        
        for cnames, gs in COMMENTS.items():

            if isinstance(gs, list):
                gens = gs
            else:
                gens = [gs]
            
            if isinstance(cnames, tuple):
                class_names = cnames
            else:
                class_names = (cnames,)
                
            for class_name in class_names:
                
                if class_name not in self:
                    self[class_name] = {}
                    
                for gen in gens:
                    
                    blid = gen.node_blid
                    if blid is None:
                        blid = 'no_node'
                        
                    if blid not in self[class_name]:
                        self[class_name][blid] = [gen]
                    else:
                        self[class_name][blid].append(gen)
            
            
        
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
                
        #if class_name == 'Domain':
        #    print("\n".join([a[0] for a in sorted(methods, key=lambda a: a[0])]))
                
                
        return sorted(methods, key=lambda a: a[0])
    
    # ----------------------------------------------------------------------------------------------------
    # Generate the functions to import in __init__
                        
    def gen_classes_import(self):

        # ----- Data classes
        
        for class_type in ['domains', 'classes']:
            for class_name in sorted(self.keys()):
                if CLASSES[class_name][0] == class_type:
                    yield f"from geonodes.nodes.{CLASSES[class_name][0]} import {class_name}\n"
                    
            yield "\n"
        
        # ----- Global functions
        
        methods = self.class_methods('function')
        
        s = None
        for f, _, _ in methods:
            if s is None:
                s = f"from geonodes.nodes.functions import {f}"
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
            if wnode is None:
                continue
            
            for line in gen.gen_source(wnode):
                yield line
            yield "\n"
            
    # ----------------------------------------------------------------------------------------------------
    # Create the __init__.py file
    
    def create_init_file(self, file_name, version):
        
        with open(file_name, 'w') as f:
            
            import bpy
            
            f.write("# geonodes init file\n\n")
            
            f.write(f"version = {version}\n")
            f.write(f"blender_version={bpy.app.version}\n\n")
            
            f.write("pi = 3.141592653589793\n\n")
            
            f.write("from geonodes.core.node import Node, GroupInput, GroupOutput, Frame, Viewer, SceneTime, Group\n")
            f.write("from geonodes.core.tree import Tree, Trees\n\n")
            f.write("from geonodes.nodes import nodes\n\n")
            
            for line in self.gen_classes_import():
                f.write(line)
                
            f.write("\n")                    
                    
    # ----------------------------------------------------------------------------------------------------
    # Create the source code files
        
    def create_files(self, folder, version=None):
        
        files = []
        for class_name in CLASSES:
            if CLASSES[class_name][0] not in files:
                files.append(CLASSES[class_name][0])
        
        for file_name in files:
        
            with open(f"{folder}nodes/{file_name}.py", 'w') as f:
                
                if file_name == 'classes':
                    f.write("from geonodes.nodes import nodes\n")
                    f.write("import geonodes.core.datasockets as geosocks\n")
                    f.write("from geonodes.nodes.domains import Vertex, Edge, Face, Corner, ControlPoint, Spline, CloudPoint, Instance\n")
                    
                elif file_name == 'domains':
                    f.write("from geonodes.nodes import nodes\n")
                    f.write("import geonodes.core.domain as geodom\n")
                    
                elif file_name == 'functions':
                    f.write("from geonodes.nodes import nodes\n")
                    
                f.write("\n")
                
                for class_name in self.keys():
                    
                    if CLASSES[class_name][0] != file_name:
                        continue
                    
                    ok_lines = False
                    for line in self.gen_class(class_name):
                        if line is not None:
                            f.write(line)
                            ok_lines = True
                    if ok_lines:
                        f.write("\n\n")
                    
        if version is not None:
            self.create_init_file(folder + '__init__.py', version)
            
    # ----------------------------------------------------------------------------------------------------
    # Create the api documentation
    
    def create_api_doc(self, folder):
        
        nav_menu = "[main](../structure.md) - [nodes](nodes.md) - [nodes menus](nodes_menus.md)"
        doc_header = f"> {nav_menu}\n\n"
        
        print("Data classes api...")
        
        # ----------------------------------------------------------------------------------------------------
        # Classes documentation
        
        for class_name in self:

            file_name = f"{folder}docs/api/{class_name}.md"

            with open(file_name, 'w') as f:
                if class_name == 'function':
                    f.write("# Functions\n\n")
                else:
                    f.write(f"# class {class_name}\n\n")
                    
                f.write(doc_header)
                    
                # ----- TOC
                
                methods = self.class_methods(class_name)
                
                for deco, title in zip(["@property", "@classmethod", "@staticmethod", None], ["Properties", "Class methods", "Static methods", "Methods"]):
                    
                    ok_title = False
                    for _, gen, wnode in methods:
                        if gen.decorator != deco:
                            continue
                        
                        if not ok_title:
                            f.write(f"## {title}\n\n")
                            ok_title = True                             
                            
                        f.write(f"- [{gen.fname(wnode)}](#{gen.anchor(wnode)})\n")
                        
                    f.write("\n")
                
                # ----- Documentation
                
                for _, gen, wnode in methods:
                    ok_lines = False
                    for line in gen.gen_api_doc(wnode):
                        if line is not None:
                            f.write(line.replace('CLASS_NAME', class_name))
                            ok_lines = True
                            
                    if ok_lines:
                        f.write(f"<sub>Go to [top](#class-{class_name}) - {nav_menu}</sub>\n\n")
                        
        # ----------------------------------------------------------------------------------------------------
        # Nodes are listed in alphabetical order and in the Blender add menu order
        # Let's share the way they are listes
        
        def list_nodes(nodes):
            
            # Table header
            
            yield "| node | class | method name |\n"
            yield "|------|-------|-------------|\n"
            
            # Loop on the nodes
            
            for node in nodes:
                
                # Select the classes implementing the current node
                
                classes = {}
                for class_name, class_nodes in self.items():
                    gens = class_nodes.get(node.bl_idname)
                    if gens is not None:
                        classes[class_name] = gens
                        
                # Loop on the classes
                        
                ok_node = False
                for class_name in sorted(classes.keys()):
                    
                    gens = classes[class_name]
                    
                    # Node reference
                    
                    if ok_node:
                        yield "|      "
                    else:
                        yield f"| [{node.bnode.name}]({node.bnode.bl_idname}.md) "
                        ok_node = True
                        
                    # Class reference
                        
                    yield f"| [{class_name}]({class_name}.md) | "
                    
                    # List of methodes
                    
                    if len(gens) == 1:
                        gen = gens[0]
                        yield f"[{gen.fname(node)}]({class_name}.md#{gen.anchor(node)}) "
                        
                    elif len(gens) < 5:
                        br = "- "
                        for gen in gens:
                            yield f"{br}[{gen.fname(node)}]({class_name}.md#{gen.anchor(node)})"
                            br = "<br>- "
                            
                    else:
                        for gen in gens:
                            yield f"[{gen.fname(node)}]({class_name}.md#{gen.anchor(node)}) / "
                        
                    yield "|\n"   
                    
            yield "\n"
                        
                        
        # ----------------------------------------------------------------------------------------------------
        # Nodes in alphabetical order
        
        print("Nodes...")
        
        file_name = f"{folder}docs/api/nodes.md"
        with open(file_name, 'w') as f:
            f.write("# Nodes in alphabetical order\n\n")
            
            f.write(doc_header)

            nodes = sorted(self.wnodes.values(), key=lambda a: a.node_name)
            
            for line in list_nodes(nodes):
                f.write(line)
                    
        # ----------------------------------------------------------------------------------------------------
        # Nodes menus
        
        menu = {
            "Attribute"         : ATTRIBUTE,
            'Color'             : COLOR,
            'Curve'             : CURVE,
            'Curve Primitives'  : CURVE_PRIMITIVES,
            'Curve Topology'    : CURVE_TOPOLOGY,
            'Geometry'          : GEOMETRY,
            'Input'             : INPUT,
            'Instances'         : INSTANCES,
            'Material'          : MATERIAL,
            'Mesh'              : MESH,
            'Mesh Primitives'   : MESH_PRIMITIVES,
            #'Output'            : OUTPUT,
            'Point'             : POINT,
            'Text'              : TEXT,
            'Texture'           : TEXTURE,
            'Utilities'         : UTILITIES,
            'UV'                : UV,
            'Vector'            : VECTOR,
            'Volume'            : VOLUME,
            }
                    
        file_name = f"{folder}docs/api/nodes_menus.md"
        with open(file_name, 'w') as f:
            f.write("# Nodes Menus\n\n")
            
            for men in menu.keys():
                f.write(f"- [{men}](#menu-{men.replace(' ', '-')})\n")
            f.write("\n")
            
            for men, dct in menu.items():
                
                f.write(f"## Menu {men}\n\n")
            
                f.write(doc_header)
                
                nodes = [self.wnodes[blid] for blid in dct]
                
                for line in list_nodes(nodes):
                    f.write(line)
                    
                f.write(f"<sub>Go to [top](#nodes-menus) - {nav_menu}</sub>\n\n")
                
        # ----------------------------------------------------------------------------------------------------
        # Individual nodes
        
        for blid, wnode in self.wnodes.items():
            
            file_name = f"{folder}docs/api/{blid}.md"
            with open(file_name, 'w') as f:
                f.write(f"# Node *{wnode.bnode.name}*\n\n")
                
                f.write(doc_header)
                
                for line in wnode.gen_markdown_doc():
                    f.write(line)
                    
                # ----- Classes using this node
                
                classes = {}
                for class_name, class_nodes in self.items():
                    gens = class_nodes.get(blid)
                    if gens is not None:
                        if class_name == "function":
                            class_name = 'A' # For sorting :-)
                        classes[class_name] = gens
                        
                if len(classes) == 0:
                    if blid not in ['NodeFrame', 'GeometryNodeGroup', 'GeometryNodeViewer', 'NodeReroute',
                                    'NodeGroupInput', 'NodeGroupOutput']:
                        print(f"CAUTION: node not implemented in classes: {blid:35} {wnode.bnode.name}")
                    
                else:
                    
                    f.write("## Implementation\n\n")

                    f.write("| Class or method name | Definition |\n")
                    f.write("|----------------------|------------|\n")
                        

                    for class_name in sorted(classes):
                        
                        gens = classes[class_name]
                        
                        if class_name == 'A': # function
                            f.write("| Global functions |\n")
                        else:
                            f.write(f"| **[{class_name}]({class_name}.md)** |\n")
                            
                        for gen in gens:
                            f.write(f"| [{gen.fname(wnode)}]({class_name}.md#{gen.anchor(wnode)}) |")
                            deco = gen.get_decorator(wnode)
                            if deco is not None:
                                f.write(f" `{deco}`<br>")
                            f.write(f" `{gen.call_string(wnode)}` |\n")
                            
                
                f.write("\n")
                f.write(f"<sub>Go to [top](#node-{wnode.bnode.name.replace(' ', '-')}) - {nav_menu}</sub>\n\n")
                
    # ----------------------------------------------------------------------------------------------------
    # Create the test file
    
    def create_test_file(self, folder):
        
        file_name = f"{folder}test_file.py"
        with open(file_name, 'w') as f:
            
            _1_ = "    "
            
            f.write("from geonodes import nodes\n")
            f.write("import geonodes as gn\n\n")
            
            f.write("with gn.Tree('Geometry Nodes') as tree:\n\n")
            f.write(_1_ + "boolean    = gn.Boolean()\n")
            f.write(_1_ + "integer    = gn.Integer()\n")
            f.write(_1_ + "float      = gn.Float()\n")
            f.write(_1_ + "vector     = gn.Vector()\n")
            #f.write(_1_ + "rotation   = gn.Vector.Rotation()\n")
            f.write(_1_ + "color      = gn.Color()\n")
            f.write(_1_ + "string     = gn.String()\n")
            
            f.write(_1_ + "texture    = gn.Texture.Input()\n")
            f.write(_1_ + "image      = gn.Image.Input()\n")
            f.write(_1_ + "material   = gn.Material.Input()\n")
            f.write(_1_ + "collection = gn.Collection.Input()\n")
            f.write(_1_ + "object     = gn.Object.Input()\n")
            
            f.write(_1_ + "geometry   = tree.ig\n")

            f.write(_1_ + "mesh       = gn.Mesh.Cube()\n")
            f.write(_1_ + "curve      = gn.Curve.Circle()\n")
            f.write(_1_ + "points     = gn.Points.Points()\n")
            f.write(_1_ + "instances  = gn.Instances.InstanceOnPoints(points=points)\n")
            f.write(_1_ + "volume     = gn.Volume.Cube()\n")
            
            f.write("\n")
            
            for class_name, nodes in self.items():
                for blid, gens in nodes.items():
                    node = self.wnodes.get(blid)
                    for gen in gens:
                        for line in gen.test_code(class_name, node):
                            f.write(_1_ + line + "\n")
            
            f.write("\n")
            f.write(_1_ + "tree.og = geometry\n\n")
                
                        
                            
                        
                            
# ====================================================================================================
# Methods which are manually implemented

COMMENTS = {
    ('Float', 'Integer'): [
        Comment(fname     ='add',
                node_blid = 'ShaderNodeMath',
                header    = 'def add(self, value=None):',
                com_args  =['value: Float or Integer or Vector'], 
                com_ret   ='self + value'),
        
        Comment(fname     ='subtract',
                node_blid = 'ShaderNodeMath',
                header    = 'def subtract(self, value=None):',
                com_args  =['value: Float or Integer or Vector'], 
                com_ret   ='self - value'),
        
        Comment(fname     ='sub',
                node_blid = 'ShaderNodeMath',
                header    = 'def sub(self, value=None):',
                com_args  =['value: Float or Integer or Vector'], 
                com_ret   ='self - value'),
        
        Comment(fname     ='multiply',
                node_blid = 'ShaderNodeMath',
                header    = 'def multiply(self, value=None):',
                com_args  =['value: Float or Integer or Vector'], 
                com_ret   ='self * value'),
        
        Comment(fname     ='mul',    
                node_blid = 'ShaderNodeMath',
                header    = 'def mul(self, value=None):',
                com_args  =['value: Float or Integer or Vector'], 
                com_ret   ='self * value'),
        
        Comment(fname     ='divide',
                node_blid = 'ShaderNodeMath',
                header    = 'def divide(self, value=None):',
                com_args  =['value: Float'], 
                com_ret   ='self / value'),
        
        Comment(fname     ='div',
                node_blid = 'ShaderNodeMath',
                header    = 'def div(self, value=None):',
                com_args  =['value: Float'], 
                com_ret   ='self / value'),
        ],
    ('Float', 'Integer', 'Boolean', 'String', 'Vector', 'Color'): 
        Comment(fname     ='Input',      
                node_blid = 'no_node',
                decorator = '@classmethod',
                header    = 'def Input(cls, value=None, name="CLASS_METHOD", min_value=None, max_value=None, description=""):',
                com_descr = "Used to create an input socket in the Group Input node.\n" +
                            "Even if homonyms are accepted, it is recommended to avoid to create to input sockets with the same name.",
                com_args  =[
                    'value: Initial value. Not changed if the group input socket already exists',
                    'name: Input socket name. Avoid homonyms!',
                    'min_value: minimum value',
                    'max_value: maxium value',
                    'description: user help',
                    ], 
                com_ret   = 'CLASS_NAME'),
    ('Collection', 'Object', 'Image', 'Texture', 'Material'): 
        Comment(fname     ='Input',      
                node_blid = 'no_node',
                decorator = '@classmethod',
                header    = 'def Input(cls, value=None, name="CLASS_METHOD", description=""):',
                com_descr = "Used to create an input socket in the Group Input node.\n" +
                            "Even if homonyms are accepted, it is recommended to avoid to create to input sockets with the same name.\n" +
                            "The initial value can be either a valid Blender CLASS_NAME or the name of an existing Blender CLASS_NAME.",
                com_args  =[
                    'value: Blender CLASS_NAME or name of an existing Blender CLASS_NAME',
                    'name: Input socket name. Avoid homonyms!',
                    'description: user help',
                    ], 
                com_ret   = 'CLASS_NAME'),
        
    }
        
        
        
# ====================================================================================================
# Attribute Menu

ATTRIBUTE = {
    'GeometryNodeAttributeStatistic': {
        'Geometry': Method(geometry='self', dtype=('data_type', 'attribute')),
        'Domain'  : [
            DomMethod(geometry='self', dtype=('data_type', 'attribute')),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_mean',   ret_socket='mean'),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_median', ret_socket='median'),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_sum',    ret_socket='sum'),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_min',    ret_socket='min'),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_max',    ret_socket='max'),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_range',  ret_socket='range'),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_std',    ret_socket='standard_deviation'),
            DomMethod(geometry='self', dtype=('data_type', 'attribute'), fname='attribute_var',    ret_socket='variance'),
            ],
        },
    'GeometryNodeCaptureAttribute': {
        'Geometry': [
            StackMethod(ret_socket='attribute',    dtype=('data_type', 'value'), geometry='self'),
            Method(fname='capture_attribute_node'), # Used to automatically capture attributes
            ],
        'Domain':   DomStackMethod(ret_socket='attribute', dtype=('data_type', 'value'), geometry='self'),
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
        'Points'   : Property(cache=True, geometry='self', component="'POINTCLOUD'",ret_socket='point_count'),
        'Instances': Property(cache=True, geometry='self', component="'INSTANCES'",  ret_socket='instance_count'),
        
        'Vertex'       : DomProperty(fname='count', component="'MESH'", ret_socket='point_count'),
        'Face'         : DomProperty(fname='count', component="'MESH'", ret_socket='face_count'),
        'Edge'         : DomProperty(fname='count', component="'MESH'", ret_socket='edge_count'),
        'Corner'       : DomProperty(fname='count', component="'MESH'", ret_socket='face_corner_count'),
        
        'Spline'       : DomProperty(fname='count', component="'CURVE'", ret_socket='spline_count'),
        'ControlPoint' : DomProperty(fname='count', component="'CURVE'", ret_socket='point_count'),
        
        'CloudPoint'   : DomProperty(fname='count', component="'POINTCLOUD'", ret_socket='point_count'),
        'Instance'     : DomProperty(fname='count', component="'INSTANCES'", ret_socket='instance_count'),
        
        },
    'GeometryNodeStoreNamedAttribute': {
        'Geometry': [
            StackMethod(geometry='self',  dtype=('data_type', 'value')),
            StackMethod(geometry='self',  fname='set_named_boolean', data_type="'BOOLEAN'"),
            StackMethod(geometry='self',  fname='set_named_integer', data_type="'INT'"),
            StackMethod(geometry='self',  fname='set_named_float',   data_type="'FLOAT'"),
            StackMethod(geometry='self',  fname='set_named_vector',  data_type="'FLOAT_VECTOR'"),
            StackMethod(geometry='self',  fname='set_named_color',   data_type="'FLOAT_COLOR'"),
            ],
        'Domain'  : [
            DomStackMethod(geometry='self',  dtype=('data_type', 'value')),
            DomStackMethod(geometry='self',  fname='set_named_boolean', data_type="'BOOLEAN'"),
            DomStackMethod(geometry='self',  fname='set_named_integer', data_type="'INT'"),
            DomStackMethod(geometry='self',  fname='set_named_float',   data_type="'FLOAT'"),
            DomStackMethod(geometry='self',  fname='set_named_vector',  data_type="'FLOAT_VECTOR'"),
            DomStackMethod(geometry='self',  fname='set_named_color',   data_type="'FLOAT_COLOR'"),
            ],
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
            Function(fname='float_mix', ret_socket='result', data_type="'FLOAT'", blend_type="'MIX'", clamp_result=False, factor_mode="'UNIFORM'"),
            Function(fname='vector_mix', ret_socket='result', data_type="'VECTOR'", blend_type="'MIX'", clamp_result=False),
            
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_mix',              ),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_darken',       blend_type="'DARKEN'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_multiply',     blend_type="'MULTIPLY'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_burn',         blend_type="'BURN'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_lighten',      blend_type="'LIGHTEN'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_screen',       blend_type="'SCREEN'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_dodge',        blend_type="'DODGE'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_add',          blend_type="'ADD'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_overlay',      blend_type="'OVERLAY'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_soft_light',   blend_type="'SOFT_LIGHT'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_linear_light', blend_type="'LINEAR_LIGHT'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_difference',   blend_type="'DIFFERENCE'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_subtract',     blend_type="'SUBTRACT'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_divide',       blend_type="'DIVIDE'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_hue',          blend_type="'HUE'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_saturation',   blend_type="'SATURATION'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_color',        blend_type="'COLOR'"),
            Function(ret_socket='result', data_type="'RGBA'", factor_mode="'UNIFORM'", fname='color_value',        blend_type="'VALUE'"),
            ],
        'Color': [
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix',              ),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_darken',       blend_type="'DARKEN'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_multiply',     blend_type="'MULTIPLY'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_burn',         blend_type="'BURN'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_lighten',      blend_type="'LIGHTEN'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_screen',       blend_type="'SCREEN'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_dodge',        blend_type="'DODGE'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_add',          blend_type="'ADD'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_overlay',      blend_type="'OVERLAY'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_soft_light',   blend_type="'SOFT_LIGHT'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_linear_light', blend_type="'LINEAR_LIGHT'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_difference',   blend_type="'DIFFERENCE'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_subtract',     blend_type="'SUBTRACT'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_divide',       blend_type="'DIVIDE'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_hue',          blend_type="'HUE'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_saturation',   blend_type="'SATURATION'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_color',        blend_type="'COLOR'"),
            Method(ret_socket='result', a='self', data_type="'RGBA'", factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_value',        blend_type="'VALUE'"),
            ],
        'Float': Method(ret_socket='result', a='self', data_type="'FLOAT'", blend_type="'MIX'", arg_rename={'b': 'value'}, clamp_result=False, factor_mode="'UNIFORM'"),
        'Vector': [
            Method(ret_socket='result', a='self', data_type="'VECTOR'", blend_type="'MIX'", arg_rename={'b': 'vector'}, clamp_result=False),
            Method(ret_socket='result', a='self', data_type="'VECTOR'", blend_type="'MIX'", arg_rename={'b': 'vector'}, clamp_result=False, fname='mix_uniform', factor_mode="'UNIFORM'", factor=None),
            Method(ret_socket='result', a='self', data_type="'VECTOR'", blend_type="'MIX'", arg_rename={'b': 'vector'}, clamp_result=False, fname='mix_non_uniform', factor_mode="'NON_UNIFORM'"),
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
            
            Property(color='self', mode="'RGB'", fname='alpha',   ret_socket='alpha'),
            
            Property(color='self', mode="'RGB'", fname='red',        ret_socket='red'),
            Property(color='self', mode="'RGB'", fname='green',      ret_socket='green'),
            Property(color='self', mode="'RGB'", fname='blue',       ret_socket='blue'),
            
            Property(color='self', mode="'HSV'", fname='hue',        ret_socket='red'),
            Property(color='self', mode="'HSV'", fname='saturation', ret_socket='green'),
            Property(color='self', mode="'HSV'", fname='value',      ret_socket='blue'),
            
            Property(color='self', mode="'HSL'", fname='lightness',  ret_socket='blue'),
            ],
    },
}


CURVE = {
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
            StackMethod(fname='trim_factor', curve='self', arg_rename={'start0': 'start', 'end0': 'end'}, start1=None, end1=None, mode="'FACTOR'"),
            StackMethod(fname='trim_length', curve='self', arg_rename={'start1': 'start', 'end1': 'end'}, start0=None, end0=None, mode="'LENGTH'"),
            ],
    },
    'GeometryNodeInputCurveHandlePositions': {
        'ControlPoint': [
            DomAttribute(fname='handle_positions'),
            DomPropAttribute(fname='left_handle_positions', ret_socket='left', relative=None),
            DomPropAttribute(fname='right_handle_positions', ret_socket='right', relative=None),
            ],
    },
    'GeometryNodeInputTangent': {
        'ControlPoint': DomPropAttribute(fname='tangent', ret_socket='tangent'),
    },
    'GeometryNodeInputCurveTilt': {
        'ControlPoint': DomPropAttribute(fname='tilt', ret_socket='tilt'),
    },
    'GeometryNodeCurveEndpointSelection': {
        'ControlPoint': DomAttribute(fname='endpoint_selection', ret_socket='selection'),
    },
    'GeometryNodeCurveHandleTypeSelection': {
        'ControlPoint': [
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
        'ControlPoint': [
            DomPropAttribute(fname='parameter',        cache=True, ret_socket=('factor', 'length', 'index')),
            DomPropAttribute(fname='parameter_factor', cache=True, ret_socket='factor'),
            DomPropAttribute(fname='parameter_length', cache=True, ret_socket='length'),
            DomPropAttribute(fname='parameter_index',  cache=True, ret_socket='index'),
            ],
    },
    'GeometryNodeInputSplineResolution': {
        'Spline': DomPropAttribute(fname='resolution', ret_socket='resolution'),
    },
    
    'GeometryNodeSetCurveNormal': {
        'Spline': [
            DomStackMethod(fname='set_normal', curve='self'),
            DomSetter(fname='normal', stack=True, curve='self', mode='attr_value', for_test="curve.splines.normal = 'MINIMUM_TWIST'"),
            ],
    },
    'GeometryNodeSetCurveRadius': {
        'ControlPoint': [
            DomStackMethod(fname='set_radius', curve='self'),
            DomSetter(fname='radius', stack=True, curve='self', radius='attr_value'),
            ],
    },
    'GeometryNodeSetCurveTilt': {
        'ControlPoint': [
            DomStackMethod(fname='set_tilt', curve='self'),
            DomSetter(fname='tilt', stack=True, curve='self', tilt='attr_value'),
            ],
    },
    'GeometryNodeSetCurveHandlePositions': {
        'ControlPoint': [
            DomStackMethod(fname='set_handle_positions',       curve='self'),
            DomStackMethod(fname='set_handle_positions_left',  curve='self', mode="'LEFT'"),
            DomStackMethod(fname='set_handle_positions_right', curve='self', mode="'RIGHT'"),
            DomSetter(fname='left_handle_positions', curve='self',  stack=True, position='attr_value', offset=None, mode="'LEFT'",
                           for_test="curve.points.left_handle_positions = (1, 2, 3)"),
            DomSetter(fname='right_handle_positions', curve='self', stack=True, position='attr_value', offset=None, mode="'RIGHT'",
                           for_test="curve.points.right_handle_positions = (1, 2, 3)"),
            ],
    },
    'GeometryNodeCurveSetHandles': {
        'ControlPoint': [
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
            DomSetter(fname='type', stack=True, curve='self', spline_type='attr_value', for_test="curve.splines.type = 'POLY'"),
            ],
    },
}

CURVE_PRIMITIVES = {
    'GeometryNodeCurveArc': {
        'Curve': [
            #Constructor(fname="ArcPrimitive"),
            Constructor(fname='Arc', ret_socket='curve', mode="'RADIUS'", start=None, middle=None, end=None, offset_angle=None),
            Constructor(fname='ArcFromPoints', mode="'POINTS'", radius=None, start_angle=None, sweep_angle=None),
        ],
    },
    'GeometryNodeCurvePrimitiveBezierSegment': {
        'Curve': Constructor(fname='bezier_segment', ret_socket='curve'),
    },
    'GeometryNodeCurvePrimitiveCircle': {
        'Curve': [
            Constructor(fname='Circle', ret_socket='curve', mode="'RADIUS'", point_1=None, point_2=None, point_3=None),
            Constructor(fname='CircleFromPoints', mode="'POINTS'", radius=None),
            ],
    },
    'GeometryNodeCurvePrimitiveLine': {
        'Curve': [
            Constructor(fname='Line', ret_socket='curve', mode="'POINTS'", direction=None, length=None),
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
        ('Vertex', 'Edge','Face', 'Spline', 'ControlPoint', 'Instance', 'CloudPoint'):
            DomStackMethod(fname='delete', geometry='self'),
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
        ('Vertex', 'ControlPoint', 'CloudPoint', 'Edge', 'Face', 'Instance'): 
            DomStackMethod(fname='duplicate', ret_socket='duplicate_index', geometry='self'),
        # For this node Spline Domain is SPLINE and nor CURVE !
        'Spline': DomStackMethod(fname='duplicate', ret_socket='duplicate_index', geometry='self', domain="'SPLINE'"),
    },
    'GeometryNodeProximity': {
        'Geometry' : [
            Attribute(fname='proximity',        ret_socket='distance'),
            Attribute(fname='proximity_points', ret_socket='distance', target_element="'POINTS'"),
            Attribute(fname='proximity_edges',  ret_socket='distance', target_element="'EDGES'"),
            Attribute(fname='proximity_faces',  ret_socket='distance', target_element="'FACES'"),
            ],
        ('Vertex', 'ControlPoint', 'CloudPoint') :
            DomAttribute(fname='proximity', ret_socket='distance', target_element="'POINTS'"),
        'Edge':
            DomAttribute(fname='proximity', ret_socket='distance', target_element="'EDGES'"),
        'Face':
            DomAttribute(fname='proximity', ret_socket='distance', target_element="'FACES'"),
    },
    'GeometryNodeGeometryToInstance': {
        'function': Function(ret_socket='instances', ret_class='Instances'),
        'Geometry': Method(fname='to_instance', first_arg=None, ret_socket='instances', ret_class='Instances'),
    },
    'GeometryNodeJoinGeometry': {
        'function': Function(ret_socket='geometry'),
        'Geometry': StackMethod(fname='join', first_arg=None, body_start="self = geometry[0]"),
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
        ('Vertex', 'Edge', 'Face', 'Corner'): DomMethod(ret_socket='index', geometry='self'),
    },
    'GeometryNodeSeparateComponents': {
        'Geometry': [
            Property(geometry='self', cache=True),
            Property(geometry='self', cache=True, fname='mesh_component',      ret_socket='mesh',        ret_class='Mesh'),
            Property(geometry='self', cache=True, fname='curve_component',     ret_socket='curve',       ret_class='Curve'),
            Property(geometry='self', cache=True, fname='points_component',    ret_socket='point_cloud', ret_class='Points'),
            Property(geometry='self', cache=True, fname='volume_component',    ret_socket='volume',      ret_class='Volume'),
            Property(geometry='self', cache=True, fname='instances_component', ret_socket='instances',   ret_class='Instances'),
            ],
    },
    'GeometryNodeSeparateGeometry': {
        'Geometry': Method(fname='separate', geometr='self', ret_socket=('selection', 'inverted')),
        ('Vertex', 'Edge', 'Face', 'ControlPoint', 'Spline', 'Instance'):
            DomMethod(fname='separate', geometr='self', ret_socket=('selection', 'inverted')),
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
        'Object': [
            Method(fname='info'),
            Method(fname='location', ret_socket='location'),
            Method(fname='rotation', ret_socket='rotation'),
            Method(fname='scale', ret_socket='scale'),
            Method(fname='geometry', ret_socket='geometry'),
            ]
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
        'Domain'  : [
            DomPropAttribute(fname='index', ret_socket='index'),
            DomPropAttribute(fname='domain_index', ret_socket='index'),
            ],
    },
    'GeometryNodeInputNamedAttribute': {
        'Geometry': [
            Attribute(fname='named_attribute',   ret_socket='attribute'),
            Attribute(fname='get_named_float',   ret_socket='attribute', data_type="'FLOAT'"),
            Attribute(fname='get_named_integer', ret_socket='attribute', data_type="'INT'"),
            Attribute(fname='get_named_vector',  ret_socket='attribute', data_type="'FLOAT_VECTOR'"),
            Attribute(fname='get_named_color',   ret_socket='attribute', data_type="'FLOAT_COLOR'"),
            Attribute(fname='get_named_boolean', ret_socket='attribute', data_type="'BOOLEAN'"),
            ],
        'Domain': [
            DomAttribute(fname='named_attribute',   ret_socket='attribute'),
            DomAttribute(fname='get_named_float',   ret_socket='attribute', data_type="'FLOAT'"),
            DomAttribute(fname='get_named_integer', ret_socket='attribute', data_type="'INT'"),
            DomAttribute(fname='get_named_vector',  ret_socket='attribute', data_type="'FLOAT_VECTOR'"),
            DomAttribute(fname='get_named_color',   ret_socket='attribute', data_type="'FLOAT_COLOR'"),
            DomAttribute(fname='get_named_boolean', ret_socket='attribute', data_type="'BOOLEAN'"),
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
        #'Domain'     : DomPropAttribute(fname='radius', ret_socket='radius'),
        #'Spline'     : DomPropAttribute(fname='radius', ret_socket='radius'),
        #'CloudPoint' : DomPropAttribute(fname='radius', ret_socket='radius'),
        'ControlPoint' : DomPropAttribute(fname='radius', ret_socket='radius'),
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
            Method(fname='on_points', ret_socket='instances', ret_classes='Instances', instance='self'),
            ],
        ('Points', 'Mesh', 'Curve') : Method(ret_socket='instances', ret_classes='Instances', points='self'),
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
        ('Face', 'Spline'):   [
            DomStackMethod(geometry='self'),
            PropReadError(fname='material', class_name='Domain'),
            DomSetter(fname='material', geometry='self', material='attr_value'),
            ]
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
            StackMethod(mesh='self', fname='boolean_intersect',  ret_socket='intersecting_edges', operation="'INTERSECT'", first_arg=None, mesh_1=None,
                        body_start="self = mesh_2[0]"),
            StackMethod(mesh='self', fname='boolean_union',      ret_socket='intersecting_edges', operation="'UNION'",     first_arg=None, mesh_1=None,
                        body_start="self = mesh_2[0]"),
            StackMethod(mesh='self', fname='boolean_difference', ret_socket='intersecting_edges', operation="'DIFFERENCE'", mesh_1='self')
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
            DomPropAttribute(fname='unsigned_angle', cache=True, ret_socket='unsigned_angle'),
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
        'Face': [
            DomPropAttribute(fname='island', cache=True),
            DomPropAttribute(fname='island_index', cache=True, ret_socket='island_index'),
            DomPropAttribute(fname='island_count', cache=True, ret_socket='island_count'),
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
            DomSetter(fname='shade_smooth', geometry='self', shade_smooth='attr_value'),
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
            Constructor(fname='LineEndPoints',           ret_socket='mesh', mode="'END_POINTS'", count_mode="'TOTAL'",      resolution=None,
                        arg_rename={'offset': 'end_location'}),
            Constructor(fname='LineOffset',              ret_socket='mesh', mode="'OFFSET'",     count_mode="'TOTAL'",      resolution=None),
            Constructor(fname='LineEndPointsResolution', ret_socket='mesh', mode="'END_POINTS'", count_mode="'RESOLUTION'", count=None,
                        arg_rename={'offset': 'end_location'}),
            Constructor(fname='LineOffsetResolution',    ret_socket='mesh', mode="'OFFSET'",     count_mode="'RESOLUTION'", count=None),
            ],
    },
    'GeometryNodeMeshUVSphere': {
        'Mesh': Constructor(fname='Circle', ret_socket='mesh'),
    },
}

MESH_TOPOLOGY = {
    'GeometryNodeCornersOfFace':           {
        'Mesh': Attribute(ret_socket=('corner_index', 'total')),
        'Face': [
            DomAttribute(fname='corners',       face_index='self.selection_index', ret_socket=('corner_index', 'total')),
            DomAttribute(fname='corners_index', face_index='self.selection_index', ret_socket='corner_index'),
            DomAttribute(fname='corners_total', face_index='self.selection_index', ret_socket='total'),
            ]
        },
    'GeometryNodeCornersOfVertex':         {
        'Mesh': Attribute(ret_socket=('corner_index', 'total')),
        'Vertex': [
            DomAttribute(fname='corners',       vertex_index='self.selection_index', ret_socket=('corner_index', 'total')),
            DomAttribute(fname='corners_index', vertex_index='self.selection_index', ret_socket='corner_index'),
            DomAttribute(fname='corners_total', vertex_index='self.selection_index', ret_socket='total'),
            ]
        },
    'GeometryNodeEdgesOfCorner':           {
        'Mesh': Attribute(ret_socket=('next_edge_index', 'previous_edge_index')),
        'Corner': [
            DomAttribute(fname='edges',               corner_index='self.selection_index', ret_socket=('next_edge_index', 'previous_edge_index')),
            DomPropAttribute(fname='previous_vertex', corner_index='self.selection_index', ret_socket='previous_edge_index'),
            DomPropAttribute(fname='next_vertex',     corner_index='self.selection_index', ret_socket='next_edge_index'),
            ]
        },
    'GeometryNodeEdgesOfVertex':           {
        'Mesh': Attribute(ret_socket=('edge_index', 'total')),
        'Vertex': [
            DomAttribute(fname='edges',       vertex_index='self.selection_index', ret_socket=('edge_index', 'total')),
            DomAttribute(fname='edges_index', vertex_index='self.selection_index', ret_socket='edge_index'),
            DomAttribute(fname='edges_total', vertex_index='self.selection_index', ret_socket='total'),
            ]
        },
    'GeometryNodeFaceOfCorner':            {
        'Mesh': Attribute(ret_socket=('face_index', 'index_in_face')),
        'Corner': [
            DomAttribute(fname='face',              corner_index='self.selection_index', ret_socket=('face_index', 'index_in_face')),
            DomPropAttribute(fname='face_index',    corner_index='self.selection_index', ret_socket='face_index'),
            DomPropAttribute(fname='index_in_face', corner_index='self.selection_index', ret_socket='index_in_face'),
            ]
        },
    'GeometryNodeOffsetCornerInFace':      {
        'Mesh':   Attribute(ret_socket='corner_index'),
        'Corner': DomAttribute(fname='offset_in_face', corner_index='self.selection_index', ret_socket='corner_index'),
        },
    'GeometryNodeVertexOfCorner':          {
        'Mesh':   Attribute(ret_socket='vertex_index'),
        'Corner': DomPropAttribute(fname='vertex_index', corner_index='self.selection_index', ret_socket='vertex_index'),
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

TEXT = {
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
            Static(fname='wave_bands', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'",
                          arg_rename={'bands_direction': 'direction'}),
            Static(fname='wave_rings', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'",
                          arg_rename={'rings_direction': 'direction'}),
        
            Static(fname='wave_bands_sine', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'", wave_profile="'SIN'",
                          arg_rename={'bands_direction': 'direction'}),
            Static(fname='wave_bands_saw', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'", wave_profile="'SAW'",
                          arg_rename={'bands_direction': 'direction'}),
            Static(fname='wave_bands_triangle', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'", wave_profile="'TRI'",
                          arg_rename={'bands_direction': 'direction'}),

            Static(fname='wave_rings_sine', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'", wave_profile="'SIN'",
                          arg_rename={'rings_direction': 'direction'}),
            Static(fname='wave_rings_saw', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'", wave_profile="'SAW'",
                          arg_rename={'rings_direction': 'direction'}),
            Static(fname='wave_rings_triangle', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'", wave_profile="'TRI'",
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
        'Vector':   StackMethod(rotation='self'),
        #'Rotation': StackMethod(rotation='self', fname='align_to_vector'),
    },
    'FunctionNodeBooleanMath': {
        'function': [
            Function(fname='b_and', ret_socket='boolean', operation="'AND'"),
            Function(fname='b_or',  ret_socket='boolean', operation="'OR'"),
            Function(fname='b_not', ret_socket='boolean', operation="'NOT'", boolean1=None),
            Function(fname='nand',  ret_socket='boolean', operation="'NAND'"),
            Function(fname='nor',   ret_socket='boolean', operation="'NOR'"),
            Function(fname='xnor',  ret_socket='boolean', operation="'XNOR'"),
            Function(fname='xor',   ret_socket='boolean', operation="'XOR'"),
            Function(fname='imply', ret_socket='boolean', operation="'IMPLY'"),
            Function(fname='nimply',ret_socket='boolean', operation="'NIMPLY'"),
            ],
        'Boolean': [
            Method(fname='b_and',   boolean0='self', ret_socket='boolean', operation="'AND'"),
            Method(fname='b_or',    boolean0='self', ret_socket='boolean', operation="'OR'"),
            Method(fname='b_not',   boolean0='self', ret_socket='boolean', operation="'NOT'", boolean1=None),
            Method(fname='nand',    boolean0='self', ret_socket='boolean', operation="'NAND'"),
            Method(fname='nor',     boolean0='self', ret_socket='boolean', operation="'NOR'"),
            Method(fname='xnor',    boolean0='self', ret_socket='boolean', operation="'XNOR'"),
            Method(fname='xor',     boolean0='self', ret_socket='boolean', operation="'XOR'"),
            Method(fname='imply',   boolean0='self', ret_socket='boolean', operation="'IMPLY'"),
            Method(fname='nimply',  boolean0='self', ret_socket='boolean', operation="'NIMPLY'"),
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
            Method(a='self', ret_socket='result', data_type="'INT'", c=None, angle=None, mode="'ELEMENT'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='less_than', operation="'LESS_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INT'", c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'INT'", c=None, angle=None, mode="'ELEMENT'",
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
            #Method(a='self', ret_socket='result', data_type="'RGBA'", c=None, angle=None, mode="'ELEMENT'"),
            Method(a='self', ret_socket='result', data_type="'RGBA'", c=None, angle=None, mode="'ELEMENT'",
                   fname='darker', operation="'DARKER'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'RGBA'", c=None, angle=None, mode="'ELEMENT'",
                   fname='brighter', operation="'BRIGHTER'", epsilon=None),
            Method(a='self', ret_socket='result', data_type="'RGBA'", c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'"),
            Method(a='self', ret_socket='result', data_type="'RGBA'", c=None, angle=None, mode="'ELEMENT'",
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
    'GeometryNodeFieldOnDomain': {
        'Geometry': Attribute(fname='interpolate_domain', dtype=('data_type', 'value'), ret_socket='value'),
        'Domain': DomAttribute(fname='interpolate', dtype=('data_type', 'value'), ret_socket='value'),
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
            
            #Function(ret_socket='value', fname='add',             operation="'ADD'",          value2=None),
            #Function(ret_socket='value', fname='subtract',        operation="'SUBTRACT'",     value2=None),
            #Function(ret_socket='value', fname='sub',             operation="'SUBTRACT'",     value2=None),
            #Function(ret_socket='value', fname='multiply',        operation="'MULTIPLY'",     value2=None),
            #Function(ret_socket='value', fname='mul',             operation="'MULTIPLY'",     value2=None),
            #Function(ret_socket='value', fname='divide',          operation="'DIVIDE'",       value2=None),
            #Function(ret_socket='value', fname='div',             operation="'DIVIDE'",       value2=None),
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
            
            # Implemented manually to take into account operation between value and vector

            #Method(ret_socket='value', fname='add',             operation="'ADD'",          value0='self', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='subtract',        operation="'SUBTRACT'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='sub',             operation="'SUBTRACT'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='multiply',        operation="'MULTIPLY'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='mul',             operation="'MULTIPLY'",     value0='self', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='divide',          operation="'DIVIDE'",       value0='self', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='div',             operation="'DIVIDE'",       value0='self', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='multiply_add',    operation="'MULTIPLY_ADD'", value0='self', arg_rename={'value1': 'multiplier', 'value2': 'addend'}),
            Method(ret_socket='value', fname='mul_add',         operation="'MULTIPLY_ADD'", value0='self', arg_rename={'value1': 'multiplier', 'value2': 'addend'}),

            Method(ret_socket='value', fname='power',           operation="'POWER'",        value0='self', arg_rename={'value1': 'exponent'}, value2=None),
            Method(ret_socket='value', fname='pow',             operation="'POWER'",        value0='self', arg_rename={'value1': 'exponent'}, value2=None),
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
            Function(fname='rotate_euler',      ret_socket='rotation', type="'EULER'", axis=None, angle=None),
            Function(fname='rotate_axis_angle', ret_socket='rotation', type="'AXIS_ANGLE'", rotate_by=None),
            ],
        #'Rotation': [
        #    Constructor(fname='Euler',     ret_socket='rotation', type="'EULER'",      axis=None, angle=None),
        #    Constructor(fname='AxisAngle', ret_socket='rotation', type="'AXIS_ANGLE'", rotate_by=None),
        #    Method(fname='rotate_euler',      ret_socket='rotation', rotation='self', type="'EULER'", axis=None, angle=None),
        #    Method(fname='rotate_axis_angle', ret_socket='rotation', rotation='self', type="'AXIS_ANGLE'", rotate_by=None),
        #    ],
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
        'Float':      Method(false='self', ret_socket='output', input_type="'FLOAT'",     com_args=['switch: Boolean', 'true: Float']),
        'Integer':    Method(false='self', ret_socket='output', input_type="'INT'",       com_args=['switch: Boolean', 'true: Integer']),
        'Boolean':    Method(false='self', ret_socket='output', input_type="'BOOLEAN'",   com_args=['switch: Boolean', 'true: Boolean']),
        'Vector':     Method(false='self', ret_socket='output', input_type="'VECTOR'",    com_args=['switch: Boolean', 'true: Vector']),
        'String':     Method(false='self', ret_socket='output', input_type="'STRING'",    com_args=['switch: Boolean', 'true: String']),
        'Color':      Method(false='self', ret_socket='output', input_type="'RGBA'",      com_args=['switch: Boolean', 'true: Color']),
        'Object':     Method(false='self', ret_socket='output', input_type="'OBJECT'",    com_args=['switch: Boolean', 'true: Object']),
        'Image':      Method(false='self', ret_socket='output', input_type="'IMAGE'",     com_args=['switch: Boolean', 'true: Image']),
        'Geometry':   Method(false='self', ret_socket='output', input_type="'GEOMETRY'",  com_args=['switch: Boolean', 'true: Geometry']),
        'Collection': Method(false='self', ret_socket='output', input_type="'COLLECTION'",com_args=['switch: Boolean', 'true: Collection']),
        'Texture':    Method(false='self', ret_socket='output', input_type="'TEXTURE'",   com_args=['switch: Boolean', 'true: Texture']),
        'Material':   Method(false='self', ret_socket='output', input_type="'MATERIAL'",  com_args=['switch: Boolean', 'true: Material']),
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
            Property(fname='separate', cache=True, vector='self'),
            #Property(fname='x', cache=True, vector='self', ret_socket='x'),
            #Property(fname='y', cache=True, vector='self', ret_socket='y'),
            #Property(fname='z', cache=True, vector='self', ret_socket='z'),
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
       **CURVE, 
       **CURVE_PRIMITIVES, 
       **CURVE_TOPOLOGY, 
       **GEOMETRY,
       **INPUT,
       **INSTANCES,
       **MATERIAL,
       **MESH,
       **MESH_PRIMITIVES,
       **MESH_TOPOLOGY,
       **POINT,
       **TEXT,
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










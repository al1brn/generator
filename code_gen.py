#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 17:41:59 2022

@author: alain
"""

# ====================================================================================================
# Class hierarchy

CLASSES = {
    
    'functions'     : ('functions', None),
    
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
# Data types

BYTE_COLOR   = "'BYTE_COLOR'"
FLOAT_COLOR  = "'FLOAT_COLOR'"  # RGBA
FLOAT        = "'FLOAT'"
STRING       = "'STRING'"
FLOAT2       = "'FLOAT2'"
BOOLEAN      = "'BOOLEAN'"
INT          = "'INT'"
RGBA         = "'RGBA'"         # FLOAT_COLOR
VECTOR       = "'VECTOR'"
FLOAT_VECTOR = "'FLOAT_VECTOR'" # VECTOR


# ====================================================================================================
# Source code generator

class Generator:
    
    INDENT = "    "
    
    def __init__(self, **kws):
        
        self.indent_      = Generator.INDENT    # Indentation
        self.decorator    = None                # if setter: generate @{fname}.setter
        self.fname_       = None                # function or method name
        self.first_arg    = None                # cls, self or None
        
        # To avoid mistakes in parameters, the use of self is controlled with self_
        # self_ = 'geometry' rather than self_='geometry'
        self.self_        = None

        self.stack        = False               # call self.stack
        self.attribute    = False               # call self.attribute
        
        self.header       = None                # replace the header generation by user source code
        self.body         = None                # replace the body generation by user source code
        self.body_start   = None                # first lines of code
        
        # Jul 2023 : ret_socket and ret_class as tuyple disabled
        # When several sockets exist, the node is returned
        
        self.ret_socket_  = None                # socket to return, returns node if None. Can be a tuple
        self.ret_class_   = None                # type of the return socket. Ignore if socket is None. must be a tuple if ret_socket is tuple.
        self.ret_node     = None                # return the node rather than a socket
        self.cache        = False               # use a cache for the node
        self.dtype        = None                # (data_type, value, color) implements: data_type = self.value_data_type(argument, data_type, color)
        
        self.is_domain    = False               # domain method
        
        self.kwargs       = {}                  # node argument values
        
        self.com_descr    = None                # Description string
        self.com_args     = None                # Args comments
        self.com_ret      = None                # Return description
        
        self.no_code      = False               # Do net generate source code (comments only)
        self.node_blid    = None                # Node bl_idname 
        
        self.for_test     = None                # Test code
        
        # ----------------------------------------------------------------------------------------------------
        # The use of self in node creation arguments is inverted for security (to track the use of self)
        #
        # We could use the following entry in **kwargs:
        # _ geometry='self'
        #
        # But we use the invert:
        # - self_ = 'geometry'
        #
        # We just have to invert it now
        
        kwargs = {**kws}
        if kwargs.get('self_') is not None:
            kwargs[kwargs['self_']] = 'self'
        
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
    # Disabling ret_socket and ret_class as tuple
    
    @property
    def ret_socket(self):
        return self.ret_socket_

    @ret_socket.setter
    def ret_socket(self, value):
        if isinstance(value, tuple):
            self.ret_socket_ = None
        else:
            self.ret_socket_ = value
    
    @property
    def ret_class(self):
        return self.ret_class_

    @ret_class.setter
    def ret_class(self, value):
        if isinstance(value, tuple):
            self.ret_class_ = None
        else:
            self.ret_class_ = value

    # ----------------------------------------------------------------------------------------------------
    # Return the node or a socket
    
    def return_node(self, node):
        if self.ret_node is None:
            if self.ret_socket is None:
                return True if node.output_sockets_count > 1 else False
            else:
                return False
        else:
            return self.ret_node
    
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
        call_arguments= args.node_init_arguments(**self.kwargs)
            
        return f"nodes.{node.node_name}({call_arguments})"
    
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
    

    # ====================================================================================================
    # Source code generation
    #
    # - Comment / documentation
    # - pyhon code    

    # ----------------------------------------------------------------------------------------------------
    # Anchor
    
    def anchor(self, node):
        s = self.fname(node)
        if self.decorator is not None:
            if self.decorator != "setter":
                if False:
                    s += f"-{self.decorator[1:]}"
        return s
    
    # ----------------------------------------------------------------------------------------------------
    # Generate the comments
    
    def gen_markdown(self, node):
        
        s = self.fname(node)
        if self.decorator is not None:
            if self.decorator == 'setter':
                yield
                
            s += f' <sub>*{self.decorator[1:]}*</sub>'
            
        if False:
            yield f"## {s}\n\n"
            
            yield "```python\n"
            yield f"{self.call_string(node)}\n\n"
            yield "```\n"
        
        if node is not None:
            yield f"> Node: [{node.bnode.name}]({node.bl_idname}.md) | [Blender reference]({node.blender_ref}) | [api reference]({node.blender_python_ref})\n\n"
        
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
        
        if isinstance(self.ret_socket, tuple) or self.return_node(node):
            yield f"![Node Image]({node.node_image_ref})\n\n"
        
        if self.com_ret is None:
            if self.decorator != 'setter':
                yield f"#### Returns:\n"
                if self.return_node(node):
                    yield f"- node with sockets {list(node.outputs.unames.keys())}\n"
                    
                elif self.ret_socket is None:
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
        
        text = ""
        for line in self.gen_markdown(node):
            if line is not None:
                text += line 
        lines = text.split("\n")
        del text
        
        yield self.indent(1) + '"""\n\n'    
        for line in lines:
            if line == "":
                yield "\n"
            else:
                yield self.indent(1) + line + "\n"
        yield self.indent(1) + '"""\n\n'

            
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
                scolor = f", color={self.dtype[2]}"
            else:
                scolor = ""
            yield self.indent(1) + f"{self.dtype[0]}_ = self.value_data_type({self.dtype[1]}, {default_data_type}{scolor})\n"
            self.kwargs[self.dtype[0]] = f"{self.dtype[0]}_"
        
        # ----- Node creation string

        snode = f"{self.node_call_str(node)}"
        ssock = None
        
        # ----- Attribute
        # attribute function returns a node

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
        # stack function returns a socket or a node
            
        if stack_func is not None:
            ssock = f"self.{stack_func}({snode})"
            snode = ssock + ".node"

        # ----- Return node, a socket or a tuple of sockets
        
        def check_output_socket(name):
            if name not in node.outputs.unames.keys():
                raise Exception(f"Node {node.bl_idname}: '{name}' is not a valid output socket name in {list(node.outputs.unames.keys())}")
        
        if self.return_node(node):
            sret = snode
            
        elif self.ret_socket is None:
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
                if class_name == 'functions':
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
    
    def gen_api_doc_OLD(self, node):
        
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
    def __init__(self, self_, **kwargs):
        
        kws = {**kwargs}
        if not 'first_arg' in kws:
            kws['first_arg'] = 'self'
        
        super().__init__(self_=self_, **kws)
        
class DomMethod(Method):
    def __init__(self, self_, **kwargs):
        super().__init__(self_=self_, is_domain=True, **kwargs)

# ----------------------------------------------------------------------------------------------------
# Property
        
class Property(Method):
    def __init__(self, self_, **kwargs):
        super().__init__(self_=self_, decorator="@property", **kwargs)
        
        self.com_args = []
        
class DomProperty(Property):
    def __init__(self, self_, **kwargs):
        super().__init__(self_=self_, is_domain=True, **kwargs)        

class Setter(Method):
    def __init__(self, self_, stack=True, **kwargs):
        super().__init__(self_=self_, decorator="setter", stack=stack, **kwargs)
        
        self.com_descr = "Node implemented as property setter."
        
        for k, v in self.kwargs.items():
            if v == 'attr_value':
                self.com_args  = [f"attr_value: {k}"]
                break
        self.com_ret = ""
        
class DomSetter(Setter):
    def __init__(self, self_, stack=True, **kwargs):
        super().__init__(self_=self_, is_domain=True, stack=stack, **kwargs)        

# ----------------------------------------------------------------------------------------------------
# Stack method
        
class StackMethod(Method):
    def __init__(self, self_, **kwargs):
        super().__init__(self_=self_, stack=True, **kwargs)

class DomStackMethod(StackMethod):
    def __init__(self, self_, **kwargs):
        super().__init__(self_=self_, is_domain=True, **kwargs)
    
# ----------------------------------------------------------------------------------------------------
# Attribute method
        
class Attribute(Method):
    def __init__(self, **kwargs):
        kws = {**kwargs}
        if not 'self_' in kws:
            kws['self_'] = None
            
        super().__init__(attribute=True, **kws)
        
class PropAttribute(Attribute):
    def __init__(self, **kwargs):
        super().__init__(decorator="@property", **kwargs)
        
class DomAttribute(Method):
    def __init__(self, **kwargs):
        kws = {**kwargs}
        if not 'self_' in kws:
            kws['self_'] = None
        
        super().__init__(is_domain=True, attribute=True, **kws)
        
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
    # Check use of self
    
    @staticmethod
    def check_use_of_self(classes, wnode):
        self_used_by = {}
        for cnames, generators in classes.items():
            if isinstance(generators, list):
                gens = generators
            else:
                gens = [generators]
                
            for gen in gens:
                ok_self = False
                for k, v in gen.kwargs:
                    if not isinstance(v, str):
                        continue
                    if v in ['self', 'self.data_socket']:
                        if not k in [self_used_by]:
                            self[k] = (cnames, gen.fname(wnode))
                            ok_self = True
                            break
                        
                if not ok_self:
                    pass
        
                        
        
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
        
        methods = self.class_methods('functions')
        
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
        
        if class_name != 'functions':
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
            
            f.write("from geonodes.core.node import Node, GroupInput, GroupOutput, Frame, SceneTime, Group\n")
            f.write("from geonodes.core.tree import Tree, Trees\n")
            f.write("from geonodes.core.simulation import Simulation\n\n")
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
    
    def create_nodes_menus(self, folder):
        
        nav_menu = "[main](../index.md) - [nodes](nodes.md) - [nodes menus](nodes_menus.md)"
        doc_header = f"> {nav_menu}\n\n"
        
        if False:
            print("Data classes api...")
            
            # ----------------------------------------------------------------------------------------------------
            # Classes documentation
            
            for class_name in self:
                
                # ----------------------------------------------------------------------------------------------------
                # Read the global and final description
                
                try:
                    descr_file_name = f"{folder}docs/{class_name}.md"
                    with open(descr_file_name, 'r') as f:
                        descr = f.readlines()
                except:
                    descr = None
                    
                try:
                    ex_file_name = f"{folder}docs/examples_{class_name}.md"
                    with open(ex_file_name, 'r') as f:
                        examples = f.readlines()
                except:
                    examples = None
                    
                # ----------------------------------------------------------------------------------------------------
                # Read the global and final description
    
                file_name = f"{folder}docs/api/{class_name}.md"
    
                with open(file_name, 'w') as f:
                    if class_name == 'functions':
                        f.write("# Functions\n\n")
                    else:
                        f.write(f"# class {class_name}\n\n")
                        
                    f.write(doc_header)
                    
                    # ----- Description
                    
                    if descr is not None:
                        f.writelines(descr)
                        
                    if examples is not None:
                        f.write("> see [examples](#examples)\n\n")
                        
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
                    
                    # ----- Documentation OLD
                    
                    if False:
                        for _, gen, wnode in methods:
                            ok_lines = False
                            for line in gen.gen_api_doc(wnode):
                                if line is not None:
                                    f.write(line.replace('CLASS_NAME', class_name))
                                    ok_lines = True
                                    
                            if ok_lines:
                                f.write(f"<sub>Go to [top](#class-{class_name}) - {nav_menu}</sub>\n\n")
                            
                    # ----- Examples
                    
                    if examples is not None:
                        f.writelines(examples)
                        
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
                    
                    # List of methods
                    
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
            'Output'            : OUTPUT,
            'Point'             : POINT,
            'Text'              : TEXT,
            'Texture'           : TEXTURE,
            'Utilities'         : UTILITIES,
            'UV'                : UV,
            'Vector'            : VECTOR_IMPL,
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
                            class_name = 'functions'
                        classes[class_name] = gens
                        
                if len(classes) == 0:
                    if blid not in ['NodeFrame', 'GeometryNodeGroup', 'NodeReroute',
                                    'NodeGroupInput', 'NodeGroupOutput']:
                        print(f"CAUTION: node not implemented in classes: {blid:35} {wnode.bnode.name}")
                    
                else:
                    
                    f.write("## Implementation\n\n")

                    f.write("| Class or method name | Definition |\n")
                    f.write("|----------------------|------------|\n")
                        

                    for class_name in sorted(classes):
                        
                        gens = classes[class_name]
                        
                        if class_name == 'functions': # function
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

            f.write(_1_ + "mesh       = gn.Mesh.Cube().mesh\n")
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
            
        # ----------------------------------------------------------------------------------------------------
        # Copy files from docs to docs/api
        
        if False:
            for fname in ['Tree.md', 'Trees.md']:
                fsource = folder + 'docs/' + fname
                ftarget = folder + 'docs/api/' + fname
                
                with open(fsource, 'r') as f:
                    text = f.readlines()
                    
                with open(ftarget, 'w') as f:
                    f.writelines(text)
                        
                            
# ====================================================================================================
# Methods which are manually implemented

COMMENTS = {}

# ====================================================================================================
# Attribute Menu

# Blender Version 3.5

ATTRIBUTE = {
    'GeometryNodeAttributeStatistic': {
        'Geometry': Method(self_='geometry', dtype=('data_type', 'attribute')),
        'Domain'  : [
            DomMethod(self_='geometry', dtype=('data_type', 'attribute')),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_mean',   ret_socket='mean'),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_median', ret_socket='median'),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_sum',    ret_socket='sum'),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_min',    ret_socket='min'),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_max',    ret_socket='max'),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_range',  ret_socket='range'),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_std',    ret_socket='standard_deviation'),
            DomMethod(self_='geometry', dtype=('data_type', 'attribute'), fname='attribute_var',    ret_socket='variance'),
            ],
        },
    
    'GeometryNodeAttributeDomainSize': {
        'Geometry' : Property(self_='geometry', cache=True),
        
        'Mesh'     : [
            Property(self_='geometry', cache=True, component="'MESH'"),
            Property(self_='geometry', cache=True, component="'MESH'", fname='point_count',  ret_socket='point_count'),
            Property(self_='geometry', cache=True, component="'MESH'", fname='face_count',   ret_socket='face_count'),
            Property(self_='geometry', cache=True, component="'MESH'", fname='edge_count',   ret_socket='edge_count'),
            Property(self_='geometry', cache=True, component="'MESH'", fname='corner_count', ret_socket='face_corner_count'),
            ],
        'Curve'    : [
            Property(self_='geometry', cache=True, component="'CURVE'"),
            Property(self_='geometry', cache=True, component="'CURVE'", fname='point_count',  ret_socket='point_count'),
            Property(self_='geometry', cache=True, component="'CURVE'", fname='spline_count',  ret_socket='spline_count'),
            ],
        'Points'   : Property(self_='geometry', cache=True, component="'POINTCLOUD'",ret_socket='point_count'),
        'Instances': Property(self_='geometry', cache=True, component="'INSTANCES'",  ret_socket='instance_count'),
        
        'Vertex'       : DomProperty(self_='geometry', fname='count', component="'MESH'", ret_socket='point_count'),
        'Face'         : DomProperty(self_='geometry', fname='count', component="'MESH'", ret_socket='face_count'),
        'Edge'         : DomProperty(self_='geometry', fname='count', component="'MESH'", ret_socket='edge_count'),
        'Corner'       : DomProperty(self_='geometry', fname='count', component="'MESH'", ret_socket='face_corner_count'),
        
        'Spline'       : DomProperty(self_='geometry', fname='count', component="'CURVE'", ret_socket='spline_count'),
        'ControlPoint' : DomProperty(self_='geometry', fname='count', component="'CURVE'", ret_socket='point_count'),
        
        'CloudPoint'   : DomProperty(self_='geometry', fname='count', component="'POINTCLOUD'", ret_socket='point_count'),
        'Instance'     : DomProperty(self_='geometry', fname='count', component="'INSTANCES'", ret_socket='instance_count'),
        
        },
    
    # V3.5 Blur attribute
    
    'GeometryNodeBlurAttribute' : {
        #  data_type, value , default = 'FLOAT' in ('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR')
        #'Geometry': Method(dtype=('data_type', 'value')),
        'Domain'  : [
            DomAttribute(dtype=('data_type', 'value'), ret_socket='value'),
            DomAttribute(fname='blur_float',   data_type=FLOAT,        ret_socket='value'),
            DomAttribute(fname='blur_integer', data_type=INT,          ret_socket='value'),
            DomAttribute(fname='blur_vector',  data_type=FLOAT_VECTOR, ret_socket='value'),
            DomAttribute(fname='blur_color',   data_type=FLOAT_COLOR,  ret_socket='value'),
            ],
        
        },
    
    'GeometryNodeCaptureAttribute': {
        'Geometry': [
            StackMethod(self_='geometry', ret_socket='attribute',    dtype=('data_type', 'value')),
            Static(fname='capture_attribute_node'), # Used to automatically capture attributes
            ],
        'Domain':   DomStackMethod(self_='geometry', ret_socket='attribute', dtype=('data_type', 'value')),
        },
    
    'GeometryNodeRemoveAttribute': {
        'Geometry': StackMethod(   self_='geometry'),
        'Domain'  : DomStackMethod(self_='geometry'),
        },
    
    'GeometryNodeStoreNamedAttribute': {
        'Geometry': [
            StackMethod(self_='geometry', dtype=('data_type', 'value')),
            StackMethod(self_='geometry',  fname='store_named_boolean', data_type=BOOLEAN),
            StackMethod(self_='geometry',  fname='store_named_integer', data_type=INT),
            StackMethod(self_='geometry',  fname='store_named_float',   data_type=FLOAT),
            StackMethod(self_='geometry',  fname='store_named_vector',  data_type=FLOAT_VECTOR),
            StackMethod(self_='geometry',  fname='store_named_color',   data_type=FLOAT_COLOR),
            ],
        'Domain'  : [
            # Before V3.5 = store_named_attribute implemented manually to operate on a selection
            # Float, integer, vector, color, byte color, boolean, 2D vector
            #('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BYTE_COLOR', 'BOOLEAN', 'FLOAT2')
            
            DomStackMethod(self_='geometry', fname='store_named_attribute',  dtype=('data_type', 'value')),
            
            DomStackMethod(self_='geometry', fname='store_named_float',      data_type=FLOAT),
            DomStackMethod(self_='geometry', fname='store_named_integer',    data_type=INT),
            DomStackMethod(self_='geometry', fname='store_named_vector',     data_type=FLOAT_VECTOR),
            DomStackMethod(self_='geometry', fname='store_named_color',      data_type=FLOAT_COLOR),
            DomStackMethod(self_='geometry', fname='store_named_byte_color', data_type=BYTE_COLOR),
            DomStackMethod(self_='geometry', fname='store_named_boolean',    data_type=BOOLEAN),
            DomStackMethod(self_='geometry', fname='store_named_2D_vector',  data_type=FLOAT2),
            ],
        },
}


COLOR = {
    'ShaderNodeValToRGB': {
        'functions': Function(),
        'Float': Property(self_='fac'),
    },
    'FunctionNodeCombineColor': {
        'functions': [
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
        'functions': [
            Function(fname='float_mix', ret_socket='result', data_type=FLOAT, blend_type="'MIX'", clamp_result=False, factor_mode="'UNIFORM'"),
            Function(fname='vector_mix', ret_socket='result', data_type=VECTOR, blend_type="'MIX'", clamp_result=False),
            
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_mix',              ),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_darken',       blend_type="'DARKEN'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_multiply',     blend_type="'MULTIPLY'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_burn',         blend_type="'BURN'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_lighten',      blend_type="'LIGHTEN'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_screen',       blend_type="'SCREEN'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_dodge',        blend_type="'DODGE'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_add',          blend_type="'ADD'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_overlay',      blend_type="'OVERLAY'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_soft_light',   blend_type="'SOFT_LIGHT'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_linear_light', blend_type="'LINEAR_LIGHT'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_difference',   blend_type="'DIFFERENCE'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_subtract',     blend_type="'SUBTRACT'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_divide',       blend_type="'DIVIDE'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_hue',          blend_type="'HUE'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_saturation',   blend_type="'SATURATION'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_color',        blend_type="'COLOR'"),
            Function(ret_socket='result', data_type=RGBA, factor_mode="'UNIFORM'", fname='color_value',        blend_type="'VALUE'"),
            ],
        'Color': [
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix',              ),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_darken',       blend_type="'DARKEN'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_multiply',     blend_type="'MULTIPLY'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_burn',         blend_type="'BURN'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_lighten',      blend_type="'LIGHTEN'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_screen',       blend_type="'SCREEN'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_dodge',        blend_type="'DODGE'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_add',          blend_type="'ADD'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_overlay',      blend_type="'OVERLAY'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_soft_light',   blend_type="'SOFT_LIGHT'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_linear_light', blend_type="'LINEAR_LIGHT'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_difference',   blend_type="'DIFFERENCE'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_subtract',     blend_type="'SUBTRACT'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_divide',       blend_type="'DIVIDE'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_hue',          blend_type="'HUE'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_saturation',   blend_type="'SATURATION'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_color',        blend_type="'COLOR'"),
            Method(ret_socket='result', self_='a', data_type=RGBA, factor_mode="'UNIFORM'", arg_rename={'b':'color'}, fname='mix_value',        blend_type="'VALUE'"),
            ],
        'Float': Method(ret_socket='result', self_='a', data_type=FLOAT, blend_type="'MIX'", arg_rename={'b': 'value'}, clamp_result=False, factor_mode="'UNIFORM'"),
        'Vector': [
            Method(ret_socket='result', self_='a', data_type=VECTOR, blend_type="'MIX'", arg_rename={'b': 'vector'}, clamp_result=False),
            Method(ret_socket='result', self_='a', data_type=VECTOR, blend_type="'MIX'", arg_rename={'b': 'vector'}, clamp_result=False, fname='mix_uniform', factor_mode="'UNIFORM'", factor=None),
            Method(ret_socket='result', self_='a', data_type=VECTOR, blend_type="'MIX'", arg_rename={'b': 'vector'}, clamp_result=False, fname='mix_non_uniform', factor_mode="'NON_UNIFORM'"),
            ]
    },
    'ShaderNodeRGBCurve': {
        'functions': Function(),
        'Color': Property(self_='color'),
    },
    'FunctionNodeSeparateColor': {
        'functions': [
            Function(fname='separate_rgb', ret_socket=('red', 'green', 'blue', 'alpha'), mode="'RGB'"),
            Function(fname='separate_hsv', ret_socket=('red', 'green', 'blue', 'alpha'), mode="'HSV'"),
            Function(fname='separate_hsl', ret_socket=('red', 'green', 'blue', 'alpha'), mode="'HSL'"),
                     ],
        # Implemented manually to manage cache
        'Color'   : [
            Method(self_='color', fname='separate_color'),
        #    Property(fname='rgb', ret_socket=('red', 'green', 'blue', 'alpha'), self_='color', mode="'RGB'"),
        #    Property(fname='hsv', ret_socket=('red', 'green', 'blue', 'alpha'), self_='color', mode="'HSV'"),
        #    Property(fname='hsl', ret_socket=('red', 'green', 'blue', 'alpha'), self_='color', mode="'HSL'"),
            
        #    Property(self_='color', mode="'RGB'", fname='alpha',   ret_socket='alpha'),
            
        #    Property(self_='color', mode="'RGB'", fname='red',        ret_socket='red'),
        #    Property(self_='color', mode="'RGB'", fname='green',      ret_socket='green'),
        #    Property(self_='color', mode="'RGB'", fname='blue',       ret_socket='blue'),
            
        #    Property(self_='color', mode="'HSV'", fname='hue',        ret_socket='red'),
        #    Property(self_='color', mode="'HSV'", fname='saturation', ret_socket='green'),
        #    Property(self_='color', mode="'HSV'", fname='value',      ret_socket='blue'),
            
        #    Property(self_='color', mode="'HSL'", fname='lightness',  ret_socket='blue'),
            ],
    },
}


CURVE = {
    'GeometryNodeCurveLength': {
        'Curve': Property(fname='length', ret_socket='length', self_='curve'),
    },
    'GeometryNodeCurveToMesh': {
        'Curve': Method(fname='to_mesh', ret_socket='mesh', ret_class='Mesh', self_='curve'),
    },
    'GeometryNodeCurveToPoints': {
        'Curve': [
            Method(self_='curve', fname='to_points',           ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None)),
            Method(self_='curve', fname='to_points_count',     ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None), mode="'COUNT'",     length=.1),
            Method(self_='curve', fname='to_points_length',    ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None), mode="'LENGTH'",    count=10),
            Method(self_='curve', fname='to_points_evaluated', ret_socket=('points', 'tangent', 'normal', 'rotation'), ret_class=('Points', None, None, None), mode="'EVALUATED'", count=10, length=.1),
            ],
    },
    'GeometryNodeDeformCurvesOnSurface': {
        'Curve': StackMethod(self_='curves', fname='deform_on_surface'),
    },
    'GeometryNodeFillCurve': {
        'Curve': [
            Method(fname='fill',           self_='curve', ret_socket='mesh', ret_class='Mesh'),
            Method(fname='fill_triangles', self_='curve', ret_socket='mesh', ret_class='Mesh', mode="'TRIANGLES'"),
            Method(fname='fill_ngons',     self_='curve', ret_socket='mesh', ret_class='Mesh', mode="'NGONS'"),
            ]
    },
    'GeometryNodeFilletCurve': {
        'Curve': [
            StackMethod(fname='fillet',        self_='curve'),
            StackMethod(fname='fillet_bezier', self_='curve', mode="'BEZIER'", count=1),
            StackMethod(fname='fillet_poly',   self_='curve', mode = "'POLY'"),
            ],
    },
    'GeometryNodeResampleCurve': {
        'Curve': [
            StackMethod(fname='resample',           self_='curve'),
            StackMethod(fname='resample_count',     self_='curve', mode="'COUNT'",     length=.1),
            StackMethod(fname='resample_length',    self_='curve', mode="'LENGTH'",    count=10),
            StackMethod(fname='resample_evaluated', self_='curve', mode="'EVALUATED'", count=10, length=.1),
            ],
        'Spline': [
            DomStackMethod(fname='resample',           self_='curve'),
            DomStackMethod(fname='resample_count',     self_='curve', mode="'COUNT'", length=.1),
            DomStackMethod(fname='resample_length',    self_='curve', mode="'LENGTH'", count=10),
            DomStackMethod(fname='resample_evaluated', self_='curve', mode="'EVALUATED'", count=10, length=.1),
            ],
    },
    'GeometryNodeReverseCurve': {
        'Curve':  StackMethod(fname='reverse', self_='curve'),
    },
    'GeometryNodeSampleCurve': {
        'Curve':  StackMethod(fname='sample', self_ = 'curves'),
    },
    'GeometryNodeSubdivideCurve': {
        'Curve':  StackMethod(fname='subdivide', self_='curve'),
    },
    'GeometryNodeTrimCurve': {
        'Curve':  [
            StackMethod(self_='curve', fname='trim',        header="def trim(self, selection=None, start=None, end=None, mode='FACTOR'):", start0='start', end0='end', start1='start', end1='end'),
            StackMethod(self_='curve', fname='trim_factor', arg_rename={'start0': 'start', 'end0': 'end'}, start1=None, end1=None, mode="'FACTOR'"),
            StackMethod(self_='curve', fname='trim_length', arg_rename={'start1': 'start', 'end1': 'end'}, start0=None, end0=None, mode="'LENGTH'"),
            ],
        'Spline': [
            DomStackMethod(self_='curve', fname='trim',        header="def trim(self, start=None, end=None, mode='FACTOR'):", start0='start', end0='end', start1='start', end1='end'),
            DomStackMethod(self_='curve', fname='trim_factor', arg_rename={'start0': 'start', 'end0': 'end'}, start1=None, end1=None, mode="'FACTOR'"),
            DomStackMethod(self_='curve', fname='trim_length', arg_rename={'start1': 'start', 'end1': 'end'}, start0=None, end0=None, mode="'LENGTH'"),
            ],
    },
    'GeometryNodeInputCurveHandlePositions': {
        'ControlPoint': [
            DomAttribute(    fname='handle_positions'),
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
            DomStackMethod(fname='set_normal', self_='curve'),
            DomSetter(fname='normal', stack=True, self_='curve', mode='attr_value', for_test="curve.splines.normal = 'MINIMUM_TWIST'"),
            ],
    },
    'GeometryNodeSetCurveRadius': {
        'ControlPoint': [
            DomStackMethod(fname='set_radius', self_='curve'),
            DomSetter(fname='radius', stack=True, self_='curve', radius='attr_value'),
            ],
    },
    'GeometryNodeSetCurveTilt': {
        'ControlPoint': [
            DomStackMethod(fname='set_tilt', self_='curve'),
            DomSetter(fname='tilt', stack=True, self_='curve', tilt='attr_value'),
            ],
    },
    'GeometryNodeSetCurveHandlePositions': {
        'ControlPoint': [
            DomStackMethod(fname='set_handle_positions',       self_='curve'),
            DomStackMethod(fname='set_handle_positions_left',  self_='curve', mode="'LEFT'"),
            DomStackMethod(fname='set_handle_positions_right', self_='curve', mode="'RIGHT'"),
            DomSetter(fname='left_handle_positions', self_='curve',  stack=True, position='attr_value', offset=None, mode="'LEFT'",
                           for_test="curve.points.left_handle_positions = (1, 2, 3)"),
            DomSetter(fname='right_handle_positions', self_='curve', stack=True, position='attr_value', offset=None, mode="'RIGHT'",
                           for_test="curve.points.right_handle_positions = (1, 2, 3)"),
            ],
    },
    'GeometryNodeCurveSetHandles': {
        'ControlPoint': [
            DomStackMethod(fname='set_handle_type_node', self_='curve'),
            Source(
                header="def set_handle_type(self, left=True, right=True, handle_type=""'AUTO'""):",
                body  ="mode={'LEFT'} if left else {}\nif right: mode.add('RIGHT')\nreturn self.set_handle_type_node(handle_type=handle_type, mode=mode)"
                )
            ],
    },
    'GeometryNodeSetSplineCyclic': {
        'Spline': [
            DomStackMethod(fname='set_cyclic', self_='geometry'),
            DomSetter(fname='cyclic', stack=True, self_='geometry', cyclic='attr_value'),
            ],
    },
    'GeometryNodeSetSplineResolution': {
        'Spline': [
            DomStackMethod(fname='set_resolution', self_='geometry'),
            DomSetter(fname='resolution', stack=True, self_='geometry', resolution='attr_value'),
            ],
    },
    'GeometryNodeCurveSplineType': {
        'Spline': [
            DomStackMethod(fname='set_type', self_='curve'),
            PropReadError(fname='type', class_name='Curve'),
            DomSetter(fname='type', stack=True, self_='curve', spline_type='attr_value', for_test="curve.splines.type = 'POLY'"),
            ],
    },
    
    # V 3.5
    
    'GeometryNodeInterpolateCurves': {
        'Curve'  : Method(self_='guide_curves', fname='interpolate'),
        'Points' : Method(self_='points',       fname='interpolate'),
        ('Vertex', 'ControlPoint', 'CloudPoint') :
            DomMethod(self_='points', fname='interpolate'),

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
        'Curve': Constructor(fname='BezierSegment', ret_socket='curve'),
    },
    'GeometryNodeCurvePrimitiveCircle': {
        'Curve': [
            Constructor(fname='Circle', ret_socket='curve', mode="'RADIUS'", point_1=None, point_2=None, point_3=None),
            Static(fname='CircleFromPoints', ret_socket=('curve', 'center'), ret_class=('Curve', None), mode="'POINTS'", radius=None),
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
        'Curve':        Attribute(   fname='offset_point',     ret_socket=('is_valid_offset', 'point_index')),
        'ControlPoint': DomAttribute(fname='offset', ret_socket=('is_valid_offset', 'point_index'), point_index='self.selection_index'),
    },
    'GeometryNodeCurveOfPoint': {
        'Curve':        Attribute(   fname='curve_of_point',  ret_socket=('curve_index', 'index_in_curve')),
        'ControlPoint': DomAttribute(fname='curve', ret_socket=('curve_index', 'index_in_curve'), point_index='self.selection_index'),
    },
    'GeometryNodePointsOfCurve': {
        'Curve':  Attribute(   fname='points_of_curve', ret_socket=('point_index', 'total')),
        'Spline': DomAttribute(fname='points',      ret_socket=('point_index', 'total'), curve_index='self.selection_index'),
    },
}

GEOMETRY = {
    'GeometryNodeBoundBox': {
        'Geometry': [
            Property(fname='bounding_box', cache=True, ret_socket='bounding_box', ret_class='Mesh', self_='geometry'),
            Property(fname='bounding_box_min', cache=True, ret_socket='min', self_='geometry'),
            Property(fname='bounding_box_min', cache=True, ret_socket='max', self_='geometry'),
            ],
    },
    'GeometryNodeConvexHull': {
        'Geometry': Property(fname='convex_hull', ret_socket='convex_hull', ret_class='Mesh', self_='geometry'),
    },
    'GeometryNodeDeleteGeometry': {
        'Geometry': StackMethod(fname='delete', self_='geometry'),
        'Mesh'    : [
            StackMethod(fname='delete_all',   self_='geometry', mode="'ALL'"),
            StackMethod(fname='delete_edges', self_='geometry', mode="'EDGE_FACE'"),
            StackMethod(fname='delete_faces', self_='geometry', mode="'ONLY_FACE'"),
            ],
        ('Vertex', 'Edge','Face', 'Spline', 'ControlPoint', 'Instance', 'CloudPoint'):
            DomStackMethod(fname='delete', self_='geometry'),
        'Vertex'  : [
            DomStackMethod(fname='delete_all',   self_='geometry', mode="'ALL'"),
            DomStackMethod(fname='delete_edges', self_='geometry', mode="'EDGE_FACE'"),
            DomStackMethod(fname='delete_faces', self_='geometry', mode="'ONLY_FACE'"),
            ],
        'Edge'  : [
            DomStackMethod(fname='delete_all',   self_='geometry', mode="'ALL'"),
            DomStackMethod(fname='delete_edges', self_='geometry', mode="'EDGE_FACE'"),
            DomStackMethod(fname='delete_faces', self_='geometry', mode="'ONLY_FACE'"),
            ],
        'Face'  : [
            DomStackMethod(fname='delete_all',   self_='geometry', mode="'ALL'"),
            DomStackMethod(fname='delete_edges', self_='geometry', mode="'EDGE_FACE'"),
            DomStackMethod(fname='delete_faces', self_='geometry', mode="'ONLY_FACE'"),
            ],
    },
    'GeometryNodeDuplicateElements': {
        'Geometry' : StackMethod(fname='duplicate',    ret_socket='duplicate_index', self_='geometry'),
        ('Vertex', 'ControlPoint', 'CloudPoint', 'Edge', 'Face', 'Instance'): 
            DomStackMethod(fname='duplicate', ret_socket='duplicate_index', self_='geometry'),
        # For this node Spline Domain is SPLINE and nor CURVE !
        'Spline': DomStackMethod(fname='duplicate', ret_socket='duplicate_index', self_='geometry', domain="'SPLINE'"),
    },
    'GeometryNodeProximity': {
        'Geometry' : [
            Attribute(fname='proximity',        ),
            Attribute(fname='proximity_points', target_element="'POINTS'"),
            Attribute(fname='proximity_edges',  target_element="'EDGES'"),
            Attribute(fname='proximity_faces',  target_element="'FACES'"),
            ],
        ('Vertex', 'ControlPoint', 'CloudPoint') :
            DomAttribute(fname='proximity', target_element="'POINTS'"),
        'Edge':
            DomAttribute(fname='proximity', target_element="'EDGES'"),
        'Face':
            DomAttribute(fname='proximity', target_element="'FACES'"),
    },
    'GeometryNodeGeometryToInstance': {
        'functions': Function(ret_socket='instances', ret_class='Instances'),
        'Geometry': Method(self_=None, fname='to_instance', first_arg=None, ret_socket='instances', ret_class='Instances'),
    },
    'GeometryNodeJoinGeometry': {
        'functions': Function(ret_socket='geometry'),
        'Geometry': Method(self_=None, fname='join', first_arg=None, body_start="self = geometry[0]", ret_socket='geometry'),
    },
    'GeometryNodeMergeByDistance': {
        'Geometry': StackMethod(self_='geometry'),
        'Vertex'  : [
            DomStackMethod(self_='geometry'),
            DomStackMethod(self_='geometry', fname='merge_by_distance_connected', mode="'CONNECTED'"),
            ],
    },
    'GeometryNodeRaycast': {
        'Geometry' : [
            Attribute(dtype=('data_type', 'attribute')),
            Attribute(fname='raycast_interpolated', dtype=('data_type', 'attribute'), mapping="'INTERPOLATED'"),
            Attribute(fname='raycast_nearest',      dtype=('data_type', 'attribute'), mapping="'NEAREST'"),
            ],
    },
    'GeometryNodeSampleIndex': {
        'Geometry': Method(   self_='geometry', dtype=('data_type', 'value'), ret_socket='value'),
        'Domain'  : DomMethod(self_='geometry', dtype=('data_type', 'value'), ret_socket='value', index_VALUE='self.index_for_sample(index)'),
    },
    'GeometryNodeSampleNearest': {
        'Geometry': Method(self_='geometry', ret_socket='index'),
        ('Vertex', 'Edge', 'Face', 'Corner', 'CloudPoint'): DomMethod(self_='geometry', ret_socket='index'),
    },
    'GeometryNodeSeparateComponents': {
        'Geometry': [
            Property(self_='geometry', cache=True),
            Property(self_='geometry', cache=True, fname='mesh_component',      ret_socket='mesh',        ret_class='Mesh'),
            Property(self_='geometry', cache=True, fname='curve_component',     ret_socket='curve',       ret_class='Curve'),
            Property(self_='geometry', cache=True, fname='points_component',    ret_socket='point_cloud', ret_class='Points'),
            Property(self_='geometry', cache=True, fname='volume_component',    ret_socket='volume',      ret_class='Volume'),
            Property(self_='geometry', cache=True, fname='instances_component', ret_socket='instances',   ret_class='Instances'),
            ],
    },
    'GeometryNodeSeparateGeometry': {
        'Geometry': Method(self_='geometry', fname='separate', ret_socket=('selection', 'inverted')),
        ('Vertex', 'Edge', 'Face', 'ControlPoint', 'Spline', 'Instance'):
            DomMethod(self_='geometry', fname='separate', ret_socket=('selection', 'inverted')),
    },
    'GeometryNodeTransform': {
        'Geometry': [
            StackMethod(self_='geometry'),
            StackMethod(self_='geometry', fname='transform'),
            ]
    },
    'GeometryNodeSetID': {
        'Geometry': StackMethod(self_='geometry'),
        'Domain'  : [
            DomStackMethod(self_='geometry'),
            DomSetter(     self_='geometry', fname='ID', ID='attr_value'),
            ],
    },
    'GeometryNodeSetPosition': {
        'Geometry': StackMethod(self_='geometry'),
        'Domain'  : [
            DomStackMethod(self_='geometry'),
            DomSetter(     self_='geometry', fname='position', position='attr_value', offset=None, 
                      body_start = "if attr_value is None: return self",
                      ),
            PropReadError(fname='position_offset', class_name='Domain'),
            DomSetter(fname='position_offset', stack=True, self_='geometry', position=None, offset='attr_value'),
            ],
    },
    
}

INPUT = {
    'FunctionNodeInputBool': {
        'Boolean': Constructor(fname='Boolean', ret_socket='boolean'),
    },
    'GeometryNodeCollectionInfo': {
        'Geometry': Constructor(fname='Collection', ret_socket='instances'),
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
            # Self is replaced by object!
            Method(self_=None, fname='info', object='self.bobject'),
            Method(self_=None, fname='location', ret_socket='location', object='self.bobject'),
            Method(self_=None, fname='rotation', ret_socket='rotation', object='self.bobject'),
            Method(self_=None, fname='scale',    ret_socket='scale',    object='self.bobject'),
            Method(self_=None, fname='geometry', ret_socket='geometry', object='self.bobject'),
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
        'Geometry': PropAttribute(   fname='ID', ret_socket='ID'),
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
            Attribute(fname='named_float',   ret_socket='attribute', data_type=FLOAT),
            Attribute(fname='named_integer', ret_socket='attribute', data_type=INT),
            Attribute(fname='named_vector',  ret_socket='attribute', data_type=FLOAT_VECTOR),
            Attribute(fname='named_color',   ret_socket='attribute', data_type=FLOAT_COLOR),
            Attribute(fname='named_boolean', ret_socket='attribute', data_type=BOOLEAN),
            
            # V3.5

            Attribute(fname='named_attribute_exists', ret_socket='exists'),
            ],
        'Domain': [
            DomAttribute(fname='named_attribute',   ret_socket='attribute'),
            DomAttribute(fname='named_float',   ret_socket='attribute', data_type=FLOAT),
            DomAttribute(fname='named_integer', ret_socket='attribute', data_type=INT),
            DomAttribute(fname='named_vector',  ret_socket='attribute', data_type=FLOAT_VECTOR),
            DomAttribute(fname='named_color',   ret_socket='attribute', data_type=FLOAT_COLOR),
            DomAttribute(fname='named_boolean', ret_socket='attribute', data_type=BOOLEAN),
            
            # V3.5
            DomAttribute(fname='named_attribute_exists', ret_socket='exists'),
            ],
    },
    'GeometryNodeInputNormal': {
        'Geometry': PropAttribute(   fname='normal', ret_socket='normal'),
        'Domain'  : DomPropAttribute(fname='normal', ret_socket='normal'),
        'Spline'  : DomPropAttribute(fname='normal', ret_socket='normal'),
    },
    'GeometryNodeInputPosition': {
        'Geometry': PropAttribute(   fname='position', ret_socket='position'),
        'Domain'  : DomPropAttribute(fname='position', ret_socket='position'),
    },
    'GeometryNodeInputRadius': {
        'Geometry'   : PropAttribute(fname='radius', ret_socket='radius'),
        #'Domain'     : DomPropAttribute(fname='radius', ret_socket='radius'),
        #'Spline'     : DomPropAttribute(fname='radius', ret_socket='radius'),
        #'CloudPoint' : DomPropAttribute(fname='radius', ret_socket='radius'),
        'ControlPoint' : DomPropAttribute(fname='radius', ret_socket='radius'),
        'CloudPoint' :   DomPropAttribute(fname='radius', ret_socket='radius'),
    },
    'GeometryNodeInputSceneTime': {
        'Float': [
            Constructor(fname='Seconds', ret_socket='seconds'),
            Constructor(fname='Frame', ret_socket='frame'),
            ]
    },
    
    # V3.5
    
    'GeometryNodeImageInfo': {
        'Image': [
            Method(self_='image', fname='info'),
            Method(self_='image', fname='width',        ret_socket='width'),
            Method(self_='image', fname='height',       ret_socket='height'),
            Method(self_='image', fname='has_alpha',    ret_socket='has_alpha'),
            Method(self_='image', fname='frame_count',  ret_socket='frame_count'),
            Method(self_='image', fname='fps',          ret_socket='fps'),
            ]
    },
    

}

INSTANCES = {
    'GeometryNodeInstanceOnPoints': {
        'Instances'     : [
            Constructor(fname='InstanceOnPoints', ret_socket='instances'),
            Method(fname='on_points', ret_socket='instances', ret_classes='Instances', self_='instance'),
            ],
        ('Points', 'Mesh', 'Curve') : Method(ret_socket='instances', ret_classes='Instances', self_='points'),
        'Vertex'        : DomMethod(ret_socket='instances', ret_class='Instances', self_='points'),
        'ControlPoint'  : DomMethod(ret_socket='instances', ret_class='Instances', self_='points'),
        'CloudPoint'    : DomMethod(ret_socket='instances', ret_class='Instances', self_='points'),
    },
    'GeometryNodeInstancesToPoints': {
        'Instances': Method(fname='to_points', ret_socket='points', ret_class='Points', self_='instances'),
        'Instance':  DomMethod(fname='to_points', ret_socket='points', ret_class='Points', self_='instances'),
        
    },
    'GeometryNodeRealizeInstances': {
        'Instances': Method(fname='realize', self_='geometry' ,ret_socket='geometry'),
    },
    'GeometryNodeRotateInstances': {
        'Instances': StackMethod(fname='rotate', self_='instances'),
        'Instance':  DomStackMethod(fname='rotate', self_='instances'),
    },
    'GeometryNodeScaleInstances': {
        'Instances': StackMethod(fname='set_scale', self_='instances'),
        'Instance':  DomStackMethod(fname='set_scale', self_='instances'),
    },
    'GeometryNodeTranslateInstances': {
        'Instances': StackMethod(   self_='instances', fname='translate'),
        'Instance':  DomStackMethod(self_='instances', fname='translate'),
    },
    'GeometryNodeInputInstanceScale': {
        'Instances': PropAttribute(   fname='scale', ret_socket='scale'),
        'Instance':  DomPropAttribute(fname='scale', ret_socket='scale'),
    },
    'GeometryNodeInputInstanceRotation': {
        'Instances': PropAttribute(   fname='rotation', ret_socket='rotation'),
        'Instance':  DomPropAttribute(fname='rotation', ret_socket='rotation'),
    },    
}

MATERIAL = {
    'GeometryNodeReplaceMaterial': {
        'Geometry': StackMethod(self_='geometry'),
    },
    'GeometryNodeInputMaterialIndex': {
        'Geometry':         PropAttribute(   ret_socket='material_index'),
        ('Face', 'Spline'): DomPropAttribute(ret_socket='material_index'),
    },
    'GeometryNodeMaterialSelection': {
        'Geometry': Attribute(   ret_socket='selection'),
        'Domain':   DomAttribute(ret_socket='selection'),
    },
    'GeometryNodeSetMaterial': {
        ('Mesh', 'Points', 'Volume'): StackMethod(self_='geometry'),
        ('Face', 'CloudPoint'):   [
            DomStackMethod(self_='geometry'),
            PropReadError(fname='material', class_name='Domain'),
            DomSetter(fname='material', self_='geometry', material='attr_value'),
            ]
    },
    'GeometryNodeSetMaterialIndex': {
        'Geometry': StackMethod(self_='geometry'),
        ('Face', 'Spline'): [
            DomStackMethod(self_='geometry'),
            DomSetter(fname='material_index', self_='geometry', material_index='attr_value'),
            ]
    },
}

MESH = {
    'GeometryNodeDualMesh': {
        'Mesh': Method(self_='mesh', ret_socket='dual_mesh', ret_class='Mesh'),
    },
    'GeometryNodeEdgePathsToCurves': {
        'Mesh': Method(   self_='mesh', ret_socket='curves', ret_class='Curve'),
        'Edge': DomMethod(self_='mesh', ret_socket='curves', ret_class='Curve'),
    },
    'GeometryNodeEdgePathsToSelection': {
        'Mesh': Method(self_='mesh', ret_socket='selection'),
    },
    'GeometryNodeExtrudeMesh': {
        'Mesh':   StackMethod(   fname='extrude', self_='mesh', ret_socket=('top', 'side')),
        'Face':   DomStackMethod(fname='extrude', self_='mesh', ret_socket=('top', 'side'), mode="'FACES'"),
        'Edge':   DomStackMethod(fname='extrude', self_='mesh', ret_socket=('top', 'side'), mode="'EDGES'"),
        'Vertex': DomStackMethod(fname='extrude', self_='mesh', ret_socket=('top', 'side'), mode="'VERTICES'"),
    },
    'GeometryNodeFlipFaces': {
        'Mesh':   StackMethod(self_='mesh'),
        'Face':   DomStackMethod(fname='flip', self_='mesh'),
    },
    'GeometryNodeMeshBoolean': {
        'Mesh':   [
            StackMethod(self_='mesh', fname='boolean_intersect',  ret_socket='intersecting_edges', operation="'INTERSECT'", first_arg=None, mesh_1=None,
                        body_start="self = mesh_2[0]"),
            StackMethod(self_='mesh', fname='boolean_union',      ret_socket='intersecting_edges', operation="'UNION'",     first_arg=None, mesh_1=None,
                        body_start="self = mesh_2[0]"),
            StackMethod(self_='mesh_1', fname='boolean_difference', ret_socket='intersecting_edges', operation="'DIFFERENCE'")
            ],
    },
    'GeometryNodeMeshToCurve': {
        'Mesh': Method(   fname='to_curve', self_='mesh', ret_socket='curve', ret_class='Curve'),
        'Edge': DomMethod(fname='to_curve', self_='mesh', ret_socket='curve', ret_class='Curve'),
    },
    'GeometryNodeMeshToPoints': {
        'Mesh':   Method(   fname='to_points', self_='mesh', ret_socket='points', ret_class='Points'),
        'Vertex': DomMethod(fname='to_points', self_='mesh', ret_socket='points', ret_class='Points'),
    },
    'GeometryNodeMeshToVolume': {
        'Mesh':   Method(   fname='to_volume', self_='mesh', ret_socket='volume', ret_class='Volume'),
        'Vertex': DomMethod(fname='to_volume', self_='mesh', ret_socket='volume', ret_class='Volume'),
    },
    'GeometryNodeSampleNearestSurface': {
        'Mesh':   Method(self_='mesh', ret_socket='value', dtype=('data_type', 'value')),
    },
    'GeometryNodeSampleUVSurface': {
        'Mesh':   Method(self_='mesh', ret_socket=('value', 'is_valid'), dtype=('data_type', 'value')),
    },
    'GeometryNodeScaleElements': {
        'Mesh':   [
            StackMethod(self_='geometry'),
            StackMethod(self_='geometry',    fname='scale_uniform',     scale_mode="'UNIFORM'", axis=None),
            StackMethod(self_='geometry',    fname='scale_single_axis', scale_mode="'SINGLE_AXIS'"),
            ],
        'Face': [
            DomStackMethod(self_='geometry', fname='scale_uniform',     scale_mode="'UNIFORM'", axis=None),
            DomStackMethod(self_='geometry', fname='scale_single_axis', scale_mode="'SINGLE_AXIS'"),
            ],
        'Edge': [
            DomStackMethod(self_='geometry', fname='scale_uniform',     scale_mode="'UNIFORM'", axis=None),
            DomStackMethod(self_='geometry', fname='scale_single_axis', scale_mode="'SINGLE_AXIS'"),
            ],
    },
    'GeometryNodeSplitEdges': {
        'Mesh': StackMethod(   self_='mesh'),
        'Edge': DomStackMethod(self_='mesh', fname='split'),
    },
    'GeometryNodeSubdivideMesh': {
        'Mesh': StackMethod(self_='mesh', fname='subdivide'),
    },
    'GeometryNodeSubdivisionSurface': {
        'Mesh': StackMethod(self_='mesh'),
    },
    'GeometryNodeTriangulate': {
        'Mesh': StackMethod(   self_='mesh'),
        'Face': DomStackMethod(self_='mesh'),
    },
    'GeometryNodeInputMeshEdgeAngle': {
        'Edge': [
            DomPropAttribute(fname='angle',          cache=True),
            DomPropAttribute(fname='unsigned_angle', cache=True, ret_socket='unsigned_angle'),
            DomPropAttribute(fname='signed_angle',   cache=True, ret_socket='signed_angle'),
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
        'Mesh': Attribute(   ret_socket='boundary_edges'),
        'Face': DomAttribute(face_group_id='self.selection_index', ret_socket='boundary_edges'),
    },
    'GeometryNodeInputMeshFaceIsPlanar': {
        'Mesh': Attribute(   ret_socket='planar'),
        'Face': DomAttribute(fname='is_planar', ret_socket='planar'),
    },
    'GeometryNodeInputShadeSmooth': {
        'Mesh': Attribute(ret_socket='smooth'),
        'Face': DomPropAttribute(fname='shade_smooth', ret_socket='smooth'),
    },
    'GeometryNodeInputMeshIsland': {
        'Mesh': [
            PropAttribute(fname='island',       cache=True),
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
        'Mesh': StackMethod(self_='geometry'),
        'Face': [
            DomStackMethod(self_='geometry'),
            DomSetter(     self_='geometry', fname='shade_smooth', shade_smooth='attr_value'),
            ],
    },
    
    # New V3.5
    
    'GeometryNodeEdgesToFaceGroups': {
        'Mesh' : Attribute(ret_socket='face_group_id'),
        'Edge' : DomAttribute(fname='to_face_groups', boundary_edges='self.selection', ret_socket='face_group_id'),
    },
    
}

MESH_PRIMITIVES = {
    'GeometryNodeMeshCone': {
        'Mesh': Static(fname='Cone')
    },
    'GeometryNodeMeshCube': {
        'Mesh': Constructor(fname='Cube')
    },
    'GeometryNodeMeshCylinder': {
        'Mesh': Static(fname='Cylinder')
    },
    'GeometryNodeMeshGrid': {
        'Mesh': Constructor(fname='Grid')
    },
    'GeometryNodeMeshIcoSphere': {
        'Mesh': Constructor(fname='IcoSphere')
    },
    'GeometryNodeMeshCircle': {
        'Mesh': Constructor(fname='Circle', ret_socket='mesh')
    },
    'GeometryNodeMeshLine': {
        'Mesh': [
            Constructor(fname='Line',                    ret_socket='mesh'),
            Constructor(fname='LineEndPoints',           ret_socket='mesh', mode="'END_POINTS'", count_mode="'TOTAL'",      resolution=None,
                        arg_rename={'offset': 'end_location'}),
            Constructor(fname='LineEndPointsResolution', ret_socket='mesh', mode="'END_POINTS'", count_mode="'RESOLUTION'", count=None,
                        arg_rename={'offset': 'end_location'}),
            Constructor(fname='LineOffset',              ret_socket='mesh', mode="'OFFSET'",     count_mode="'TOTAL'",      resolution=None),
            ],
    },
    'GeometryNodeMeshUVSphere': {
        'Mesh': Constructor(fname='UVSphere'),
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

OUTPUT = {
    'GeometryNodeViewer': {
        'Geometry': [
            Method(fname= 'viewer', self_='geometry', dtype=('data_type', 'value')),
            Method(fname= 'view',   self_='geometry', dtype=('data_type', 'value')),
            ],
        'Domain':   [
            DomMethod(fname= 'viewer', self_='geometry', dtype=('data_type', 'value')),
            DomMethod(fname= 'view',   self_='geometry', dtype=('data_type', 'value')),
            ],
        },
    }

POINT = {
    'GeometryNodeDistributePointsInVolume': {
        'Volume': [
            Method(self_='volume', ret_socket='points', ret_class='Points', fname='distribute_points',),
            Method(self_='volume', ret_socket='points', ret_class='Points', fname='distribute_points_random', mode="'DENSITY_RANDOM'", spacing=None, threshold=None),
            Method(self_='volume', ret_socket='points', ret_class='Points', fname='distribute_points_grid',   mode="'DENSITY_GRID'", density=None, seed=None),
            ],
    },
    'GeometryNodeDistributePointsOnFaces': {
        'Mesh': Method(self_='mesh', ret_socket=('points', 'normal', 'rotation'), ret_class=('Points', None, None), fname='distribute_points_on_faces',),
        'Face': [
            DomMethod(self_='mesh', ret_socket=('points', 'normal', 'rotation'), ret_class=('Points', None, None),
                fname='distribute_points_random', distribute_method="'RANDOM'", distance_min=None, density_max=None, density_factor=None),
            DomMethod(self_='mesh', ret_socket=('points', 'normal', 'rotation'), ret_class=('Points', None, None),
                fname='distribute_points_poisson', distribute_method="'POISSON'", density=None),
            ]
    },
    'GeometryNodePoints': {
        'Points': Constructor(fname='Points', ret_socket='geometry'),
    },
    'GeometryNodePointsToVertices': {
        'Points':     Method(   fname='to_vertices', self_='points', ret_socket='mesh', ret_class='Mesh'),
        'CloudPoint': DomMethod(fname='to_vertices', self_='points', ret_socket='mesh', ret_class='Mesh'),
    },
    'GeometryNodePointsToVolume': {
        'Points':  [
            Method(fname='to_volume',        self_='points', ret_socket='volume', ret_class='Volume'),
            Method(fname='to_volume_size',   self_='points', ret_socket='volume', ret_class='Volume', resolution_mode="'VOXEL_SIZE'", voxel_amount=None),
            Method(fname='to_volume_amount', self_='points', ret_socket='volume', ret_class='Volume', resolution_mode="'VOXEL_AMOUNT'", voxel_size=None),
            ]
    },
    'GeometryNodeSetPointRadius': {
        'Points':     StackMethod(self_='points'),
        'CloudPoint': DomSetter(fname='radius', self_='points', radius='attr_value'),
        
    },
}

TEXT = {
    'GeometryNodeStringJoin': {
        'functions': Function(ret_socket='string'),
        'String':   [
            Method(self_='delimiter', ret_socket='string', fname='join'),
            Method(self_=None,        ret_socket='string', fname='string_join', first_arg=None),
            ],
    },
    'FunctionNodeReplaceString': {
        'functions': Function(ret_socket='string'),
        'String':   Method(fname='replace', self_='string', ret_socket='string'),
    },
    'FunctionNodeSliceString': {
        'functions': Function(ret_socket='string'),
        'String':   Method(fname='slice', self_='string', ret_socket='string'),
    },
    'FunctionNodeStringLength': {
        'functions': Function(ret_socket='length'),
        'String':   Property(fname='length', self_='string', ret_socket='length'),
    },
    'GeometryNodeStringToCurves': {
        'functions': Function(), #ret_socket=('curve_instances', 'line', 'pivot_point'), ret_class=('Instances', None, None)),
        'String':   Method(fname='to_curves', self_='string'), #, ret_socket=('curve_instances', 'line', 'pivot_point'), ret_class=('Instances', None, None)),
    },
    'FunctionNodeValueToString': {
        'functions' : Function(ret_socket='string'),
        'Float'    : Method(self_='value', fname='to_string', ret_socket='string'),
        'Integer'  : Method(self_='value', fname='to_string', ret_socket='string', decimals=0),
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
        'Texture': Constructor(fname='Brick', ret_socket=('color', 'fac')),
    },
    'ShaderNodeTexChecker': {
        'Texture': Constructor(fname='Checker', ret_socket=('color', 'fac')),
    },
    'ShaderNodeTexGradient': {
        'Texture': [
            Constructor(fname='Gradient',                  ret_socket=('color', 'fac')),
            Constructor(fname='GradientLinear',           ret_socket=('color', 'fac'), gradient_type="'LINEAR'"),
            Constructor(fname='GradientQuadratic',        ret_socket=('color', 'fac'), gradient_type="'QUADRATIC'"),
            Constructor(fname='GradientEeasing',           ret_socket=('color', 'fac'), gradient_type="'EASING'"),
            Constructor(fname='GradientDiagonal',         ret_socket=('color', 'fac'), gradient_type="'DIAGONAL'"),
            Constructor(fname='GradientSpherical',        ret_socket=('color', 'fac'), gradient_type="'SPHERICAL'"),
            Constructor(fname='GradientQuadratic_sphere', ret_socket=('color', 'fac'), gradient_type="'QUADRATIC_SPHERE'"),
            Constructor(fname='GradientRadial',           ret_socket=('color', 'fac'), gradient_type="'RADIAL'"),
            ],
    },
    'GeometryNodeImageTexture': {
        'Texture': Constructor(fname='Image', ret_socket=('color', 'alpha')),
        'Image'  : Method(fname='texture', self_='image', ret_socket=('color', 'alpha')),
    },
    'ShaderNodeTexMagic': {
        'Texture': Constructor(fname='Magic', ret_socket=('color', 'fac')),
    },
    'ShaderNodeTexMusgrave': {
        'Texture': Constructor(fname='Musgrave', ret_socket='fac'),
    },
    'ShaderNodeTexNoise': {
        'Texture': [
            Constructor(fname='Noise',    ret_socket=('color', 'fac')),
            Constructor(fname='Noise1D', ret_socket=('color', 'fac'), noise_dimensions="'1D'", vector=None),
            Constructor(fname='Noise2D', ret_socket=('color', 'fac'), noise_dimensions="'2D'", w=None),
            Constructor(fname='Noise3D', ret_socket=('color', 'fac'), noise_dimensions="'3D'", w=None),
            Constructor(fname='Noise4D', ret_socket=('color', 'fac'), noise_dimensions="'4D'"),
            ],
    },
    'ShaderNodeTexVoronoi': {
        'Texture': [
            Constructor(fname='Voronoi',    ret_socket=('distance', 'color', 'position', 'w')),
            Constructor(fname='Voronoi1D', ret_socket=('distance', 'color', 'w'),             vector=None),
            Constructor(fname='Voronoi2D', ret_socket=('distance', 'color', 'position'),      w=None),
            Constructor(fname='Voronoi3D', ret_socket=('distance', 'color', 'position'),      w=None),
            Constructor(fname='Voronoi4D', ret_socket=('distance', 'color', 'position', 'w')),
            ],
    },
    'ShaderNodeTexWave': {
        'Texture': [
            Constructor(fname='Wave', ret_socket=('color', 'fac')),
            Constructor(fname='WaveBands', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'",
                          arg_rename={'bands_direction': 'direction'}),
            Constructor(fname='WaveRings', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'",
                          arg_rename={'rings_direction': 'direction'}),
        
            Constructor(fname='WaveBands_sine', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'", wave_profile="'SIN'",
                          arg_rename={'bands_direction': 'direction'}),
            Constructor(fname='WaveBands_saw', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'", wave_profile="'SAW'",
                          arg_rename={'bands_direction': 'direction'}),
            Constructor(fname='WaveBands_triangle', ret_socket=('color', 'fac'), wave_type="'BANDS'", rings_direction="'X'", wave_profile="'TRI'",
                          arg_rename={'bands_direction': 'direction'}),

            Constructor(fname='WaveRings_sine', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'", wave_profile="'SIN'",
                          arg_rename={'rings_direction': 'direction'}),
            Constructor(fname='WaveRings_saw', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'", wave_profile="'SAW'",
                          arg_rename={'rings_direction': 'direction'}),
            Constructor(fname='WaveRings_triangle', ret_socket=('color', 'fac'), wave_type="'RINGS'", bands_direction="'X'", wave_profile="'TRI'",
                          arg_rename={'rings_direction': 'direction'}),
            ],
    },
    'ShaderNodeTexWhiteNoise': {
        'Texture': [
            Constructor(fname='WhiteNoise',    ret_socket=('value', 'color')),
            Constructor(fname='WhiteNoise1D', ret_socket=('value', 'color'), noise_dimensions = "'1D'", vector=None),
            Constructor(fname='WhiteNoise2D', ret_socket=('value', 'color'), noise_dimensions = "'2D'", w=None),
            Constructor(fname='WhiteNoise3D', ret_socket=('value', 'color'), noise_dimensions = "'3D'", w=None),
            Constructor(fname='WhiteNoise4D', ret_socket=('value', 'color'), noise_dimensions = "'3D'"),
            ],
    },
}

UTILITIES = {
    'GeometryNodeAccumulateField': {
        'Domain': DomAttribute(ret_socket=('leading', 'trailing', 'total'), dtype=('data_type', 'value')),
    },
    'FunctionNodeAlignEulerToVector': {
        'functions': Function(ret_socket='rotation'),
        'Vector':   [
            StackMethod(self_='rotation'),
            Constructor(fname="AlignToVector", rotation=None, ret_socket='rotation'),
            ]
        #'Rotation': StackMethod(rotation='self', fname='align_to_vector'),
    },
    'FunctionNodeBooleanMath': {
        'functions': [
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
            Method(fname='b_and',   self_='boolean0', ret_socket='boolean', operation="'AND'"),
            Method(fname='b_or',    self_='boolean0', ret_socket='boolean', operation="'OR'"),
            Method(fname='b_not',   self_='boolean0', ret_socket='boolean', operation="'NOT'", boolean1=None),
            Method(fname='nand',    self_='boolean0', ret_socket='boolean', operation="'NAND'"),
            Method(fname='nor',     self_='boolean0', ret_socket='boolean', operation="'NOR'"),
            Method(fname='xnor',    self_='boolean0', ret_socket='boolean', operation="'XNOR'"),
            Method(fname='xor',     self_='boolean0', ret_socket='boolean', operation="'XOR'"),
            Method(fname='imply',   self_='boolean0', ret_socket='boolean', operation="'IMPLY'"),
            Method(fname='nimply',  self_='boolean0', ret_socket='boolean', operation="'NIMPLY'"),
            ],
    },
    'ShaderNodeClamp': {
        'functions': [
            Function(ret_socket='result'),
            Function(ret_socket='result', fname='clamp_min_max', clamp_type="'MINMAX'"),
            Function(ret_socket='result', fname='clamp_range',   clamp_type="'RANGE'"),
            ],
        'Float': [
            Method(ret_socket='result', self_='value'),
            Method(ret_socket='result', self_='value', fname='clamp_min_max', clamp_type="'MINMAX'"),
            Method(ret_socket='result', self_='value', fname='clamp_range',   clamp_type="'RANGE'"),
            ],
    },
    'FunctionNodeCompare': {
        'functions': Function(ret_socket='result'),
        'Float': [
            Method(self_='a', ret_socket='result', data_type=FLOAT, c=None, angle=None, mode="'ELEMENT'"),
            Method(self_='a', ret_socket='result', data_type=FLOAT, c=None, angle=None, mode="'ELEMENT'",
                   fname='less_than', operation="'LESS_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=FLOAT, c=None, angle=None, mode="'ELEMENT'",
                   fname='less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=FLOAT, c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=FLOAT, c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=FLOAT, c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'"),
            Method(self_='a', ret_socket='result', data_type=FLOAT, c=None, angle=None, mode="'ELEMENT'",
                   fname='not_equal', operation="'NOT_EQUAL'"),
            ],
        'Integer': [
            Method(self_='a', ret_socket='result', data_type=INT, c=None, angle=None, mode="'ELEMENT'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=INT, c=None, angle=None, mode="'ELEMENT'",
                   fname='less_than', operation="'LESS_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=INT, c=None, angle=None, mode="'ELEMENT'",
                   fname='less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=INT, c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=INT, c=None, angle=None, mode="'ELEMENT'",
                   fname='greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=INT, c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=INT, c=None, angle=None, mode="'ELEMENT'",
                   fname='not_equal', operation="'NOT_EQUAL'", epsilon=None),
            ],
        'String': [
            Method(self_='a', ret_socket='result', data_type=STRING, c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=STRING, c=None, angle=None, mode="'ELEMENT'",
                   fname='not_equal', operation="'NOT_EQUAL'", epsilon=None),
            ],
        'Vector': [
            Method(self_='a', ret_socket='result', data_type=VECTOR),

            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_equal', operation="'EQUAL'"),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'ELEMENT'",
                   fname='elements_not_equal', operation="'NOT_EQUAL'"),

            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'LENGTH'",
                   fname='length_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'LENGTH'",
                   fname='length_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'LENGTH'",
                   fname='length_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'LENGTH'",
                   fname='length_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'LENGTH'",
                   fname='length_equal', operation="'EQUAL'"),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'LENGTH'",
                   fname='length_not_equal', operation="'NOT_EQUAL'"),

            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'AVERAGE'",
                   fname='average_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'AVERAGE'",
                   fname='average_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'AVERAGE'",
                   fname='average_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'AVERAGE'",
                   fname='average_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'AVERAGE'",
                   fname='average_equal', operation="'EQUAL'"),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, angle=None, mode="'AVERAGE'",
                   fname='average_not_equal', operation="'NOT_EQUAL'"),
            
            Method(self_='a', ret_socket='result', data_type=VECTOR, angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_equal', operation="'EQUAL'"),
            Method(self_='a', ret_socket='result', data_type=VECTOR, angle=None, mode="'DOT_PRODUCT'",
                   fname='dot_product_not_equal', operation="'NOT_EQUAL'"),
            
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, mode="'DIRECTION'",
                   fname='direction_less_than', operation="'LESS_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, mode="'DIRECTION'",
                   fname='direction_less_equal', operation="'LESS_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, mode="'DIRECTION'",
                   fname='direction_greater_than', operation="'GREATER_THAN'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, mode="'DIRECTION'",
                   fname='direction_greater_equal', operation="'GREATER_EQUAL'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, mode="'DIRECTION'",
                   fname='direction_equal', operation="'EQUAL'"),
            Method(self_='a', ret_socket='result', data_type=VECTOR, c=None, mode="'DIRECTION'",
                   fname='direction_not_equal', operation="'NOT_EQUAL'"),
            ],
        
        'Color': [
            #Method(self_='a', ret_socket='result', data_type=RGBA, c=None, angle=None, mode="'ELEMENT'"),
            Method(self_='a', ret_socket='result', data_type=RGBA, c=None, angle=None, mode="'ELEMENT'",
                   fname='darker', operation="'DARKER'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=RGBA, c=None, angle=None, mode="'ELEMENT'",
                   fname='brighter', operation="'BRIGHTER'", epsilon=None),
            Method(self_='a', ret_socket='result', data_type=RGBA, c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'"),
            Method(self_='a', ret_socket='result', data_type=RGBA, c=None, angle=None, mode="'ELEMENT'",
                   fname='equal', operation="'EQUAL'"),
            ],
    },
    'GeometryNodeFieldAtIndex': {
        'Geometry': Attribute(ret_socket='value', dtype=('data_type', 'value')),
        'Domain'  : DomAttribute(ret_socket='value', dtype=('data_type', 'value')),
    },
    'ShaderNodeFloatCurve': {
        'Float' : Method(self_='value', ret_socket='value'),
    },
    'FunctionNodeFloatToInt': {
        'Float' : [
            Method(self_='float', ret_socket='integer', fname='to_integer'),
            Method(self_='float', ret_socket='integer', fname='round',    rounding_mode="'ROUND'"),
            Method(self_='float', ret_socket='integer', fname='floor',    rounding_mode="'FLOOR'"),
            Method(self_='float', ret_socket='integer', fname='ceiling',  rounding_mode="'CEILING'"),
            Method(self_='float', ret_socket='integer', fname='truncate', rounding_mode="'TRUNCATE'"),
            ],
    },
    'GeometryNodeFieldOnDomain': {
        'Geometry': Attribute(fname='interpolate_domain', dtype=('data_type', 'value'), ret_socket='value'),
        'Domain': DomAttribute(fname='interpolate', dtype=('data_type', 'value'), ret_socket='value'),
    },
    'ShaderNodeMapRange': {
        'Float': [
            Method(self_='value', ret_socket='result', vector=None, data_type=FLOAT),
            Method(self_='value', ret_socket='result', vector=None, data_type=FLOAT, fname='map_range_linear',   interpolation_type="'LINEAR'", steps=None),
            Method(self_='value', ret_socket='result', vector=None, data_type=FLOAT, fname='map_range_stepped',  interpolation_type="'STEPPED'"),
            Method(self_='value', ret_socket='result', vector=None, data_type=FLOAT, fname='map_range_smooth',   interpolation_type="'SMOOTHSTEP'", steps=None),
            Method(self_='value', ret_socket='result', vector=None, data_type=FLOAT, fname='map_range_smoother', interpolation_type="'SMOOTHERSTEP'", steps=None),
            ],
        'Vector': [
            Method(self_='vector', ret_socket='vector', value=None, data_type=FLOAT_VECTOR),
            Method(self_='vector', ret_socket='vector', value=None, data_type=FLOAT_VECTOR, fname='map_range_linear',   interpolation_type="'LINEAR'", steps=None),
            Method(self_='vector', ret_socket='vector', value=None, data_type=FLOAT_VECTOR, fname='map_range_stepped',  interpolation_type="'STEPPED'"),
            Method(self_='vector', ret_socket='vector', value=None, data_type=FLOAT_VECTOR, fname='map_range_smooth',   interpolation_type="'SMOOTHSTEP'", steps=None),
            Method(self_='vector', ret_socket='vector', value=None, data_type=FLOAT_VECTOR, fname='map_range_smoother', interpolation_type="'SMOOTHERSTEP'", steps=None),
            ],
    },
    'ShaderNodeMath': {
        'functions': [
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

            #Method(ret_socket='value', fname='add',             operation="'ADD'",          self_='value0', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='subtract',        operation="'SUBTRACT'",     self_='value0', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='sub',             operation="'SUBTRACT'",     self_='value0', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='multiply',        operation="'MULTIPLY'",     self_='value0', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='mul',             operation="'MULTIPLY'",     self_='value0', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='divide',          operation="'DIVIDE'",       self_='value0', arg_rename={'value1': 'value'}, value2=None),
            #Method(ret_socket='value', fname='div',             operation="'DIVIDE'",       self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='multiply_add',    operation="'MULTIPLY_ADD'", self_='value0', arg_rename={'value1': 'multiplier', 'value2': 'addend'}),
            Method(ret_socket='value', fname='mul_add',         operation="'MULTIPLY_ADD'", self_='value0', arg_rename={'value1': 'multiplier', 'value2': 'addend'}),

            Method(ret_socket='value', fname='power',           operation="'POWER'",        self_='value0', arg_rename={'value1': 'exponent'}, value2=None),
            Method(ret_socket='value', fname='pow',             operation="'POWER'",        self_='value0', arg_rename={'value1': 'exponent'}, value2=None),
            Method(ret_socket='value', fname='logarithm',       operation="'LOGARITHM'",    self_='value0', arg_rename={'value1': 'base'}, value2=None),
            Method(ret_socket='value', fname='log',             operation="'LOGARITHM'",    self_='value0', arg_rename={'value1': 'base'}, value2=None),
            Method(ret_socket='value', fname='sqrt',            operation="'SQRT'",         self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='inverse_sqrt',    operation="'INVERSE_SQRT'", self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='absolute',        operation="'ABSOLUTE'",     self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='abs',             operation="'ABSOLUTE'",     self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='exponent',        operation="'EXPONENT'",     self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='exp',             operation="'EXPONENT'",     self_='value0', value1=None, value2=None),

            Method(ret_socket='value', fname='minimum',         operation="'MINIMUM'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='min',             operation="'MINIMUM'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='maximum',         operation="'MAXIMUM'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='max',             operation="'MAXIMUM'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='math_less_than',    operation="'LESS_THAN'",    self_='value0', arg_rename={'value1': 'threshold'}, value2=None),
            Method(ret_socket='value', fname='math_greater_than', operation="'GREATER_THAN'", self_='value0', arg_rename={'value1': 'threshold'}, value2=None),
            Method(ret_socket='value', fname='sign',            operation="'SIGN'",         self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='math_compare',    operation="'COMPARE'",      self_='value0', arg_rename={'value1': 'value', 'value2': 'epsilon'}),
            Method(ret_socket='value', fname='smooth_minimum',  operation="'SMOOTH_MIN'",   self_='value0', arg_rename={'value1': 'value', 'value2': 'distance'}),
            Method(ret_socket='value', fname='smooth_maximum',  operation="'SMOOTH_MAX'",   self_='value0', arg_rename={'value1': 'value', 'value2': 'distance'}),
            
            Method(ret_socket='value', fname='math_round',      operation="'ROUND'",        self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='math_floor',      operation="'FLOOR'",        self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='math_ceil',       operation="'CEIL'",         self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='math_truncate',   operation="'TRUNC'",        self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='math_trunc',      operation="'TRUNC'",        self_='value0', value1=None, value2=None),
            
            Method(ret_socket='value', fname='fraction',        operation="'FRACT'",        self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='fact',            operation="'FRACT'",        self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='modulo',          operation="'MODULO'",       self_='value0', arg_rename={'value1': 'value'}, value2=None),

            Method(ret_socket='value', fname='wrap',            operation="'WRAP'",         self_='value0', arg_rename={'value1': 'max', 'value2': 'min'}),
            Method(ret_socket='value', fname='snap',            operation="'SNAP'",         self_='value0', arg_rename={'value1': 'increment'}, value2=None),
            Method(ret_socket='value', fname='ping_pong',       operation="'PINGPONG'",     self_='value0', arg_rename={'value1': 'scale'}, value2=None),

            Method(ret_socket='value', fname='sine',            operation="'SINE'",         self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='sin',             operation="'SINE'",         self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='cosine',          operation="'COSINE'",       self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='cos',             operation="'COSINE'",       self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='tangent',         operation="'TANGENT'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='tan',             operation="'TANGENT'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),

            Method(ret_socket='value', fname='arcsine',         operation="'ARCSINE'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arcsin',          operation="'ARCSINE'",      self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arccosine',       operation="'ARCCOSINE'",    self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arccos',          operation="'ARCCOSINE'",    self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arctangent',      operation="'ARCTANGENT'",   self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arctan',          operation="'ARCTANGENT'",   self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='arctan2',         operation="'ARCTAN2'",      self_='value0', value2=None),
            
            Method(ret_socket='value', fname='sinh',            operation="'SINH'",         self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='cosh',            operation="'COSH'",         self_='value0', arg_rename={'value1': 'value'}, value2=None),
            Method(ret_socket='value', fname='tanh',            operation="'TANH'",         self_='value0', arg_rename={'value1': 'value'}, value2=None),
            
            Method(ret_socket='value', fname='to_radians',      operation="'RADIANS'",      self_='value0', value1=None, value2=None),
            Method(ret_socket='value', fname='to_degrees',      operation="'DEGREES'",      self_='value0', value1=None, value2=None),
            ],
    },
    'FunctionNodeRandomValue': {
        'functions': [
            Function(ret_socket='value', fname='random_float',   data_type=FLOAT,        probability=None),
            Function(ret_socket='value', fname='random_integer', data_type=INT,          probability=None),
            Function(ret_socket='value', fname='random_vector',  data_type=FLOAT_VECTOR, probability=None),
            Function(ret_socket='value', fname='random_boolean', data_type=BOOLEAN,      min=None, max=None),
            ],
        'Geometry': [
            Static(ret_socket='value', fname='random_float',   data_type=FLOAT,        probability=None),
            Static(ret_socket='value', fname='random_integer', data_type=INT,          probability=None),
            Static(ret_socket='value', fname='random_vector',  data_type=FLOAT_VECTOR, probability=None),
            Static(ret_socket='value', fname='random_boolean', data_type=BOOLEAN,      min=None, max=None),
            ],
        'Domain': [
            Static(ret_socket='value', fname='random_float',   data_type=FLOAT,        probability=None),
            Static(ret_socket='value', fname='random_integer', data_type=INT,          probability=None),
            Static(ret_socket='value', fname='random_vector',  data_type=FLOAT_VECTOR, probability=None),
            Static(ret_socket='value', fname='random_boolean', data_type=BOOLEAN,      min=None, max=None),
            ],
        'Boolean': Constructor(fname='Random', ret_socket='value', data_type=BOOLEAN,      min=None, max=None),
        'Integer': Constructor(fname='Random', ret_socket='value', data_type=INT,           probability=None),
        'Float'  : Constructor(fname='Random', ret_socket='value', data_type=FLOAT,        probability=None),
        'Vector' : Constructor(fname='Random', ret_socket='value', data_type=FLOAT_VECTOR, probability=None),
        
        
    },
    'FunctionNodeRotateEuler': {
        'functions': [
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
        'functions': [
            Function(ret_socket='output'),
            Function(ret_socket='output', fname='switch_float',      input_type=FLOAT),
            Function(ret_socket='output', fname='switch_integer',    input_type=INT),
            Function(ret_socket='output', fname='switch_boolean',    input_type=BOOLEAN),
            Function(ret_socket='output', fname='switch_vector',     input_type=VECTOR),
            Function(ret_socket='output', fname='switch_string',     input_type=STRING),
            Function(ret_socket='output', fname='switch_color',      input_type=RGBA),
            Function(ret_socket='output', fname='switch_object',     input_type="'OBJECT'"),
            Function(ret_socket='output', fname='switch_image',      input_type="'IMAGE'"),
            Function(ret_socket='output', fname='switch_geometry',   input_type="'GEOMETRY'"),
            Function(ret_socket='output', fname='switch_collection', input_type="'COLLECTION'"),
            Function(ret_socket='output', fname='switch_texture',    input_type="'TEXTURE'"),
            Function(ret_socket='output', fname='switch_material',   input_type="'MATERIAL'"),
            ],
        'Float':      Method(self_='false', ret_socket='output', input_type=FLOAT,     com_args=['switch: Boolean', 'true: Float']),
        'Integer':    Method(self_='false', ret_socket='output', input_type=INT,       com_args=['switch: Boolean', 'true: Integer']),
        'Boolean':    Method(self_='false', ret_socket='output', input_type=BOOLEAN,   com_args=['switch: Boolean', 'true: Boolean']),
        'Vector':     Method(self_='false', ret_socket='output', input_type=VECTOR,    com_args=['switch: Boolean', 'true: Vector']),
        'String':     Method(self_='false', ret_socket='output', input_type=STRING,    com_args=['switch: Boolean', 'true: String']),
        'Color':      Method(self_='false', ret_socket='output', input_type=RGBA,      com_args=['switch: Boolean', 'true: Color']),
        'Object':     Method(self_='false', ret_socket='output', input_type="'OBJECT'",    com_args=['switch: Boolean', 'true: Object']),
        'Image':      Method(self_='false', ret_socket='output', input_type="'IMAGE'",     com_args=['switch: Boolean', 'true: Image']),
        'Geometry':   Method(self_='false', ret_socket='output', input_type="'GEOMETRY'",  com_args=['switch: Boolean', 'true: Geometry']),
        'Collection': Method(self_='false', ret_socket='output', input_type="'COLLECTION'",com_args=['switch: Boolean', 'true: Collection']),
        'Texture':    Method(self_='false', ret_socket='output', input_type="'TEXTURE'",   com_args=['switch: Boolean', 'true: Texture']),
        'Material':   Method(self_='false', ret_socket='output', input_type="'MATERIAL'",  com_args=['switch: Boolean', 'true: Material']),
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

VECTOR_IMPL = {
    'ShaderNodeCombineXYZ': {
        'Vector': Constructor(fname='Combine', ret_socket='vector'),
    },
    'ShaderNodeSeparateXYZ': {
        # Implemented manually to manage cache
        'Vector': [
            Property(fname='separate', cache=True, self_='vector'),
        #    #Property(fname='x', cache=True, self_='vector', ret_socket='x'),
        #    #Property(fname='y', cache=True, self_='vector', ret_socket='y'),
        #    #Property(fname='z', cache=True, self_='vector', ret_socket='z'),
            ],
    },
    'ShaderNodeVectorCurve': {
        'Vector': Method(fname='curves', ret_socket='vector', self_='vector'),
    },
    'ShaderNodeVectorMath': {
        'Vector': [
            Method(ret_socket='vector', fname='add',             operation="'ADD'",           self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='subtract',        operation="'SUBTRACT'",      self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='sub',             operation="'SUBTRACT'",      self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='multiply',        operation="'MULTIPLY'",      self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='mul',             operation="'MULTIPLY'",      self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='divide',          operation="'DIVIDE'",        self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='div',             operation="'DIVIDE'",        self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='multiply_add',    operation="'MULTIPLY_ADD'",  self_='vector0', arg_rename={'vector1': 'multiplier', 'vector2':'addend'}, scale=None),
            Method(ret_socket='vector', fname='mul_add',         operation="'MULTIPLY_ADD'",  self_='vector0', arg_rename={'vector1': 'multiplier', 'vector2':'addend'}, scale=None),

            Method(ret_socket='vector', fname='cross_product',   operation="'CROSS_PRODUCT'", self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='cross',           operation="'CROSS_PRODUCT'", self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='project',         operation="'PROJECT'",       self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='reflect',         operation="'REFLECT'",       self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='refract',         operation="'REFRACT'",       self_='vector0', arg_rename={'vector1': 'vector', 'scale':'ior'}, vector2=None),
            Method(ret_socket='vector', fname='face_forward',    operation="'FACEFORWARD'",   self_='vector0', arg_rename={'vector1': 'incident', 'vector2':'reference'}, scale=None),
            Method(ret_socket='value',  fname='dot_product',     operation="'DOT_PRODUCT'",   self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='value',  fname='dot',             operation="'DOT_PRODUCT'",   self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            
            Method(ret_socket='value',  fname='distance',        operation="'DISTANCE'",      self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Property(ret_socket='value',  fname='length',        operation="'LENGTH'",        self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='scale',           operation="'SCALE'",         self_='vector0', vector1=None, vector2=None),
            
            Method(ret_socket='vector', fname='normalize',       operation="'NORMALIZE'",     self_='vector0', vector1=None, vector2=None, scale=None),
            
            Method(ret_socket='vector', fname='absolute',        operation="'ABSOLUTE'",      self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='abs',             operation="'ABSOLUTE'",      self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='minimum',         operation="'MINIMUM'",       self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='min',             operation="'MINIMUM'",       self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='maximum',         operation="'MAXIMUM'",       self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='max',             operation="'MAXIMUM'",       self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='floor',           operation="'FLOOR'",         self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='ceil',            operation="'CEIL'",          self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='fraction',        operation="'FRACTION'",      self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='fract',           operation="'FRACTION'",      self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='modulo',          operation="'MODULO'",        self_='vector0', arg_rename={'vector1': 'vector'}, vector2=None, scale=None),
            Method(ret_socket='vector', fname='wrap',            operation="'WRAP'",          self_='vector0', arg_rename={'vector1': 'max', 'vector2':'min'}, scale=None),
            Method(ret_socket='vector', fname='snap',            operation="'SNAP'",          self_='vector0', arg_rename={'vector1': 'increment'}, vector2=None, scale=None),
            
            Method(ret_socket='vector', fname='sine',            operation="'SINE'",          self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='sin',             operation="'SINE'",          self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='cosine',          operation="'COSINE'",        self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='cos',             operation="'COSINE'",        self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='tangent',         operation="'TANGENT'",       self_='vector0', vector1=None, vector2=None, scale=None),
            Method(ret_socket='vector', fname='tan',             operation="'TANGENT'",       self_='vector0', vector1=None, vector2=None, scale=None),            
            ],
    },
    'ShaderNodeVectorRotate': {
        'Vector' : [
            #rotation_type (str): 'AXIS_ANGLE' in [AXIS_ANGLE, X_AXIS, Y_AXIS, Z_AXIS, EULER_XYZ]
            Method(ret_socket='vector', self_='vector', fname='rotate_euler',     rotation_type= "'EULER_XYZ'",  axis=None, angle=None),
            Method(ret_socket='vector', self_='vector', fname='rotate_axis_angle', rotation_type="'AXIS_ANGLE'", rotation=None),
            Method(ret_socket='vector', self_='vector', fname='rotate_x',          rotation_type="'X_AXIS'",     rotation=None, axis=None),
            Method(ret_socket='vector', self_='vector', fname='rotate_y',          rotation_type="'Y_AXIS'",     rotation=None, axis=None),
            Method(ret_socket='vector', self_='vector', fname='rotate_z',          rotation_type="'Z_AXIS'",     rotation=None, axis=None),
            ],
    },
}

VOLUME = {
    'GeometryNodeVolumeCube': {
        'Volume': Constructor(fname='Cube', ret_socket='volume'),
    },    
    'GeometryNodeVolumeToMesh': {
        'Volume': Method(self_='volume', fname='to_mesh', ret_socket='mesh', ret_class='Mesh'),
    },
}


V36 = {
    'GeometryNodeIndexOfNearest': {
        'Geometry': Attribute(),
        'Domain'  : DomAttribute(),
    },
    'GeometryNodeInputSignedDistance': {
        'Geometry': PropAttribute(ret_socket='signed_distance'),
    },    
    'GeometryNodeMeanFilterSDFVolume': {
        'Volume': Method(self_='volume', fname='mean_filter_sdf_volume', ret_socket='volume', ret_class='Volume'),
    },
    'GeometryNodeMeshToSDFVolume': {
        'Mesh':   Method(   fname='to_sdf_volume', self_='mesh', ret_socket='volume', ret_class='Volume'),
        'Vertex': DomMethod(fname='to_sdf_volume', self_='mesh', ret_socket='volume', ret_class='Volume'),
    },
    'GeometryNodeOffsetSDFVolume': {
        'Volume': StackMethod(   fname='offset_sdf_volume', self_='volume', ret_socket='volume'),
        #'PointCloud': DomStackMethod(fname='offset_sdf_volume', self_='volume', ret_socket='volume'),
    },
    'GeometryNodePointsToSDFVolume': {
        'Points': Method(   fname='to_sdf_volume', self_='points', ret_socket='volume', ret_class='Volume'),
        'CloudPoint':  DomMethod(fname='to_sdf_volume', self_='points', ret_socket='volume', ret_class='Volume'),
    },
    'GeometryNodeSDFVolumeSphere': {
        'Volume': Constructor(fname='SdfSphere', ret_socket='volume'),
    },
    'GeometryNodeSampleVolume': {
        'Volume': [
            Method(self_='volume', fname='sample',         ret_socket='value'),
            Method(self_='volume', fname='sample_float',   ret_socket='value', grid_type=FLOAT),
            Method(self_='volume', fname='sample_vector',  ret_socket='value', grid_type=FLOAT_VECTOR),
            Method(self_='volume', fname='sample_integer', ret_socket='value', grid_type=INT),
            Method(self_='volume', fname='sample_boolean', ret_socket='value', grid_type=BOOLEAN),
            ],
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
       **OUTPUT,
       **POINT,
       **TEXT,
       **TEXTURE,
       **UTILITIES,
       **UV,
       **VECTOR_IMPL,
       **VOLUME,
       **V36,
       }

def get_class_generators(wnodes):
    cg = ClassGenerator(wnodes)
    cg.add_generators(ALL)
    
    return cg










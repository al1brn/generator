#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 13 14:49:27 2022

@author: alain
"""

from datetime import date
from generator.documentation import Doc, Section, Text


def indent_set(depth=0):
    _indent_ = "    "
    _0_ = "\n" + _indent_ * max(0, 0 + depth)
    _1_ = "\n" + _indent_ * max(0, 1 + depth)
    _2_ = "\n" + _indent_ * max(0, 2 + depth)
    _3_ = "\n" + _indent_ * max(0, 3 + depth)
    _4_ = "\n" + _indent_ * max(0, 4 + depth)
    
    return _indent_, _0_, _1_, _2_, _3_, _4_

_indent_, _0_, _1_, _2_, _3_, _4_ = indent_set(0)


FAMILIES = {
    'CONSTRUCTOR' : ('Constructor',      'Constructors'          , False),
    'STATIC'      : ('Static method',    'Static methods'        , False),
    'CLASS'       : ('Class method',     'Class methods'         , False),    
    'PROPERTY'    : ('Property',         'Properties'            , True ),
    'METHOD'      : ('Method',           'Methods'               , True ),        
    
    'FUNCTION'    : ('Function',         'Functions'             , False),
    }

BOOL_MATH = {
    'AND'    : 'b_and',
    'OR'     : 'b_or',
    'NOT'    : 'b_not',
    'NAND'   : 'nand',
    'NOR'    : 'nor',
    'XNOR'   : 'xnor',
    'XOR'    : 'xor',
    'IMPLY'  : 'imply',
    'NIMPLY' : 'nimply',
}        


MATH = {
    'ADD'                : ('add'                 , 'SAME'      ),
    'SUBTRACT'           : ('subtract'            , 'SAME'      ),
    'MULTIPLY'           : ('multiply'            , 'SAME'      ),
    'DIVIDE'             : ('divide'              , 'Float'     ),
    'MULTIPLY_ADD'       : ('multiply_add'        , 'SAME'      ),
    'POWER'              : ('pow'                 , 'SAME'      ),
    'LOGARITHM'          : ('log'                 , 'Float'     ),
    'SQRT'               : ('sqrt'                , 'Float'     ),
    'INVERSE_SQRT'       : ('inverse_sqrt'        , 'Float'     ),
    'ABSOLUTE'           : ('abs'                 , 'SAME'      ),
    'EXPONENT'           : ('exp'                 , 'Float'     ),
    'MINIMUM'            : ('min'                 , 'SAME'      ),
    'MAXIMUM'            : ('max'                 , 'SAME'      ),
    'LESS_THAN'          : ('less_than'           , 'Boolean'   ),
    'GREATER_THAN'       : ('greater_than'        , 'Boolean'   ),
    'SIGN'               : ('sign'                , 'Integer'   ),
    'COMPARE'            : ('compare'             , 'Boolean'   ),
    'SMOOTH_MIN'         : ('smooth_min'          , 'SAME'      ),
    'SMOOTH_MAX'         : ('smooth_max'          , 'SAME'      ),
    'ROUND'              : ('round'               , 'Integer'   ),
    'FLOOR'              : ('floor'               , 'Integer'   ), 
    'CEIL'               : ('ceil'                , 'Integer'   ),
    'TRUNC'              : ('trunc'               , 'Integer'   ), 
    'FRACT'              : ('fract'               , 'Float'     ),
    'MODULO'             : ('modulo'              , 'SAME'      ),
    'WRAP'               : ('wrap'                , 'SAME'      ),
    'SNAP'               : ('snap'                , 'SAME'      ),
    'PINGPONG'           : ('pingpong'            , 'SAME'      ),
    'SINE'               : ('sin'                 , 'Float'     ),
    'COSINE'             : ('cos'                 , 'Float'     ),
    'TANGENT'            : ('tan'                 , 'Float'     ),
    'ARCSINE'            : ('arcsin'              , 'Float'     ),
    'ARCCOSINE'          : ('arccos'              , 'Float'     ),
    'ARCTANGENT'         : ('arctan'              , 'Float'     ),
    'ARCTAN2'            : ('arctan2'             , 'Float'     ),
    'SINH'               : ('sinh'                , 'Float'     ),
    'COSH'               : ('cosh'                , 'Float'     ),
    'TANH'               : ('tanh'                , 'Float'     ),
    'RADIANS'            : ('radians'             , 'Float'     ),
    'DEGREES'            : ('degrees'             , 'Float'     ),   
 }

VECTOR_MATH = {
    'ADD'                : 'add',
    'SUBTRACT'           : 'subtract',
    'MULTIPLY'           : 'multiply',
    'DIVIDE'             : 'divide',
    'MULTIPLY_ADD'       : 'multiply_add',
    'CROSS_PRODUCT'      : 'cross',
    'PROJECT'            : 'project',
    'REFLECT'            : 'reflect',
    'REFRACT'            : 'refract',
    'FACEFORWARD'        : 'faceforward',
    'DOT_PRODUCT'        : 'dot',
    'DISTANCE'           : 'distance',
    'LENGTH'             : 'length',
    'SCALE'              : 'scale',
    'NORMALIZE'          : 'normalize',
    'ABSOLUTE'           : 'absolute',
    'MINIMUM'            : 'min',
    'MAXIMUM'            : 'max',
    'FLOOR'              : 'floor',
    'CEIL'               : 'ceil',
    'FRACTION'           : 'fraction',
    'MODULO'             : 'modulo',
    'WRAP'               : 'wrap',
    'SNAP'               : 'snap',
    'SINE'               : 'sin',
    'COSINE'             : 'cos',
    'TANGENT'            : 'tan',
}

COLOR_MIX = {
    'MIX'           : 'mix',
    'DARKEN'        : 'darken',
    'MULTIPLY'      : 'multiply',
    'BURN'          : 'burn',
    'LIGHTEN'       : 'lighten',
    'SCREEN'        : 'screen',
    'DODGE'         : 'dodge',
    'ADD'           : 'add',
    'OVERLAY'       : 'overlay',
    'SOFT_LIGHT'    : 'soft_light',
    'LINEAR_LIGHT'  : 'linear_light',
    'DIFFERENCE'    : 'difference',
    'SUBTRACT'      : 'subtract',
    'DIVIDE'        : 'divide',
    'HUE'           : 'hue',
    'SATURATION'    : 'saturation',
    'COLOR'         : 'mix_color',
    'VALUE'         : 'value',
}

MULTI_CLASSES_NODES = { # Function name and is an attribute. If it is an attribute, use the geometry as geometry socket
    'FunctionNodeRandomValue'        : ('Random',              False ), # ('FLOAT', 'INT', 'FLOAT_VECTOR', 'BOOLEAN')
    'GeometryNodeAccumulateField'    : ('accumulate_field',    False ), # ('FLOAT', 'INT', 'FLOAT_VECTOR')
    'GeometryNodeAttributeStatistic' : ('attribute_statistic', True  ), # ('FLOAT', 'FLOAT_VECTOR')
    #'GeometryNodeAttributeTransfer'  : ('transfer_attribute',  True  ), # ('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BOOLEAN')
    'GeometryNodeCaptureAttribute'   : ('capture_attribute',   True  ), # ('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BOOLEAN')
    'GeometryNodeFieldAtIndex'       : ('field_at_index',      False ), # ('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BOOLEAN')
    'GeometryNodeRaycast'            : ('raycast',             True  ), # ('FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'BOOLEAN')
    'GeometryNodeSwitch'             : ('switch',              False ), # ('FLOAT', 'INT', 'BOOLEAN', 'VECTOR', 'STRING', 'RGBA', 'OBJECT', 'IMAGE', 'GEOMETRY', 'COLLECTION', 'TEXTURE', 'MATERIAL')
    'ShaderNodeMapRange'             : ('map_range',           False ), # ('FLOAT', 'FLOAT_VECTOR')
    
}

DATA_TYPES = {
    'Integer'     : 'INT',
    'Color'       : 'RGBA',
    'Vector'      : 'FLOAT_VECTOR',
    'Color'       : 'FLOAT_COLOR',
}

# =============================================================================================================================
# Node calling

class NodeCall:
    
    def __init__(self, family, wnode, class_name, meth_name, self_name=None, out_name=None, ret_class=None, stack=False, **fixed):
        
        self.family     = family

        self.wnode      = wnode
        self.class_name = class_name
        self.meth_name  = meth_name
        self.stack      = stack
        
        self.self_name  = self_name
        self.out_name   = out_name
        self.ret_class  = ret_class

        self.fixed      = dict(fixed)

    # ----------------------------------------------------------------------------------------------------
    # A property
    
    @classmethod
    def Property(cls, wnode, class_name, meth_name, settable=False, main_prop_name=None, output_index = 0, **fixed):
        
        nc = cls('PROPERTY', wnode, class_name, meth_name, **fixed)
        
        if main_prop_name is None:
            nc.is_main_prop   = True
            nc.main_prop_name = meth_name
        else:
            nc.is_main_prop   = False
            nc.main_prop_name = main_prop_name
            
        nc.prop_is_settable = settable
        nc.output_index     = output_index

        return nc

    # ----------------------------------------------------------------------------------------------------
    # The call is a method using self
    
    @property
    def use_self(self):
        return FAMILIES[self.family][2]
    
    # ----------------------------------------------------------------------------------------------------
    # Line comment: used to build the list of methods in the class documentation
    
    @property
    def line_doc(self):
        
        unames = self.wnode.output_unames(self.fixed)
        
        if len(unames) == 0:
            ret_str = "None"
            
        elif len(unames) == 1:
            uname = list(unames)[0]
            ret_str = f"{uname} ({unames[uname]})"
            
        elif len(unames) == 2 and self.stack:
            uname = list(unames)[1]
            ret_str = f"{uname} ({unames[uname]})"
            
        else:
            if self.family == 'PROPERTY' and not self.is_main_prop:
                try:
                    uname = self.wnode.outputs[self.output_index].uname
                    #uname = list(unames.keys())[self.output_index]
                except Exception as e:
                    print(self.output_index)
                    print(unames)
                    print(self.wnode)
                    print(self.wnode.outputs)
                    print(test)
                    raise e
                ret_str = f"{uname} ({unames[uname]}) = {self.main_prop_name}.{uname}"
                
            else:
                ret_str = "Sockets      ["
                sep = ""
                for uname, class_name in unames.items():
                    ret_str += f"{sep}{uname} ({class_name})"
                    sep = ", "
                ret_str += "]"
                
        #node_link = f"[{self.wnode.node_name}](id:{self.wnode.node_name})"
        return f"- [{self.meth_name}](#{self.meth_name.lower()}) : {ret_str}"

    
    # ====================================================================================================
    # Generate a call
    #
    # data_class is passed as an argument to collect to documentation
    
    def gen_call(self, data_class):
        
        from generator.generator import Argument, Arguments
        
        _indent_, _0_, _1_, _2_, _3_, _4_ = indent_set(-1 if self.family == 'FUNCTION' else 0)
        
        # ---------------------------------------------------------------------------
        # To ease the reading
        
        family      = self.family
        class_name  = self.class_name
        meth_name   = self.meth_name
        self_name   = self.self_name
        fixed       = self.fixed

        # ---------------------------------------------------------------------------
        # Configure the node to steer the enablement

        self.wnode.set_params(fixed)
        
        # ---------------------------------------------------------------------------
        # Dictionary : {uname : class_name}
        # of the input / ouput sockets in this configuration
        
        inp_unames = self.wnode.input_unames(fixed)
        ret_unames = self.wnode.output_unames(fixed)
        
        # ---------------------------------------------------------------------------
        # If self_name is None, use the first enabled input socket of the proper class

        if family in ['FUNCTION', 'STATIC', 'CLASS', 'CONSTRUCTOR']:
            if self_name is not None:
                raise RuntimeError(f"The method {meth_name} on node {self.node_name} is {family}: it can have a self argument: {self_name}.")
                
        elif self_name is None and self.wnode.inputs:
            geo_socket = None
            for wsock in self.wnode.inputs:
                if wsock.enabled:

                    if wsock.class_name == class_name:
                        self_name = wsock.uname
                        break
                    
                    if wsock.class_name == 'Geometry' and geo_socket is None:
                        geo_socket = wsock.uname
                        #geo_socket = wsock.class_name
                    
            if self_name is None:
                if class_name in ['Mesh', 'Points', 'Instances', 'Volume', 'Curve'] and geo_socket is not None:
                    self_name = geo_socket
                else:
                    raise RuntimeError(f"The method {meth_name} on node {self.wnode.node_name} is {family}: it requires a self argument for class {class_name}.")
                
        # ---------------------------------------------------------------------------
        # Arguments
        
        args = Arguments()

        for uname in inp_unames:
            wsocks = self.wnode.inputs.unames[uname]
            
            wsock = None
            if isinstance(wsocks, list):
                for ws in wsocks:
                    if ws.enabled:
                        wsock = ws
                        break
            else:
                wsock = wsocks
                
            if wsock is None:
                continue
                
            is_self  = uname == self_name
            args.add(Argument.Socket(uname, wsocket=wsock, is_self=is_self))
            
        for name, param in self.wnode.parameters.items():
            is_fixed = name in fixed
            value = fixed[name] if is_fixed else param.default
            args.append(Argument.Param(name, value, param=param, is_fixed=is_fixed))
            
        if family == 'PROPERTY':
            args.add(Argument.Other(header_str="", call_str="label=f\"{self.node_chain_label}." + meth_name + "\""))

        if family not in ['PROPERTY']:
            args.add(Argument.Other(header_str="node_label = None", call_str="label=node_label"))
            args.add(Argument.Other(header_str="node_color = None", call_str="node_color=node_color"))

        # ----- Ensure the socket arguments are properly ordered
        
        args.check_order(self.wnode.bl_idname)
        
        # ----------------------------------------------------------------------------------------------------
        # Function header
        #
        # @decorator
        # def method(self, args...):
        
        # ----- Static method
        # @staticmethod
        # def method(args,...):
        
        is_cls = False
        if family in 'STATIC':
            yield _1_ + "@staticmethod"

        # ----- Class method
        # @classmethod
        # def method(cls, args,...):

        elif family in ['CLASS', 'CONSTRUCTOR']:
            yield _1_ + "@classmethod"
            args.add(Argument.Cls())
            is_cls = True

        # ----- Property
        # @property
        # def method(self, args,...):

        elif family == 'PROPERTY':
            yield _1_ + "@property"
        
        # ----- Other
        # def method(self, args,...):
        
        yield _1_ + f"def {meth_name}({args.sheader}):"
        
        # ----------------------------------------------------------------------------------------------------
        # Node call string
        
        snode_call = f"nodes.{self.wnode.node_name}({args.scall})"
        
        # ----------------------------------------------------------------------------------------------------
        # Comment
        
        if family == 'PROPERTY':
            sample = f"v = {class_name.lower()}.{meth_name}"
            
        elif family in ['CONSTRUCTOR', 'STATIC', 'CLASS']:
            sample = f"v = {class_name}.{meth_name}({args.scall_demo})"
            
        else:
            sample = f"v = {class_name.lower()}.{meth_name}({args.scall_demo})"
            
        if len(ret_unames) == 0:
            sret = "self"

        elif len(ret_unames) == 1:
            sret = str(ret_unames[list(ret_unames)[0]])
        
        else:
            s = ", ".join([f"{uname} ({ret_unames[uname]})" for uname in ret_unames])
            sret = f"Sockets [{s}]"
        
        section = Section(None, f"{meth_name}")
        section.family = FAMILIES[self.family][1]
        
        text = f"""

        > Node: [{self.wnode.node_name}](id:{self.wnode.node_name})
        
        <sub>go to: [top](#data-socket-{self.class_name.lower()}) [index](ref:index)
        blender ref [{self.wnode.bl_idname}]({self.wnode.blender_python_ref})
        node ref [{self.wnode.bnode.name}]({self.wnode.blender_ref}) </sub>
                          
        ```python
        {sample}
        ```
        
        Arguments
        ---------
            {args.documentation()}
        
        Node creation
        -------------
        
        ```python
        from geondes import nodes
        {snode_call}
        ``` 

        Returns
        -------
            {sret}
        """
        
        # ----- Remove temporarily the section title
        
        section.set_text(text)
        title = section.title
        section.title = None

        # ----- Loop on the lines
        
        first = True
        for line in section.gen_text(False):
            if first:
                if line.strip() != "":
                    yield _2_ + '""" ' + line.strip()
                    first = False
            else:
                yield _1_ + line
        yield _2_ + '"""' + "\n"
        
        section.title = title
        
        data_class.class_doc.add_section(section)

    
        # ----------------------------------------------------------------------------------------------------
        # ----- Call and return

        # ----------------------------------------------------------------------------------------------------
        # PROPERTY: create a local attribute plus create children properties
        # if the resulting node has several sockets:
        #
        # @property
        # def length(self):
        #     if self.length_ is None:
        #         self.length_ = Node(...).length
        #     return self.length_
        #
        # or
        #
        # @property
        # def components(self):
        #     if self.components is None:
        #         self.components_ = Node(...)
        #     return self.components_
        #
        # @property
        # def mesh_component(self):
        #     return self.components.mesh
        #
        # @property
        # def curve_component(self):
        #     return self.components.curve
    
        if family == 'PROPERTY':
            
            if len(ret_unames) == 0:
                raise RuntimeError(f"Impossible to implement a property on {self.node_name} with not output sockets!")
                
            # ----- Main property
            
            if self.is_main_prop:
                yield _2_ + f"if self.{self.main_prop_name}_ is None:"
                yield _3_ + f"self.{self.main_prop_name}_ = {snode_call}"
            
                if len(ret_unames) == 1:
                    yield f".{list(ret_unames)[0]}"
                    
                yield _2_ + f"return self.{meth_name}_\n"
                
            # ----- Socket prperty
            
            else:
                
                #sock_name = list(ret_unames)[self.output_index]
                sock_name = self.wnode.outputs[self.output_index].uname
                
                yield _2_ + f"return self.{self.main_prop_name}.{sock_name}\n"
    
                if self.prop_is_settable:
                    yield _1_ +f"@{meth_name}.setter"
                    yield _1_ + f"def {meth_name}(self, value):"
                    yield _2_ + f"self.{self.main_prop_name}.{sock_name} = value\n"
              
        # ----------------------------------------------------------------------------------------------------
        # Other : can return 3 things depending on the number of output sockets in ret_unames
        #
        # 0. no socket   : return None
        # 1. 1 socket    : return the socket
        # 2: > 1 sockets : return the node
        #
        # def method(self,...):
        #     Node(...)
        #
        # def method(self,...):
        #     return Node(...).mesh
        #
        # def method(self,...):
        #     return Node(...)
    
        else:
            if len(ret_unames) == 0:
                yield _2_ + f"{snode_call}\n"
                
            else:
                if self.stack:
                    
                    if len(ret_unames) == 1:
                        yield _2_ + f"return self.stack({snode_call})\n"
                        
                    else:
                        yield _2_ + f"node = {snode_call}"
                        yield _2_ + "self.stack(node)"
                        
                        if len(ret_unames) == 2:
                            yield _2_ + f"return node.{list(ret_unames)[1]}\n"
                        else:
                            yield _2_ + "return node\n"

                else:
                    if len(ret_unames) == 1:
                        if is_cls:
                            yield _2_ + f"return cls({snode_call}.{list(ret_unames)[0]})\n"
                        else:
                            yield _2_ + f"return {snode_call}.{list(ret_unames)[0]}\n"
                    
                    else:
                        yield _2_ + f"return {snode_call}\n"    
    

# ========================================================================================================================
# The data class generator                
        
class DataClass:
    
    GENS = {
        'FunctionNodeInputBool',
        'FunctionNodeInputColor',
        'FunctionNodeInputInt',
        'FunctionNodeInputSpecialCharacters',
        'FunctionNodeInputString',
        'FunctionNodeInputVector',
        'GeometryNodeGroup',
        'GeometryNodeInputMaterial',
        'GeometryNodeViewer',
        'NodeFrame',
        'NodeGroupInput',
        'NodeGroupOutput',
        'NodeReroute',
        'ShaderNodeValue',
    }
    
    def __init__(self, wnodes, class_name, super_class, is_global=False):
        
        self.wnodes      = wnodes
        self.class_name  = class_name
        self.super_class = super_class
        
        self.methods_    = []
        
        self.is_global   = is_global
        
        # ----- Class documentation
        
        title = "geonodes functions" if self.is_global else f"Data socket {class_name}"        
        self.class_doc = Section(parent=None, title=title)
        
        self.class_doc.id = f"{self.class_name}"
        self.class_doc.md_file = f"{self.class_name}.md"
        
        if self.is_global:
            text = f"""
            > global functions
            
            <sub>go to [index](ref:index)</sub>
            
            Example of use:
            
            ```python
            import geonodes as gn
            value = gn.Float(14.) # A float value
            v = gn.sin(v)         # The sine of this value
            ```
            
            """
        else:
            text = f"""
            > Inherits from {self.super_class}
            
            <sub>go to [index](ref:index)</sub>
            
            """
        
        self.class_doc.set_text(text)
        
        
        # ----------------------------------------------------------------------------------------------------
        # Add the multi classes methods
        
        for blid, spec in MULTI_CLASSES_NODES.items():
            wn = self.wnodes[blid]
            if not self.data_type in wn.parameters[wn.driving_param].values:
                continue
            
            meth_name = spec[0]
            
            fixed = {wn.driving_param: self.data_type}
            
            family = 'CONSTRUCTOR' if meth_name[0].upper() == meth_name[0] else 'METHOD'
            
            self.add_call(family, blid, meth_name, **fixed)
            
        # ----------------------------------------------------------------------------------------------------
        # FunctionNodeCompare is a little bit complex !
        
        blid    = 'FunctionNodeCompare'
        val_ops = ('LESS_THAN', 'LESS_EQUAL', 'GREATER_THAN', 'GREATER_EQUAL', 'EQUAL', 'NOT_EQUAL')
        vec_ops = ('ELEMENT', 'LENGTH', 'AVERAGE', 'DOT_PRODUCT', 'DIRECTION')
        col_ops = ('EQUAL', 'NOT_EQUAL', 'BRIGHTER', 'DARKER')
        str_ops = ('EQUAL', 'NOT_EQUAL')
        
        if self.class_name == 'Integer':
            for op in val_ops:
                self.add_call('METHOD', blid, op.lower(), data_type='INT', operation=op, mode='ELEMENT')
                
        elif self.class_name == 'Float':
            for op in val_ops:
                self.add_call('METHOD', blid, op.lower(), data_type='FLOAT', operation=op, mode='ELEMENT')
                
        elif self.class_name == 'Vector':
            modes = ('ELEMENT', 'LENGTH', 'AVERAGE', 'DOT_PRODUCT', 'DIRECTION')
            for op in vec_ops:
                self.add_call('METHOD', blid, op.lower(), data_type='VECTOR', operation=op)
                
        elif self.class_name == 'String':
            for op in str_ops:
                self.add_call('METHOD', blid, op.lower(), data_type='STRING', operation=op, mode='ELEMENT')
                
        elif self.class_name == 'Color':
            for op in col_ops:
                self.add_call('METHOD', blid, op.lower(), data_type='RGBA', operation=op, mode='ELEMENT')
                
    # ----------------------------------------------------------------------------------------------------
    # Specific code
    
    def gen_specific(self):
        yield ""
        
    # ----------------------------------------------------------------------------------------------------
    # Data type for multi classes nodes (random for instance)

    @property
    def data_type(self):
        if self.class_name in DATA_TYPES:
            return DATA_TYPES[self.class_name]
        else:
            return self.class_name.upper()
        
    # ----------------------------------------------------------------------------------------------------
    # Methods per family
    
    def methods(self, family=None):
        meths = []
        for meth in self.methods_:
            if family is None or family == meth.family:
                meths.append(meth)
        return meths
    
    # ----------------------------------------------------------------------------------------------------
    # Add a method
    
    def add_call(self, family, bl_idname, meth_name, **kwargs):
        if family == 'STACK':
            stack = True
            family = 'METHOD'
        else:
            stack = False
        
        self.methods_.append(NodeCall(family, self.wnodes[bl_idname], class_name=self.class_name, meth_name=meth_name, stack=stack, **kwargs))
        
    # ----------------------------------------------------------------------------------------------------
    # Add node properties
    
    def add_property(self, bl_idname, meth_name, settable=False, prop_names=None, **kwargs):

        # ----- The main property
        
        self.methods_.append(NodeCall.Property(self.wnodes[bl_idname], self.class_name, meth_name, **kwargs))
        if prop_names is None:
            return
        
        # ----- Several output sockets --> several properties
        
        # List: all the outputs are used, the index is the output socket index
        if isinstance(prop_names, (list, tuple)):
            dct = {prop_name: index for index, prop_name in enumerate(prop_names)}
        else:
            dct = prop_names
            
        # Dct: the outputs are not all used, the index is given by the key
        for prop_name, index in dct.items():
            self.methods_.append(NodeCall.Property(self.wnodes[bl_idname], self.class_name, prop_name, settable=settable, main_prop_name=meth_name, output_index=index, **kwargs))

        #for index, prop_name in enumerate(prop_names):
        #    self.methods_.append(NodeCall.Property(self.wnodes[bl_idname], self.class_name, prop_name, settable=settable, main_prop_name=meth_name, output_index=index, **kwargs))
        
            

    # ----------------------------------------------------------------------------------------------------
    # Template
    
    @staticmethod
    def get_template(template, replace={}):
        #s = inspect.getsource(method)
        s = template
        for templ, repl in replace.items():
            s = s.replace(templ, repl)
        return s

    # ----------------------------------------------------------------------------------------------------
    # Generate the class source code
        
    def gen_class(self):
        
        import bpy
        
        _indent_, _0_, _1_, _2_, _3_, _4_ = indent_set(-1 if self.is_global else 0)
        
        # ----------------------------------------------------------------------------------------------------
        # Generates module header
        
        QUOTES = '"""'
        
        yield f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

{QUOTES}
Created on {date.today()}
@author: Generated from generator module
Blender version: {bpy.app.version_string}
{QUOTES}

import geonodes as gn
from geonodes.core import datasockets as dsock
from geonodes.nodes import nodes
import geonodes.core.domains as domains

import logging
logger = logging.Logger('geonodes')

"""
    
        # ----------------------------------------------------------------------------------------------------
        # Class header or list of function to import
        
        if self.is_global:
            meths = [nc.meth_name for nc in self.methods_]
            meths.sort()
            
            simport = "from geonodes.sockets.functions import " 
            s = ""
            sep = simport
            
            yield '"""' + " Function to declare in file __init__.py\n"
            
            wmax = 100
            for i, meth_name in enumerate(meths):
                s += sep + meth_name
                sep = ", "
                if len(s) > wmax or i == len(meths)-1:
                    yield s + "\n"
                    s = ""
                    sep = simport
                    
            yield '"""' + "\n"
            
        else:
            yield  "# " + '='*110 + "\n"
            yield f"# Data class {self.class_name}\n"
            
            yield _0_ + f"class {self.class_name}({self.super_class}):"

        # ----------------------------------------------------------------------------------------------------
        # Class documentation
        
        for family in FAMILIES:
            meths = sorted(self.methods(family), key=lambda nc: nc.meth_name)
            if not meths:
                continue
            
            section = Section(self.class_doc, FAMILIES[family][1])
            text = "\n".join([nc.line_doc for nc in meths])
            section.set_text(text)
        
        first = True
        indent = _1_ + '""" '
        for line in self.class_doc.gen_text(False):
            yield indent + line
            indent = _1_
        yield _1_ + '"""' + "\n"
        
        # ----------------------------------------------------------------------------------------------------
        # Copy
        
        if not self.is_global:
            yield _0_ + _1_ +  "def copy(self):"
            yield _0_ + _2_ + f"return {self.class_name}(self)\n"
            
        
        # ----------------------------------------------------------------------------------------------------
        # Specific
        
        for line in self.gen_specific():
            yield line
        
        # ----------------------------------------------------------------------------------------------------
        # Properties attributes
        
        meths = self.methods('PROPERTY')
        if meths:
            yield _0_ + _1_ + "def reset_properties(self):"
            yield _0_ + _2_ + "super().reset_properties()"
            for nc in meths:
                yield _0_ + _2_ + f"self.{nc.meth_name}_ = None"

        # ----------------------------------------------------------------------------------------------------
        # Methods
        
        for family, label in FAMILIES.items():
            
            meths = self.methods(family)
            if not meths:
                continue
            
            yield f"\n{_1_}# {'-'*100}{_1_}# {label[1]}\n"
            
            for nc in meths:

                # Register the node which is implemented
                DataClass.GENS.add(nc.wnode.bl_idname)
                
                # Yield the lines

                for line in nc.gen_call(self):
                    yield line
                    
    # ----------------------------------------------------------------------------------------------------
    # Register the methods in the nodes
                    
    def register_nodes(self):
        
        for nc in self.methods_:
            nc.wnode.register_socket(self.class_name, nc.meth_name, FAMILIES[nc.family][0])
                    

# -----------------------------------------------------------------------------------------------------------------------------
# Global functions
                    
class GlobalGen(DataClass):
    
    def __init__(self, nodes):
        super().__init__(nodes, 'functions', '', is_global=True)

        self.add_call('FUNCTION', 'FunctionNodeCompare',          meth_name="compare"             )
        self.add_call('FUNCTION', 'GeometryNodeStringJoin',       meth_name="join_strings"        )
        
        self.add_call('FUNCTION', 'GeometryNodeInputSceneTime', 'scene')
        self.add_call('FUNCTION', 'GeometryNodeSwitch', 'switch')
        
        

        blid = 'FunctionNodeBooleanMath'
        for op, meth_name in BOOL_MATH.items():
            self.add_call('FUNCTION', blid, meth_name, blend_type=op)
        
        blid = 'ShaderNodeMath'
        for op, spec in MATH.items():
            self.add_call('FUNCTION', blid, spec[0], operation=op)
            
        blid = 'ShaderNodeVectorMath'
        for op, meth_name in VECTOR_MATH.items():
            f_name = f"vector_{meth_name}" if op in MATH else meth_name
            self.add_call('FUNCTION', blid, f_name, operation=op)
            
        blid = 'ShaderNodeMixRGB'
        for op, meth_name in COLOR_MIX.items():
            self.add_call('FUNCTION', blid, f"color_{meth_name}", blend_type=op)
            


# -----------------------------------------------------------------------------------------------------------------------------
# Boolean

class BooleanGen(DataClass):
    def __init__(self, nodes):
        
        super().__init__(nodes, 'Boolean', 'dsock.Boolean')
        
        # ----------------------------------------------------------------------------------------------------
        # Boolean math
        
        blid = 'FunctionNodeBooleanMath'
        self.add_call('METHOD', blid, 'b_and',  operation='AND'     )
        self.add_call('METHOD', blid, 'b_or',   operation='OR'      )
        self.add_call('METHOD', blid, 'b_not',  operation='NOT'     )
        self.add_call('METHOD', blid, 'nand',   operation='NAND'    )
        self.add_call('METHOD', blid, 'nor',    operation='NOR'     )
        self.add_call('METHOD', blid, 'xnor',   operation='XNOR'    )
        self.add_call('METHOD', blid, 'xor',    operation='XOR'     )
        self.add_call('METHOD', blid, 'imply',  operation='IMPLY'   )
        self.add_call('METHOD', blid, 'nimply', operation='NIMPLY'  )
        
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# Integer
        
class IntegerGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Integer', 'dsock.Integer')
        

        # ----------------------------------------------------------------------------------------------------
        # Operations
        
        blid = 'ShaderNodeMath'
        for op, spec in MATH.items():
            ret_class = 'Integer' if spec[1] == 'SAME' else spec[1]
            self.add_call('METHOD', blid, spec[0], self_name="value0", ret_class=ret_class, operation=op)


# -----------------------------------------------------------------------------------------------------------------------------
# Float

class FloatGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Float', 'dsock.Float')
        
        # ----------------------------------------------------------------------------------------------------
        # Operations
        
        blid = 'ShaderNodeMath'
        for op, spec in MATH.items():
            ret_class = 'Float' if spec[1] == 'SAME' else spec[1]
            self.add_call('METHOD', blid, spec[0], ret_class=ret_class, operation=op)

        # ----------------------------------------------------------------------------------------------------
        # Methods

        self.add_call('METHOD', 'FunctionNodeFloatToInt',     'to_integer',   ret_class='Integer')
        self.add_call('METHOD', 'FunctionNodeValueToString',  'to_string',    ret_class='String' )

        self.add_call('METHOD', 'ShaderNodeValToRGB',        'color_ramp'       )

        self.add_call('STACK', 'ShaderNodeFloatCurve',       'curve',         self_name="value"  )
        self.add_call('STACK', 'ShaderNodeClamp',            'clamp'            )
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# Vector
        
class VectorGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Vector', 'dsock.Vector')
        
        # ----------------------------------------------------------------------------------------------------
        # Constructors

        self.add_call('CONSTRUCTOR', 'ShaderNodeCombineXYZ',            'Combine')
        self.add_call('CONSTRUCTOR', 'FunctionNodeAlignEulerToVector',  'AlignToVector')
        
        # ----------------------------------------------------------------------------------------------------
        # Operations
        
        blid = 'ShaderNodeVectorMath'
        for op, meth_name in VECTOR_MATH.items():
            self.add_call('METHOD', blid, meth_name, operation=op)

        # ----------------------------------------------------------------------------------------------------
        # x, y, z properties
        
        self.add_property('ShaderNodeSeparateXYZ', 'separate', settable=True, prop_names=['x', 'y', 'z'])

        # ----------------------------------------------------------------------------------------------------
        # Methods
    
        self.add_call('STACK', 'ShaderNodeVectorCurve',           'curves'          )
        self.add_call('STACK', 'FunctionNodeAlignEulerToVector',  'align_to_vector' )
        self.add_call('STACK', 'FunctionNodeRotateEuler',         'rotate_euler'    )
        self.add_call('METHOD', 'ShaderNodeVectorRotate',         'rotate'          )
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# String

class ColorGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Color', 'dsock.Color')
        
        # ----------------------------------------------------------------------------------------------------
        # Constructor
        
        self.add_call('CONSTRUCTOR', 'ShaderNodeCombineRGB', 'Combine')
        
        # ----------------------------------------------------------------------------------------------------
        # Operations
        
        blid = 'ShaderNodeMixRGB'
        for op, meth_name in COLOR_MIX.items():
            self.add_call('METHOD', blid, meth_name, self_name="color1", blend_type=op)
        
        # ----------------------------------------------------------------------------------------------------
        # r, g, b properties
        
        self.add_property('ShaderNodeSeparateRGB', 'separate', settable=True, prop_names = ['r', 'g', 'b'])

        # ----------------------------------------------------------------------------------------------------
        # Methods

        self.add_call('STACK', 'ShaderNodeRGBCurve',         'curves')
        self.add_call('METHOD', 'ShaderNodeMixRGB',          'mix')
        

# -----------------------------------------------------------------------------------------------------------------------------
# String

class StringGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'String', 'dsock.String')
        
        # ----------------------------------------------------------------------------------------------------
        # Property
        
        self.add_property('FunctionNodeStringLength', 'length')
        
        # ----------------------------------------------------------------------------------------------------
        # Operation

        # Implemented manually
        # self.add_call('METHOD', 'GeometryNodeStringJoin', meth_name="join_strings", self_name="strings")        
        
        # ----------------------------------------------------------------------------------------------------
        # Methods
        
        
        self.add_call('STACK', 'FunctionNodeReplaceString',      'replace')
        
        self.add_call('METHOD', 'FunctionNodeSliceString',       'slice')        
        self.add_call('METHOD', 'GeometryNodeStringToCurves',    'to_curves',  ret_class = 'Curve')        
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# Geometry
        
class GeometryGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Geometry', 'dsock.Geometry')
        
        self.add_call('STATIC', 'GeometryNodeIsViewport', 'is_viewport')
        
        # ----- Properties
        
        self.add_property('GeometryNodeBoundBox',           'bound_box',  prop_names=['box', 'box_min', 'box_max'])
        self.add_property('GeometryNodeSeparateComponents', 'components', 
                          prop_names=('mesh_component', 'points_component', 'curve_component', 'volume_component', 'instances_component'))
        
        # ----- Methods
        
        self.add_call('STACK',  'GeometryNodeCaptureAttribute',     'capture_attribute')
        
        self.add_call('METHOD', 'GeometryNodeAttributeTransfer',    'transfer_boolean', data_type = 'BOOLEAN'      )
        self.add_call('METHOD', 'GeometryNodeAttributeTransfer',    'transfer_integer', data_type = 'INT'          )
        self.add_call('METHOD', 'GeometryNodeAttributeTransfer',    'transfer_float',   data_type = 'FLOAT'        )
        self.add_call('METHOD', 'GeometryNodeAttributeTransfer',    'transfer_vector',  data_type = 'FLOAT_VECTOR' )
        self.add_call('METHOD', 'GeometryNodeAttributeTransfer',    'transfer_color',   data_type = 'FLOAT_COLOR'  )

        self.add_call('METHOD', 'GeometryNodeDuplicateElements',    'duplicate_elements')
        self.add_call('METHOD', 'GeometryNodeDuplicateElements',    'duplicate_points',    domain = 'POINT'   )
        

        self.add_call('STACK', 'GeometryNodeDeleteGeometry',       'delete_geometry'    )
        self.add_call('STACK', 'GeometryNodeMergeByDistance',      'merge_by_distance'  )
        self.add_call('STACK', 'GeometryNodeReplaceMaterial',      'replace_material'   )
        self.add_call('STACK', 'GeometryNodeScaleElements',        'scale_elements'     )
        self.add_call('STACK', 'GeometryNodeSetID',                'set_ID'             )
        self.add_call('STACK', 'GeometryNodeSetMaterial',          'set_material'       )
        self.add_call('STACK', 'GeometryNodeSetMaterialIndex',     'set_material_index' )
        self.add_call('STACK', 'GeometryNodeSetPosition',          'set_position'       )
        self.add_call('STACK', 'GeometryNodeSetShadeSmooth',       'set_shade_smooth'   )
        self.add_call('STACK', 'GeometryNodeTransform',            'transform'          )
        
        self.add_call('STACK', 'GeometryNodeStoreNamedAttribute',  'store_named_attribute')

        self.add_call('STACK', 'GeometryNodeStoreNamedAttribute',  'store_named_float',      data_type = 'FLOAT'       )
        self.add_call('STACK', 'GeometryNodeStoreNamedAttribute',  'store_named_integer',    data_type = 'INT'         )
        self.add_call('STACK', 'GeometryNodeStoreNamedAttribute',  'store_named_vector',     data_type = 'FLOAT_VECTOR')
        self.add_call('STACK', 'GeometryNodeStoreNamedAttribute',  'store_named_color',      data_type = 'FLOAT_COLOR' )
        self.add_call('STACK', 'GeometryNodeStoreNamedAttribute',  'store_named_byte_color', data_type = 'BYTE_COLOR'  )
        self.add_call('STACK', 'GeometryNodeStoreNamedAttribute',  'store_named_boolean',    data_type = 'BOOLEAN'     )
        
        #self.add_call('METHOD', 'GeometryNodeAttributeDomainSize',  'attribute_domain_size' )
        self.add_call('METHOD', 'GeometryNodeRemoveAttribute',      'remove_named_attribute' )
        
        self.add_call('METHOD', 'GeometryNodeSeparateGeometry',     'components'            )
        self.add_call('METHOD', 'GeometryNodeConvexHull',           'convex_hull'           )
        self.add_call('METHOD', 'GeometryNodeGeometryToInstance',   'to_instance'           )
        self.add_call('METHOD', 'GeometryNodeJoinGeometry',         'join'                  )
        self.add_call('METHOD', 'GeometryNodeProximity',            'proximity'             )
        
# -----------------------------------------------------------------------------------------------------------------------------
# Mesh  
        
class MeshGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Mesh', 'gn.Geometry')
        
        # ----------------------------------------------------------------------------------------------------
        # Constructors
        
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshCircle'        ,'Circle'     )
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshCone'          ,'Cone'       )
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshCube'          ,'Cube'       )
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshCylinder'      ,'Cylinder'   )
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshGrid'          ,'Grid'       )
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshIcoSphere'     ,'IcoSphere'  )
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshLine'          ,'Line'       )
        self.add_call('CONSTRUCTOR', 'GeometryNodeMeshUVSphere'      ,'UVSphere'   )
        
        # ----------------------------------------------------------------------------------------------------
        # Properties
        #                 - component : str (default = 'MESH') in ('MESH', 'POINTCLOUD', 'CURVE', 'INSTANCES')

        self.add_property('GeometryNodeAttributeDomainSize', 'domain_size', settable=False,
                          prop_names={'point_count' : 0, 'edge_count' : 1, 'face_count' : 2, 'corner_count' : 3}, component='MESH')
        
        # ----------------------------------------------------------------------------------------------------
        # Boolean operation

        self.add_call('METHOD', 'GeometryNodeMeshBoolean', 'intersect',  operation='INTERSECT'  )
        self.add_call('METHOD', 'GeometryNodeMeshBoolean', 'union',      operation='UNION'      )
        self.add_call('METHOD', 'GeometryNodeMeshBoolean', 'difference', self_name='mesh_1',    operation='DIFFERENCE')

        # ----------------------------------------------------------------------------------------------------
        # Methods

        self.add_call('STACK', 'GeometryNodeSplitEdges',         'split_edges'          )
        self.add_call('STACK', 'GeometryNodeSubdivideMesh',      'subdivide'            )
        self.add_call('STACK', 'GeometryNodeSubdivisionSurface', 'subdivision_surface'  )
        self.add_call('STACK', 'GeometryNodeTriangulate',        'triangulate'          )
        self.add_call('STACK', 'GeometryNodeDualMesh',           'dual'                 )
        self.add_call('STACK', 'GeometryNodeFlipFaces',          'flip_faces'           )
        
        self.add_call('METHOD', 'GeometryNodeDuplicateElements',    'duplicate_edges',     domain = 'EDGE'    )
        self.add_call('METHOD', 'GeometryNodeDuplicateElements',    'duplicate_faces',     domain = 'FACE'    )
        
        self.add_call('METHOD', 'GeometryNodeExtrudeMesh',              'extrude',                       )
        self.add_call('METHOD', 'GeometryNodeMeshToCurve',              'to_curve',                     ret_class='Curve')
        self.add_call('METHOD', 'GeometryNodeMeshToPoints',             'to_points',                    ret_class='Points')
        self.add_call('METHOD', 'GeometryNodeDistributePointsOnFaces',  'distribute_points_on_faces',   ret_class='Points')
        
    # ----------------------------------------------------------------------------------------------------
    # Specific code
    
    def gen_specific(self):
        yield "\n"
        yield "    def init_domains(self):\n"
        yield "        self.verts   = domains.Vertex(self)\n"
        yield "        self.edges   = domains.Edge(self)\n"
        yield "        self.faces   = domains.Face(self)\n"
        yield "        self.corners = domains.Corner(self)\n\n"
        
        yield "    @property\n"
        yield "    def point(self):\n"
        yield "        return self.verts\n\n"
        
        yield "    @property\n"
        yield "    def edge(self):\n"
        yield "        return self.edges\n"
        
        yield "    @property\n"
        yield "    def face(self):\n"
        yield "        return self.faces\n"
        
        yield "    @property\n"
        yield "    def corner(self):\n"
        yield "        return self.corners\n\n"
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# Points
        
class PointsGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Points', 'gn.Geometry')
        
        # ----------------------------------------------------------------------------------------------------
        # Properties
        #                 - component : str (default = 'MESH') in ('MESH', 'POINTCLOUD', 'CURVE', 'INSTANCES')

        self.add_property('GeometryNodeAttributeDomainSize', 'domain_size', settable=False,
                          prop_names={'point_count' : 0}, component='POINTCLOUD')
        
        
        self.add_call('STACK',  'GeometryNodeSetPointRadius',    'set_radius'          )
        
        self.add_call('METHOD', 'GeometryNodeInstanceOnPoints',  'instance_on_points', ret_class='Instances')
        self.add_call('METHOD', 'GeometryNodePointsToVertices',  'to_vertices',        ret_class='Mesh'     )
        self.add_call('METHOD', 'GeometryNodePointsToVolume',    'to_volume',          ret_class='Volume'   )
        
    # ----------------------------------------------------------------------------------------------------
    # Specific code
    
    def gen_specific(self):
        yield "\n"
        yield "    def init_domains(self):\n"
        yield "        self.points = domains.CloudPoint(self)\n\n"
        
        yield "    @property\n"
        yield "    def point(self):\n"
        yield "        return self.points\n"

# -----------------------------------------------------------------------------------------------------------------------------
# Instances
        
class InstancesGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Instances', 'gn.Geometry')
        
        # ----------------------------------------------------------------------------------------------------
        # Constructors
        
        self.add_call('STATIC', 'GeometryNodeInstanceOnPoints',   'InstanceOnPoints')
        self.add_call('STATIC', 'GeometryNodeGeometryToInstance', 'FromGeometries')
        
        
        # ----------------------------------------------------------------------------------------------------
        # Properties
        #                 - component : str (default = 'MESH') in ('MESH', 'POINTCLOUD', 'CURVE', 'INSTANCES')

        self.add_property('GeometryNodeAttributeDomainSize', 'domain_size', settable=False,
                          prop_names={'instance_count' : 5}, component='INSTANCES')
        
        
        self.add_call('STACK', 'GeometryNodeRotateInstances',    'rotate'     )
        self.add_call('STACK', 'GeometryNodeScaleInstances',     'scale'      )
        self.add_call('STACK', 'GeometryNodeTranslateInstances', 'translate'  )

        self.add_call('METHOD', 'GeometryNodeRealizeInstances',   'realize'   )
        self.add_call('METHOD', 'GeometryNodeInstancesToPoints',  'to_points' )
        self.add_call('METHOD', 'GeometryNodeDuplicateElements',  'duplicate_instances', domain = 'INSTANCE')
        
    def gen_specific(self):
        yield "\n"
        yield "    def init_domains(self):\n"
        yield "        self.insts = domains.Instance(self)\n\n"
        
        yield "    @property\n"
        yield "    def instance(self):\n"
        yield "        return self.insts\n\n"
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# Volume
        
class VolumeGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Volume', 'gn.Geometry')
        
        self.add_call('METHOD', 'GeometryNodeVolumeToMesh', 'to_mesh' )
        
# -----------------------------------------------------------------------------------------------------------------------------
# Curve 
        
class CurveGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Curve', 'gn.Geometry')
        
        self.add_call('CONSTRUCTOR', 'GeometryNodeCurvePrimitiveBezierSegment', 'BezierSegment'     )
        self.add_call('CONSTRUCTOR', 'GeometryNodeCurvePrimitiveCircle',        'Circle'            )
        self.add_call('CONSTRUCTOR', 'GeometryNodeCurvePrimitiveLine',          'Line'              )
        self.add_call('CONSTRUCTOR', 'GeometryNodeCurvePrimitiveQuadrilateral', 'Quadrilateral'     )
        self.add_call('CONSTRUCTOR', 'GeometryNodeCurveQuadraticBezier',        'QuadraticBezier'   )
        self.add_call('CONSTRUCTOR', 'GeometryNodeCurveStar',                   'Star'              )
        self.add_call('CONSTRUCTOR', 'GeometryNodeCurveSpiral',                 'Spiral'            )
        
        # Depending upon the way it is initialized, the node GeometryNodeCurveArc has
        # only one output socket or several

        self.add_call('CONSTRUCTOR', 'GeometryNodeCurveArc',            'ArcFromRadius', mode = 'RADIUS')
        self.add_call('STATIC',      'GeometryNodeCurveArc',            'ArcFromPoints', mode = 'POINTS')
        
        # ----------------------------------------------------------------------------------------------------
        # Properties
        #                 - component : str (default = 'MESH') in ('MESH', 'POINTCLOUD', 'CURVE', 'INSTANCES')

        self.add_property('GeometryNodeAttributeDomainSize', 'domain_size', settable=False,
                          prop_names={'point_count' : 0, 'spline_count' : 4}, component='CURVE')
        
        
        self.add_call('STACK', 'GeometryNodeSetSplineCyclic',          'set_cyclic'               )
        self.add_call('STACK', 'GeometryNodeSetSplineResolution',      'set_resolution'           )
        self.add_call('STACK', 'GeometryNodeCurveSetHandles',          'set_handles'              )
        self.add_call('STACK', 'GeometryNodeCurveSplineType',          'set_spline_type'          )
        self.add_call('STACK', 'GeometryNodeFilletCurve',              'fillet'                   )
        self.add_call('STACK', 'GeometryNodeResampleCurve',            'resample'                 )
        self.add_call('STACK', 'GeometryNodeReverseCurve',             'reverse'                  )
        self.add_call('STACK', 'GeometryNodeSetCurveHandlePositions',  'set_handle_positions'     )
        self.add_call('STACK', 'GeometryNodeSetCurveRadius',           'set_radius'               )
        self.add_call('STACK', 'GeometryNodeSetCurveTilt',             'set_tilt'                 )
        self.add_call('STACK', 'GeometryNodeSubdivideCurve',           'subdivide'                )
        self.add_call('STACK', 'GeometryNodeTrimCurve',                'trim'                     )
        
        self.add_call('METHOD', 'GeometryNodeDuplicateElements',       'duplicate_splines',   domain = 'SPLINE'  )
        self.add_call('METHOD', 'GeometryNodeFillCurve',               'fill',        ret_class='Mesh'   )
        self.add_call('METHOD', 'GeometryNodeCurveToMesh',             'to_mesh',     ret_class='Mesh'   )
        self.add_call('METHOD', 'GeometryNodeCurveToPoints',           'to_points',   ret_class='Points' )
        self.add_call('METHOD', 'GeometryNodeSampleCurve',             'sample',      ret_class='NODE'   )
        self.add_call('METHOD', 'GeometryNodeCurveLength',             'length',      ret_class='Float'  )
        
    # ----------------------------------------------------------------------------------------------------
    # Specific code
    
    def gen_specific(self):
        yield "\n"
        yield "    def init_domains(self):\n"
        yield "        self.points  = domains.ControlPoint(self)\n"
        yield "        self.splines = domains.Spline(self)\n\n"
        
        yield "    @property\n"
        yield "    def point(self):\n"
        yield "        return self.points\n"
        
        yield "    @property\n"
        yield "    def spline(self):\n"
        yield "        return self.splines\n"
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# Texture

class TextureGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Texture', 'dsock.Texture')
        
        self.add_call('STATIC', 'ShaderNodeTexBrick'          ,'Brick'     )
        self.add_call('STATIC', 'ShaderNodeTexChecker'        ,'Checker'   )
        self.add_call('STATIC', 'ShaderNodeTexGradient'       ,'Gradient'  )
        self.add_call('STATIC', 'ShaderNodeTexMagic'          ,'Magic'     )
        self.add_call('STATIC', 'ShaderNodeTexMusgrave'       ,'Musgrave'  )
        self.add_call('STATIC', 'ShaderNodeTexNoise'          ,'Noise'     )
        self.add_call('STATIC', 'ShaderNodeTexVoronoi'        ,'Voronoi'   )
        self.add_call('STATIC', 'ShaderNodeTexWave'           ,'Wave'      )
        self.add_call('STATIC', 'ShaderNodeTexWhiteNoise'     ,'WhiteNoise')
        self.add_call('STATIC', 'GeometryNodeImageTexture'    ,'Image'     )
        
# -----------------------------------------------------------------------------------------------------------------------------
# Material
        
class MaterialGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Material', 'dsock.Material')

        self.add_call('METHOD', 'GeometryNodeMaterialSelection', 'selection', ret_class='Boolean')
        
# -----------------------------------------------------------------------------------------------------------------------------
# Image 
        
class ImageGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Image', 'dsock.Image')
        
        
# -----------------------------------------------------------------------------------------------------------------------------
# Collection
        
class CollectionGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Collection', 'dsock.Collection')

        self.add_call('METHOD', 'GeometryNodeCollectionInfo', 'info')
        
# -----------------------------------------------------------------------------------------------------------------------------
# Object
        
class ObjectGen(DataClass):
    def __init__(self, nodes):
        super().__init__(nodes, 'Object', 'dsock.Object')

        self.add_property('GeometryNodeObjectInfo', 'info', prop_names = ['location', 'rotation', 'scale', 'geometry'])


# =============================================================================================================================
# The classes generators
        

DATA_CLASSES = [GlobalGen, BooleanGen, IntegerGen, FloatGen, VectorGen, ColorGen, StringGen,
                GeometryGen, CurveGen, MeshGen, PointsGen, InstancesGen, VolumeGen,
                CollectionGen, ObjectGen, TextureGen, MaterialGen, ImageGen]


#DATA_CLASSES = [BooleanGen]

     


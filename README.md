# generator

> Generator of python for the module geonodes

# Short description

The geonodes implements two layers:
- **Nodes layer**
  One class per geometry nodes, for instance AlignEulerToVector wraps the node FunctionNodeAlignEulerToVector
  The Node class initialization creates the geometry nodes
- **Sockets layer**
  One class per data type:
  - Basis data: Boolean, Integer, Float, Vector, Color, String
  - Geometry  : Geometry, Spline, Curve, Mesh, Point, Instance, Volume
  - Special   : Collection, Object, Material, Texture, Image
  The methods and properties of the sockets are implemented by creating nodes:
  ```python
  import geonodes as gn
  
  circle = gn.Mesh.Circle(radius=2.) # creates the node GeometryNodeMeshCircle
  ```
At creation time, a node takes two types or arguments:
- the input sockets
- the node parameters

```python
import geonodes as gn
from geonodes import nodes

# rotation   : first node socket
# factor     : second socket
# vector     : third socket
# axis       : first parameter
# pivot_axis : second parameter

node = nodes.AlignEulerToVector(rotation=None, factor=None, vector=None, axis='X', pivot_axis='AUTO')
```
# Source code generation

In a Blender project, create a Geometry nodes modifier and run the following script
```python
from generator.generator import gen_geonodes

# fpath is the location to where the geonodes folder is located
# within the Blender modules folder

fpath = ".../blender/modules/scripts/modules/geonodes/"
gen_geonodes(fpath)
```
# geonodes folder structure

## geonodes.core
### geonodes.core.node

- **Tree**        : Blender NodeTree wrapper
- **DataSocket**  : Root class for socket wrappers
- **Node**        : Root class for blender geometry nodes wrappers

  Some specific nodes are implemented in this module. They are used by **Tree**:
    
  - **GroupInput** : Wrapper for node NodeGroupInput.
    ```python
    # The group input is initialized in the Tree
    Tree.group_input = GroupInput()
    ```
  - **GroupOutput** : Wrapper for node NodeGroupOutput
    ```python
    # The group output is initialized in the Tree
    Tree.group_output = GroupOutput()
    ```       
  - **Viewer**      : Wrapper for node GeometryNodeViewer
    ```python
    # The viewer is initialized by the Tree when required
    Tree.viewer = None
    ...
    if self.viewer is None:
        self.viewer = Viewer()
    ```
    One viewer per tree. Data sockets can use the method to_viewer()
              
  - **Frame**       : Wrapper for node NodeFrame
    ```python
    def new_layout(self, label, color):
       self.layouts.append(Frame(label, color))
    ```
  - **SceneTime**   : Wrapper for GeometryNodeInputSceneTime
    ```python
    Tree.scene_ = None
    
    @property
    def scene(self):
        if self.scene_ is None:
            self.scene_ = SceneTime()
        return self.scene_
    ```
    
### geonodes.core.datasockets

Implements the base class for DataSockets
All the classes are base on geonode.node.DataSocket
For geometry data, only the class Geometry is implemented in this module
The final classes will be created in geonodes.sockets with the following inheritance
Geometry
    - Spline
        - Curve
    - Mesh
        - Points
        - Instance
        - Volume
        
----- geonodes.core.colors
Some colors constants
----- geonodes.core.arrange
arrange function locates the nodes to make the whole tree somehow readable
It works independantly of the geonodes structure and just take the name
of the NodeTree as an argument.
----------------------------------------------------------------------------------------------------
----- geonodes.nodes.nodes
All he nodes generated by the generator
----------------------------------------------------------------------------------------------------
----- geonodes.nodes.sockets
One file per data socket class plus functions.py which contains the global functions
----------------------------------------------------------------------------------------------------
----- geonodes.__init__.py
The pack initi file contains
====================================================================================================
Generation principle
The generation module is designed to ease the updates with the new versions of geometry nodes
Step 1
------
    try to create all the possible nodes by listing all the types in bpy.types:
    
    for type_name in dir(bpy.types):
        try:
            node = nodes.new(type_name)
        except:
            continue
        
        # We have a valid type
        
    The legacy nodes are excluded from the scane
    
Step 2
------
    Each node is analyzed by:
        - Identifying the parameters (non standard attributes)
            Three types of parameters are possible:
                - Non settable parameters, for instance the color selector of an input color node
                - Enum parameters: str param with a list of valid values
                - Non enum settable parameters, the resolution of a circle for instance
            The settable parameters will be part of the node creation argument
        
        - Identifying if the node has "shared sockets"
            Shared sockets are sockets of different types but sharing the same name.
            Only one socket is enabled at a time, depending upon a "driving parameter"
            Example: node FunctionNodeCompare:
                    - Driving parameter : data_type in ('FLOAT', 'INT', 'VECTOR', 'STRING', 'RGBA')
                    - Input sockets     : ['a', 'b']
                    a and b are names shared by sockets of type Float, Integer, Vector, String and Color
                    
        - Renaming sockets homonyms when exist
            For instance node ShaderNodeMath has three input sockets named Value. They are renamed
            value0, value1 and value2
                    
Step 3
------
    file nodes.py generation in folder geonodes.nodes
    
    The __init__ method of the node class is the concatenation of the input sockets and the settable parameters
    
    for instance, the __init__ method of ShaderNodeMath is:
        
        def __init__(self, value0=None, value1=None, value2=None, operation='ADD'):
            
            The node has 3 sockets and one parameter named operation.
            The default value 'ADD' is the one of the parameter at creation time.
            When a socket has the value None, it is left unplugged.
            A socket can be either a value or data socket class. If it is a value, it
            must be an acceptable default value for the input socket.
            
    An additional argument label is used to allow the user to change the node label:
        def __init__(self, value0=None, value1=None, value2=None, operation='ADD', label=None):
            
Step 4
------
    Generation of the data sockets classes.
    
    A data socket basically wraps an output node socket.
    The methods of a data class consist in creating a node and to plug the socket to one
    input socket of this node.
    
    Example:
        Let use x as a Float which is the output socket of a node.
        We can write:
            
            y = x ** 3
            
        This will create the node ShaderNodeMath with the following parameters:
            
            node = Math(value0=self, value1=3, operation='POWER')
            return node.value
        
    Implementation types
    ---------------------
    
    Depending on their behaviors, the nodes can be implented in the following ways:
        
        Constructor
        -----------
            For nodes which don't transform a socket but create new data
            
            Example: GeometryNodeMeshCircle is implemented as a Mesh constructor
            
            @classmethod
            def Circle(cls, vertices=None, radius=None, fill_type='NONE'):
                return cls(nodes.MeshCircle(vertices=vertices, radius=radius, fill_type=fill_type).mesh)
            
        Property
        --------
            For node which return info on data sockets. The properties are kept in local attributes:
                
                self.prop_ = ... node creation
                return self.prop_
            
            Example: GeometryNodeBoundBox returns 3 infos on the geometry : bounding_box, min and max
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 10 17:31:08 2022

@author: alain
"""

import geonodes as gn

def test_viewer():
    
    with gn.Tree("Test Viewer") as tree:
        
        mesh = gn.Mesh(tree.ig)
        
        mesh.verts.view(mesh.verts.position)
        
        tree.og = mesh
        
def test_sample_curve():
    
    with gn.Tree("Test Sample Curve") as tree:
        
        c = gn.Curve.Circle().curve
        line = gn.Mesh.Line(count=10)
        
        curves = gn.Curve(line.verts.instance_on_points(c).realize())
        
        sample=curves.sample(value=curves.splines.position)
        
        curves.splines.view(sample.value)
        
        tree.og = curves
        
def test_mesh_topology():

    with gn.Tree("Test Mesh Topology") as tree:
        
        mat0 = gn.Material.Input("Material 1")
        mat1 = gn.Material.Input("Material 2")
        
        with tree.layout("Corners of face, Offset corner in face, Vertex of corner"):

            ico = gn.Mesh.IcoSphere()
            ico.faces.material = mat0
            
            fidx = gn.Integer.Input(0, "Face index")
            cidx = gn.Integer.Input(3, "Corner index")
            ofs  = gn.Integer.Input(1, "Corner offset")
        
            faces = ico.faces[fidx]
            
            faces.corners[cidx].offset_in_face(ofs).vertex.position += (0, 0, .1)
            faces.corners[cidx+1].vertex.position += (0, 0, .2)
            
        geo = ico
            
        with tree.layout("Corners of vertex, Face of corner"):
            
            cube = gn.Mesh.Cube()
            cube.transform(translation=(2, 0, 0))
            cube.faces.material = mat0
            
            vidx = gn.Integer.Input(0, "Vertex index")
            
            corners = cube.verts[vidx].corners
            corners[cidx].face.shade_smooth = True
            corners[cidx].face.material = mat1
            corners[cidx+1].face.material_index = 1
            
        geo = geo + cube

        with tree.layout("Edges of vertex, Edges of corner"):
            
            sphere = gn.Mesh.UVSphere(segments=5, rings=5)
            sphere.transform(translation=(4, 0, 0))
            sphere.faces.material = mat0
            
            vertex = sphere.verts[vidx]
            loc = vertex.position
            
            sphere.verts[vidx].edges[0].scale(scale=.2)
            
            sphere.edges[sphere.corners[cidx].previous_edge_index].scale(scale=2)
            sphere.edges[sphere.corners[cidx].next_edge_index].scale(scale=2)
            
            
        geo = geo + sphere
        
        
        tree.og = geo
        
def test_curve_topology():

    with gn.Tree("Test Curve Topology") as tree:
        
        pidx = gn.Integer.Input(0, "Point index")
        cidx = gn.Integer.Input(5, "Curve index")
        piic = gn.Integer.Input(3, "Point index in curve")
        pofs = gn.Integer.Input(3, "Point offset")
        
        with tree.layout("Several circles and Set curve normal"):
    
            circle = gn.Curve.Circle().curve
            
            line = gn.Mesh.Line(count=10)
            curves = gn.Curve(line.verts.instance_on_points(instance=circle).realize())
            
            curves.splines[cidx].set_normal_z_up()
            
        with tree.layout("Curve of point"):
            curves.points[pidx].curve.cyclic = False
            
        with tree.layout("Points of curve and Offset in curve"):
            curve = curves.splines[cidx]
            point = curves.splines[cidx].points[piic].offset_in_curve(pofs)
            point.position += (1, 0, 0)
        
        tree.og = curves
        
def test_volume():
    
    with gn.Tree("Test Volume") as tree:
        
        volume = gn.Volume.Cube()
        
        tree.og = volume.distribute_points(density=gn.Float.Input(1., "Density"), seed=gn.Integer.Input(0, "Seed"))
        
def test_mesh():
    
    with gn.Tree("Test Mesh") as tree:
        
        ico = gn.Mesh.IcoSphere(subdivisions=5)
        
        face_set = gn.Integer.Random(0, gn.Integer.Input(1, "Face set max"), seed=gn.Integer.Input(0, "Seed"))
        
        sel = ico.face_set_boundaries(face_set=face_set)
        
        ico.edges[sel].scale(scale=.5)
        
        # ---- Just to test
        
        a = ico.verts.sample_nearest()
        b = ico.edges.sample_index(index=a)
        b.to_output("Test")
        
        c = ico.sample_nearest_surface(value=ico.verts.index)
        d = ico.sample_uv_surface(value=ico.verts.position)
        
        c.to_output()
        d.value.to_output()
        

        tree.og = ico
        
def test_self():
    
    with gn.Tree("Test Self Object") as tree:
        
        geo = tree.ig
        geo.set_position(offset=-gn.Object.Self().location())
        tree.og = geo
        
        
    
    


def tests():
    test_viewer()
    test_sample_curve()
    test_mesh_topology()
    test_curve_topology()
    test_volume()
    test_mesh()
    test_self()
        
        
        
        
        
    
    
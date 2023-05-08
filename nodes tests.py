#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  5 15:54:31 2023

@author: alain
"""

# ----------------------------------------------------------------------------------------------------

def blur_attribute():
    with gn.Tree("Test") as tree:
        
        mesh = gn.Mesh(tree.ig)
        
        mesh.subdivide()
        
        col = gn.Color.HSL(hue=gn.Float.Random(), saturation=1, lightness=.5)
        
        col = mesh.faces.capture_attribute(value=col)
        mesh.subdivide(4)
        blur = mesh.faces.blur_attribute(value=col)
        mesh.faces.store_named_color(name="Color", value=blur)
        
        tree.og = mesh    
        
# ----------------------------------------------------------------------------------------------------

def edges_to_face_groups():
    with gn.Tree("Test") as tree:
        
        mesh = gn.Mesh(tree.ig)
        mesh.faces.store_named_attribute(name='Color', value=gn.Color.HSV(0, .5, .5))
        
        fid = mesh.edges[0].to_face_groups()
        
        mesh.faces[mesh.faces.ID.equal(fid)].store_named_attribute(name='Color', value=gn.Color.HSV(.5, 1, 1))
        
        tree.og = mesh
        
# ----------------------------------------------------------------------------------------------------

def image_info():

    with gn.Tree("Test") as tree:
        
        mesh = gn.Mesh(tree.ig)
        
        image = gn.Image("TestImage")
        print(image)
        
        #print(image)
        #print(image.width())
        
        
        mesh.faces.store_named_integer(name="Color", value=image.width())
        mesh.faces.store_named_integer(name="Color", value=image.height())
        mesh.faces.store_named_integer(name="Color", value=image.has_alpha())
        mesh.faces.store_named_integer(name="Color", value=image.frame_count())
        mesh.faces.store_named_integer(name="Color", value=image.fps())
        
        tree.og = mesh
        
# ----------------------------------------------------------------------------------------------------

def interpolate_curves():
    with gn.Tree("Test") as tree:
        
        bases = gn.Points.Points(count=10)
        line  = gn.Curve.Line((0, 0, 0), (10, 10, 10))
        lines = bases.instance_on_points(instance=line)
        curves = lines.realize()
        curves.points.position = gn.Vector.Random((-10, -10, -10), (10, 10, 10))
        
        
        children = gn.Points.Points(count=1000)
        children.points.position = gn.Vector.Random((-10, -10, -10), (10, 10, 10))
        
        ico = gn.Mesh.IcoSphere(radius=5, subdivisions=5)
        
        mode = 3
        if mode == 0:
            new_curves = gn.Curve(curves).interpolate(points=children).curves
        elif mode == 1:
            new_curves = children.interpolate(guide_curves=curves).curves
        elif mode == 2:
            new_curves = children.points.interpolate(guide_curves=curves).curves
        elif mode == 3:
            new_curves = ico.verts.interpolate(guide_curves=curves).curves
        
        tree.og = new_curves
    
    
# ----------------------------------------------------------------------------------------------------

def trim():
    
    with gn.Tree("Test") as tree:
        
        bases = gn.Points.Points(count=10)
        line  = gn.Curve.Line((0, 0, 0), (10, 10, 10))
        lines = bases.instance_on_points(instance=line)
        curves = gn.Curve(lines.realize())
        curves.points.position = gn.Vector.Random((-10, -10, -10), (10, 10, 10))
        
        mode = 3
        if mode == 0:
            curves.trim(start=0, end=.5)
        elif mode == 1:
            curves.trim_factor(start=0, end=.5)
        elif mode == 2:
            curves.trim_length(start=0, end=3)
    
        elif mode == 3:
            curves.splines[0].trim(start=0, end=.5)
        elif mode == 4:
            curves.splines[0].trim_factor(start=0, end=.5)
        elif mode == 5:
            curves.splines[0].trim_length(start=0, end=3)
        
        meshes = curves.to_mesh(profile_curve=gn.Curve.Circle(radius=0.1))
        
        
        tree.og = meshes
        
# ----------------------------------------------------------------------------------------------------

                
    
        


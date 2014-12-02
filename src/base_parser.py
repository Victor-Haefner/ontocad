#!/usr/bin/env python

import numpy
from numpy import *
from ocad_primitives import *
from ocad_math import *
import xml.etree.ElementTree as ET
from layer import layer

import sys

PI = 3.14159265359

class base_parser:
	def __init__(self):
		#parser variables
		self.N = 16
		self.rescale = 1.0
		
		self.rot_angle = 0.
		self.transformation = array([1.,0.,0.,0.,1.,0.,0.,0.,1.]).reshape(3,3)
		
		self.offset_stack = []
		self.scale_stack = []
		self.rotation_stack = []
		self.rot_angle_stack = []
		self.compute_current_transformation()
		
		self.last_controle_point = array([0,0])
		self.element_id = long(0)
		#self.layers = {}
		self.viewports = {}
		self.elem_dict = {}
		
		#ifc
		self.data = {}

#helper functions-------------------------------
	def compute_current_transformation(self):
		#self.offset = array([0.0,0.0]);
		#self.scale = array([1.0,1.0]);
		#self.rotation = array([1.0,0.0,0.0,1.0]).reshape(2,2);
		
		rs = self.rescale
		self.transformation = array([rs,0.0,0.0,0.0,rs,0.0,0.0,0.0,1.0]).reshape(3,3)
		for i in range(len(self.offset_stack)):
			o = self.offset_stack[i]
			s = self.scale_stack[i]
			f = self.rot_angle_stack[i]
			r = [cos(f), -sin(f), sin(f), cos(f)]
			
			#transformation matrix 3x3
			#t = array([r[0]*s[0], r[1], o[0],   r[2], r[3]*s[1], o[1],    0., 0., 1. ]).reshape(3,3)
			t = array([r[0], r[1], o[0],   r[2], r[3], o[1],    0., 0., 1. ]).reshape(3,3)
			S = array([s[0], 0., 0.,   0., s[1], 0.,    0., 0., 1. ]).reshape(3,3)
			t = dot(t,S)
			self.transformation = dot(self.transformation, t)
		
		self.rot_angle = 0.
		for f in self.rot_angle_stack:
			self.rot_angle += f
		
	#creates a layer if not present and returns it
	def getLayer(self, v_name, l_name):
		# get viewport
		if not v_name in self.viewports:
			self.viewports[v_name] = viewport(v_name)
		v = self.viewports[v_name]
		
		# get layer
		if not l_name in v.layers:
			v.layers[l_name] = layer(l_name)
			
		return v.layers[l_name]
		
	def multWithTrans(self, v, point = True):
		w = array([v[0], v[1], 1.0])
		if not point:
			w[2] = 0.0
			
		w = dot(self.transformation, w)
		return array([w[0], w[1]])

#primitives-------------------------------------
	#all primitives are converted to lines
	def addPoint(self, p):
		p = self.multWithTrans(p)
		self.layer.addPoint( point(p[0], p[1], 100) )
	
	def addLine(self, vec1, vec2):
		v1 = self.multWithTrans(vec1)	
		v2 = self.multWithTrans(vec2)
		self.layer.addLine( line(v1[0], v1[1], v2[0], v2[1]) )

	def addCircle(self, cx, cy, _r):
		c = array([cx, cy])
		c = self.multWithTrans(c)

		s = array([1, 0])
		s = self.multWithTrans(s, False)
		
		r = _r*sqrt(s[0]*s[0] + s[1]*s[1])
		
		self.layer.addArc( arc(c[0], c[1], r, 0, 2*PI) )

	def addEllipse(self, cx, cy, a, b):		
		c = array([cx, cy])
		c = self.multWithTrans(c)
		
		box = array([a, b])
		box = self.multWithTrans(box, False)
		box[0] = abs(box[0])
		box[1] = abs(box[1])
		
		#e = arc(c[0] - 0.5*box[0], c[1] + 0.5*box[1], 1, 0, 360*64)
		e = arc(c[0], c[1], 1, 0, 2*PI)
		e.box.x = box[0]
		e.box.y = box[1]
		self.layer.addArc( e )
		
	def addArc(self, cx, cy, _r, _a1, _a2, bulge = 0):		
		#compute start and end point, transform them and compute back to angles
		scos, ssin, ecos, esin = math.cos(_a1), math.sin(_a1), math.cos(_a2), math.sin(_a2)
		sp = [_r*scos+cx, _r*ssin+cy]
		ep = [_r*ecos+cx, _r*esin+cy]
		sp = self.multWithTrans(sp)	
		ep = self.multWithTrans(ep)
		
		#transform the center
		c = array([cx, cy])
		c = self.multWithTrans(c)
		
		#scale the radius
		s = array([1, 0])
		s = self.multWithTrans(s, False)
		r = _r*sqrt(s[0]*s[0] + s[1]*s[1])
		
		#calc start and end angle------------------------------------
		_a1 = math.atan2(sp[1] - c[1], sp[0] - c[0]) + PI
		_a2 = math.atan2(ep[1] - c[1], ep[0] - c[0]) + PI
		
		#check for mirror transformation
		ang = [_a1, _a2]
		det = linalg.det(self.transformation)
		if det < 0:
			ang = [_a2, _a1]
			
			
		self.layer.addArc( arc(c[0], c[1], r, ang[0], ang[1]) )


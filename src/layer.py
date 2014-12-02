#!/usr/bin/env python

import numpy
from numpy import *
from ocad_primitives import *
import itertools

class layer:
	def __init__(self, _name):
		self.name = _name

		self.visible = 1
		self.changed = 1

		#pensil
		self.line_width = 1
		self.point_size = 3
		self.caps = 0
		self.line_style = 0
		self.color = array([0,0,0])
		self.offset = None
		self.size = None

		#primitives
		self.lines = []
		self.lines_dict = {} #dict, length is key
		self.arcs = []
		self.points = []

		self.pixbuf = None
		self.pixmap = None

		self.bg_pb = None

	def copyPrimitives(self, layer):#fetch primitives from the layer
		self.lines = layer.lines[:]
		self.arcs = layer.arcs[:]
		self.points = layer.points[:]
		self.offset = layer.offset[:]
		self.size = layer.size[:]

	def clear(self):
		self.lines = []
		self.arcs = []
		self.points = []

	def initMinMax(self, p):
		if self.offset == None:
			self.offset = p[:]
		if self.size == None:
			self.size = point()

	def checkMinMax(self, p):
		p = p[:]

		self.initMinMax(p)

		if p.x < self.offset.x:
			self.offset.x = p.x
		if p.x > self.size.x:
			self.size.x = p.x

		if p.y < self.offset.y:
			self.offset.y = p.y
		if p.y > self.size.y:
			self.size.y = p.y

	# Add primitives in world coordinates

	def addPoint(self, p):
		"""Add a point.

		:param p: p.x = point[0][0]
		          p.y = point[0][1]
			  point[1] is an offset to define the bounding box
		
		"""
		self.points.append(p)
		self.checkMinMax(p)

	def addLine(self, line):
		self.lines.append(line)
		
		l = round(line.length,2)
		if not l in self.lines_dict:
			self.lines_dict[l] = []
		self.lines_dict[l].append(line)
		
		
		self.checkMinMax(line.p1)
		self.checkMinMax(line.p2)
		
	def addArc(self, arc):
		self.arcs.append(arc)
		
		self.checkMinMax(arc.center + arc.box)
		self.checkMinMax(arc.center - arc.box)

	def drawPixmap(self, gtk, rescale, _offset, redraw = False):			
		if self.size == None:
			return
			
		size = self.size*rescale - self.offset*rescale + point(1,1)
		offset = self.offset*rescale
		
		self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, int(size.x), int(size.y))
		self.pixbuf.fill(0x00ffffff)#RGBA -> white
		
		if self.bg_pb != None:
			o = self.offset*rescale - _offset
			ox = int(o.x)
			oy = int(o.y)
			w = self.pixbuf.get_width()
			h = self.pixbuf.get_height()
			bgw = self.bg_pb.get_width()
			bgh = self.bg_pb.get_height()
			
			if ox < 0:
				ox = 0
			if oy < 0:
				oy = 0
			if ox + w > bgw:
				w = bgw - ox
			if oy + h > bgh:
				h = bgh - oy
				
			self.bg_pb.copy_area(ox, oy, w, h, self.pixbuf, 0, 0)
			
		if self.bg_pb == None or redraw == True:
			self.pixmap, mask = self.pixbuf.render_pixmap_and_mask()
			
			gc = self.pixmap.new_gc()
			gc.line_width = self.line_width
			gc.cap_style = self.caps
			gc.line_style = self.line_style
			c = self.color
			uncol = gtk.gdk.color_from_hsv(c[0], c[1], c[2])
			col = gc.get_colormap().alloc_color(uncol)
			gc.foreground = col
			
			#lines
			for l in self.lines:
				self.pixmap.draw_line(gc, 	int(l.p1.x*rescale - offset.x), 
											int(-l.p1.y*rescale - offset.y), 
											int(l.p2.x*rescale - offset.x), 
											int(-l.p2.y*rescale - offset.y))
			
			#arcs
			for a in self.arcs:
				self.pixmap.draw_arc(gc, 0, int(a.center.x*rescale - offset.x), 
											int(-a.center.y*rescale - offset.y), 
											int(a.box.x*rescale), 
											int(a.box.y*rescale), 
											int(-a.a1), 
											int(-a.a2))
				
			#points
			gc.cap_style = 2
			gc.line_style = 0
			for p in self.points:
				gc.line_width = int(p.rad*rescale)
				ix = int(p.x*rescale - offset.x)
				iy = int(p.y*rescale - offset.y)
				self.pixmap.draw_line(gc, ix, iy, ix, iy)
			gc.line_width = self.line_width
			gc.line_style = self.line_style
			gc.cap_style = self.caps
		
			self.pixbuf.get_from_drawable(self.pixmap, gc.get_colormap(), 0,0,0,0, int(size.x), int(size.y))
			
		if self.bg_pb == None:
			self.pixbuf = self.pixbuf.add_alpha(True, 0, 255, 255)

	def setBackground(self, bg_pb):
		self.bg_pb = bg_pb

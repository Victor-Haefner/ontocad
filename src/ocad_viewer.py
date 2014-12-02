#!/usr/bin/env python

import numpy
from numpy import *
from ocad_primitives import *
import copy

import layer

class ocad_viewer:
	def __init__( self, data, gtk, toplvlwin ):
		self.data = data
		self.gtk = gtk
		self.toplevel = toplvlwin
		self.rescale = 0.07
		self.layer = "None"
		self.navChanged = 1
		self.window = None
		self.layers = None
		self.dataOffset = None
				
	def draw_layer_to_view(self, layer, offset, redraw = False, reset = False):
		if layer.offset == None:
			#print "BUH"
			return
		
		v = self.viewer
		p = v.get_pixbuf()
		p_bg = v.get_pixbuf()
		if reset == True:
			p_bg = self.data.reference_image
		
		layer.setBackground(p_bg)
		layer.drawPixmap(self.gtk, self.rescale, offset, redraw)
		
		oint = layer.offset*self.rescale - offset
		offset_int = [ int(oint.x), int(oint.y) ]
		
		w = layer.pixbuf.get_width()
		h = layer.pixbuf.get_height()
		
		src_x, src_y = 0,0
		"""if offset_int[0] < 0:
			src_x = -offset_int[0]
			w -= src_x
			offset_int[0] = 0
		if offset_int[1] < 0:
			src_y = -offset_int[1]
			h -= src_y
			offset_int[1] = 0"""
		
		if offset_int[0] + w > p.get_width():
			w = p.get_width() - offset_int[0]
		if offset_int[1] + h > p.get_height():
			h = p.get_height() - offset_int[1]
				
		#print "X", src_x, w, offset_int[0]
		#print "Y", src_y, h, offset_int[1]
		layer.pixbuf.copy_area(src_x, src_y, w, h, p, offset_int[0], offset_int[1])
		
		#r = [offset_int[0], offset_int[1], w, h]
		#v.damage_pixels(r) # geht nicht wirklich gut
		v.queue_draw()
			
	def defineNeededSpace(self, layers):
		offset = None
		size = None
		for l_key in layers:
			l = layers[l_key]
			if l.offset == None:
				continue
			if offset == None:
				offset = l.offset[:]
				size = l.size[:]
				
			if offset.x > l.offset.x:
				offset.x = l.offset.x
				
			if offset.y > l.offset.y:
				offset.y = l.offset.y
				
			if size.x < l.size.x:
				size.x = l.size.x
				
			if size.y < l.size.y:
				size.y = l.size.y
		
		if offset == None or size == None:
			return [0,0], [400,400]
			
		return offset*self.rescale, size*self.rescale - offset*self.rescale + point(1,1)
				
	def redraw(self):
		if self.layers == None:
			return
			
		#self.viewer.redraw()
		#return
		
			
		#old code
			
		#define the space needed
		offset, size = self.defineNeededSpace(self.layers)
		self.dataOffset = offset
		self.dataSize = size
		
		if self.viewer.get_pixbuf() == None:
			self.viewer.init(int(size.x), int(size.y))
		
		#draw acad layers
		for i,l in enumerate(self.layers):
			if self.layers[l].visible == 0:
				continue
			self.draw_layer_to_view(self.layers[l], offset, True)
			print int(100*i/len(self.layers))
			
			
		self.viewer.store_pixbuf()
		
	def resetSelectionLayer(self):
		self.draw_layer_to_view(self.data.highlight, self.dataOffset, False, True)
		self.draw_layer_to_view(self.selector.selection, self.dataOffset, False, True)
		
	def redrawSelectionLayer(self):
		self.draw_layer_to_view(self.selector.selection, self.dataOffset, True, True)
		
	def redrawHightlightLayer(self):
		self.draw_layer_to_view(self.data.highlight, self.dataOffset, True)
	
	def selectLayer(self, l):
		self.resetSelectionLayer()
		self.data.highlight.copyPrimitives(l)
		self.redrawHightlightLayer()
	
	def arr_length(self,a):
		return sqrt(a[0]*a[0] + a[1]*a[1])


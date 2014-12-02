#!/usr/bin/env python
import numpy
from numpy import *
from ocad_primitives import *
import layer

PI = 3.14159265359

class selector:
	def __init__( self ):
		self.selectionLasso = layer.layer("poly_lasso_selection")
		self.selectionLasso.line_style = 1 #self.gtk.gdk.LINE_ON_OFF_DASH
		self.selectionLasso.line_width = 3 
		self.selectionLasso.color = [0.5, 0.5, 0.5]
		
		self.selectionPin = layer.layer("poly_pin_selection")
		self.selectionPin.point_size = 10 
		self.selectionPin.color = [0.5, 0.5, 0.5]
		
		self.lastPosition = None
		self.firstPosition = None
		self.closed = False
		self.active = False
		self.img_pnts = []
		self.wrl_pnts = []
		
		self.mode = "LASSO"
		
	def cancel(self):
		self.closeLoop()
		self.clear()

	def appendToPolySelect(self, pos, imgpos):
		self.img_pnts.append(imgpos)
		self.wrl_pnts.append(pos)
		if self.lastPosition == None:#first point
			self.firstPosition = pos[:]
			self.lastPosition = pos[:]
			if self.mode == "LASSO":
				self.selectionLasso.clear()
				self.selectionLasso.addPoint( pos[:] )
			if self.mode == "PIN":
				self.selectionPin.clear()
				self.selectionPin.addPoint( pos[:] )
			self.closed = False
			self.active = True
			return

		lp = self.lastPosition
		if self.mode == "LASSO":
			self.selectionLasso.addLine( line(lp.x, lp.y, pos.x, pos.y) )
			self.selectionLasso.addPoint( pos[:] )
		if self.mode == "PIN":
			self.selectionPin.addPoint( pos[:] )
		self.lastPosition = pos

	def closeLoop(self):
		if self.lastPosition == None:
			return

		lp = self.lastPosition 
		fp = self.firstPosition
		if self.mode == "LASSO":
			self.selectionLasso.addLine( line(lp.x, lp.y, fp.x, fp.y) )
		self.firstPosition = None
		self.lastPosition = None
		self.closed = True

	def clear(self):
		rec = None
		if self.active == True:
			self.selectionLasso.clear()
			self.selectionPin.clear()
			self.closed = False
			self.active = False
			self.img_pnts = []
			self.wrl_pnts = []

	def setMode(self, mode):
		self.mode = mode


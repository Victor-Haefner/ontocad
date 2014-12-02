#!/usr/bin/env python
from ocad_math import *
from math import sqrt
import pickle

# --------------- CAD Primitives ---------

class point:
	def __init__(self, x=0,y=0,r=1):
		self.x = x
		self.y = y
		self.rad = r
		self.linePtr = None
		
	def __add__(self, p):
		return point(self.x+p.x, self.y+p.y)
		
	def __sub__(self, p):
		return point(self.x-p.x, self.y-p.y)
		
	def __mul__(self, f):
		return point(self.x*f, self.y*f)
		
	def __slots__(self):
		pass
		
	def __str__(self):
		return str(self.x) + " " + str(self.y)
		
	def __getitem__(self, key):
		if isinstance( key, slice ) :
			return point(self.x, self.y)
		else:
			if key == 0:
				return self.x
			if key == 1:
				return self.y
			#raise IndexError, "Point: no index"
			#return [self.x, self.y]
		
class line:
	def __init__(self, x1=0,y1=0,x2=0,y2=0):
		self.p1 = point(x1,y1)
		self.p1.linePtr = self
		self.p2 = point(x2,y2)
		self.p2.linePtr = self
		self.squareLength = distSquare(self.p1, self.p2)
		self.length = sqrt(self.squareLength)
		self.box = point( abs(x1 - x2) , abs(y1 - y2) )
		self.stamp = 0
		
	def __slots__(self):
		pass
		
	def __getitem__(self, key):
		if isinstance( key, slice ) :
			return line(self.p1.x, self.p1.y, self.p2.x, self.p2.y)
		else:
			raise IndexError, "Line: no index"
		
class arc:
	def __init__(self, cx=0,cy=0,r=0,a1=0,a2=360):
		self.center = point(cx,cy)
		self.rad = r
		self.a1 = a1
		self.a2 = a2
		
		self.box = point( 2*r , 2*r )
		
	def __slots__(self):
		pass
		
	def __getitem__(self, key):
		if isinstance( key, slice ) :
			a = arc(self.center.x, self.center.y, self.rad, self.a1, self.a2)
			a.box.x = self.box.x
			a.box.y = self.box.y
			return a
		else:
			raise IndexError, "Arc: no index"

class viewport:
	def __init__(self, _name):
		self.name = _name
		#self.visible = 1
		self.layers = {}
	
class layout:
	def __init__(self):
		self.path = ""
		self.viewports = None
	
# --------------- Ontology Primitives ---------
	
class ontoclass:
	def __init__(self):
		self.name = None
		self.parent = None
		self.children = []
		self.individuals = {}
		self.dataproperties = {}
		self.objectproperties = {}
		
class dataproperty:
	def __init__(self):
		self.name = None
		self.datarange = None
		self.domains = {}
		self.function = None
		
class objectproperty:
	def __init__(self):
		self.name = None
		self.domains = {}
		self.function = None
 	
class individual:
	def __init__(self):
		self.guid = 0
		self.domain = None
		self.label = None
		self.xml_element = None
		self.dataProperties = {}
		self.objectProperties = {}
		
		self.perimeter = None
		self.position = point(0,0)
		self.width = None
		self.height = None
		
		self.isZone = False
		self.isPosition = False
		
	def stringToPerimeter(self, data):
		perim = data.split(";")
		for i,p in enumerate(perim):
			perim[i] = point()
			xy = p.split(":")
			perim[i].x = float(xy[0])
			perim[i].y = float(xy[1])
		return perim
		
	def drawBBox(self, l):
		if self.isZone and self.perimeter:
			pnts = self.stringToPerimeter(self.perimeter)
			p2 = pnts[-1]
			for p in pnts:
				l.addLine( line(p.x, p.y, p2.x, p2.y) )
				p2 = p
			
		elif self.width != None and self.height != None:
			p = self.position
			w = self.width/2
			h = self.height/2
			l.addLine( line(p.x-w, p.y-h, p.x+w, p.y-h) )
			l.addLine( line(p.x-w, p.y-h, p.x-w, p.y+h) )
			l.addLine( line(p.x+w, p.y+h, p.x-w, p.y+h) )
			l.addLine( line(p.x+w, p.y+h, p.x+w, p.y-h) )
			
		else:
			l.addPoint( self.position[:] )

class ontology:
	def __init__(self):
		self.classes = {}
		self.individuals = {}
		self.dataproperties = {}
		self.objectproperties = {}
		
		self.dpmap = {}
		self.opmap = {}
		
		self.path = ""
		self.xml_tree = None
		
	def clear(self):
		self.classes.clear()
		self.individuals.clear()
		self.dataproperties.clear()
		self.objectproperties.clear()
		
		self.generic_path = ""
		self.specific_path = ""
		self.xml_tree = None
		

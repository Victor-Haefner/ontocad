#!/usr/bin/env python

import layer
import math
from base_parser import *
from time import sleep


#convert the bulge of lwpolylines to arcs
def cvtbulge(bulge, sp, ep):
	x1, y1 = sp[0], sp[1]
	x2, y2 = ep[0], ep[1]
	cotbce = (1.0/bulge - bulge)/ 2.0

	# Compute center point and radius
	cen = [(x1 + x2 - (y2-y1)*cotbce) /2.0, (y1 + y2 + (x2-x1)*cotbce) /2.0]
	rad = sqrt((cen[0]-sp[0])**2 + (cen[1]-sp[1])**2)

	# Compute start and end angles
	sa = math.atan2(y1 - cen[1], x1 - cen[0])
	ea = math.atan2(y2 - cen[1], x2 - cen[0])
	
	#check new start and end point
	c_x2 = math.cos(ea)*rad + cen[0]
	c_y2 = math.sin(ea)*rad + cen[1]
	if abs(c_x2 - x2) > 0.001:
		print "error in cvtbulge, x"
	if abs(c_y2 - y2) > 0.001:
		print "error in cvtbulge, y"
	

	# Eliminate negative angles # does nothing
	if sa < 0.0:
		sa = sa + 2.0*PI
	if ea < 0.0:
		ea = ea + 2.0*PI

	# Swap angles if clockwise # works
	if bulge < 0.0:                  
		tmp = ea
		ea = sa
		sa = tmp
		
	return cen, rad, sa, ea

def get_attrib(item, dat):
	for it in item.data:
		if it[0] == dat:
			return it[1]
	return None

class dxf_parser(base_parser):
	def __init__(self):
		base_parser.__init__(self)
		self.rescale = 0.8
		#self.rescale = 100.0
		#self.rescale = 0.3
		self.compute_current_transformation()
		self.viewport = "Default"
		
	def parse_rec(self, item, drawing, first = False):
		#sleep(0.001)
		if item.type in ['viewport', 'vport']:
			print "VIEWPORT", item.name
			self.viewport = item.name
			self.getLayer(self.viewport, self.layer)
		
		if hasattr(item, "layer"):
			self.layer = self.getLayer(self.viewport, item.layer)
			
		#primitives
		d2r = PI/180.0
		
		#extrusion hack :/
		extr = False
		if hasattr(item, 'extrusion'):
			if item.extrusion[2] == -1:
				extr = True
				self.offset_stack.append(array([0, 0]))
				self.scale_stack.append(array([-1,1]))
				self.rot_angle_stack.append(0)
				self.compute_current_transformation()
		
		if item.type == "line":
			self.addLine(item.points[0], item.points[1])
			pass
		if item.type == "circle":
			self.addCircle(item.loc[0], item.loc[1], item.radius)
			pass
		if item.type == "ellipse":
			self.addEllipse(item.loc[0], item.loc[1], item.major[0], item.major[1])#major???
			pass
		if item.type == "arc":
			self.addArc(item.loc[0], item.loc[1], item.radius, item.start_angle*d2r, item.end_angle*d2r)
			#if extr:
			#	self.addArc(item.loc[0], item.loc[1], item.radius, item.end_angle*d2r, item.start_angle*d2r)
			#else:
			#	self.addArc(item.loc[0], item.loc[1], item.radius, item.start_angle*d2r, item.end_angle*d2r)
			
		if item.type in ["lwpolyline","polyline"]:
			for i,p in enumerate(item.points):
				_p = item.points[i-1]
				if i > 0 or item.closed == 1:
					if abs(_p.bulge) < 0.0001:
						self.addLine(_p,p)
					else:
						if extr:
							_p.bulge = - _p.bulge
						arc = cvtbulge(_p.bulge, _p, p)
						self.addArc(arc[0][0], arc[0][1], arc[1], arc[2], arc[3], _p.bulge)
					
		if item.type == "3dface":
			for i,p in enumerate(item.points):
				self.addLine(item.points[i-1],p)
				pass
			
		if item.type == "insert": # transformation		
			block = None # get block
			for bl in drawing.blocks.data:
				if item.block == bl.name:
					block = bl
			if block == None:
				return
				
			self.offset_stack.append(array([item.loc[0], item.loc[1]]))
			self.scale_stack.append(array([item.scale[0],item.scale[1]]))
			self.rot_angle_stack.append(item.rotation*PI/180.0)
			self.compute_current_transformation()
			
			for child in block.entities.data:
				self.parse_rec(child, drawing)
				
			self.offset_stack.pop()
			self.scale_stack.pop()
			self.rot_angle_stack.pop()
			self.compute_current_transformation()
		
		if extr:
			self.offset_stack.pop()
			self.scale_stack.pop()
			self.rot_angle_stack.pop()
			self.compute_current_transformation()
			
	def parse(self, path):
		drawing = readDXF(path, objectify)
					
		for item in drawing.entities.data:
			self.parse_rec(item, drawing, True)

def get_dxf_layer(data):
	value = None
	for i, item in enumerate(data):
		if item[0] == 8:
			value = item[1]
			break
			
	return item, value, i

class Line:
	def __init__(self, obj):
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True
		
		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]

		self.points = self.get_points(obj.data)
     
	def get_points(self, data):
		sx, sy, sz, ex, ey, ez = 0, 0, 0, 0, 0, 0
		
		for item in data:
			if item[0] == 10:   # 10 = x
				sx = item[1]
			elif item[0] == 20: # 20 = y
				sy = item[1]
			elif item[0] == 30: # 30 = z
				sz = item[1]
			elif item[0] == 11: # 11 = x
				ex = item[1]
			elif item[0] == 21: # 21 = y
				ey = item[1]
			elif item[0] == 31: # 31 = z
				ez = item[1]
		return [[sx, sy, sz], [ex, ey, ez]]

	def __repr__(self):
		return "%s: layer - %s, points - %s" %(self.__class__.__name__, self.layer, self.points)
	
class Circle:
	"""Class for objects representing dxf Circles."""

	def __init__(self, obj):
		"""Expects an entity object of type circle as input."""
		if not obj.type == 'circle':
			raise TypeError, "Wrong type %s for circle object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True

		# required data
		self.radius = obj.get_type(40)[0]

		# optional data (with defaults)
		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.loc = self.get_loc(obj.data)
		self.extrusion = self.get_extrusion(obj.data)

	def get_loc(self, data):
		"""Gets the center location for circle type objects.

		Circles have a single coord location.
		"""
		loc = [0, 0, 0]
		for item in data:
			if item[0] == 10:   # 10 = x
				loc[0] = item[1]
			elif item[0] == 20: # 20 = y
				loc[1] = item[1]
			elif item[0] == 30: # 30 = z
				loc[2] = item[1]
		return loc

	def get_extrusion(self, data):
		"""Find the axis of extrusion.

		Used to get the objects Object Coordinate System (ocs).
		"""
		vec = [0,0,1]
		for item in data:
			if item[0] == 210:   # 210 = x
				vec[0] = item[1]
			elif item[0] == 220: # 220 = y
				vec[1] = item[1]
			elif item[0] == 230: # 230 = z
				vec[2] = item[1]
		return vec

	def __repr__(self):
		return "%s: layer - %s, radius - %s" %(self.__class__.__name__, self.layer, self.radius)

class Arc:
	"""Class for objects representing dxf arcs."""

	def __init__(self, obj):
		"""Expects an entity object of type arc as input."""
		if not obj.type == 'arc':
			raise TypeError, "Wrong type %s for arc object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True

		# required data
		self.radius = obj.get_type(40)[0]
		self.start_angle = obj.get_type(50)[0]
		self.end_angle = obj.get_type(51)[0]

		# optional data (with defaults)
		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.loc = self.get_loc(obj.data)
		self.extrusion = self.get_extrusion(obj.data)

	def get_loc(self, data):
		"""Gets the center location for arc type objects.

		Arcs have a single coord location.
		"""
		loc = [0, 0, 0]
		for item in data:
			if item[0] == 10:   # 10 = x
				loc[0] = item[1]
			elif item[0] == 20: # 20 = y
				loc[1] = item[1]
			elif item[0] == 30: # 30 = z
				loc[2] = item[1]
		return loc

	def get_extrusion(self, data):
		"""Find the axis of extrusion.

		Used to get the objects Object Coordinate System (ocs).
		"""
		vec = [0,0,1]
		for item in data:
			if item[0] == 210:   # 210 = x
				vec[0] = item[1]
			elif item[0] == 220: # 220 = y
				vec[1] = item[1]
			elif item[0] == 230: # 230 = z
				vec[2] = item[1]
		return vec

	def __repr__(self):
		return "%s: layer - %s, radius - %s" %(self.__class__.__name__, self.layer, self.radius)

class Ellipse:
	"""Class for objects representing dxf ellipses."""

	def __init__(self, obj):
		"""Expects an entity object of type ellipse as input."""
		if not obj.type == 'ellipse':
			raise TypeError, "Wrong type %s for ellipse object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True

		# required data
		self.ratio = obj.get_type(40)[0]
		self.start_angle = obj.get_type(41)[0]
		self.end_angle = obj.get_type(42)[0]

		# optional data (with defaults)
		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.loc = self.get_loc(obj.data)
		self.major = self.get_major(obj.data)
		self.extrusion = self.get_extrusion(obj.data)
		self.radius = sqrt(self.major[0]**2 + self.major[0]**2 + self.major[0]**2)

	def get_loc(self, data):
		"""Gets the center location for arc type objects.

		Arcs have a single coord location.
		"""
		loc = [0, 0, 0]
		for item in data:
			if item[0] == 10:   # 10 = x
				loc[0] = item[1]
			elif item[0] == 20: # 20 = y
				loc[1] = item[1]
			elif item[0] == 30: # 30 = z
				loc[2] = item[1]
		return loc

	def get_major(self, data):
		"""Gets the major axis for ellipse type objects.

		The ellipse major axis defines the rotation of the ellipse and its radius.
		"""
		loc = [0, 0, 0]
		for item in data:
			if item[0] == 11:   # 11 = x
				loc[0] = item[1]
			elif item[0] == 21: # 21 = y
				loc[1] = item[1]
			elif item[0] == 31: # 31 = z
				loc[2] = item[1]
		return loc

	def get_extrusion(self, data):
		"""Find the axis of extrusion.

		Used to get the objects Object Coordinate System (ocs).
		"""
		vec = [0,0,1]
		for item in data:
			if item[0] == 210:   # 210 = x
				vec[0] = item[1]
			elif item[0] == 220: # 220 = y
				vec[1] = item[1]
			elif item[0] == 230: # 230 = z
				vec[2] = item[1]
		return vec

	def __repr__(self):
		return "%s: layer - %s, radius - %s" %(self.__class__.__name__, self.layer, self.radius)

class Layer:
	"""Class for objects representing dxf layers."""
	def __init__(self, obj):
		"""Expects an entity object of type line as input."""
		self.type = obj.type
		self.data = obj.data[:]

		self.name = obj.get_type(2)[0]
		self.color = obj.get_type(62)[0]
		self.flags = obj.get_type(70)[0]
		self.frozen = self.flags&1

	def __repr__(self):
		return "%s: name - %s, color - %s" %(self.__class__.__name__, self.name, self.color)

class BlockRecord:#in table
	"""Class for objects representing dxf block_records."""

	def __init__(self, obj):
		"""Expects an entity object of type block_record as input."""
		if not obj.type == 'block_record':
			raise TypeError, "Wrong type %s for block_record object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]

		# required data
		self.name = obj.get_type(2)[0]

		# optional data (with defaults)
		self.insertion_units = obj.get_type(70)
		if not self.insertion_units:
			self.insertion_units = None
		else:
			self.insertion_units = self.insertion_units[0]

		self.insert_units = obj.get_type(1070)
		if not self.insert_units:
			self.insert_units = None
		else:
			self.insert_units = self.insert_units[0]

	def __repr__(self):
		return "%s: name - %s, insert units - %s" %(self.__class__.__name__, self.name, self.insertion_units)

class Block:
	"""Class for objects representing dxf blocks."""

	def __init__(self, obj):
		"""Expects an entity object of type block as input."""
		if not obj.type == 'block':
			raise TypeError, "Wrong type %s for block object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True

		# required data
		self.flags = obj.get_type(70)[0]
		self.entities = Object('block_contents')
		self.entities.data = objectify([ent for ent in obj.data if type(ent) != list])

		# optional data (with defaults)
		self.name = obj.get_type(3)
		if self.name:
			self.name = self.name[0]
		else:
			self.name = obj.get_type(2)
			if self.name:
				self.name = self.name[0]
			else:
				self.name = 'blank'

		self.path = obj.get_type(1)
		if self.path:
			self.path = self.path[0]
		else:
			self.path = ''

		self.discription = obj.get_type(4)
		if self.discription:
			self.discription = self.discription[0]
		else:
			self.discription = ''

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.loc = self.get_loc(obj.data)

	def get_loc(self, data):
		"""Gets the insert point of the block."""
		loc = [0, 0, 0]
		for item in data:
			if type(item) != list:
				continue
			if item[0] == 10:   # 10 = x
				loc[0] = item[1]
			elif item[0] == 20: # 20 = y
				loc[1] = item[1]
			elif item[0] == 30: # 30 = z
				loc[2] = item[1]
		return loc

	def __repr__(self):
		return "%s: name - %s, description - %s, xref-path - %s" %(self.__class__.__name__, self.name, self.discription, self.path)

class Insert:
	"""Class for objects representing dxf inserts."""

	def __init__(self, obj):
		"""Expects an entity object of type insert as input."""
		if not obj.type == 'insert':
			raise TypeError, "Wrong type %s for insert object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True

		# required data
		self.block = obj.get_type(2)[0]

		# optional data (with defaults)
		self.rotation = obj.get_type(50)
		if self.rotation:
			self.rotation = self.rotation[0]
		else:
			self.rotation = 0

		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.loc = self.get_loc(obj.data)
		self.scale = self.get_scale(obj.data)
		self.rows, self.columns = self.get_array(obj.data)
		self.extrusion = self.get_extrusion(obj.data)

	def get_loc(self, data):
		"""Gets the center location for circle type objects.

		Circles have a single coord location.
		"""
		loc = [0, 0, 0]
		for item in data:
			if item[0] == 10:   # 10 = x
				loc[0] = item[1]
			elif item[0] == 20: # 20 = y
				loc[1] = item[1]
			elif item[0] == 30: # 30 = z
				loc[2] = item[1]
		return loc

	def get_scale(self, data):
		"""Gets the x/y/z scale factor for the block.
		"""
		scale = [1, 1, 1]
		for item in data:
			if item[0] == 41:   # 41 = x scale
				scale[0] = item[1]
			elif item[0] == 42: # 42 = y scale
				scale[1] = item[1]
			elif item[0] == 43: # 43 = z scale
				scale[2] = item[1]
		return scale

	def get_array(self, data):
		"""Returns the pair (row number, row spacing), (column number, column spacing)."""
		columns = 1
		rows = 1
		cspace = 0
		rspace = 0
		for item in data:
			if item[0] == 70:   # 70 = columns
				columns = item[1]
			elif item[0] == 71: # 71 = rows
				rows = item[1]
			if item[0] == 44:   # 44 = columns
				cspace = item[1]
			elif item[0] == 45: # 45 = rows
				rspace = item[1]
		return (rows, rspace), (columns, cspace)

	def get_extrusion(self, data):
		"""Find the axis of extrusion.

		Used to get the objects Object Coordinate System (ocs).
		"""
		vec = [0,0,1]
		for item in data:
			if item[0] == 210:   # 210 = x
				vec[0] = item[1]
			elif item[0] == 220: # 220 = y
				vec[1] = item[1]
			elif item[0] == 230: # 230 = z
				vec[2] = item[1]
		return vec

	def __repr__(self):
		return "%s: layer - %s, block - %s" %(self.__class__.__name__, self.layer, self.block)

class LWpolyline:
	"""Class for objects representing dxf LWpolylines."""

	def __init__(self, obj):
		"""Expects an entity object of type lwpolyline as input."""
		if not obj.type == 'lwpolyline':
			raise TypeError, "Wrong type %s for polyline object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True

		# required data
		self.num_points = obj.get_type(90)[0]

		# optional data (with defaults)
		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		self.elevation = obj.get_type(38)
		if self.elevation:
			self.elevation = self.elevation[0]
		else:
			self.elevation = 0

		self.flags = obj.get_type(70)
		if self.flags:
			self.flags = self.flags[0]
		else:
			self.flags = 0

		self.closed = self.flags&1 # byte coded, 1 = closed, 128 = plinegen
		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.points = self.get_points(obj.data)
		self.extrusion = self.get_extrusion(obj.data)

	def get_points(self, data):
		"""Gets points for a polyline type object.

		Polylines have no fixed number of verts, and 
		each vert can have a number of properties.
		Verts should be coded as 
		10:xvalue
		20:yvalue
		40:startwidth or 0
		41:endwidth or 0
		42:bulge or 0
		for each vert
		"""
		num = self.num_points
		point = None
		points = []
		for item in data:
			if item[0] == 10:   # 10 = x
				if point:
					points.append(point)
				point = Vertex()
				point.x = item[1]
			elif item[0] == 20: # 20 = y
				point.y = item[1]
			elif item[0] == 40: # 40 = start width
				point.swidth = item[1]
			elif item[0] == 41: # 41 = end width
				point.ewidth = item[1]
			elif item[0] == 42: # 42 = bulge
				point.bulge = item[1]
		points.append(point)
		return points

	def get_extrusion(self, data):
		"""Find the axis of extrusion.

		Used to get the objects Object Coordinate System (ocs).
		"""
		vec = [0,0,1]
		for item in data:
			if item[0] == 210:   # 210 = x
				vec[0] = item[1]
			elif item[0] == 220: # 220 = y
				vec[1] = item[1]
			elif item[0] == 230: # 230 = z
				vec[2] = item[1]
		return vec

	def __repr__(self):
		return "%s: layer - %s, points - %s" %(self.__class__.__name__, self.layer, self.points)

class Polyline:
	"""Class for objects representing dxf LWpolylines."""

	def __init__(self, obj):
		"""Expects an entity object of type polyline as input."""
		if not obj.type == 'polyline':
			raise TypeError, "Wrong type %s for polyline object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		self.points = []
		obj.visited_flag = True

		# optional data (with defaults)
		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		self.elevation = obj.get_type(30)
		if self.elevation:
			self.elevation = self.elevation[0]
		else:
			self.elevation = 0

		self.flags = obj.get_type(70)
		if self.flags:
			self.flags = self.flags[0]
		else:
			self.flags = 0

		self.closed = self.flags&1 # byte coded, 1 = closed, 128 = plinegen

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.extrusion = self.get_extrusion(obj.data)

	def get_extrusion(self, data):
		"""Find the axis of extrusion.

		Used to get the objects Object Coordinate System (ocs).
		"""
		vec = [0,0,1]
		for item in data:
			if item[0] == 210:   # 210 = x
				vec[0] = item[1]
			elif item[0] == 220: # 220 = y
				vec[1] = item[1]
			elif item[0] == 230: # 230 = z
				vec[2] = item[1]
		return vec

	def __repr__(self):
		return "%s: layer - %s, points - %s" %(self.__class__.__name__, self.layer, self.points)

class Vertex(object):
	"""Generic vertex object used by polylines (and maybe others)."""

	def __init__(self, obj=None):
		"""Initializes vertex data.

		The optional obj arg is an entity object of type vertex.
		"""
		self.loc = [0,0,0]
		self.bulge = 0
		self.swidth = 0
		self.ewidth = 0
		self.flags = 0
		if obj:
			obj.visited_flag = True

		if obj is not None:
			if not obj.type == 'vertex':
				raise TypeError, "Wrong type %s for vertex object!" %obj.type
			self.type = obj.type
			self.data = obj.data[:]

			self.get_props(obj.data)
	
	def get_props(self, data):
		"""Gets coords for a vertex type object.

		Each vert can have a number of properties.
		Verts should be coded as 
		10:xvalue
		20:yvalue
		40:startwidth or 0
		41:endwidth or 0
		42:bulge or 0
		"""
		for item in data:
			if item[0] == 10:   # 10 = x
				self.x = item[1]
			elif item[0] == 20: # 20 = y
				self.y = item[1]
			elif item[0] == 30: # 30 = z
				self.z = item[1]
			elif item[0] == 40: # 40 = start width
				self.swidth = item[1]
			elif item[0] == 41: # 41 = end width
				self.ewidth = item[1]
			elif item[0] == 42: # 42 = bulge
				self.bulge = item[1]
			elif item[0] == 70: # 70 = vert flags
				self.flags = item[1]

	def __len__(self):
		return 3

	def __getitem__(self, key):
		return self.loc[key]

	def __setitem__(self, key, value):
		if key in [0,1,2]:
			self.loc[key]

	def __iter__(self):
		return self.loc.__iter__()

	def __str__(self):
		return str(self.loc)

	def __repr__(self):
		return "Vertex %s, swidth=%s, ewidth=%s, bulge=%s" %(self.loc, self.swidth, self.ewidth, self.bulge)

	def getx(self):
		return self.loc[0]
	def setx(self, value):
		self.loc[0] = value
	x = property(getx, setx)

	def gety(self):
		return self.loc[1]
	def sety(self, value):
		self.loc[1] = value
	y = property(gety, sety)

	def getz(self):
		return self.loc[2]
	def setz(self, value):
		self.loc[2] = value
	z = property(getz, setz)

class Face:
	"""Class for objects representing dxf 3d faces."""

	def __init__(self, obj):
		"""Expects an entity object of type 3dfaceplot as input."""
		if not obj.type == '3dface':
			raise TypeError, "Wrong type %s for 3dface object!" %obj.type
		self.type = obj.type
		self.data = obj.data[:]
		obj.visited_flag = True

		# optional data (with defaults)
		self.space = obj.get_type(67)
		if self.space:
			self.space = self.space[0]
		else:
			self.space = 0

		self.color_index = obj.get_type(62)
		if self.color_index:
			self.color_index = self.color_index[0]
		else:
			self.color_index = 0

		discard, self.layer, discard_index = get_dxf_layer(obj.data)
		del obj.data[discard_index]
		self.points = self.get_points(obj.data)

	def get_points(self, data):
		"""Gets 3-4 points for a 3d face type object.
		Faces have three or optionally four verts.
		"""
		a = [0, 0, 0]
		b = [0, 0, 0]
		c = [0, 0, 0]
		d = False
		for item in data:
			# ----------- a -------------
			if item[0] == 10:   # 10 = x
				a[0] = item[1]
			elif item[0] == 20: # 20 = y
				a[1] = item[1]
			elif item[0] == 30: # 30 = z
				a[2] = item[1]
			# ----------- b -------------
			elif item[0] == 11: # 11 = x
				b[0] = item[1]
			elif item[0] == 21: # 21 = y
				b[1] = item[1]
			elif item[0] == 31: # 31 = z
				b[2] = item[1]
			# ----------- c -------------
			elif item[0] == 12: # 12 = x
				c[0] = item[1]
			elif item[0] == 22: # 22 = y
				c[1] = item[1]
			elif item[0] == 32: # 32 = z
				c[2] = item[1]
			# ----------- d -------------
			elif item[0] == 13: # 13 = x
				d = [0, 0, 0]
				d[0] = item[1]
			elif item[0] == 23: # 23 = y
				d[1] = item[1]
			elif item[0] == 33: # 33 = z
				d[2] = item[1]
		out = [a,b,c]
		if d:
			out.append(d)
		return out

	def __repr__(self):
		return "%s: layer - %s, points - %s" %(self.__class__.__name__, self.layer, self.points)

			
			
type_map = {
	'line':Line,
	'lwpolyline':LWpolyline,
	'circle':Circle,
	'arc':Arc,
	'layer':Layer,
	'3dface':Face,
	'ellipse':Ellipse,
	'block_record':BlockRecord,
	'block':Block, 
	'insert':Insert, 
}

skip_types = [
	'hatch', 'point',
	'xrecord','dictionary','cellstylemap','scale','tablestyle','visualstyle','dictionaryvar','plotsettings','acdbplaceholder','sortentstable','layout','material','mlinestyle',
	'dimension', 'mtext', 'viewport', 'acdbdictionarywdflt', 'seqend', 'vertex', 'attrib', '3dface', 'solid', 'region', 'leader',
	'vport', 'ltype', 'style', 'appid', 'dimstyle'
]
				
def objectify(data):	
	#sleep(0.001)
	objects = [] # colector for finished objects
	
	for i, item in enumerate(data):
		if type(item) == list:
			continue
						
		if item.type in type_map.keys():
			objects.append(type_map[item.type](item))
			continue
		
		if item.type == 'table':
			item.data = objectify(item.data) # tables have sub-objects
			objects.append(item)
			continue
			
		if item.type == 'polyline':
			pline = Polyline(item)
			index = i
			while data[index].type != 'seqend':
				index += 1
				if data[index].type != 'vertex':
					break
				v = Vertex(data[index])
				if v.loc[0] != 0:
					pline.points.append(v)
				
			objects.append(pline)
			continue
			
		objects.append(item)
		
	return objects

# DXF PARSER-----------

class Object:
	"""Empty container class for dxf objects"""

	def __init__(self, _type='', block=False):
		"""_type expects a string value."""
		self.type = _type
		self.name = ''
		self.data = []
		self.visited_flag = False		

	def __str__(self):
		if self.name:
			return self.name
		else:
			return self.type

	def __repr__(self):
		return str(self.data)

	def get_type(self, kind=''):
		"""Despite the name, this method actually returns all objects of type 'kind' from self.data."""
		if type:
			objects = []
			for item in self.data:
				if type(item) != list and item.type == kind:
					# we want this type of object
					objects.append(item)
				elif type(item) == list and item[0] == kind:
					# we want this type of data
					objects.append(item[1])
			return objects

class InitializationError(Exception): pass

class StateMachine:
	"""(finite) State Machine from the great David Mertz's great Charming Python article."""

	def __init__(self):
		self.handlers = []
		self.startState = None
		self.endStates = []

	def add_state(self, handler, end_state=0):
		"""All states and handlers are functions which return
		a state and a cargo."""
		self.handlers.append(handler)
		if end_state:
			self.endStates.append(handler)
	def set_start(self, handler):
		"""Sets the starting handler function."""
		self.startState = handler


	def run(self, cargo=None):
		if not self.startState:
			raise InitializationError,\
				  "must call .set_start() before .run()"
		if not self.endStates:
			raise InitializationError, \
				  "at least one state must be an end_state"
		handler = self.startState
		while 1:
			(newState, cargo) = handler(cargo)
			#print cargo
			if newState in self.endStates:
				return newState(cargo)
				#break
			elif newState not in self.handlers:
				raise RuntimeError, "Invalid target %s" % newState
			else:
				handler = newState

def get_name(data):
	"""Get the name of an object from its object data.

	Returns a pair of (data_item, name) where data_item is the list entry where the name was found
	(the data_item can be used to remove the entry from the object data).  Be sure to check
	name not None before using the returned values!
	"""
	value = None
	for item in data:
		if item[0] == 2:
			value = item[1]
			break
	return item, value

def get_layer(data):
	"""Expects object data as input.

	Returns (entry, layer_name) where entry is the data item that provided the layer name.
	"""
	value = None
	for item in data:
		if item[0] == 8:
			value = item[1]
			break
	return item, value


def convert(code, value):
	"""Convert a string to the correct Python type based on its dxf code.
	code types:
		ints = 60-79, 170-179, 270-289, 370-389, 400-409, 1060-1070
		longs = 90-99, 420-429, 440-459, 1071
		floats = 10-39, 40-59, 110-139, 140-149, 210-239, 460-469, 1010-1059
		hex = 105, 310-379, 390-399
		strings = 0-9, 100, 102, 300-309, 410-419, 430-439, 470-479, 999, 1000-1009
	"""
	if 59 < code < 80 or 169 < code < 180 or 269 < code < 290 or 369 < code < 390 or 399 < code < 410 or 1059 < code < 1071:
		value = int(float(value))
	elif 89 < code < 100 or 419 < code < 430 or 439 < code < 460 or code == 1071:
		value = long(float(value))
	elif 9 < code < 60 or 109 < code < 150 or 209 < code < 240 or 459 < code < 470 or 1009 < code < 1060:
		value = float(value)
	elif code == 105 or 309 < code < 380 or 389 < code < 400:
		value = int(value, 16) # should be left as string?
	else: # it's already a string so do nothing
		pass
	return value


def findObject(infile, kind=''):
	"""Finds the next occurance of an object."""
	obj = False
	while 1:
		line = infile.readline()
		if not line: # readline returns '' at eof
			return False
		if not obj: # We're still looking for our object code
			if line.lower().strip() == '0':
				obj = True # found it
		else: # we are in an object definition
			if kind: # if we're looking for a particular kind
				if line.lower().strip() == kind:
					obj = Object(line.lower().strip())
					break
			else: # otherwise take anything non-numeric
				if line.lower().strip() not in string.digits:
					obj = Object(line.lower().strip())
					break
			obj = False # whether we found one or not it's time to start over
	return obj

def handleObject(infile):
	"""Add data to an object until end of object is found."""
	line = infile.readline()
	if line.lower().strip() == 'section':
		return 'section' # this would be a problem
	elif line.lower().strip() == 'endsec':
		return 'endsec' # this means we are done with a section
	else: # add data to the object until we find a new object
		obj = Object(line.lower().strip())
		obj.name = obj.type
		done = False
		data = []
		while not done:
			line = infile.readline()
			if not data:
				if line.lower().strip() == '0':
					#we've found an object, time to return
					return obj
				else:
					# first part is always an int
					data.append(int(line.lower().strip()))
			else:
				data.append(convert(data[0], line.strip()))
				obj.data.append(data)
				data = []

def handleTable(table, infile):
	"""Special handler for dealing with nested table objects."""
	item, name = get_name(table.data)
	if name: # We should always find a name
		table.data.remove(item)
		table.name = name.lower()
	# This next bit is from handleObject
	# handleObject should be generalized to work with any section like object
	while 1:
		obj = handleObject(infile)
		if obj.type == 'table':
			print "Warning: previous table not closed!"
			return table
		elif obj.type == 'endtab':
			return table # this means we are done with the table
		else: # add objects to the table until one of the above is found
			table.data.append(obj)


def handleBlock(block, infile):
	"""Special handler for dealing with nested table objects."""
	item, name = get_name(block.data)
	if name: # We should always find a name
		block.data.remove(item)
		block.name = name
	# This next bit is from handleObject
	# handleObject should be generalized to work with any section like object
	while 1:
		obj = handleObject(infile)
		if obj.type == 'block':
			print "Warning: previous block not closed!"
			return block
		elif obj.type == 'endblk':
			return block # this means we are done with the table
		else: # add objects to the table until one of the above is found
			block.data.append(obj)


"""These are the states/functions used in the State Machine.
states:
 start - find first section
 start_section - add data, find first object
   object - add obj-data, watch for next obj (called directly by start_section)
 end_section - look for next section or eof
 end - return results
"""

def start(cargo):
	"""Expects the infile as cargo, initializes the cargo."""
	#print "Entering start state!"
	infile = cargo
	drawing = Object('drawing')
	section = findObject(infile, 'section')
	if section:
		return start_section, (infile, drawing, section)
	else:
		return error, (infile, "Failed to find any sections!")

def start_section(cargo):
	"""Expects [infile, drawing, section] as cargo, builds a nested section object."""
	#print "Entering start_section state!"
	infile = cargo[0]
	drawing = cargo[1]
	section = cargo[2]
	# read each line, if it is an object declaration go to object mode
	# otherwise create a [index, data] pair and add it to the sections data.
	done = False
	data = []
	while not done:
		line = infile.readline()

		if not data: # if we haven't found a dxf code yet
			if line.lower().strip() == '0':
				# we've found an object
				while 1: # no way out unless we find an end section or a new section
					obj = handleObject(infile)
					if obj == 'section': # shouldn't happen
						print "Warning: failed to close previous section!"
						return end_section, (infile, drawing)
					elif obj == 'endsec': # This section is over, look for the next
						drawing.data.append(section)
						return end_section, (infile, drawing)
					elif obj.type == 'table': # tables are collections of data
						obj = handleTable(obj, infile) # we need to find all there contents
						section.data.append(obj) # before moving on
					elif obj.type == 'block': # the same is true of blocks
						obj = handleBlock(obj, infile) # we need to find all there contents
						section.data.append(obj) # before moving on
					else: # found another sub-object
						section.data.append(obj)
			else:
				data.append(int(line.lower().strip()))
		else: # we have our code, now we just need to convert the data and add it to our list.
			data.append(convert(data[0], line.strip()))
			section.data.append(data)
			data = []
def end_section(cargo):
	"""Expects (infile, drawing) as cargo, searches for next section."""
	#print "Entering end_section state!"
	infile = cargo[0]
	drawing = cargo[1]
	section = findObject(infile, 'section')
	if section:
		return start_section, (infile, drawing, section)
	else:
		return end, (infile, drawing)

def end(cargo):
	"""Expects (infile, drawing) as cargo, called when eof has been reached."""
	#print "Entering end state!"
	infile = cargo[0]
	drawing = cargo[1]
	#infile.close()
	return drawing

def error(cargo):
	"""Expects a (infile, string) as cargo, called when there is an error during processing."""
	#print "Entering error state!"
	infile = cargo[0]
	err = cargo[1]
	infile.close()
	print "There has been an error:"
	print err
	return False

def readDXF(filename, objectify):
	"""Given a file name try to read it as a dxf file.

	Output is an object with the following structure
	drawing
		header
			header data
		classes
			class data
		tables
			table data
		blocks
			block data
		entities
			entity data
		objects
			object data
	where foo data is a list of sub-objects.  True object data
	is of the form [code, data].
"""
	infile = open(filename)

	sm = StateMachine()
	sm.add_state(error, True)
	sm.add_state(end, True)
	sm.add_state(start_section)
	sm.add_state(end_section)
	sm.add_state(start)
	sm.set_start(start)
	
	
	try:
		drawing = sm.run(infile)
		if drawing:
			drawing.name = filename
			for obj in drawing.data:
				item, name = get_name(obj.data)
				if name:
					obj.data.remove(item)
					obj.name = name.lower()
					setattr(drawing, name.lower(), obj)
					# Call the objectify function to cast
					# raw objects into the right types of object							
					obj.data = objectify(obj.data)
					
	finally:
		infile.close()
	return drawing


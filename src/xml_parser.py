#!/usr/bin/env python

import numpy
from numpy import *
import xml.etree.ElementTree as ET

import sys
from base_parser import *
import layer

class xml_parser(base_parser):
	def __init__(self):
		base_parser.__init__(self)
		
	def parse(self, path):
		parser = ET.XMLParser(encoding="ISO-8859-1")
		
		tree = ET.parse(path, parser)
		N = len(list(tree.getroot()))
		
		parser = ET.XMLParser(encoding="ISO-8859-1")	
		
		count = 0.0
		depth = 0
		for (event, elem) in ET.iterparse(path, ['start', 'end', 'start-ns', 'end-ns'], parser):
			if event == 'end':
				depth -= 1
				self.onCloseTag(elem)
			if event == 'start':
				depth += 1					
				if depth == 2:
					#print int(100*count/N)
					count += 1.0
				self.onOpenTag(elem)
				self.elem_dict[id(elem)] = elem
		
	def onOpenTag(self, elem):
		tag = elem.tag
		attr = elem.attrib
		_id = id(elem)
		#TAG: Root//todo
		#TAG: AcDbMText
		#TAG: AcDbHatch
		#TAG: AcDbPoint
		
		self.element_id = _id
		
		if "Layer" in attr:
			self.layer = self.getLayer("Default", attr["Layer"])
		else:
			self.layer = self.getLayer("Default", "None")
			
		
		if "CenterX" in attr:
			cx = float(attr["CenterX"])
		if "CenterY" in attr:
			cy = float(attr["CenterY"])
		if "Radius" in attr:
			r = float(attr["Radius"])
		
		#primitves
		if tag == "AcDbCircle":
			self.addCircle(cx, cy, r)
			return
		
		if tag == "AcDbEllipse":
			max = array([attr["MaxX"], attr["MaxY"], attr["MaxZ"]])
			min = array([attr["MinX"], attr["MinY"], attr["MinZ"]])
			a = float(max[0]) - float(min[0])
			b = float(max[1]) - float(min[1])
			self.addEllipse(cx, cy, a, b)
			return
			
		if tag == "AcDbArc":
			a1 = float(attr["StartAngle"])
			a2 = float(attr["EndAngle"])
			self.addArc(cx, cy, r, a1, a2)
			return
			
		if tag in ["AcDbLine", "LineSegment"]:
			v1 = array([float(attr["StartPointX"]), float(attr["StartPointY"])])
			v2 = array([float(attr["EndPointX"]), float(attr["EndPointY"])])
			self.addLine(v1, v2)
			self.last_controle_point = v2
			if self.closed_loop == True and self.first_controle_point == None:
				self.first_controle_point = v1
			return
			
		#start a spline
		if tag in ["AcDbSpline", "AcDbMline", "AcDb2dPolyline", "AcDbPolyline", "AcDbSolid"]:
			self.last_controle_point = None
			self.closed_loop = False
			self.first_controle_point = None
			if "IsClosed" in attr:
				if attr["IsClosed"] == '1':
					self.closed_loop = True
			return
			
		#spline point
		#if tag in ["Control", "Line", "Segment", "Solid"]:#Solid are not interesting
		if tag in ["Control", "Line", "Segment"]:
			v = array([float(attr["PointX"]), float(attr["PointY"])])
			cp = self.last_controle_point
			if cp != None:
				self.addLine(cp, v)
			self.last_controle_point = v
			if self.closed_loop == True and self.first_controle_point == None:
				self.first_controle_point = v
			return

		#transformations
		if tag == "AcDbBlockReference":			
			self.offset_stack.append(array([float(attr["PositionX"]), float(attr["PositionY"])]))
			self.scale_stack.append(array([float(attr["ScaleFactorX"]), float(attr["ScaleFactorY"])]))
			self.rot_angle_stack.append(float(attr["Rotation"]))
			
			self.compute_current_transformation()
			return
			
		if tag in ["AcDbHatch", "AcDbPoint", "AcDbMText", "Root", "AcDbText", "Solid"]:#hatch = fill type
			return
			
		print "UNKNOWN TAG: ", tag

	def onCloseTag(self, elem):
		if elem.tag == "AcDbBlockReference":
			self.offset_stack.pop()
			self.scale_stack.pop()
			self.rot_angle_stack.pop()
			
			self.compute_current_transformation()

		if elem.tag in ["AcDbSpline", "AcDbMline", "AcDb2dPolyline", "AcDbPolyline", "AcDbSolid"]:
			if self.closed_loop and self.first_controle_point != None:
				self.addLine(self.last_controle_point, self.first_controle_point)
				self.closed_loop = False
				self.first_controle_point = None
			self.last_controle_point = None;

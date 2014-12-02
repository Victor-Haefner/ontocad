#!/usr/bin/env python

from owl_parser import owl_parser
from ocad_primitives import *
import lxml.etree as ET
from random import *
import sys
from uuid import *
from ocad_math import *

class ocad_ontology:
	def __init__(self, data):
		self.data = data

	def open_file(self, path):
		owlparser = owl_parser()
		owlparser.parse(path, self.data.project)

	def updateAllIndivsProps(self):
		ontology = self.data.project.ontology
		for k, i in ontology.individuals.items():
			self.updateIndivsProps(i)

	def updateIndivsProps(self, i):
		ontology = self.data.project.ontology

		x,y = self.data.getIndivPosition(i)
		w,h = self.data.getIndivBox(i)
		#print i.label,x,y,w,h

		if x and y:
			i.position = point(x,y)
		if w and h:
			i.width = w
			i.height = h
		if self.isZone(i.domain):
			i.isZone = True
			for k,dtp in i.dataProperties.items():
				fkt = ontology.dataproperties[k].function
				if fkt == "Perimeter":
					i.perimeter = dtp
		if i.domain == self.data.positionObject:
			i.isPosition = True

	#-------------------------populate owl----------------------

	def isPointInPolygon(self, poly, pos):
		if type(poly) != list:
			self.data.status.set_text("ERROR: wrong data as polygon")
			return False

		count = 0
		for i,p in enumerate(poly): # algo: cast a ray along y direction and count how many times we enter and exit the polygon
			_p = poly[i-1]
			if _p.x == pos.x: # avoid points on the ray
				_p.x += 0.01
			if p.x == pos.x: # avoid points on the ray
				p.x += 0.01

			if p.x > pos.x and _p.x < pos.x or p.x < pos.x and _p.x > pos.x: # line _p p intersects the ray in y direction
				ipy = _p.y + (pos.x - _p.x)*(p.y-_p.y)/(p.x-_p.x)  # intersection point
				if ipy < pos.y: # check if intersection point before pos
					count += 1

		if count % 2 == 1: # if uneven the point is in the polygon
			return True

		return False

	def isPointOnPolygon(self, poly, pos):
		if type(poly) != list:
			self.data.status.set_text("ERROR: wrong data as polygon")
			return False

		for i,p in enumerate(poly):
			_p = poly[i-1]
			l = line(_p.x, _p.y, p.x, p.y)
			d = distPointSegment(pos, l)
			if d < l.length*0.1:
				return True

		return False

	# check if zone exists with pos inside it
	def getZonesAtPos(self, pos, edge = False):
		indivs = []

		ontology = self.data.project.ontology

		for k,i in ontology.individuals.items():
			if i.perimeter != None:
				perim = i.stringToPerimeter(i.perimeter) # zone perimeter : "x:y:z;x:y:z; ..."
				# TODO: obsolete if-statement?
				if edge:
					if self.isPointOnPolygon( perim , pos):
						indivs.append(i.label)
				else:
					if self.isPointInPolygon( perim , pos):
						indivs.append(i.label)

		return indivs

	def getObjectsInZone(self, cl, perim = None, edge = False): # search cl in zone
		ontology = self.data.project.ontology
		classes = ontology.classes
		if not cl in classes:
			return []

		if not perim:
			return []

		res = []
		for c in self.getAllClassesInSubTree(cl): # get all indivs of subtree classes
			for k,i in c.individuals.items():
				x,y = self.data.getIndivPosition(i)
				if x and y:
					if edge:
						if self.isPointOnPolygon( perim , point(x,y) ): # zone perimeter : "x:y:z;x:y:z; ..."
							res.append(i.label)
					else:
						if self.isPointInPolygon( perim , point(x,y) ): # zone perimeter : "x:y:z;x:y:z; ..."
							res.append(i.label)

		return res

	def getAllClassesInSubTree(self, cl):
		classes = self.data.project.ontology.classes
		res = [classes[cl]]
		for child in classes[cl].children:
			res.extend( self.getAllClassesInSubTree(child.name) )
		return res

	# check if class has Perimeter as data property, then it is a zone
	def isZone(self, cl):
		if not cl in self.data.project.ontology.classes:
			return False
		cla = self.data.project.ontology.classes[cl]
		for k,dp in cla.dataproperties.items():
			if dp.function == "Perimeter":
				return True
		return False

	def isOnZoneEdge(self, cl):
		return self.isAncestorOf(self.data.openingObject, cl)

	def removeIndiv(self, i):
		ontology = self.data.project.ontology
		e = i.xml_element
		p = e.getparent()
		if p != None:
			p.remove(e)#remove e from its parent
			ontology.xml_tree.write(ontology.specific_path, pretty_print=True)

			del ontology.classes[i.domain].individuals[i.label]
			del ontology.individuals[i.label]
			return

	def owl_append(self, i, data): # props are dicts of values, key is property
		#user chooses cl from class dropdown and inputs the name for the individual
		print "Populate:", i.domain, i.label

		#get namespaces
		ontology = self.data.project.ontology
		NS = ontology.namespaces

		NS_indiv = "{" + NS["owl"] + "}NamedIndividual"
		NS_type = "{" + NS["rdf"] + '}type'
		NS_knoholem = NS["knoholem"]
		NS_xml = "http://www.w3.org/2001/XMLSchema#"
		NS_about = "{" + NS["rdf"] + '}about'
		NS_res = "{" + NS["rdf"] + '}resource'
		NS_dt = "{" + NS["rdf"] + '}datatype'

		#create new element
		e = ET.SubElement(ontology.xml_tree.getroot(), NS_indiv, { NS_about:NS_knoholem + i.label } ) # new individual element
		i.xml_element = e
		e1= ET.SubElement(e, NS_type, { NS_res:NS_knoholem + i.domain } )								# new class element of individual

		# add data properties
		for prop, dp in i.dataProperties.items():
			if dp == "":
				continue
			ei = ET.SubElement(e, prop, {})					# new property element of individual
			ei.text = dp

		# add object properties
		for prop in i.objectProperties:
			for obj in i.objectProperties[prop]:
				ei = ET.SubElement(e, prop, { NS_res:NS_knoholem + obj } )						# new property element of individual

		#append to indivs (tool internal list)
		ontology.individuals[i.label] = i

		#write all to file
		ontology.xml_tree.write(ontology.specific_path, pretty_print=True)

	def addObjProp(self, obj, p, name):
		ontology = self.data.project.ontology

		obprops = ontology.individuals[obj].objectProperties
		obprops[p] = name

		NS = ontology.namespaces
		NS_knoholem = NS["knoholem"]
		NS_res = "{" + NS["rdf"] + '}resource'

		e = ontology.individuals[obj].xml_element
		ET.SubElement(e, p, { NS_res:NS_knoholem + name })						# new property element of individual

		#write all to file
		ontology.xml_tree.write(ontology.specific_path, pretty_print=True)

	def isAncestorOf(self, ancestor, cl, verbose = False):
		classes = self.data.project.ontology.classes
		if not ancestor in classes:
			return False
		if not cl in classes:
			return False

		parent = classes[cl].parent
		if parent:
			if parent.name == ancestor:
				return True
		if parent:
			return self.isAncestorOf(ancestor, parent.name, verbose)
		return False

	# compute the data for the indiv to populate
	def computeObPropData(self, obj, cl): # obj is the number corresponding to the i-th object to populate
		ontology = self.data.project.ontology
		if not cl in ontology.classes:
			return {}

		uin = self.data.sel_user_input #  get the user gui input
		pos = self.data.sel_prim_gc[obj]

		obpdata = {}
		for k,p in ontology.classes[cl].objectproperties.items():
			fkt = p.function #  ocad funktion fuer die object property

			if fkt == "User input": # user input could be a class
				fkt = str(uin[k])

			res = []
			if fkt == self.data.positionObject: # check if object property is a position
				res.append(self.newPosition(pos))

			elif self.isZone(cl): # cl is a zone, fkt must be a class of objects expected in the zone (populating a zone)
				res = self.getObjectsInZone(fkt, self.data.sel_wrl_points, self.isOnZoneEdge(fkt)) # populate that list of objects
				if len(res) == 0:
					continue

			elif self.isZone(fkt): # fkt is a zone class, cl must be an object expected in zones (populating an object)
				res = self.getZonesAtPos(pos, self.isOnZoneEdge(cl)) # checks what zones are at pos
				if len(res) == 0:
					continue

			if not fkt == 'None':
				obpdata[k] = res

		return obpdata

	def perimeterToString(self, perim):
		data = ""
		for i,p in enumerate(perim):
			if i != 0:
				data += ";"
			data += str(p.x)
			data += ":"
			data += str(p.y)
		return data

	# compute the data for the indiv to populate
	def computeDtPropData(self, obj, cl, pos = None):
		ontology = self.data.project.ontology
		if not cl in ontology.classes:
			print "Warning:", cl, " is not a class!"
			return {}

		uin = self.data.sel_user_input#  get the user gui input

		if not pos:
			pos = self.data.sel_prim_gc[obj]
		bbox = self.data.sel_prim_bbox[obj]

		selPoints = self.data.sel_wrl_points

		dtpdata = {}
		for k,p in ontology.classes[cl].dataproperties.items():
			fkt = p.function #  ocad funktion fuer die data property
			res = ""
			if fkt == "User input" and k in uin:
				res = str(uin[k])
			if fkt == "X Coordinate":
				res = str(pos.x)
			if fkt == "Y Coordinate":
				res = str(pos.y)
			if fkt == "Width":
				res = str(bbox[1].x-bbox[0].x)
			if fkt == "Length":
				res = str(bbox[1].y-bbox[0].y)
			if fkt == "Area":
				res = str((bbox[1].x-bbox[0].x)*(bbox[1].y-bbox[0].y))
			if fkt == "Perimeter":
				res = self.perimeterToString(selPoints)
			if fkt == "GUID":
				res = str(uuid4())

			if not fkt == "None":
				dtpdata[k] = res

		return dtpdata

	def getUniqueName(self, base):
		name = base
		while name in self.data.project.ontology.individuals.keys():
			name += "_" + str(randint(0,sys.maxint))
		return name

	def newPosition(self, pos):
		cl = self.data.positionObject
		name = self.getUniqueName("position")
		self.appendToOntology(0, cl, name, None, pos) # create a position object
		return name

	#def checkSubZones(self, cl, dtpdata, obpdata):
	#	if not self.isZone(cl):
	#		return

	def appendToOntology(self, n, cl, name, obj, pos = None):
		dtpdata = self.computeDtPropData(n, cl, pos)
		obpdata = self.computeObPropData(n, cl)
		#self.checkSubZones(cl, dtpdata, obpdata)
		name = self.getUniqueName(name)

		i = individual()
		i.domain = cl
		i.label = name
		i.objectProperties = obpdata
		i.dataProperties = dtpdata

		self.updateIndivsProps(i)

		ontology = self.data.project.ontology
		ontology.individuals[name] = i
		ontology.classes[cl].individuals[name] = i

		# append to OWL
		self.owl_append(i, self.data)

		# check if cl is an object expected inside a zone
		if cl != self.data.positionObject:
			zones = self.getZonesAtPos(self.data.sel_prim_gc[n], self.isOnZoneEdge(cl)) # checks what zones are at pos
			for z in zones:
				zi = ontology.individuals[z]
				zcl = ontology.classes[zi.domain]
				for prop in zcl.objectproperties:
					fkt = ontology.objectproperties[prop].function
					if self.isAncestorOf(fkt, cl): # check if the ancestor of this class is a obprop of the object
						if not z == name:
							self.addObjProp(z, prop, name)

		# update object properties from other objects
		for objl in obpdata:
			if ontology.objectproperties[objl].name == self.data.positionObject:
				continue
			for obj in obpdata[objl]:
				if obj in ontology.individuals:
					for prop in ontology.individuals[obj].objectProperties:
						if self.isAncestorOf(ontology.objectproperties[prop].function, cl): # check if the ancestor of this class is a obprop of the object
							self.addObjProp(obj, prop, name)

		#append new entity to gui tree
		tree = self.data.builder.get_object("owlindivtree")
		it = tree.get_iter_root()# first child
		while it != None:
			if tree.get_value(it, 0) == cl:
				break
			it = tree.iter_next(it)

		if it == None:#append class
			it = tree.append(None, [cl, ""])
		tree.append(it, [name, ""])#append individual

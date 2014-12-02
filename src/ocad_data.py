#!/usr/bin/env python

import gobject
import layer

class ocad_data:
	def __init__(self):
		self.project = None

		#---------------------
		#-----Viewer + GUI----
		#---------------------
		#gtk
		self.gtk = None
		self.builder = None
		self.status = None

		self.active_viewport = None
		self.highlight = None
		self.ObjectLayer = None
		self.ZoneLayer = None
		self.initLayers()

		self.fileDialogTrigger = None

		#---------------------
		#-----Ontology-------
		#---------------------

		self.positionObject = "Placement"
		self.openingObject = "Opening"
		self.dtPropFkts = ["User input", "Area", "X Coordinate", "Y Coordinate", "Width", "Length", "Perimeter", "GUID", "None"]# also sync with the function computeDtPropData in ocad_core

		#---------------------
		#-----Selection-------
		#---------------------

		self.sel_mode = "LASSO"

		#selection points
		self.sel_wrl_points = None

		#selection data
		self.sel_area = None
		self.sel_gc = None
		self.sel_bbox = None

		#grouped primitives to objects
		self.objects = None

		#selected objects data
		self.sel_prim_gc = None
		self.sel_prim_bbox = None	#TODO

		#population input data
		self.sel_user_input = None

	def initLayers(self):
		self.highlight = layer.layer("highlight")
		self.highlight.line_width = 10
		self.highlight.point_size = 10
		#self.highlight.color = array([0.16667, 1, 1])
		self.highlight.color = [1, 0.2, 0.2]
		self.highlight.caps = 2#self.gtk.gdk.CAP_ROUND

		self.ObjectLayer = layer.layer("objects")
		self.ZoneLayer = layer.layer("zones")

		self.ObjectLayer.line_width = 6
		self.ObjectLayer.color = [0.2, 0.7, 0.2]
		self.ObjectLayer.visible = False
		self.ObjectLayer.point_size = 15
		self.ZoneLayer.line_width = 10
		self.ZoneLayer.color = [0.2, 0.7, 0.2]
		self.ZoneLayer.visible = False

	def printStatus(self, s):
		gobject.idle_add( self.status.set_text, s)

	def getIndivPosition(self, indiv):
		def getXY(ontology, data):
			x,y = None,None
			for p in data:
				if p in ontology.dataproperties:
					if ontology.dataproperties[p].function == "X Coordinate":
						x = float(data[p])
					if ontology.dataproperties[p].function == "Y Coordinate":
						y = float(data[p])
			return x,y

		def isPosition(ontology,prop):
			if prop in ontology.objectproperties:
				if ontology.objectproperties[prop].function == self.positionObject:
					return True
			return False

		ontology = self.project.ontology
		x,y = getXY(ontology, indiv.dataProperties)
		if x and y:
			return x,y

		for prop, value in indiv.objectProperties.items(): # search for a position
			#print prop
			if isPosition(ontology,prop):
				pos = indiv.objectProperties[prop]
				if type(pos) is list:
					pos = pos[0]
				#print pos
				if not pos in ontology.individuals:
					continue
				data = ontology.individuals[pos].dataProperties
				x,y = getXY(ontology, data)

		return x,y

	def getIndivBox(self, indiv):
		w,h = None,None

		ontology = self.project.ontology
		for prop in indiv.dataProperties:
			if prop in ontology.dataproperties:
				if ontology.dataproperties[prop].function == "Width":
					w = float(indiv.dataProperties[prop])
				if ontology.dataproperties[prop].function == "Length":
					h = float(indiv.dataProperties[prop])

		return w,h

#!/usr/bin/env python

import ocad_data
import ocad_gui
import selector
from selection_polygon import selection_polygon
import ocad_semantic
import xml_parser
import dxf_parser
import ifc_parser
import os
import copy
import threading
import gobject
import gtk
from threading import Thread
from time import sleep
from ocad_primitives import *
from math import sqrt
from random import *
from ocad_ontology import *
import pickle
import re
from ocad_project import *

class ocad_core:
	def __init__( self ):
		self.onlyLayerHint = 0
		self.mouseTool = 0
		
		print "Init modules"
		self.data = ocad_data.ocad_data()
		self.gui = ocad_gui.ocad_gui(self.data)
		self.selector = selector.selector()
		self.miner = ocad_semantic.ocad_semantic(self.data)
		self.ontology = ocad_ontology(self.data)
		
		#self.gui.viewer.selector = self.selector
		
		print "Connect signals"
		sigs = {"open_file" : self.open_file,
			"open_file_dialog" : self.gui.open_dialog,
			"on_layer_box_cursor_changed" : self.clickLayer,
			"on_viewport_box_changed" : self.switchViewport,
			"on_cellrenderertext1_toggled" : self.edit_layer_visible,
			"on_showall_clicked" : self.gui.view.showAll, #reset view
			"on_save_clicked" : self.saveProject,
			"on_open_clicked" : self.gui.open_dialog,
			"on_exit_clicked" : self.close,
			"on_individuals_clicked" : self.showIndivs,
			"on_zones_clicked" : self.showZones,
			"on_treeview1_cursor_changed" : self.displayIndivParams,
			"on_class_box_changed" : self.gui.updateClassDataProps,
			"on_button4_clicked" : self.searchForTemplate,
			"on_button5_clicked" : self.stopPatternMatching,
			"on_invert_clicked" : self.invert_visible,
			"on_hide_all_clicked" : self.hide_all,
			"on_button3_clicked" : self.addOntEntity,
			"on_new_clicked" : self.new,
			"on_file_new_activate" : self.new,
			"on_file_quit_activate" : self.close,
			"on_button7_clicked" : self.cancelNew,
			"on_button6_clicked" : self.newProject,
			"on_button10_clicked" : self.deleteAllIndivs,
			"on_button11_clicked" : self.deleteIndiv,
			"on_button8_clicked" : self.gui.open_dialog,
			"on_button9_clicked" : self.gui.open_dialog,
			"on_button12_clicked" : self.gui.open_dialog,
			"on_button1_clicked" : self.gui.close_dialog,
			"on_treeview3_row_activated" : self.openProject,
			"on_toolbutton2_clicked" : self.userHelp,
			"on_lasso_clicked" : self.setLassoMode,
			"on_pin_clicked" : self.setPinMode
			}


		self.data.builder.connect_signals(sigs)
		self.gui.connectViewerMouseHandler(self.viewPress)
				
	def start(self):
		def ListProjects():
			if not os.path.exists("../Projects"):
				return
			for p in os.listdir("../Projects"):
				if (p.split(".")[-1] != "ocp"):
					continue
					
				l = self.data.builder.get_object("recentProjects")
				
				f = open("../Projects/" + p, "r")
				content = f.read().split("\n")
				f.close()
				
				l.append([content[0], content[4]])
			
		print "Start gui"
		self.gui.window.maximize()
		self.gui.window.show()
		
		ListProjects()
		
		self.gui.start() #enter gtk main loop		
		
		#gobject.timeout_add_seconds(10, self.thread1.join)
		#gobject.timeout_add_seconds(10, self.thread2.join)
	
#--------------------GUI Callbacks------------------------------------------------	

	def userHelp(self, b): # TODO
		pass
		
	def setLassoMode(self, b):
		self.data.sel_mode = "LASSO"
		self.selector.cancel()
		self.resetSelectionLayer()
		self.gui.view.redraw()
		
	def setPinMode(self, b):
		self.data.sel_mode = "PIN"
		self.selector.cancel()
		self.resetSelectionLayer()
		self.gui.view.redraw()

	def saveProject(self, b):
		self.data.project.save()

	def close(self, b):
		exit()

	def new(self, b):
		self.data.builder.get_object("dialog1").show()

	def cancelNew(self, b):
		self.data.builder.get_object("dialog1").hide()

	def newProject(self, b):			
		title = self.data.builder.get_object("entry3").get_text()
		cad_file = self.data.builder.get_object("entry2").get_text()
		owl_file = self.data.builder.get_object("entry1").get_text()
		
		if title == "" or cad_file == "" or owl_file == "":
			return
			
		self.data.builder.get_object("dialog1").hide()
		self.gui.showViewer()
		
		spec_ont = self.data.builder.get_object("entry4").get_text()
		self.data.project = ocad_project(self.data, title)
		self.data.project.addToList()
		self.open_cad(cad_file)
		pS = self.open_owl(owl_file, spec_ont)
		
		self.data.project.ontology.specific_path = pS
		self.data.project.ontology.generic_path = owl_file
		
		self.data.project.save()
			
	def showZones(self, b):
		zl = self.data.ZoneLayer
		zl.visible = not zl.visible
		
		if not zl.visible:
			self.gui.view.redraw()
			return
		
		# TODO : draw to zone layer when populating!
		ontology = self.data.project.ontology
		self.data.ZoneLayer.clear()
		for k, i in ontology.individuals.items():
			if i.isZone and i.perimeter:
				i.drawBBox(self.data.ZoneLayer)
				
		self.gui.view.remLayer(self.data.ZoneLayer)
		self.gui.view.addLayer(self.data.ZoneLayer)
		self.gui.view.redraw()
		
	def showIndivs(self, b):
		ol = self.data.ObjectLayer
		ol.visible = not ol.visible
		
		if not ol.visible:
			self.gui.view.redraw()
			return
		
		# TODO : draw to object layer when populating!
		ontology = self.data.project.ontology
		self.data.ObjectLayer.clear()
		for k, i in ontology.individuals.items():
			if i.isZone:
				continue
			if i.isPosition:
				continue
					
			i.drawBBox(self.data.ObjectLayer)
				
		self.gui.view.remLayer(self.data.ObjectLayer)
		self.gui.view.addLayer(self.data.ObjectLayer)
		self.gui.view.redraw()
		
	def invert_visible(self, b):
		for k,l in self.data.active_viewport.layers.items():
			l.visible = not l.visible
		
		self.gui.view.redraw()
		
	def hide_all(self, b):
		for k,l in self.data.active_viewport.layers.items():
			l.visible = False
		
		self.gui.view.redraw()
		
	def displayIndivParams(self, tree):
		selection = tree.get_selection()
		ontology = self.data.project.ontology
		
		model, item = selection.get_selected()
		if item == None:
			return
			
		if model.iter_parent(item) == None: #ignore top level classes
			return
			
		indiv_name = model.get_value(item, 0)
		if not indiv_name in ontology.individuals:
			return
		indiv = ontology.individuals[indiv_name]

		self.data.builder.get_object("indiv_x_b").set_text(str(indiv.position.x))
		self.data.builder.get_object("indiv_y_b").set_text(str(indiv.position.y))
		self.data.builder.get_object("indiv_w_b").set_text(str(indiv.width))
		self.data.builder.get_object("indiv_h_b").set_text(str(indiv.height))
		self.data.builder.get_object("indiv_perim_b").set_text(str(indiv.perimeter))
		dpstr = str(indiv.dataProperties)
		dpstr = re.sub('[{\'}]', '', dpstr)
		dpstr = re.sub('[,]', '\n', dpstr)
		opstr = str(indiv.objectProperties)
		opstr = re.sub('[{\'}]', '', opstr)
		opstr = re.sub('[,]', '\n', opstr)
		self.data.builder.get_object("indiv_dp_b").set_text(dpstr)
		self.data.builder.get_object("indiv_op_b").set_text(opstr)
		
		# highlight in viewer
		self.data.highlight.clear()
		indiv.drawBBox(self.data.highlight)
		self.redrawHightlightLayer()
		
	def deleteIndiv(self, b):
		selection = self.data.builder.get_object("treeview1").get_selection()
		ontology = self.data.project.ontology
		
		model, item = selection.get_selected()
		if item == None:
			return
			
		if model.iter_parent(item) == None: #ignore top level classes
			return
		
		indiv_name = model.get_value(item, 0)
		if not indiv_name in ontology.individuals:
			return
		indiv = ontology.individuals[indiv_name]
		
		self.ontology.removeIndiv(indiv)
		model.remove(item)
		
	def deleteAllIndivs(self, b):
		ontology = self.data.project.ontology
		for k,i in ontology.individuals.items():
			self.ontology.removeIndiv(i)
			
		self.data.builder.get_object("owlindivtree").clear()

#----------------Project Management------------------------------------------------------

	def openProject(self, p1, p2, p3):
		l = self.data.builder.get_object("recentProjects")
		row = l.get(l.get_iter(p2[0]), 0)
		
		if (self.data.project != None):
			if (self.data.project.title == row[0]):
				print "Project", row[0], "allready open."
				return
		
		f = open("../Projects/" + row[0] + ".ocp", "r")
		content = f.read().split("\n")
		f.close()
		
		self.gui.showViewer()
		self.data.project = ocad_project(self.data, content[0])
		self.data.project.listIndex = p2[0]
		self.data.project.lastChanged = content[4]
		
		pS = self.open_owl(content[1], content[2])
		self.data.project.ontology.specific_path = pS
		self.data.project.ontology.generic_path = content[1]
		self.open_cad(content[3])
		
	def open_cad(self, path, isthread = False):#change to false to use threads, needs cheking the concurency!
		if not isthread:
			thread = Thread(target = self.open_cad, args=(path,True,))
			thread.start()
			return

		if not os.path.isfile(path):
			print path, "does not exist!"
			return

		self.gui.clean_status = False
		self.data.printStatus("DXF import - parse file ...")

		self.data.project.layout.path = path

		#choose importer based on extension
		ext = path.split(".")[-1]
		if ext == "xml":
			parser = xml_parser.xml_parser()
		if ext == "dxf":
			parser = dxf_parser.dxf_parser()

		#start parser
		parser.parse(path)
		self.data.project.layout.viewports = parser.viewports
		self.data.active_viewport = parser.viewports[ parser.viewports.keys()[0] ]
		self.colorizeLayers()

		#execute post stuff in gtk main thread
		gobject.idle_add(self.gui.updateViewportList)

		self.data.printStatus("DXF import - done")
		self.gui.clean_status = True

	def open_owl(self, pathG, pathS):
		path = pathS[:]
		if pathS == "" or not os.path.isfile(path):
			path = pathG[:]
			pathS = "".join(pathG.split(".")[:-1]) + "_specific.owl"
			open(pathS, 'w').close() # create file
			
		print path, pathS, pathG
		
		if not os.path.isfile(path):
			print path, "does not exist!"
			return ""

		self.ontology.open_file(path)
		self.gui.updateOntology()

		self.ontology.updateAllIndivsProps()
		self.ontology.updateAllIndivsProps() #twice because of the placements
		
		return pathS
				
	def open_file(self, p1):
		"""Open file via file open dialog."""
		f = self.gui.getFileDialog().get_file()
		if f == None:
			return

		name = f.get_basename()
		ext = name.split(".")[-1]

		exts = ["xml", "dxf", "owl"]

		if not ext in exts:
			print "Wrong file type! choose another file"
			return

		self.gui.getFileDialog().hide()
		
		# depending on triggering button, decide what to load
		b_trig = self.data.fileDialogTrigger
		b_cad = self.data.builder.get_object("button8")
		b_gowl = self.data.builder.get_object("button9")
		b_sowl = self.data.builder.get_object("button12")
		
		if b_trig == b_cad:
			self.data.builder.get_object("entry2").set_text( f.get_path() )
		if b_trig == b_gowl:
			self.data.builder.get_object("entry1").set_text( f.get_path() )
		if b_trig == b_sowl:
			self.data.builder.get_object("entry4").set_text( f.get_path() )

	def colorizeLayers(self):
		def hex_to_rgb(value):
			value = value[1:]
			lv = len(value)
			return tuple(int(value[i:i+lv/3], 16)/65535.0 for i in range(0, lv, lv/3))

		vpts = self.data.project.layout.viewports
		for k, v in vpts.items():
			N = len(v.layers) * 0.8
			for i,l in enumerate(v.layers):
				c = gtk.gdk.color_from_hsv(i*N, 0.9, 0.9)
				v.layers[l].color = hex_to_rgb(str(c))

	def switchViewport(self, b):
		if not b.get_active_text() in self.data.project.layout.viewports:
			return
		self.data.active_viewport = self.data.project.layout.viewports[ b.get_active_text() ]
		self.gui.updateLayerList()
		self.gui.updateImageViewer()

#----------------Ontology-------------------------------------------------------------
	def check_selection(self):
		if self.selector.active == False:
			self.data.status.set_text("ERROR: No active selection  (polygon selection with right click)")
			return False
			
		if self.selector.closed == False:
			self.data.status.set_text("ERROR: No closed selection  (close selection with left double click)")
			return False

		return True

	def addOntEntity(self, b):
		"""Add individual button handler. Populates the ontology with the user data."""
		if not self.check_selection():
			return
			
		# get user input
		def getInputValue(widget):
			uinput = self.data.sel_user_input
			if type(widget) == gtk.Entry:
				uinput[widget.propName] = widget.get_text()

		properties = self.data.builder.get_object("table7")
		properties.foreach(getInputValue)
		
		form = self.gui.getOwlPopForm()#get gui data
		cl = form[0].get_active_text()#class
		name = form[1].get_text()#entity name

		# checks and warnings
		if cl == None:
			self.data.status.set_text("ERROR: No class selected  (choose a class in the dropdown list)")
			return
		if name == '':
			self.data.status.set_text("ERROR: No valid name given  (please enter something in the name text entry)")
			return
		if len(self.data.objects) == 0:
			self.data.status.set_text("ERROR: Nothing selected")
			return

		# compute the missing stuff for all objects and append to owl (via parser to the tree structure)
		for i,o in enumerate(self.data.objects): 
			self.ontology.appendToOntology(i, cl, name, o )
	
#----------------Template matching----------------------------------------------------

	def searchForTemplate(self, b, isthread = False):
		if not self.check_selection():
			return
					
		if not isthread:
			thread = Thread(target = self.searchForTemplate, args=(b,True,))
			thread.start()
			return
		
		gobject.idle_add( b.set_sensitive, False ) # disable 'find similar' button
		self.gui.clean_status = False # disable the clean of the status bar
		
		self.miner.groupObjects()
		gobject.idle_add( self.redrawHightlightLayer )
		
		self.gui.clean_status = True
		gobject.idle_add( b.set_sensitive, True )
		
	def stopPatternMatching(self, b):
		self.miner.process_break = True
		
#----------------Interaction----------------------------------------------------------

	def edit_layer_visible( self, w, row):
		"""Change layer visibility state."""
		l = self.gui.getLayerList()[row]
		l[1] = abs(l[1] - 1) # toggle gui checkbox

		self.data.active_viewport.layers[ l[0] ].visible = l[1] # set visibility of layer to checkbox status

		self.gui.view.redraw()

	def convertWidgetPositionToWorld(self, widget, b): # TODO
		pos = widget.gl.imgToWorld(point(b.x, b.y))
		return pos, pos - widget.gl.offset
		
	def viewPress(self, widget, b):
		"""Intercept mouse clicks on the viewport."""
		# pos is in world coords and imgpos is in image coords
		pos, imgpos = self.convertWidgetPositionToWorld(widget, b)
		if b.button == 3: # right click
			self.selector.setMode(self.data.sel_mode)
			if self.selector.closed == True and self.selector.active == True: # new selection, first point
				self.selector.clear()
				self.resetSelectionLayer()
				
			self.selector.appendToPolySelect(pos, imgpos)
			self.updateSelStats(self.selector.wrl_pnts)
			self.redrawSelectionLayer()

		if b.button == 1 and b.type == 5: #double click
			if self.selector.closed == False and self.selector.active == True:
				self.selector.closeLoop() 						#close selection line
				self.updateSelStats(self.selector.wrl_pnts) #update the stats
				self.redrawSelectionLayer() 				#redraw the layer
				self.data.sel_wrl_points = self.selector.wrl_pnts #send the selection point list

				self.miner.groupObject()# group selected object and highlight it
				self.redrawHightlightLayer()

			elif self.selector.active == True:
				self.selector.clear()
				self.resetSelectionLayer()
		
		self.gui.view.redraw()

		# ------------ Selection layer ---------
	def resetSelectionLayer(self):
		self.gui.view.remLayer(self.data.highlight.name)
		self.gui.view.remLayer(self.selector.selectionLasso.name)
		self.gui.view.remLayer(self.selector.selectionPin.name)
		self.gui.view.redraw()

	def redrawSelectionLayer(self):
		if self.data.sel_mode == "LASSO":
			self.gui.view.addLayer(self.selector.selectionLasso)
		if self.data.sel_mode == "PIN":
			self.gui.view.addLayer(self.selector.selectionPin)
		self.gui.view.redraw()

	def redrawHightlightLayer(self):
		self.gui.view.addLayer(self.data.highlight)
		self.gui.view.redraw()

	def selectLayer(self, l):
		self.resetSelectionLayer()
		if l.offset == None:
			return

		self.data.highlight.copyPrimitives(l)
		self.redrawHightlightLayer()

	def updateSelStats(self, points):
		"""Update selection data."""
		polygon = selection_polygon(points)

		area = polygon.close().calculateArea()
		gc = polygon.geometricCenter()
		bbox = polygon.boundingBox()

		# Feed data to gui
		self.gui.setSelPoints(polygon.points)
		self.gui.setSelGeoCenter(gc)
		self.gui.setSelArea(area)

		# Update data
		self.data.sel_area = area
		self.data.sel_gc = gc
		self.data.sel_bbox = bbox

	def clickLayer(self, p1):
		"""Select layer from list with mouse."""
		if self.onlyLayerHint == 1:
			self.onlyLayerHint = 0
			return
		l = self.gui.getSelectedLayer()
		self.selectLayer( self.data.active_viewport.layers[l] )

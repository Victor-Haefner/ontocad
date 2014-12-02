#!/usr/bin/env python

import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
#import gtk.gtkgl

import pickle # to store and load dicts to file
import os, sys, inspect

import ocad_viewer
import gtkviewer
import gobject
from layer import layer
from ocad_primitives import *

from pygtkgl_area import GtkGlDrawingArea

class ocad_gui:
	def __init__( self, data ):
		self.data = data
		self.data.gtk = gtk
		self.data.builder = gtk.Builder()

		factory = gtk.IconFactory()
		factory.add_default()

		builder = self.data.builder
		builder.add_from_file("../res/gui.glade")
		self.window = builder.get_object("window1")
		self.window.connect("delete_event", self.delete_event)
		self.setCellRenderers()

		#self.pb_blue = gtk.gdk.pixbuf_new_from_file("../pixbuf1.png")
		#self.pb_green = gtk.gdk.pixbuf_new_from_file("../pixbuf2.png")
		#self.pb_red = gtk.gdk.pixbuf_new_from_file("../pixbuf3.png")

		self.data.status = builder.get_object("gui_status")

		self.viewer = ocad_viewer.ocad_viewer(self.data, gtk, self.window)
		self.viewer.isLayerVisible = self.isLayerVisible

		self.initImageViewer()
		self.viewer.viewer = self.view

		#every second check if status is empty
		gobject.timeout_add_seconds(1, self.check_status, False)
		self.clean_status = True

	def updateOntology(self):

		def insertClassInTree(elemtree, cl, _iter = None):
			c_iter = elemtree.append(_iter, [cl.name, 0, None])
			for c in cl.children:#insert children
				insertClassInTree(elemtree, c, c_iter)

		ontology = self.data.project.ontology

		#gtk structures
		cltree = self.data.builder.get_object("owlclasstree")
		cllist = self.data.builder.get_object("owlclasslist")
		intree = self.data.builder.get_object("owlindivtree")
		inlist = self.data.builder.get_object("owlindivlist")
		inlist = self.data.builder.get_object("owlindivlist")
		inlist = self.data.builder.get_object("owlindivlist")
		dtTable = self.data.builder.get_object("dtPropTab")
		obTable = self.data.builder.get_object("obPropTab")

		cltree.clear()
		cllist.clear()
		intree.clear()
		inlist.clear()

		#class list
		classes = ontology.classes.keys()
		classes.sort()
		for c in classes:
			cllist.append([c])

		#class tree
		for k, c in ontology.classes.items():
			if not c.parent:
				insertClassInTree(cltree, c)

		#indiv tree
		for k,c in ontology.classes.items():
			if len(c.individuals) == 0:
				continue
			n = intree.append(None, [k, ""])
			for j,i in c.individuals.items():
				inlist.append([i.label])
				intree.append(n, [i.label, ""])

		#data and object properties----

		#list of ocad functions
		fktlist = gtk.ListStore(str)
		for fkt in self.data.dtPropFkts:
			fktlist.append([fkt])

		# list store with all classes
		classlist = gtk.ListStore(str)
		for r in cllist:
			classlist.append(r)
		classlist.prepend(["None"])
		classlist.prepend(["User input"])

		#load old map from file
		dtmap = self.loadData("OCAD_fkt_map_dp")
		obmap = self.loadData("OCAD_fkt_map_op")

		#fill table
		self.updatePropsTable(ontology.dataproperties, dtTable, dtmap, fktlist, self.changeDTPmap, 1)
		self.updatePropsTable(ontology.objectproperties, obTable, obmap, classlist, self.changeOBPmap, 3)

	def check_status(self, _del):
		timelaps = 1
		if self.data.status.get_text() != '' and self.clean_status:
			if _del:
				self.data.status.set_text('')
				_del = False
			else:
				timelaps = 3
				_del = True
		gobject.timeout_add_seconds(timelaps, self.check_status, _del)

	def getOwlPopForm(self):
		bu = self.data.builder
		return bu.get_object("class_box"), bu.get_object("class_name_field")

	def addOwlPixbuf(self, model, path, iter):
		_id = model.get_value(iter, 1)
		if _id == 0:
			pix = self.pb_blue
		if _id == 1:
			pix = self.pb_green
		if _id == 2:
			pix = self.pb_red
		model.set_value(iter, 2, pix)

	def updateOwlTree(self):
		builder = self.data.builder
		owltree = builder.get_object("owlclasstree")
		owltree.foreach(self.addOwlPixbuf)

		treeview = builder.get_object("treeview2")
		treeview.expand_all()

	#user just chosed a class via drop down and needs to see the input fields
	def updateClassDataProps(self, b):
		def addEntry(fkt):
			label = gtk.Label("")
			label.set_text(prop)
			label.set_padding(0, 5)

			if fkt == "User input":
				entry = gtk.Entry(0)
				entry.propName = prop
			else:
				entry = gtk.Label("")
				entry.set_text(fkt)

			Nr = table.get_property('n-rows')
			table.resize(Nr+1, 3)
			table.attach(label, 0, 1, Nr, Nr+1)
			table.attach(entry, 1, 3, Nr, Nr+1)

		ontology = self.data.project.ontology

		#get the class from user selection
		form = self.getOwlPopForm()
		cl_name = form[0].get_active_text()#class
		if not cl_name in ontology.classes:
			return

		cl = ontology.classes[cl_name]

		#construct the gui elements for each datatype that the user should input
		table = self.data.builder.get_object("table7")

		#delete old fields
		table.foreach(table.remove)
		table.resize(1, 3)

		#reset user input
		self.data.sel_user_input = {}

		#create new fields
		for i,prop in enumerate(cl.dataproperties):
			addEntry(cl.dataproperties[prop].function)

		for i,prop in enumerate(cl.objectproperties):
			addEntry(cl.objectproperties[prop].function)

		table.show_all()

	def changeDTPmap(self, cb, prop):
		ontology = self.data.project.ontology
		ontology.dataproperties[prop].function = cb.get_active_text()
		ontology.dpmap[prop] = cb.get_active_text()
		self.updateClassDataProps(0)
		f = open("OCAD_fkt_map_dp", "w")
		pickle.dump(ontology.dpmap, f )
		f.close()

	def changeOBPmap(self, cb, prop):
		ontology = self.data.project.ontology
		ontology.objectproperties[prop].function = cb.get_active_text()
		ontology.opmap[prop] = cb.get_active_text()
		self.updateClassDataProps(0)
		f = open("OCAD_fkt_map_op", "w")
		pickle.dump(ontology.opmap, f )
		f.close()

	def loadData(self, filename):
		try:
			f = open(filename, "r")
		except:
			return None
		else:
			data = pickle.load( f )
			f.close()
			return data

	def updatePropsTable(self, props, table, old_map, liststore, callback, wrap):
		table.foreach(table.remove)
		table.resize(1, 3)

		for i,prop in enumerate(props):
			label = gtk.Label("")
			label.set_text(prop)

			combobox = gtk.ComboBox(liststore)
			combobox.set_wrap_width(wrap)
			cell = gtk.CellRendererText()
			combobox.pack_start(cell, True)
			combobox.add_attribute(cell, 'text', 0)
			combobox.connect("changed", callback, prop)

			combobox.set_active(0)
			if old_map:
				if prop in old_map:
					for j,pf in enumerate(liststore):
						if pf[0] == old_map[prop]:
							combobox.set_active(j)

			Nr = table.get_property('n-rows')
			table.resize(Nr+1, 3)
			table.attach(label, 0, 1, Nr, Nr+1, yoptions = 0)
			table.attach(combobox, 1, 3, Nr, Nr+1, yoptions = 0)

		table.show_all()

	def setCellRenderers(self):
		"""Sets the data rendering functions on the selection polygon TreeView."""
		def getColumn(index):
			return self.data.builder.get_object("selection_points_view_col" + str(index))
		def getCellRenderer(index):
			return self.data.builder.get_object("selection_points_view_colrenderer" + str(index))
		for i in range(3):
			getColumn(i+1).set_cell_data_func(getCellRenderer(i+1), self.decimalFormat, data=None)

	def decimalFormat(self, column, cellRenderer, model, iter):
		"""
		A cell renderer data callable. Converts a float to an integer
		and appends "`mm"' to the text to render.

		"""
		toRender = cellRenderer.get_property('text')
		toRender = str(int(toRender)) + " mm"
		cellRenderer.set_property('text', toRender)
		return

	def setSelGeoCenter(self, gc):
		"""Update the text field displaying the geocenter of the selection polygon.

		:param gc: the geocenter to display.
		:type gc: point
		"""
		buff = self.data.builder.get_object("sel_geo_center")
		buff.set_text("X: " + str(int(gc.x)) + "\t\tY: " + str(int(gc.y)) + "\t[mm]")

	def setSelArea(self, area):
		"""Update the text field displaying the area of the selection polygon.

		:param area: the area to display.
		:type area: float
		"""
		buff = self.data.builder.get_object("sel_area")
		buff.set_text("A: " + str(abs(area)) + "\t\t[mm*mm]")

	def setSelPoints(self, points):
		model = self.data.builder.get_object("pointsInSelection")
		model.clear()
		for i in range(0, len(points)):
			row = []
			p = points[i]
			row.append(int(p.x))
			row.append(int(p.y))
			if i == 0:
				row.append(0)
			else:
				_p = points[i-1]
				d = p - _p
				l = sqrt(d.x*d.x + d.y*d.y)
				row.append(int(l))
			model.append(row)

	def initImageViewer(self):
		"""Image viewport."""
		alignment = self.data.builder.get_object("alignment1")
		#self.view = gtkviewer.gtkviewer(self.data)
		self.view = GtkGlDrawingArea()
		alignment.add(self.view)
		alignment.show_all()

	def updateImageViewer(self):
		self.view.clear()
		layers = self.data.active_viewport.layers
		for l in layers:
			self.view.addLayer(layers[l])
		self.view.showAll()

	def connectViewerMouseHandler(self, func):
		self.view.add_events(gtk.gdk._2BUTTON_PRESS)
		self.view.connect("button-press-event", func)

	def updateViewportList(self):
		vpb = self.data.builder.get_object("viewports")
		vpb.clear()
		for v in self.data.project.layout.viewports:
			vpb.append([v])
		self.data.builder.get_object("viewport_box").set_active(0)

	def updateLayerList(self):
		layers = self.data.active_viewport.layers
		self.getLayerList().clear()
		for l in layers:
			self.getLayerList().append([layers[l].name, 1, 1])

	def getFileDialog(self):
		return self.data.builder.get_object("file_open_dialog")

	def getLayerList(self):
		return self.data.builder.get_object("layer_list")

	def getSelectedLayer(self):
		box = self.data.builder.get_object("layer_box")

		model, rows = box.get_selection().get_selected()
		if rows == None:
			return "None"
		return model.get_value(rows, 0)

	def selectLay(self, layer):
		box = self.data.builder.get_object("layer_box")

		model, rows = box.get_selection().get_selected()
		count = 0
		for r in model:
			if (r[0] == layer):
				break
			count += 1

		box.set_cursor(count)

	def isLayerVisible(self, layer):
		if layer == None:
			return 1
		for row in self.getLayerList():
			if row[0] == layer:
				return row[1]

	def showViewer(self):
		nb = self.data.builder.get_object("notebook4")
		nb.set_current_page(1)

	def open_dialog(self, p1):
		self.data.fileDialogTrigger = p1
		diag = self.data.builder.get_object("file_open_dialog")
		diag.set_select_multiple(False)
		path = os.getcwd()[:-4]
		print "Path ", path
		diag.set_current_folder(path + "/data")
		diag.show()

	def close_dialog(self, p1):
		diag = self.data.builder.get_object("file_open_dialog")
		diag.hide()

	def setMouseCursor(self, cursor):
		window = self.data.builder.get_object("window1").get_window()
		crosshair = gtk.gdk.Cursor(gtk.gdk.CROSSHAIR)
		default = gtk.gdk.Cursor(gtk.gdk.TOP_LEFT_ARROW)
		if cursor == "rec_select":
			window.set_cursor(crosshair)
		else:
			window.set_cursor(default)

	def start(self):
		gtk.gdk.threads_init()
		gtk.main()

	def delete_event(self, widget, event):
		self.quit(None)
		return False

	def quit(self, widget):
		gtk.main_quit()
		sys.exit(0)

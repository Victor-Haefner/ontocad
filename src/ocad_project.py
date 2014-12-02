#!/usr/bin/env python

from datetime import datetime
from ocad_primitives import *

class ocad_project:
	def __init__(self, data, title):
		self.data = data
		self.lastChanged = ""
		self.listIndex = 0
		self.updateDate()
		
		self.title = title # TODO : get only filename
		self.ontology = ontology()
		self.layout = layout()
		
	def addToList(self):
		self.updateDate()
		l = self.data.builder.get_object("recentProjects")
		l.append([self.title, self.lastChanged])
		self.listIndex = len(l)-1
		
	def delFromList(self):
		l = self.data.builder.get_object("recentProjects")
		l.remove(l.get_iter(self.listIndex))
		
	def updateDate(self):
		self.lastChanged = datetime.now().strftime("%d.%m.%Y %H:%M")
		
	def save(self):
		p_file = "../Projects/" + self.title + ".ocp"
		
		f = open(".ocad.tmp", "w")   # remember
		f.write(p_file)
		f.close()

		f = open(p_file, "w")
		f.write(self.title + "\n")
		f.write(self.ontology.generic_path + "\n")
		f.write(self.ontology.specific_path + "\n")
		f.write(self.layout.path + "\n")
		f.write(self.lastChanged)
		f.close()

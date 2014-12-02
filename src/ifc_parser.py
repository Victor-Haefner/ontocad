#!/usr/bin/env python

import numpy
from numpy import *
import xml.etree.ElementTree as ET
import layer

import sys
from base_parser import *

class ifc_parser(base_parser):
	def __init__(self):
		base_parser.__init__(self)
			
	def parse(self, path):
		tag_histogram = {}
		data = self.data
		data.clear()
		#parse all lines in a structure id : element
		for line in file(path):
			strs = line.split("=", 1)
			if len(strs) != 2:
				continue
				
			_id = int(strs[0].split("#", 1)[1])
			_tag = strs[1].split("(", 1)
			
			if len(_tag) != 2:
				continue
			tag = _tag[0]
			tag = tag[3:]#skip the 'IFC'
				
			#param
			param = strs[1].split("(", 1)[1]
			for c in "()#;'$*":
				param = param.replace(c, "")
				
			params = param.split(",")
			
			#convert in ints and floats
			for i,p in enumerate(params):
				if '.' in p:
					try:
						params[i] = float(p)
					except:
						pass
					continue
				
				try:
					params[i] = int(p)
				except:
					pass
				
			
			data[_id] = [tag, params]
			
		#order all primitives by tag
		data_tag = {}
		for k in data:
			tag = data[k][0]
			val = data[k][1]
			
			if not tag in data_tag:
				data_tag[tag] = {}
			data_tag[tag][k] = val
			
		#go throught all layers
		for k, l in data_tag["PRESENTATIONLAYERWITHSTYLE"].iteritems():
			self.layer = self.getLayer(l[0])#set layer
			#go throught all shapes from layers
			for shape_id in l:
				if not type(shape_id) is int:
					continue
				if data[shape_id][0] != "SHAPEREPRESENTATION":
					continue
				#go throught all models from shapes
				mod_ids = []
				for mod_id in data[shape_id][1][3:]:
					if data[mod_id][0] == "MAPPEDITEM":#CASE 1
						repmap_id = data[mod_id][1][0]
						trans_id = data[mod_id][1][1]
						if data[repmap_id][0] != "REPRESENTATIONMAP":#allways the case, some are used more than once
							continue
						shap_id = data[repmap_id][1][1]
						if data[shap_id][0] != "SHAPEREPRESENTATION":
							continue
						for mo_id in data[shap_id][1][3:]:
							mod_ids.append([trans_id, mo_id])
						continue
					if data[mod_id][0] == "SHELLBASEDSURFACEMODEL" or data[mod_id][0] == "FACETEDBREP":#CASE 2 and 3
						mod_ids.append([None, mod_id])
						continue
						
				#go throught all shells
				for [trans_id, mod_id] in mod_ids:
					if trans_id != None:
						val = data[trans_id][1]
						self.offset = array(data[val[2]][1][:2]);#translation
						self.scale = val[3]#scale
						
						#R rotation matrix:
						# a c
						# b d
						a = data[val[0]][1][0]
						b = data[val[1]][1][0]
						c = data[val[0]][1][1]
						d = data[val[1]][1][1]
						self.rotation = array([a, b, c, d]).reshape(2,2)
						
						#if data[val[4]][1] != [0.0, 0.0, 1.0]:
							#print data[val[4]]
						
						#print data[val[0]][1], data[val[1]][1]#, data[val[3]][1]
						if data[trans_id][0] == "CARTESIANTRANSFORMATIONOPERATOR3DNONUNIFORM":
							print data[trans_id]
					
					shell_id = data[mod_id][1][0]
					if data[shell_id][0] != "CLOSEDSHELL":
						continue
						
					#do all shells
					for face_id in data[shell_id][1]:
						bound_id = data[face_id][1][0]
						loop_id = data[bound_id][1][0]
						if data[loop_id][0] != "POLYLOOP":
							continue
						val = data[loop_id][1]
						#draw all lines
						for i in range(len(val)):
							if i > 0:
								self.addLine(data[val[i-1]][1][:2] , data[val[i]][1][:2])
		

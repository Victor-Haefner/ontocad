#!/usr/bin/env python
import gtk
import numpy
from numpy import *
from ocad_math import *
from ocad_primitives import *
from time import sleep
from time import time
from scipy.spatial.kdtree import KDTree

#IDEA:
# use the relations to actively search for the right line in the quadtree!

class SObject:
	def __init__( self):
		self.points = []
		self.lines = []
		self.arcs = []
		
		self.Np = 0
		self.Nl = 0
		self.Na = 0
		
		self.w = 0
		self.h = 0
		self.pos = point()

class ocad_semantic:
	def __init__( self, data ):
		self.data = data
		self.data.objects = []
		self.process_break = False
		self.stamp = 0
	
	#primitive criteria-------------------------------------------------------Relationen zwischen primitiven
	
	#line to line relation
	def linesRelation(self, l1, l2):
		d1 = distSquare(l1.p1, l2.p1)
		d2 = distSquare(l1.p2, l2.p1)
		d3 = distSquare(l1.p1, l2.p2)
		d4 = distSquare(l1.p2, l2.p2)
		l = [d1, d2, d3, d4]
		l.sort(reverse = True) # sort the distances to faster compare relations
		l.append(l1.length) # append the lengths of the lines
		l.append(l2.length) # append the lengths of the lines
		#a = sqrt( (-d+r-R)*(-d-r+R)*(-d+r+R)*(d+r+R) )/d # circle-circle intersection, a is the distance between the two intersection points
		return l #return the 4 distances between the segment endpoints
		
	#-------------------------------------------------------------------------Compare relations
	
	#compare the relations between lines
	def linesRelComp(self, r1, r2):
		for i in range(4):
			if not sameFl(r1[i],r2[i]):
				return False
		return True
			
	
	#-------------------------------------------------------------------------Other
	#extract all primitives contained in the selection
	def extractPrimitives(self):
		self.selected_points = []
		self.selected_lines = []
		self.selected_arcs = []
		
		layers = self.data.active_viewport.layers
		for l in layers:
			la = layers[l]
			if not la.visible:
				continue
			
			for p in la.points:
				if self.isSelected(p):
					self.selected_points.append(p)
					
			for li in la.lines:
				if self.isSelected(li.p1) and self.isSelected(li.p2):
					self.selected_lines.append(li)
					
			for a in la.arcs:
				c = a.center
				r1 = a.box.x
				r2 = a.box.y
				
				p1 = c + point(r1*cos(a.a1), r2*sin(a.a1))
				p2 = c + point(r1*cos(a.a2), r2*sin(a.a2))
				if self.isSelected(p1) and self.isSelected(p2):
					self.selected_arcs.append(a)
		
		bb, w, h = self.getBoundingBox(self.data.sel_wrl_points)
			
	def createEmptyObject(self):
		return SObject()
	
	def createObjectfromSelection(self): 
		self.extractPrimitives()
		
		obj = self.createEmptyObject()
		for p in self.selected_points:
			obj.points.append(p) # extends??
		for l in self.selected_lines:
			obj.lines.append(l)
		for a in self.selected_arcs:
			obj.arcs.append(a)
			
		obj.Np = len(obj.points)
		obj.Nl = len(obj.lines) 
		obj.Na = len(obj.arcs)
		return obj
	
	def getBoundingBox(self, selection):
		
		#get BBox
		p0 = selection[0]
		bb = [p0[:], p0[:]]
		for p in selection:
			if p.x < bb[0].x:
				bb[0].x = p.x
			if p.y < bb[0].y:
				bb[0].y = p.y
			if p.x > bb[1].x:
				bb[1].x = p.x
			if p.y > bb[1].y:
				bb[1].y = p.y
				
		w = bb[1].x - bb[0].x
		h = bb[1].y - bb[0].y
		
		return bb, w, h
							
	def isSelected(self, p): #TODO: dont call getBB in here!
		bb, w, h = self.getBoundingBox(self.data.sel_wrl_points)
		if (p.x > bb[0].x and p.y > bb[0].y and p.x < bb[1].x and p.y < bb[1].y):
			return True
			
		return False
	
	#------------------

	def findSimilarLines(self):#optimiert
		layers = self.data.active_viewport.layers
		obj_dict = []
		s_obj = self.createObjectfromSelection()
		
		if s_obj.Nl == 0: # nothing selected!
			return None, None
				
		#reduce the number of same length in the selected reference list
		prim_list = {}
		for l in s_obj.lines:
			ll = round(l.length,2)
			if not ll in prim_list:
				prim_list[ll] = []
		print "Found", len(prim_list), "different lengths in the", s_obj.Nl, " selected lines"
		
		#find similar lines in all lines
		for k, layer in layers.items():
			if not layer.visible:
				continue
			for le, lis in prim_list.items():
				if le in layer.lines_dict:
					lis.extend(layer.lines_dict[le][:])
					
					
		return prim_list, s_obj
	
	def getGroupRelations(self, gr):
		rel = []
		for i, l1 in enumerate(gr.lines):
			for l2 in gr.lines[i+1:]:
				rel.append(self.linesRelation(l1, l2))
			
		rel.sort(key=lambda r: r[0], reverse=True)
		return rel
	
	def groupLines(self):
		def getSmallesList(d):
			l = []
			for i, pl in d.items():
				if len(pl) < len(l) or len(l) == 0:
					l = pl
			return l
			
		def getKDTDict(pdict):
			kdtdict = {}
			
			for l, li in pdict.items():
				pnts1 = [lin.p1 for lin in li]
				#pnts2 = [lin.p2 for lin in li]
				
				pnts = [ [p.x, p.y] for p in pnts1 ]
				#pnts.extend( [ [p.x, p.y] for p in pnts2 ] )
				
				kdtdict[l] = KDTree(pnts)
			
			return kdtdict
			
		self.stamp += 1	
		status = "Pattern matching - Search Similar Lines - ..."
		self.data.printStatus(status)
		
		#find all similar lines
		prim_dict, selected_group = self.findSimilarLines()
		if prim_dict == None:
			return
		selected_gr_rel = self.getGroupRelations(selected_group)
		
		#get longest distance in reference relations
		d_max = max(r[0] for r in selected_gr_rel)*1.0001
		
		#try to group all lines
		N = len(selected_group.lines)
		groups = []
		rel_comp_count = 0
		
		# get smallest list
		prim_list = getSmallesList(prim_dict)
		
		kdt_dict = getKDTDict(prim_dict)
		
		t0 = time()
		
		for j, l1 in enumerate(prim_list): # line				
			status = "Pattern matching - Grouping objects: " + str(j) + " from " + str(len(prim_list))
			self.data.printStatus(status)
			
			if l1.stamp == self.stamp:
				continue
		
			ref_rel = [r for r in selected_gr_rel if sameFl(r[4],l1.length) or sameFl(r[5],l1.length)]#relations wich match the segment length
			group = [l1]
			
			for ir,r in enumerate(ref_rel): # go through relations
				sameL = sameFl(r[4], r[5]) #special case
			
				len2 = r[4] # get length of other line
				if sameFl(r[4], l1.length):
					len2 = r[5]
				
				# get lines with len2 length
				l2id = round(len2, 2)
				lines = prim_dict[l2id]
					
				neighbours = kdt_dict[l2id].query_ball_point([l1.p1.x, l1.p1.y], 2*sqrt(d_max))
				
				for n in neighbours:
					rel_comp_count += 1
					
					if sameL and n <= j:
						continue
						
					l2 = lines[n]
					if l2.stamp == self.stamp:
						continue
					
					if distSquare(l1.p1, l2.p1) > d_max:#discard if too far away
						continue
						
					_r = self.linesRelation(l1, l2)
							
					if self.linesRelComp(_r, r):#l1 and l2 are in a group
						group.append(l2)
						l2.stamp = self.stamp
						break
						
				if len(group) == N:#full group
					gr = self.createEmptyObject()
					gr.lines = group
					groups.append(gr)
					break
					
		print "TIME", time() - t0
				
		status = "Found " + str(len(groups)) + " similar objects after " + str(rel_comp_count) + " comparisons"
		self.data.printStatus(status)
		print status
		self.data.objects = groups
		
	def computeObjectData(self):
		
		self.data.sel_prim_gc = []
		self.data.sel_prim_bbox = []
		
		for o in self.data.objects:
			#BBox center
			bc = point(0,0,100)	
			bbox = [0,0]	
								
			#bounding box
			if self.data.sel_mode == "LASSO":
				p0 = o.lines[0].p1
				bbox = [p0[:], p0[:]]	
				
				for l in o.lines:
					bbox[0].x = min(bbox[0].x, l.p1.x, l.p2.x)
					bbox[0].y = min(bbox[0].y, l.p1.y, l.p2.y)
					bbox[1].x = max(bbox[1].x, l.p1.x, l.p2.x)
					bbox[1].y = max(bbox[1].y, l.p1.y, l.p2.y)
							
				bc.x = (bbox[0].x + bbox[1].x)/2
				bc.y = (bbox[0].y + bbox[1].y)/2
				
				self.data.highlight.addLine( line(bbox[0].x, bbox[0].y, bbox[0].x, bbox[1].y) )
				self.data.highlight.addLine( line(bbox[0].x, bbox[0].y, bbox[1].x, bbox[0].y) )
				self.data.highlight.addLine( line(bbox[1].x, bbox[1].y, bbox[0].x, bbox[1].y) )
				self.data.highlight.addLine( line(bbox[1].x, bbox[1].y, bbox[1].x, bbox[0].y) )
				
			if self.data.sel_mode == "PIN":
				bc.x = o.points[0].x
				bc.y = o.points[0].y
					
			self.data.highlight.addPoint( bc[:] )
			self.data.sel_prim_gc.append(bc)
			self.data.sel_prim_bbox.append(bbox)
			
	def groupObject(self):
		self.data.highlight.clear()
		self.data.objects = []
		
		if self.data.sel_mode == "LASSO":
			obj = self.createObjectfromSelection()
			if obj.Nl == 0:
				return
			self.data.objects.append(obj)
			
		if self.data.sel_mode == "PIN":
			for p in self.data.sel_wrl_points:
				obj = self.createEmptyObject()
				obj.points.append(p)
				obj.Np = 1
				self.data.objects.append(obj)
			
		self.computeObjectData()
	
	def groupObjects(self):
		self.data.highlight.clear()
		self.groupLines()
		self.computeObjectData()

#!/usr/bin/env python

import lxml.etree as ET
from ocad_primitives import *

class owl_parser:
	def __init__(self):
		self.nameSpacesDict = {}
				
	def parse(self, path, project):
		self.nameSpacesDict.clear()
		project.ontology.clear()
		project.ontology.namespaces = self.nameSpacesDict
		
		#parse file
		project.ontology.xml_tree = ET.parse(path, ET.XMLParser(encoding="ISO-8859-1", remove_blank_text=True) )
		
		self.parseRDF(project.ontology)
		
		self.parseElementTags(project.ontology)
		self.updateClassHirarchy(project.ontology.classes) # link classes 
		self.updateClassProperties(project.ontology) # link classes 
				
		#population
		self.parseIndividuals(project.ontology)
		
	#------------parse to gui container---------------------------------------------
		
	def parseRDF(self, ontology):
		root = ontology.xml_tree.getroot()
		for a, val in root.nsmap.items():
			self.nameSpacesDict[a] = val
		
	#clean the tag and the attribs from the child
	def cleanTagAndAttribs(self, elem):
		if str(type(elem)) != "<type 'lxml.etree._Element'>":
			#print type(elem)
			return '', {}
	
		attr = {}
		
		for a, val in elem.attrib.items():
			tmp_a = a.split('}',1)
			tmp_attr = val.split('#',1)
			
			b = a
			if len(tmp_a) > 1:
				b = tmp_a[1]
			#b is now key value
			
			attr[b] = val
			if len(tmp_attr) > 1:
				attr[b] = tmp_attr[1]				
			#attr[b] is now attrib value
				
			self.nameSpacesDict["attr_" + b] = [a, tmp_attr[0]]#fill namespace dict		
		
		tag = elem.tag.split('}',1)[1]
		self.nameSpacesDict["tag_" + tag] = elem.tag
		
		return tag, attr
		
	#get tag and attribs from a child with the tag child_tag
	def getChildTagAndAttribs(self, elem, child_tag):
		for c in list(elem):
			t, a = self.cleanTagAndAttribs(c)
			if t == child_tag:
				return t, a, c
			
		return None, {}, None
		
	#get tag and attribs from a child with the tag child_tag
	def getAllChildTagAndAttribs(self, elem, child_tag):
		tags = []
		attrs = []
		for c in list(elem):
			t, a = self.cleanTagAndAttribs(c)
			if t == child_tag:
				tags.append(t)
				attrs.append(a)
			
		return tags, attrs
							
	def parseElementTags(self, ontology, elem = None):
		def getClassParent(self, elem):
			t, a, e = self.getChildTagAndAttribs(elem, "subClassOf")
			if "resource" in a: # parent
				return a["resource"]
			return None
		def getElementName(attr):
			if "about" in attr: # name
				return attr["about"]
			return None
		def getDataRange(self, elem):
			t, a, e = self.getChildTagAndAttribs(elem, "range") # range element
			return a
		def getPropertyDomains(self, elem):
			ts, bs = self.getAllChildTagAndAttribs(elem, "domain") # b is dict of all attributes in tag domain
			domains = {}
			for b in bs:
				if "resource" in b:
					domains[b["resource"]] = 0
			return domains
		def getIndivDomain(self, elem):
			t, a, e = self.getChildTagAndAttribs(elem, "type")
			if "resource" in a: #classtype
				return a["resource"]
			return None

		if elem == None:
			elem = ontology.xml_tree.getroot()
		tag, attr = self.cleanTagAndAttribs(elem)
		
		name = getElementName(attr)
		if name:
			if tag == "Class":
				cl = ontoclass()
				cl.parent = getClassParent(self, elem)
				cl.name = name
				ontology.classes[name] = cl
					
			if tag == "DatatypeProperty":
				dp = dataproperty()
				dp.datarange = getDataRange(self, elem)
				dp.domains = getPropertyDomains(self, elem)
				dp.name = name
				ontology.dataproperties[name] = dp
					
			if tag == "ObjectProperty":
				op = objectproperty()
				op.domains = getPropertyDomains(self, elem)
				op.name = name
				ontology.objectproperties[name] = op
				
				
				
		for child in elem.getchildren():
			self.parseElementTags(ontology, child)
			
	def updateClassHirarchy(self, classes):
		for i, cl in classes.items():
			if cl.parent:
				if cl.parent in classes:
					cl.parent = classes[cl.parent]
					cl.parent.children.append(cl)
			
	def updateClassProperties(self, ontology):
		def getInheritedProps(cl, dprops, oprops):			
			for i,dp in cl.dataproperties.items():
				dprops[dp.name] = dp
			for i,op in cl.objectproperties.items():
				oprops[op.name] = op
			
			if cl.parent != None:
				getInheritedProps(cl.parent, dprops, oprops)
		
		#local data properties
		for i, dp in ontology.dataproperties.items():
			for cl_name in dp.domains:
				cl = ontology.classes[cl_name]
				cl.dataproperties[dp.name] = dp
				dp.domains[cl.name] = cl
				
		#local object properties
		for i, op in ontology.objectproperties.items():
			for cl_name in op.domains:
				cl = ontology.classes[cl_name]
				cl.objectproperties[op.name] = op
				op.domains[cl.name] = cl
				
		#inherited properties
		for k, cl in ontology.classes.items():
			dprops, oprops = {},{}
			getInheritedProps(cl, dprops, oprops)
				
			cl.dataproperties = dprops
			cl.objectproperties = oprops
					
	def parseIndividuals(self, ontology, elem = None): #TODO: parse multiple object properties!!
		def getElementName(attr):
			if "about" in attr: # name
				return attr["about"]
			return None
		def getIndivDomain(self, elem):
			t, a, e = self.getChildTagAndAttribs(elem, "type")
			if "resource" in a: #classtype
				return a["resource"]
			return None

		if elem == None:
			elem = ontology.xml_tree.getroot()
		tag, attr = self.cleanTagAndAttribs(elem)
		
		name = getElementName(attr)
	
		if tag == "NamedIndividual":
			i = individual()
			i.xml_element = elem
			i.label = name
			i.domain = getIndivDomain(self, elem) # the class of the individual
			if i.domain:
				ontology.classes[i.domain].individuals[i.label] = i
				ontology.individuals[i.label] = i
			
				dprops = ontology.classes[i.domain].dataproperties
				for k, dp in dprops.items():
					t, a, e = self.getChildTagAndAttribs(elem, k) # get the data for the property
					if t:
						i.dataProperties[t] = e.text
						
				oprops = ontology.classes[i.domain].objectproperties
				for k, op in oprops.items(): # for obj properties in class
					t, a, e = self.getChildTagAndAttribs(elem, k) # get the data for the property
					if t and "resource" in a:
						i.objectProperties[t] = a["resource"]
				
		for child in elem.getchildren():
			self.parseIndividuals(ontology, child)

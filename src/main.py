#!/usr/bin/env python

#CAD Segmentation and Classification

from ocad_core import *
import cProfile

if __name__ == "__main__":
	core = ocad_core()
	
	core.start()

	#print "Open testfile"
	
	#f = "../data/dxf/sample.dxf"
	#f = "../data/dxf/ACAD-49301_pl-0_geb-1_fromMEP2010_dxf2010.dxf"
	#f = "../data/dxf/arc_test1.dxf"
	#f = "../data/acad/ACAD-L-Vis-Wohnung.xml"
	#f = "../data/dxf/DXF_for_OntoCAD_Population/BdigitalInstAsBuilt_BDIGITAL DISTRIBUCION - DIN A3.dxf"
	
	#f_owl = "../data/ontologies/knoholem-ont-rdf-xml.owl"
	#f_owl = "../data/ontologies/knoholem-ont-mediatic-rdf-xml.owl"
	#f_owl = "../data/ontologies/knoholem-ont-forum-rdf-xml.owl"

	#**** OntoCAD Showroom ****
	#f = "/home/ontocad/Desktop/DATA/DXF/MediaTIC.dxf"
	#f_owl = "/home/ontocad/Desktop/DATA/OWL/knoholem-ont-rdf-xml.owl"
	
	#testing = True
	
	#if not testing:
		#core.startpage()
	#	core.openLastProject()
	#	pass
	#else:
	#	core.newProject(None)
	#	core.open_cad(f)
	#	core.open_owl(f_owl)
	
	#core.start()


	
#TODO:
# delete the placement objects when deleting indivs
# check if primitives allready parsed to objects, keep track of objects
# display the number and stats of the selected object(s)

# in owl parser, parse Indivs, parse multiple object properties
# create indiv browser

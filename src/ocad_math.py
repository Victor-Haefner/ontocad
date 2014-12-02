#!/usr/bin/env python

from math import sqrt

def sameFl(f1, f2):
	return abs(f1 - f2) < 0.00001

def distSquare(p1, p2):
	dx = p2.x - p1.x
	dy = p2.y - p1.y
	return dx*dx + dy*dy
	 
def squareLength(l):
	return distSquare(l.p1, l.p2)
	
def lineMidPoint(l):
	x = (l.p1.x + l.p2.x) /2
	y = (l.p1.y + l.p2.y) /2
	return point(x,y)  	

def segDot(l1, l2):
	p1 = l1.p2 - l1.p1
	p2 = l2.p2 - l2.p1
	return pntDot(p1, p2)
	
def pntDot(p1, p2):
	return p1.x*p2.x + p1.y*p2.y

#cos of a triangle where the line is the hypotenuse	 
def triCos(l):
	return (l.p1.x - l.p2.x)/sqrt(squareLength(l))

#cos a, with a the angle between the lines
def linesCos(l1, l2):
	return segDot(l1,l2) / sqrt(squareLength(l1)*squareLength(l2))
	
def distPointSegment(p, s):
	#find the point on the segment closest to p
	v = s.p2 - s.p1
	v *= 1.0/s.length # normalize
	d = pntDot(p, v) - pntDot(s.p1, v)
	if d <= 0:
		a = s.p1
	elif d >= s.length:
		a = s.p2
	else:
		a = s.p1 + v*d
	
	_d = a - p	
	return sqrt( pntDot(_d,_d) )

			

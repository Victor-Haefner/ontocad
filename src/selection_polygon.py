#!/usr/bin/env python
from ocad_primitives import point

class selection_polygon(object):
	"""
	Models a set of points representing the selection polygon and provides
	helper function to compute data about it. Instances operate on a
	safe copy of the points.
	"""

	def __init__(self, _points, mirror=True):
		if mirror:
			points = []
			for point in _points:
				s = point[:]
				s.y *= -1
				points.append(s)
			self.points = points
		else:
			self.points = _points

	def close(self):
		"""Returns a new instance after closing the polygon."""
		points = self.points
		points.append(points[0])
		return selection_polygon(points, False)

	def geometricCenter(self):
		"""Calculates the centroid of the polygon."""
		gc = point()
		for p in self.points:
			gc += p
		l = len(self.points)
		gc.x = int(gc.x/l)
		gc.y = int(gc.y/l)
		return gc

	def boundingBox(self):
		"""Calculates the bounding box of the polygon."""
		bbox = [self.points[0][:], self.points[0][:]]
		for p in self.points:
			if p.x < bbox[0].x:
				bbox[0].x = p.x
			if p.y < bbox[0].y:
				bbox[0].y = p.y
			if p.x > bbox[1].x:
				bbox[1].x = p.x
			if p.y > bbox[1].y:
				bbox[1].y = p.y
		return bbox

	def calculateArea(self):
		"""Calculates polygon area with Gaussche Trapezformel."""
		area = 0.0
		for i in range(0, len(self.points)-1):
			pi = self.points[i]
			pi1 = self.points[i+1]

			a = (pi.x + pi1.x)*(pi.y - pi1.y)*0.5
			area += a
		return area

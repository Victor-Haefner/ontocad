#!/usr/bin/env python

import string

import pygtk
pygtk.require('2.0')
import gobject
import gtk
import gtk.gtkgl
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *
import OpenGL.arrays.vbo as glvbo
from numpy import *
from layer import layer
from ocad_primitives import *

class GLlayer():
	def __init__(self, l):
		self.init = False
		self.vbo_points = None
		self.vbo_lines = None
		self.pixelsize = point(0,0)
		self.layer = l
		
	def setPixelSize(self, p):
		self.pixelsize = p
		
	def initVBO(self):		
		points = [None] * len(self.layer.points)
		lines = [None] * 2*len(self.layer.lines)
		arcs = [None] * 4*len(self.layer.arcs)
		arc_tc = [None] * len(arcs)
		arc_a = [None] * len(arcs)
		
		for i,p in enumerate(self.layer.points):
			points[i] = [p.x, p.y]
			
		for i,l in enumerate(self.layer.lines):
			lines[2*i]   = [l.p1.x, l.p1.y]
			lines[2*i+1] = [l.p2.x, l.p2.y]
			
			
		for i,a in enumerate(self.layer.arcs):
			p1 = a.center - a.box*0.5
			p2 = a.center + a.box*0.5
			b = a.box
		
			arcs[4*i]   = [p1.x, p1.y]
			arcs[4*i+1] = [p2.x, p1.y]
			arcs[4*i+2] = [p2.x, p2.y]
			arcs[4*i+3] = [p1.x, p2.y]
			
			arc_tc[4*i] = [-1,-1, b.x, b.y]
			arc_tc[4*i+1] = [1,-1, b.x, b.y]
			arc_tc[4*i+2] = [1,1, b.x, b.y]
			arc_tc[4*i+3] = [-1,1, b.x, b.y]
						
			arc_a[4*i] = [a.a1, a.a2]
			arc_a[4*i+1] = [a.a1, a.a2]
			arc_a[4*i+2] = [a.a1, a.a2]
			arc_a[4*i+3] = [a.a1, a.a2]
			
		self.vbo_points = glvbo.VBO( array(points, 'f') )
		self.vbo_lines  = glvbo.VBO( array(lines , 'f') )
		self.vbo_arcs  = glvbo.VBO( array(arcs , 'f') )
		
		self.vbo_arc_tc = glvbo.VBO( array(arc_tc , 'f') )
		self.vbo_arc_a = glvbo.VBO( array(arc_a , 'f') )
		
		# circle shader
		fp = file("circle.fp", 'r')
		vp = file("circle.vp", 'r')
		fs = shaders.compileShader(fp.read(), GL_FRAGMENT_SHADER)
		vs = shaders.compileShader(vp.read(), GL_VERTEX_SHADER)
		self.circle_shader = shaders.compileProgram(vs,fs)
		# uniforms - TODO
		self.locations = {
			'pixelsize': glGetUniformLocation( self.circle_shader, 'pixelsize' ),
			'angles': glGetAttribLocation( self.circle_shader, 'angles' )
		}
        
		glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)                             
		glEnable (GL_BLEND)                                                   
		glEnable ( GL_LINE_SMOOTH );    
		glEnable( GL_POINT_SMOOTH );                                                 
		glHint (GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
		self.init = True
					
	def paintGL(self):			
		if not self.layer.visible:
			return
		
		if not self.init:
			self.initVBO()
		
		c = self.layer.color
		glColor(c[0], c[1], c[2])
		glLineWidth(self.layer.line_width) 
		glPointSize(self.layer.point_size)
		
		# enable vertex states
		glEnableClientState(GL_VERTEX_ARRAY)
		
		# bind all vbos and draw them
		# draw points
		if len(self.vbo_points) > 0:
			self.vbo_points.bind()
			glVertexPointer(2, GL_FLOAT, 0, self.vbo_points) #define a vertex as a 2D float array
			glDrawArrays(GL_POINTS, 0, len(self.vbo_points)) # draw all points from the VBO
			
		# draw lines
		if len(self.vbo_lines) > 0:
			# check for dotted lines
			if self.layer.line_style == 1:
				glLineStipple(3, 0x9999);  # [1]
				glEnable(GL_LINE_STIPPLE);
			self.vbo_lines.bind()
			glVertexPointer(2, GL_FLOAT, 0, self.vbo_lines) #define a vertex as a 2D float array
			glDrawArrays(GL_LINES, 0, len(self.vbo_lines)) # draw all points from the VBO
		
		# draw arcs - via special fragment shader
		if len(self.vbo_arcs) > 0:
			self.vbo_arcs.bind()
			glVertexPointer(2, GL_FLOAT, 0, self.vbo_arcs)
		
			# enable texture coords
			glClientActiveTexture(GL_TEXTURE0)
			glEnableClientState(GL_TEXTURE_COORD_ARRAY)
			self.vbo_arc_tc.bind()
			glTexCoordPointer(4, GL_FLOAT, 0, self.vbo_arc_tc);
		
			#arc angles
			self.vbo_arc_a.bind()
			glEnableVertexAttribArray(self.locations['angles']);
			glVertexAttribPointer(self.locations['angles'],2,GL_FLOAT, GL_FALSE, 0, self.vbo_arc_a)
		
			glUseProgram(self.circle_shader)
			glUniform2f( self.locations['pixelsize'], self.pixelsize.x, self.pixelsize.y)
		
			glDrawArrays(GL_QUADS, 0, len(self.vbo_arcs))
		
			# drop current programs and states
			glUseProgram(0)
			glDisableClientState(GL_TEXTURE_COORD_ARRAY)
			
		glDisableClientState(GL_VERTEX_ARRAY)
		glDisableVertexAttribArray(0);
		
		if len(self.vbo_lines) > 0:
			if self.layer.line_style == 1:
				glDisable(GL_LINE_STIPPLE);

class GlViewer():
	# This is just a container class to hold all the GL stuff in one place.
	def __init__(self):
		self.initializeGL()
		self.layers = {}
		
		self.offset = None
		self.size = None
		self.resize = None
		self.pixelsize = None
		
		self.drag = False
		self.drag_pnt = None
		self.drag_off = None
		self.drag_siz = None
		
		self.wsize = point(0,0)

	def initializeGL(self):
		pass
	
	def paintGL(self):
		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT)
		for l in self.layers:
			self.layers[l].paintGL()

	def rescale(self, s):
		s = s[:]
				
		if (self.wsize.x <= 0):
			self.wsize.x = 1
		if (self.wsize.y <= 0):
			self.wsize.y = 1
			
		# window ratio and world ratio
		r = float(self.wsize.y)/self.wsize.x 
		w = float(s.y)/s.x
		
		if r <= 1:
			s.x /= r
			s.y /= w
		else:
			s.x *= w
			s.y *= r
			
		# pixel size in world dimensions
		self.pixelsize = point(s.x/self.wsize.x, s.y/self.wsize.y) # test if move to top needed
		
		return s

	def resizeGL(self, w = None, h = None):
		if w:
			self.wsize = point(w,h)
		else:
			w = self.wsize.x
			h = self.wsize.y
		
		if self.offset == None:
			return
		
		if h == 0: h = 1 # Prevent divide by 0 errors.

		# paint within the whole window
		glViewport(0, 0, w, h)
		# set orthographic projection (2D only)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		
		o = self.offset
		s = self.size - self.offset
		
		# window ratio and world ratio
		rs = self.rescale(s)
		glOrtho(o.x, o.x+rs.x, o.y + (s.y - rs.y), o.y+s.y, -1, 1)
		self.resize = rs
		
		for l in self.layers:
			self.layers[l].setPixelSize(self.pixelsize)

	def showAll(self):
		o = None
		s = None
		#o = self.offset
		#s = self.size
		for l_key in self.layers:
			l = self.layers[l_key].layer
			
			if l.offset == None:
				continue
				
			if o == None:
				o = l.offset[:]
				s = l.size[:]
				continue
				
			o.x = min(o.x, l.offset.x)
			o.y = min(o.y, l.offset.y)
			
			s.x = max(s.x, l.size.x)
			s.y = max(s.y, l.size.y)
		
		#square region
		d = s - o
		d.x = max(d.x, d.y)
		d.y = d.x
		s = o + d
			
		self.offset = o
		self.size = s
		self.resizeGL(self.wsize.x, self.wsize.y)
				
	def zoom(self, z):
		o = self.offset
		s = self.size - self.offset
		
		o += (s - s*z) *0.5
		s *= z
		
		self.offset = o
		self.size = s + o
		self.resizeGL()
	
	def imgToWorld(self, pos):
		d = self.size - self.offset
		rs = self.resize
		
		pos.x *= float(rs.x)/self.wsize.x
		pos.y = d.y - pos.y*float(rs.y)/self.wsize.y
					
		return self.offset + pos
		
	def startDrag(self, pos):
		self.drag = True
		self.drag_pnt = pos
		self.drag_off = self.offset
		self.drag_siz = self.size
		
	def stopDrag(self):
		self.drag = False
		
	def updateDrag(self, pos):
		if not self.drag:
			return
		
		rs = self.resize
		
		# displacement
		dp = pos - self.drag_pnt
		tmp = dp[:]
		dp.x *= float(rs.x)/self.wsize.x
		dp.y *= -1*float(rs.y)/self.wsize.y
		
		# apply
		self.offset = self.drag_off - dp
		self.size = self.drag_siz - dp
		self.resizeGL()
							
class GtkGlDrawingArea(gtk.gtkgl.DrawingArea):
	def __init__(self):

		# Create an double buffered RGB mode with depth checking.
		glconfig = gtk.gdkgl.Config(mode = (gtk.gdkgl.MODE_RGB |
												 gtk.gdkgl.MODE_DOUBLE |
												 gtk.gdkgl.MODE_DEPTH))
												 
		# Associate GL with this specific GTK window.
		super(GtkGlDrawingArea, self).__init__(glconfig)
		
		# Allocate the GL guts and gore.
		self.gl = GlViewer()

		# draw events
		self.connect('configure_event', self.resize_cb) 	# resize event
		self.connect('expose_event', self.expose_cb)		# expose event
		
		# mouse events		
		self.connect('scroll-event', self.scroll_event)
		self.connect('motion-notify-event', self.motion_notify_event)
		self.connect('button-press-event', self.button_press_event)
		self.connect('button-release-event', self.button_release_event)
		
		self.set_events(gtk.gdk.EXPOSURE_MASK
						| gtk.gdk.LEAVE_NOTIFY_MASK
						| gtk.gdk.BUTTON_PRESS_MASK
						| gtk.gdk.BUTTON_RELEASE_MASK
						| gtk.gdk.POINTER_MOTION_MASK
						| gtk.gdk.POINTER_MOTION_HINT_MASK)

	def button_release_event(self, w1, w2):
		if w2.button == 1: #stop drag
			self.gl.stopDrag()
		
	def button_press_event(self, w1, w2):
		if w2.button == 1: #start drag
			self.gl.startDrag(point(w2.x, w2.y))
		
	def motion_notify_event(self, w1, w2):
		if self.gl.drag:
			self.gl.updateDrag(point(w2.x, w2.y))
			self.redraw()
				
	def scroll_event(self, w1, w2):
		#scale
		f = 1.0
		if w2.direction == gtk.gdk.SCROLL_DOWN:
			f = 0.9
		if w2.direction == gtk.gdk.SCROLL_UP:
			f = 1.1
			
		self.gl.zoom(f)
			
		w = self.gl.wsize.x
		h = self.gl.wsize.y
			
		self.gl.resizeGL(w,h)
		self.redraw()

	def expose_cb(self, gl_area, event):		
		gc = gl_area.get_gl_context()
		drawable = gl_area.get_gl_drawable()
		
		if not drawable.gl_begin(gc): return
		
		self.gl.paintGL()
		drawable.swap_buffers()
		drawable.gl_end()
		return True

	def resize_cb(self, gl_area, event):
		gc = gl_area.get_gl_context()
		drawable = gl_area.get_gl_drawable()
		
		if not drawable.gl_begin(gc): return

		x, y, width, height = gl_area.get_allocation()
		self.gl.resizeGL(width, height)

		drawable.gl_end()

		return True

	def redraw(self):
		if (self.window):
			self.window.invalidate_rect(self.allocation, False)
			self.window.process_updates(False)
			return True
		return False
		
	def addLayer(self, l):
		self.gl.layers[l.name] = GLlayer(l)

	def remLayer(self, name):
		if name in self.gl.layers:
			del self.gl.layers[name]

	def clear(self):
		self.gl.layers = {}
	
	def showAll(self, b = None):
		self.gl.showAll()
		self.redraw()
	

class ApplicationMainWindowDemo(gtk.Window):
	def __init__(self, parent=None):
		# Create the toplevel window
		gtk.Window.__init__(self)
		#self.set_screen(parent.get_screen())

		self.set_title("GLTest")
		self.set_default_size(200, 200)

		area = GtkGlDrawingArea()
		self.add(area)

		area.grab_focus()
		
		
		
		#testlayer
		l1 = layer("testlayer")
		l2 = layer("testlayer2")
		
		l1.color = array([1,0,1])
		l2.color = array([1,1,0])
		
		l1.addLine(line(0, 0,  0.5, 0.5))
		l2.addLine(line(0, 0, -0.5, 0.5))
		l1.addPoint(point(-0.5, -0.5))
		l2.addPoint(point(-0.5, -0.4))
		
		l1.addArc( arc(0,0,0.3) )
		
		area.addLayer(l1)
		area.addLayer(l2)
		
		self.show_all()
		area.showAll()

def main():
	print "Press <ESC> to exit demo"
	ApplicationMainWindowDemo()
	gtk.main()

if __name__ == '__main__':
	main()

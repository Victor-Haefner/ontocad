#!/usr/bin/env python

import gtk
import cairo

class gtkviewer(gtk.DrawingArea):
	def __init__( self, data):
		gtk.DrawingArea.__init__(self)
		self.data = data
		self.connect('expose-event', self._do_expose)
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
		
		#pixbuf that is drawn on the screen
		self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 32, 32)#resize autam. to window
		self.pixbuf.fill(0xffffffff)
		self.ref_pixbuf = None #cached full image
		
		self.scale = 1.0
		self.offset = [0.0, 0.0]
		self.zoffset = [0.0, 0.0]
		self.drag = False
		self.drag_pnt = [0.0, 0.0]
		self.drag_off = [0.0, 0.0]
		
		self.show_all = False

	def _do_expose(self, widget, event):
		w,h = widget.window.get_size()
		if w <= 1 or h <= 1:
			return
		self.transform(w,h)
		widget.window.draw_pixbuf(widget.get_style().fg_gc[gtk.STATE_NORMAL], self.pixbuf, 0, 0, 0, 0)
		
	def init(self, w, h):
		#create empty pixbuf and pixmap to draw on
		p = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h)
		p.fill(0xffffffff)
		self.set_pixbuf(p)
		
	#put the data on the drawing area
	def transform(self, w, h):# w,h the window size
		#show all job
		if self.ref_pixbuf == None:
			return
		if self.pixbuf == None:
			return
		
		if self.show_all:
			self.show_all = False
			sw = float(w) / self.ref_pixbuf.get_width()
			sh = float(h) / self.ref_pixbuf.get_height()
			if sw < sh:
				self.scale = sw
			else :
				self.scale = sh
			self.offset = [0,0]
			self.zoffset = [0,0]
			
		#data
		o = self.offset
		zo = self.zoffset
		s = self.scale
		pwh = [self.pixbuf.get_width(), self.pixbuf.get_height()]
		rpwh = [self.ref_pixbuf.get_width(), self.ref_pixbuf.get_height()]
		
		#resize pixbuf if needed
		if pwh[0] != w or pwh[1] != h:
			self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h)
			
		self.pixbuf.fill(0x888888ff)
		
		#actual offset
		of = [int(o[0]*s+zo[0]), int(o[1]*s+zo[1])]
		of_src = of[:]
		
		#clamp to viewport
		if of[0] > w:
			of[0] = w
		if of[1] > h:
			of[1] = h
			
		if of[0] < 0:
			of[0] = 0
		if of[1] < 0:
			of[1] = 0
			
		#actual width and height
		wh = [int(rpwh[0]*s)+1, int(rpwh[1]*s)+1]
		
		#clamp to viewport
		if of_src[0] < 0:
			wh[0] += of_src[0]
		if of_src[1] < 0:
			wh[1] += of_src[1]
			
		if wh[0] < 0:
			wh[0] = 0
		if wh[1] < 0:
			wh[1] = 0
			
		if wh[0]+of[0] > w:
			wh[0] = w - of[0]
		if wh[1]+of[1] > h:
			wh[1] = h - of[1]
			
		self.ref_pixbuf.scale(self.pixbuf, of[0], of[1], wh[0], wh[1], of_src[0], of_src[1], s, s, gtk.gdk.INTERP_TILES)
		
	def get_pixbuf(self):
		return self.ref_pixbuf
		
	def set_pixbuf(self, pixbuf):
		self.ref_pixbuf = pixbuf
		self.showAll()
		self.queue_draw()
		
	def store_pixbuf(self): # copy the pixbuf and store a ref in data
		_p = self.get_pixbuf()
		w = _p.get_width()
		h = _p.get_height()
		p = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h)
		_p.copy_area(0, 0, w, h, p, 0, 0)
		self.data.reference_image = p
		
	def clear(self):
		self.set_pixbuf(None)
		
	def damage_pixels(self, rect):
		self.queue_draw_area(rect[0], rect[1], rect[2], rect[3])
		
	def button_release_event(self, w1, w2):
		if w2.button == 1: #stop drag
			self.drag = False
			#print "drop"
		
	def button_press_event(self, w1, w2):
		s = self.scale
		o = self.offset
		if w2.button == 1: #start drag
			self.drag = True
			self.drag_pnt = [w2.x, w2.y]
			self.drag_off = [s*o[0], s*o[1]]
			#print "drag"
		
	def motion_notify_event(self, w1, w2):
		s = self.scale
		o = self.offset
		dp = self.drag_pnt
		do = self.drag_off
		if self.drag:
			o[0] = (do[0] + w2.x - dp[0]) /s
			o[1] = (do[1] + w2.y - dp[1]) /s
			self.queue_draw()
				
	def scroll_event(self, w1, w2):
		#scale
		f = 1.0
		if w2.direction == gtk.gdk.SCROLL_DOWN:
			f = 0.9
		if w2.direction == gtk.gdk.SCROLL_UP:
			f = 1.1
			
		w = self.pixbuf.get_width()
		h = self.pixbuf.get_height()
		#x = w2.x
		#y = w2.y
		x = w/2
		y = h/2
		s = self.scale
			
			
		#offset
		dx = s*x*(f-1)
		dy = s*y*(f-1)
		self.zoffset[0] = self.zoffset[0] - dx
		self.zoffset[1] = self.zoffset[1] - dy
		
		self.scale = self.scale*f
			
		self.queue_draw()
				
	def showAll(self):
		self.show_all = True
		self.queue_draw()

'''
Created on Oct 18, 2014

@author: jan
'''
import time, threading
import tmb_module, tmb_main
import logging
import collections
import Queue
import numpy as np
from array import array

use_ledmodule = True
try:
	from neopixel import *
except ImportError:
	logging.exception("Error importing neopixel!")
	use_ledmodule = False
	


class LedThread(threading.Thread):
	'''
	classdocs
	'''

	def __init__(self, strip):
		'''
		Constructor
		'''
		threading.Thread.__init__(self)
		
		self._loop = True
		self._strip = strip
		self._showStrip = False

		self._ledColor = [[]] * self._strip.numPixels()

		self.tasks = Queue.Queue()

	@property
	def loop(self):
		return self._loop
	
	@loop.setter
	def loop(self, value):
		self._loop = value

	def addTask(self, task):
		self.tasks.put_nowait(task)

	def _clampToColor(self, r, g, b):

		return Color(
			max(0, min(255, r)),
			max(0, min(255, g)),
			max(0, min(255, b))
			)

	def _fadeColor(self, colorBegin, colorEnd, steps):
		if colorBegin == colorEnd:
			return []

		rgbBegin = np.array([(colorBegin >> 16) & 0xFF,
			(colorBegin >> 8) & 0xFF,
			colorBegin & 0xFF])

		rgbEnd = np.array([(colorEnd >> 16) & 0xFF,
			(colorEnd >> 8) & 0xFF,
			colorEnd & 0xFF])

		rgbDir = (rgbEnd - rgbBegin) / steps

		colorSteps = [0] * steps
		for i in range(steps):
			step = rgbBegin + (rgbDir * i)
			colorSteps[i] = self._clampToColor(*step)

		''' return in reverse order '''
		colorSteps.reverse()
		return colorSteps

	def _pulseColor(self, color, steps):
		rgbBegin = np.array([(color >> 16) & 0xFF,
			(color >> 8) & 0xFF,
			color & 0xFF])

		rgbDir = rgbBegin / steps

		colorSteps = [0] * (steps * 2)
		for i in range(steps):
			step = rgbBegin - (rgbDir * i)
			colorSteps[i] = colorSteps[i] = self._clampToColor(*step)

			colorSteps[((steps * 2) - i) - 1] = colorSteps[i]

		return colorSteps


	def fade(self, led, color, steps):
		self._ledColor[led] = self._fadeColor(self._strip.getPixelColor(led), color, steps)

	def pulse(self, led, steps):
		self._ledColor[led] = self._pulseColor(self._strip.getPixelColor(led), steps)

	def _updateLed(self):
		for i in range(self._strip.numPixels()):
			led = self._ledColor[i]
			if len(led) > 0:
				self._strip.setPixelColor(i , led.pop())
				self._showStrip = True
			

	def _process(self, task):
		if task['target'] == 'strip':
			exec('self._strip.' + task['function'])
			self._showStrip = True

		if task['target'] == 'self':
			func = getattr(self, task['function'])
			func(*task['arguments'])

	def run(self):
		self._strip.begin()
		self.loop = True
		while self.loop:
			
			try:
				while self.loop:
					task = self.tasks.get_nowait()
					self._process(task)

			except Queue.Empty:
				pass					
			self._updateLed()

			if self._showStrip:
				self._strip.show()
				self._showStrip = False

			time.sleep(1/100.0)	
				

class LedModule(tmb_module.TMB_Module):
	
	def __init__(self, config):
		'''
		Constructor
		'''
		tmb_module.TMB_Module.__init__(self, config)
		
		self._count = config.getint('led', 'count')
		self._pin = config.getint('led', 'pin')
		self._frequenz = config.getint('led', 'frequenz')
		self._dma = config.getint('led', 'dma')
		self._invert = config.getboolean('led', 'invert')
		self._strip = None
		
		self._ledmapping = {}
		for i in range(self._count):
			section = 'input_{0}'.format(i)
			name = config.get(section, 'name')
			self._ledmapping[name] = i

		self._led = 0
		self._color = 0
				
	def start(self):
		tmb_module.TMB_Module.start(self)
		
		if not use_ledmodule:
			return

		self._strip = Adafruit_NeoPixel(self._count, self._pin, self._frequenz, self._dma, self._invert)
		self._thread = LedThread(self._strip)

		''' initialize led '''
		
		for i in range(self._count):
			self.setLedColor(i, (Color(255,255,255) / self._count) * i )
		
		
		self._thread.start()
		
	def stop(self):
		if use_ledmodule:
			self._thread.loop = False
			self._thread.join()
		
		tmb_module.TMB_Module.stop(self)

	def update(self):
		tmb_module.TMB_Module.update(self)

	def setBrightness(self, brightness):
		if use_ledmodule:
			self._thread.addTask(dict(target = 'strip', function = 'setBrightness({})'.format(brightness)))

	def setLedColorRGB(self, led, r, g, b):
		self.setLedColor(led, Color(r, g, b))

	def setLedColor(self, led, color):
		if led in self._ledmapping:
			mappedLed = self._ledmapping[led]
			if use_ledmodule:
				self._thread.addTask(dict(target = 'strip', function = 'setPixelColor({}, {})'.format(mappedLed, color)))

	def setFadeLedColorRGB(self, led, r, g, b, steps = 15):
		self.setFadeLedColor(led, Color(r, g, b), steps)

	def setFadeLedColor(self, led, color, steps = 15):
		if led in self._ledmapping:
			mappedLed = self._ledmapping[led]
			if use_ledmodule:
				self._thread.addTask(dict(
										target = 'self', 
										function = 'fade',
										arguments = [led, color, steps]
										)
									)

	def pulse(self, led, steps = 15):
		if use_ledmodule:
			self._thread.addTask(dict(
				target = 'self', 
				function = 'pulse',
				arguments = [led, steps]
				)
			)

	def show(self):
		if use_ledmodule:
			self._thread.addTask(dict(target = 'strip', function = 'show()'))

		
		 
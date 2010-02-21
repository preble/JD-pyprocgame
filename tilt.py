import procgame
from procgame import *

class Tilt(game.Mode):
	"""docstring for Bonus"""
	def __init__(self, game, priority, font_big, font_small, tilt_sw='None', slam_tilt_sw='None'):
		super(Tilt, self).__init__(game, priority)
		self.font_big = font_big
		self.font_small = font_small
		self.text_layer = dmd.TextLayer(128/2, 7, font_big, "center")
		if tilt_sw != 'None':
			self.add_switch_handler(name=tilt_sw, event_type='inactive', delay=None, handler=self.tilt_handler)
		if slam_tilt_sw != 'None':
			self.add_switch_handler(name=slam_tilt_sw, event_type='inactive', delay=None, handler=self.slam_tilt_handler)
		self.num_tilt_warnings = 0

	def mode_started(self):
		self.times_warned = 0
		self.layer = None

	def tilt_handler(self, sw):
		if self.times_warned == self.num_tilt_warnings:
			self.game.sound.play('tilt')
			self.text_layer.set_text('TILT')
			self.tilt_callback()
		else:
			self.times_warned += 1
			self.game.sound.play('tilt_warning')
			self.text_layer.set_text('Warning',3)
		self.layer = dmd.GroupedLayer(128, 32, [self.text_layer])

	def slam_tilt_handler(self, sw):
		self.game.sound.play('slam_tilt')
		self.text_layer.set_text('SLAM TILT')
		self.slam_tilt_callback()
		self.layer = dmd.GroupedLayer(128, 32, [self.text_layer])


import procgame
import locale
import time
from procgame import *
import os.path
import random

sound_path = "./games/jd/sound/FX/"
voice_path = "./games/jd/sound/Voice/boring/"

class Boring(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Boring, self).__init__(game, priority)
		#filename = 'jd - its way too quiet.wav'
		#self.game.sound.register_sound('boring', voice_path+filename)
		filename = 'jd - this is boring.wav'
		self.game.sound.register_sound('boring', voice_path+filename)
		#filename = 'lets order a pizza.wav'
		#self.game.sound.register_sound('boring', voice_path+filename)
		filename = 'wake me when something happens.wav'
		self.game.sound.register_sound('boring', voice_path+filename)
		self.enable_reset = False
	
	def mode_started(self):
		self.delay(name='timer', event_type=None, delay=20, handler=self.timer_expired)
	def mode_stopped(self):
		self.cancel_delayed('timer')

	def timer_expired(self):
		self.delay(name='timer', event_type=None, delay=8, handler=self.timer_expired)
		self.game.sound.play('boring')

	def pause(self):
		self.cancel_delayed('timer')

	def reset(self):
		self.cancel_delayed('timer')
		self.mode_started()
		
	def sw_subwayEnter2_active(self, sw):
		self.reset()

	def sw_rightRampExit_active(self, sw):
		self.reset()

	def sw_leftRampExit_active(self, sw):
		self.reset()

	def sw_popperR_active_for_1s(self, sw):
		self.pause()
		self.enable_reset = True

	def sw_popperR_inactive_for_1s(self, sw):
		if (self.enable_reset):
			self.reset()
			self.enable_reset = False

	def sw_popperL_active_for_1s(self, sw):
		self.pause()
		self.enable_reset = True

	def sw_popperL_inactive_for_1s(self, sw):
		if (self.enable_reset):
			self.reset()
			self.enable_reset = False

	def sw_shooterL_active_for_1s(self, sw):
		self.pause()
		self.enable_reset = True

	def sw_shooterL_inactive_for_1s(self, sw):
		if (self.enable_reset):
			self.reset()
			self.enable_reset = False

	def sw_shooterR_active(self, sw):
		self.pause()

	def sw_shooterR_active(self, sw):
		self.pause()

	def sw_shooterR_inactive_for_1s(self, sw):
		self.reset()

	def sw_leftRollover_active(self, sw):
		self.reset()

	def sw_outlaneR_active(self, sw):
		self.reset()

	def sw_outlaneL_active(self, sw):
		self.reset()

	def sw_craneRelease_active(self,sw):
		self.reset()

	def sw_leftRampToLock_active(self, sw):
		self.reset()

	def sw_trough1_active(self, sw):
		self.reset()

	def sw_trough6_active(self, sw):
		self.reset()

	def sw_dropTargetJ_active(self, sw):
		self.reset()

	def sw_dropTargetU_active(self, sw):
		self.reset()

	def sw_dropTargetD_active(self, sw):
		self.reset()

	def sw_dropTargetG_active(self, sw):
		self.reset()

	def sw_dropTargetE_active(self, sw):
		self.reset()
	

import procgame
from procgame import *
from random import *

class Missile_Award_Mode(game.Mode):
	"""docstring for Bonus"""
	def __init__(self, game, priority, font):
		super(Missile_Award_Mode, self).__init__(game, priority)
		self.font = font
		self.title_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.element_layer = dmd.TextLayer(128/2, 15, font, "center")
		self.value_layer = dmd.TextLayer(128/2, 22, font, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.title_layer,self.element_layer, self.value_layer])
		self.awards = ['Light Extra Ball', 'Advance Crimescenes', '30000 Points', 'Bonus X+1', 'Hold Bonus X']
		self.awards_allow_repeat = [False, True, True, True, False]
		self.awards_remaining = self.awards[:]
		self.delay_time = 0.200
		self.award_ptr = 0
		self.award_ptr_adj = 0
		self.title_layer.set_text("Missile Award")
		self.element_layer.set_text("Left Fire btn collects:")
		self.active = False

	def mode_started(self):
		self.rotate_awards()
		self.delay(name='update', event_type=None, delay=self.delay_time, handler=self.update)
		self.timer = 70
		self.active = False
		

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.awards_remaining = info_record['awards_remaining']
		else:
			self.swards_remaining = self.awards

	def get_info_record(self):
		info_record = {}
		info_record['awards_remaining'] = self.awards_remaining
		return info_record


	def sw_fireL_active(self, sw):
		self.timer = 3

	def update(self):
		if self.timer == 0:
			self.active = False
			self.game.modes.remove(self)
		elif self.timer == 3:
			self.game.coils.shooterL.pulse()
			self.award()
			self.delay(name='update', event_type=None, delay=self.delay_time, handler=self.update)
			self.timer -= 1
		else:
			self.active = True
			self.delay(name='update', event_type=None, delay=self.delay_time, handler=self.update)
			if self.timer > 10:
				self.rotate_awards()
			self.timer -= 1

	def award(self):
		self.callback(self.current_award)
		if not self.awards_allow_repeat[self.award_ptr_adj]:
			self.awards_remaining[self.award_ptr_adj] = str(10000*(self.award_ptr_adj + 1)) + ' Points'
		
	def rotate_awards(self):
		self.award_ptr += randint(0,4)
		self.award_ptr_adj = self.award_ptr% len(self.awards_remaining)
		self.current_award = self.awards_remaining[self.award_ptr_adj]
		self.value_layer.set_text(self.current_award)
		

import procgame
from procgame import *

class Bonus(game.Mode):
	"""docstring for Bonus"""
	def __init__(self, game, priority, font_big, font_small):
		super(Bonus, self).__init__(game, priority)
		self.font_big = font_big
		self.font_small = font_small
		self.title_layer = dmd.TextLayer(128/2, 7, font_big, "center")
		self.element_layer = dmd.TextLayer(128/2, 7, font_small, "center")
		self.value_layer = dmd.TextLayer(128/2, 20, font_small, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.title_layer,self.element_layer, self.value_layer])
		self.timer = 0
		self.delay_time = 1

	def compute(self, base, x, exit_function):
		self.exit_function = exit_function
		self.elements = []
		self.value = []
		print "base"
		print base
		for element, value in base.iteritems():
			self.elements.append(element)
			self.value.append(value)
		self.x = x
		self.delay(name='bonus_computer', event_type=None, delay=self.delay_time, handler=self.bonus_computer)
		self.title_layer.set_text('BONUS:',self.delay_time)
		self.total_base = 0

	def bonus_computer(self):
		self.title_layer.set_text('')
		self.element_layer.set_text(self.elements[self.timer])
		self.value_layer.set_text(str(self.value[self.timer]))
		self.total_base += self.value[self.timer]
		self.timer += 1

		if self.timer == len(self.elements) or len(self.elements) == 0:
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
			self.timer = 0
		else:
			self.delay(name='bonus_computer', event_type=None, delay=self.delay_time, handler=self.bonus_computer)

	def bonus_finish(self):
		if self.timer == 0:
			self.element_layer.set_text('Total Base:')
			self.value_layer.set_text(str(self.total_base))
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		elif self.timer == 1:
			self.element_layer.set_text('Multiplier:')
			self.value_layer.set_text(str(self.x))
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		elif self.timer == 2:
			total_bonus = self.total_base * self.x
			self.element_layer.set_text('Total Bonus:')
			self.value_layer.set_text(str(total_bonus))
			self.game.score(total_bonus)
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		else:
			self.exit_function()
		self.timer += 1

	def sw_flipperLwL_active(self, sw):
		if self.game.switches.flipperLwR.is_active():
			self.delay_time = 0.250

	def sw_flipperLwR_active(self, sw):
		if self.game.switches.flipperLwL.is_active():
			self.delay_time = 0.250


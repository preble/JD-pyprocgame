from procgame import *

class AirRade(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(AirRade, self).__init__(game, priority)
		self.banner_layer = dmd.TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.instruction_layer_1 = dmd.TextLayer(128/2, 7, self.game.fonts['tiny7'], "center")
		self.instruction_layer_2 = dmd.TextLayer(128/2, 20, self.game.fonts['tiny7'], "center")
		self.award_layer_1 = dmd.TextLayer(1, 12, self.game.fonts['tiny7'], "left")
		self.award_layer_2 = dmd.TextLayer(127, 12, self.game.fonts['tiny7'], "right")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
		self.time = 0
		self.awards = ['award1','award2']
	
	def mode_started(self):
		self.time = 0
		self.banner_layer.set_text("Pick-A-Prize")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
		# Disable the flippers
		self.game.enable_flippers(enable=False)
		self.selection_made = False
		self.selection_enabled = False

		self.delay(name='selector_timer', event_type=None, delay=2.0, handler=self.progress)
		self.state = 'intro'

	def mode_stopped(self):
		# Enable the flippers
		self.game.enable_flippers(enable=True)

	def sw_flipperLwL_active(self,sw):
		if self.game.switches.flipperLwR.is_active() and not self.state == 'choices':
			self.progress()
		if self.selection_enabled and not self.selection_made:
			self.selection_made = True
			self.finish_award(0)

	def sw_flipperLwR_active(self,sw):
		if self.game.switches.flipperLwL.is_active() and not self.state == 'choices':
			self.progress()
		if self.selection_enabled and not self.selection_made:
			self.selection_made = True
			self.finish_award(1)

	def progress(self):
		self.cancel_delayed('selector_timer')
		if self.state == 'intro':
			self.show_instructions()
		elif self.state == 'instructions':
			self.show_choices()
		elif self.state == 'choices':
			self.finish_award(0)
		elif self.state == 'finish':
			self.exit()

	def show_instructions(self):
		self.state = 'instructions'
		self.instruction_layer_1.set_text("Select award")	
		self.instruction_layer_2.set_text("with flipper buttons")	
		self.layer = dmd.GroupedLayer(128, 32, [self.instruction_layer_1, self.instruction_layer_2])
		self.delay(name='selector_timer', event_type=None, delay=2.0, handler=self.progress)

	def show_choices(self):
		self.state = 'choices'
		self.award_layer_1.set_text(self.awards[0])
		self.award_layer_2.set_text(self.awards[1])
		self.layer = dmd.GroupedLayer(128, 32, [self.award_layer_1, self.award_layer_2])
		self.delay(name='selector_timer', event_type=None, delay=8.0, handler=self.progress)
		self.delay(name='selector_enabler', event_type=None, delay=0.1, handler=self.selector_enabler)

	def selector_enabler(self):
		self.selection_enabled = True
			

	def finish_award(self, choice):
		self.state = 'finish'
		self.selection = choice;
		self.instruction_layer_1.set_text("Selection:")	
		self.instruction_layer_2.set_text(self.awards[choice])	
		self.delay(name='award_exit_delay', event_type=None, delay=2.0, handler=self.progress)
		self.layer = dmd.GroupedLayer(128, 32, [self.instruction_layer_1, self.instruction_layer_2])
		self.cancel_delayed('selector_timer')


	def exit(self):
		self.callback(self.awards[self.selection])

	

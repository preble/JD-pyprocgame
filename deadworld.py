import procgame
from procgame import *

class Deadworld(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, deadworld_mod_installed):
		super(Deadworld, self).__init__(game, priority)
		self.deadworld_mod_installed = deadworld_mod_installed
		self.lock_enabled = 0
		self.num_balls_locked = 0
		self.num_player_balls_locked = 0
		self.num_balls_to_eject = 0
		self.ball_eject_in_progress = 0
		self.performing_ball_search = 0
		self.add_switch_handler(name='globePosition2', event_type='active', delay=None, handler=self.crane_activate)
	
	def mode_started(self):
		pass

	def mode_stopped(self):
		self.game.coils.globeMotor.disable()

	def initialize(self, lock_enabled=0, num_player_balls_locked=0):
		self.lock_enabled = lock_enabled
		self.num_player_balls_locked = num_player_balls_locked
		if self.lock_enabled or self.num_player_balls_locked > 0:
			self.game.coils.globeMotor.pulse(0)

	def enable_lock(self):
		self.lock_enabled = 1
		self.game.coils.globeMotor.pulse(0)

	def disable_lock(self):
		self.lock_enabled = 0

	def sw_leftRampToLock_active(self, sw):
		if self.deadworld_mod_installed:
			self.num_balls_locked += 1
			#self.game.set_status("balls locked: " + str(self.num_balls_locked))

	def eject_balls(self,num):
		if not self.num_balls_to_eject:
			self.perform_ball_eject()
		self.num_balls_to_eject += num
		self.ball_eject_in_progress = 1
		
	def perform_ball_search(self):
		self.performing_ball_search = 1
		self.perform_ball_eject()
		self.ball_eject_in_progress = 1

	def perform_ball_eject(self):
		self.game.coils.globeMotor.pulse(0)
		if self.deadworld_mod_installed:
			switch_num = self.game.switches['globePosition2'].number
			self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)

	def sw_craneRelease_active(self,sw):
		if not self.performing_ball_search:
			self.num_balls_to_eject -= 1
			self.num_balls_locked -= 1
			
		
	def sw_magnetOverRing_open(self,sw):
		if self.ball_eject_in_progress:
			self.game.coils.craneMagnet.pulse(0)
			self.delay(name='crane_release', event_type=None, delay=2, handler=self.crane_release)

	def crane_release(self):
		self.game.coils.crane.disable()
		self.game.coils.craneMagnet.disable()
		self.performing_ball_search = 0
		self.delay(name='crane_release_check', event_type=None, delay=1, handler=self.crane_release_check)


	def crane_release_check(self):
		if self.num_balls_to_eject > 0:
			self.perform_ball_eject()
		else:
			if self.num_balls_locked > 0:
				self.game.coils.globeMotor.pulse(0)
			self.ball_eject_in_progress = 0
			switch_num = self.game.switches['globePosition2'].number
			self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, False)

	def crane_activate(self,sw):
		if self.ball_eject_in_progress:
			self.game.coils.crane.pulse(0)

	def get_num_balls_locked(self):
		return self.num_balls_locked - self.num_balls_to_eject


class DeadworldTest(service.ServiceModeSkeleton):
	"""Coil Test"""
	def __init__(self, game, priority, font):
		super(DeadworldTest, self).__init__(game, priority, font)
		self.name = "Deadworld Test"
		self.title_layer = dmd.TextLayer(1, 1, font, "left")
		self.globe_layer = dmd.TextLayer(1, 9, font, "left")
		self.arm_layer = dmd.TextLayer(1, 17, font, "left")
		self.magnet_layer = dmd.TextLayer(1, 25, font, "left")
		self.layer = dmd.GroupedLayer(128, 32, [self.title_layer, self.globe_layer, self.arm_layer, self.magnet_layer])

		self.title_layer.set_text(self.name)
		self.globe_layer.set_text('Start BTN: Globe: Off')
		self.arm_layer.set_text('SuperGame BTN: Crane: Off')
		self.magnet_layer.set_text('Buy-In BTN: Magnet: Off')

	def mode_started(self):
		super(DeadworldTest, self).mode_started()
		self.game.coils.globeMotor.disable()
		self.game.coils.crane.disable()
		self.game.coils.craneMagnet.disable()
		self.globe_state = False
		self.crane_state = False
		self.magnet_state = False
		self.globe_layer.set_text('Start BTN: Globe: Off')
		self.arm_layer.set_text('SuperGame BTN: Crane: Off')
		self.magnet_layer.set_text('Buy-In BTN: Magnet: Off')
		self.game.lamps.startButton.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)
		self.game.lamps.superGame.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)
		self.game.lamps.buyIn.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)

	def mode_stopped(self):
		self.game.coils.globeMotor.disable()
		self.game.coils.crane.disable()
		self.game.coils.craneMagnet.disable()
		self.globe_state = False
		self.crane_state = False
		self.magnet_state = False
		self.globe_layer.set_text('Start BTN: Globe: Off')
		self.arm_layer.set_text('SuperGame BTN: Crane: Off')
		self.magnet_layer.set_text('Buy-In BTN: Magnet: Off')
		self.game.lamps.startButton.disable()
		self.game.lamps.superGame.disable()
		self.game.lamps.buyIn.disable()

	def sw_exit_active(self,sw):
		self.game.modes.remove(self)
		return True

	def sw_startButton_active(self,sw):
		if self.globe_state:
			self.globe_state = False
			self.game.coils.globeMotor.disable()
		else:
			self.globe_state = True
			self.game.coils.globeMotor.pulse(0)
		self.set_texts()
		return True

	def sw_superGame_active(self,sw):
		if self.crane_state:
			self.crane_state = False
			self.game.coils.crane.disable()
		else:
			self.crane_state = True
			self.game.coils.crane.pulse(0)
		self.set_texts()
		return True

	def sw_buyIn_active(self,sw):
		self.magnet_state = True
		self.game.coils.craneMagnet.pulse(0)
		self.set_texts()
		return True

	def sw_buyIn_inactive(self,sw):
		self.magnet_state = False
		self.game.coils.craneMagnet.disable()
		self.set_texts()
		return True

	def sw_enter_active(self,sw):
		return True

	def sw_up_active(self,sw):
		return True

	def sw_down_active(self,sw):
		return True

	def sw_magnetOverRing_active(self,sw):
		self.arm_layer.set_text('SuperGame BTN: Crane: Ring')

	def sw_magnetOverRing_inactive(self,sw):
		self.set_texts()
		
	def sw_globePosition1_active(self,sw):
		self.globe_layer.set_text('Start BTN: Globe: P1')

	def sw_globePosition1_inactive(self,sw):
		self.set_texts()

	def sw_globePosition2_active(self,sw):
		self.globe_layer.set_text('Start BTN: Globe: P2')

	def sw_globePosition2_inactive(self,sw):
		self.set_texts()

	def set_texts(self):
		if self.crane_state:
			self.arm_layer.set_text('SuperGame BTN: Crane: On')
		else:
			self.arm_layer.set_text('SuperGame BTN: Crane: Off')
		
		if self.globe_state:
			self.globe_layer.set_text('Start BTN: Globe: On')
		else:
			self.globe_layer.set_text('Start BTN: Globe: Off')

		if self.magnet_state:
			self.magnet_layer.set_text('Buy-In BTN: Magnet: On')
		else:
			self.magnet_layer.set_text('Buy-In BTN: Magnet: Off')

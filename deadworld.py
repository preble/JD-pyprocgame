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
		self.ball_eject_in_progress = False
		self.crane_delay_active = False
		self.setting_up_eject = False
	
	def mode_started(self):
		#self.debug()
		pass

	def sw_globePosition2_active(self, sw):
		if self.game.user_settings['Machine']['Deadworld fast eject']:
			if self.setting_up_eject:
				self.setting_up_eject = False
				self.delay(name='crane_restart_delay', event_type=None, delay=0.9, handler=self.crane_start)
				switch_num = self.game.switches['globePosition2'].number
				self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)
		else:
			self.crane_activate()

	def crane_activate(self):
		if self.ball_eject_in_progress:
			self.game.coils.crane.pulse(0)

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
		# Make sure globe disable rule is off.
		switch_num = self.game.switches['globePosition2'].number
		self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, False)

	def disable_lock(self):
		self.lock_enabled = 0

	def sw_leftRampToLock_active(self, sw):
		#if self.deadworld_mod_installed:
		self.num_balls_locked += 1
		self.game.trough.num_balls_locked += 1

	def eject_balls(self,num):
		if not self.ball_eject_in_progress:
			self.perform_ball_eject()

		self.num_balls_to_eject += num

		# Tell the trough the balls aren't locked anymore so 
		# it can count properly.
		self.game.trough.num_balls_locked -= num
		# Error check.
		if self.game.trough.num_balls_locked < 0:
			self.game.trough.num_balls_locked = 0
		self.ball_eject_in_progress = True
		
	def perform_ball_search(self):
		if not self.ball_eject_in_progress:
			self.perform_ball_eject()
			self.ball_eject_in_progress = True

	def perform_ball_eject(self):
		# Make sure globe is turning
		self.game.coils.globeMotor.pulse(0)

		if self.game.user_settings['Machine']['Deadworld fast eject']:
			# If globe not in position to start (globePosition2),
			# it needs to get there first.
			if self.game.switches['globePosition2'].is_inactive():
				self.setting_up_eject = True
				switch_num = self.game.switches['globePosition2'].number
				self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, False)
			else:
				self.delay(name='crane_restart_delay', event_type=None, delay=1.9, handler=self.crane_start)
				switch_num = self.game.switches['globePosition2'].number
				self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)
		
			self.delay(name='globe_restart_delay', event_type=None, delay=1, handler=self.globe_start)
		else:
			#if self.deadworld_mod_installed:
			switch_num = self.game.switches['globePosition2'].number
			self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)

	def sw_craneRelease_active(self,sw):
		if not self.crane_delay_active:
			self.delay(name='crane_delay', event_type=None, delay=2, handler=self.end_crane_delay)
			self.crane_delay_active = True
			self.num_balls_to_eject -= 1
			self.num_balls_locked -= 1
			# error check
			if self.num_balls_locked < 0:
				self.num_balls_locked = 0

	def end_crane_delay(self):
		self.crane_delay_active = False
			
		
	def sw_magnetOverRing_open(self,sw):
		if self.ball_eject_in_progress:
			self.game.coils.craneMagnet.pulse(0)
			self.delay(name='crane_release', event_type=None, delay=2, handler=self.crane_release)

	def globe_start(self):
		self.game.coils.globeMotor.pulse(0)

	def crane_start(self):
		self.game.coils.crane.pulse(0)

	def crane_release(self):
		if self.game.user_settings['Machine']['Deadworld fast eject']:
			self.delay(name='globe_restart_delay', event_type=None, delay=1, handler=self.globe_start)

		self.game.coils.craneMagnet.disable()
		self.game.coils.crane.disable()
		self.delay(name='crane_release_check', event_type=None, delay=1, handler=self.crane_release_check)

	def debug(self):
		self.delay(name='debug', event_type=None, delay=1, handler=self.debug)
		self.game.set_status(str(self.num_balls_to_eject) + "," + str(self.num_balls_locked))

	def crane_release_check(self):
		if self.num_balls_to_eject > 0:
			# Only restart if not in fast mode.  Fast mode will just
			# keep going until finished.
			if self.game.user_settings['Machine']['Deadworld fast eject']:
				self.delay(name='crane_restart_delay', event_type=None, delay=0.9, handler=self.crane_start)
			else:
				self.perform_ball_eject()
		else:
			self.game.coils.crane.disable()
			if self.num_balls_locked > 0:
				self.game.coils.globeMotor.pulse(0)
			else:
				self.game.coils.globeMotor.disable()

			self.ball_eject_in_progress = False

	def get_num_balls_locked(self):
		return self.num_balls_locked - self.num_balls_to_eject

class DeadworldTest(service.ServiceModeSkeleton):
	"""Coil Test"""
	def __init__(self, game, priority, font):
		super(DeadworldTest, self).__init__(game, priority, font)
		self.name = "DEADWORLD TEST"
		self.title_layer = dmd.TextLayer(1, 1, font, "left")
		self.globe_layer = dmd.TextLayer(1, 9, font, "left")
		self.arm_layer = dmd.TextLayer(1, 17, font, "left")
		self.magnet_layer = dmd.TextLayer(1, 25, font, "left")
		self.layer = dmd.GroupedLayer(128, 32, [self.title_layer, self.globe_layer, self.arm_layer, self.magnet_layer])

		self.title_layer.set_text(self.name)
		self.globe_layer.set_text( 'START BTN:      Globe:  Off')
		self.arm_layer.set_text(   'SUPERGAME BTN: Crane:   Off')
		self.magnet_layer.set_text('BUY-IN BTN:     Magnet: Off')

	def mode_started(self):
		super(DeadworldTest, self).mode_started()
		self.game.coils.globeMotor.disable()
		self.game.coils.crane.disable()
		self.game.coils.craneMagnet.disable()
		self.globe_state = False
		self.crane_state = False
		self.magnet_state = False
		self.globe_layer.set_text( 'START BTN:      Globe:  Off')
		self.arm_layer.set_text(   'SUPERGAME BTN: Crane:   Off')
		self.magnet_layer.set_text('BUY-IN BTN:     Magnet: Off')
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
		self.globe_layer.set_text( 'START BTN:      Globe:  Off')
		self.arm_layer.set_text(   'SUPERGAME BTN: Crane:   Off')
		self.magnet_layer.set_text('BUY-IN BTN:     Magnet: Off')
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
		self.arm_layer.set_text('SUPERGAME BTN: Crane:  Ring')

	def sw_magnetOverRing_inactive(self,sw):
		self.set_texts()
		
	def sw_globePosition1_active(self,sw):
		self.globe_layer.set_text('START BTN:      Globe:  P1')

	def sw_globePosition1_inactive(self,sw):
		self.set_texts()

	def sw_globePosition2_active(self,sw):
		self.globe_layer.set_text('START BTN:      Globe:  P2')

	def sw_globePosition2_inactive(self,sw):
		self.set_texts()

	def set_texts(self):
		if self.crane_state:
			self.arm_layer.set_text('SUPERGAME BTN: Crane:   On')
		else:
			self.arm_layer.set_text('SUPERGAME BTN: Crane:   Off')
		
		if self.globe_state:
			self.globe_layer.set_text('START BTN:      Globe:  On')
		else:
			self.globe_layer.set_text('START BTN:      Globe:  Off')

		if self.magnet_state:
			self.magnet_layer.set_text('BUY-IN BTN:     Magnet: On')
		else:
			self.magnet_layer.set_text('BUY-IN BTN:     Magnet: Off')

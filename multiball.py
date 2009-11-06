import procgame
from procgame import *

class Multiball(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, deadworld_mod_installed, font):
		super(Multiball, self).__init__(game, priority)
		self.deadworld_mod_installed = deadworld_mod_installed
		self.lock_enabled = 0
		self.num_balls_locked = 0
		self.num_balls_to_eject = 0
		self.virtual_locks_needed = 0
		self.banner_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
		self.state = 'load'
		self.paused = 0
		self.num_locks_lit = 0
		self.targets = {'J':'up', 'U':'up', 'D':'up', 'G':'up', 'E':'up'}
		self.num_times_played = 0
		self.num_left_ramp_shots_hit = 0
		self.num_left_ramp_shots_needed = 1
		self.jackpot_lit = False
		self.lock_level = 1
		self.drops = procgame.modes.BasicDropTargetBank(self.game, priority=priority+1, prefix='dropTarget', letters='JUDGE')
		self.jackpot_collected = False
	
	def mode_started(self):
		self.game.coils.globeMotor.disable()
		self.lock_lamps()
		self.game.deadworld.initialize()
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, False)
		for target in self.targets:
			self.targets[target] = 'up'
			self.game.lamps['dropTarget' + target].pulse(0)
		self.drops.on_advance = self.on_drops_advance
		self.drops.on_completed = self.possibly_light_lock
		self.drops.auto_reset = True
		self.game.modes.add(self.drops)

	def mode_stopped(self):
		self.game.coils.flasherGlobe.disable()
		self.game.modes.remove(self.drops)

	def on_drops_advance(self, mode):
		pass

	def is_active(self):
		return self.state == 'multiball'

	def end_multiball(self):
		self.state = 'load'
		self.game.set_status(self.state)
		self.end_callback()
		self.jackpot_lit = False
		self.game.lamps.multiballJackpot.disable()
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active(): 
			self.game.coils.resetDropTarget.pulse(40)
		self.num_locks_lit = 0
		self.lock_level += 1
		self.lock_lamps()

	def start_multiball(self):
		self.num_balls_locked = 0
		self.state = 'multiball'
		self.display_text("Multiball!")
		self.start_callback()
		self.num_left_ramp_shots_hit = 0
		self.num_left_ramp_shots_needed = 1
		self.jackpot_lit = False
		self.lock_lamps()

	def jackpot(self):
		self.game.score(100000)
		self.lock_lamps()
		#self.jackpot_callback()

	def sw_subwayEnter2_active(self,sw):
		if self.jackpot_lit:
			self.display_text("Jackpot!")
			self.jackpot_lit = False
			self.delay(name='jackpot', event_type=None, delay=1.5, handler=self.jackpot)
			self.game.lamps.multiballJackpot.disable()
			self.num_left_ramp_shots_hit = 0
			self.jackpot_collected = True

	def reset_jackpot_collected(self):
		self.jackpot_collected = False

	def display_text(self, text):
		self.banner_layer.set_text(text, 3)

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.state = info_record['state']
			self.num_balls_locked = info_record['num_balls_locked']
			self.num_locks_lit = info_record['num_locks_lit']
			self.num_times_played = info_record['num_times_played']
			self.lock_level = info_record['lock_level']
			self.jackpot_collected = info_record['jackpot_collected']

		# Virtual locks are needed when there are more balls physically locked 
		# than the player has locked through play.  This happens when
		# another player locks more balls than the current player.  Use
		# Virtual locks > 0 for this case.
		# Use Virtual locks < 0 when the player has locked more balls than are
		# physically locked.  This could happen when another player plays
		# multiball and empties the locked balls.
		if self.deadworld_mod_installed:
			self.virtual_locks_needed = self.game.deadworld.num_balls_locked - self.num_balls_locked
		else:
			self.virtual_locks_needed = 0

		if self.virtual_locks_needed < 0:
			# enable the lock so the player can quickly re-lock
			self.enable_lock()
			self.display_text("Lock is Lit!")
			self.num_balls_locked = self.game.deadworld.num_balls_locked
			self.num_locks_lit = 0 - self.virtual_locks_needed
		elif self.num_balls_locked < self.num_locks_lit:
			self.enable_lock()
			self.display_text("Lock is Lit!")
			
		self.lock_lamps()

	def get_info_record(self):
		info_record = {}
		info_record['state'] = self.state
		info_record['num_balls_locked'] = self.num_balls_locked
		info_record['num_locks_lit'] = self.num_locks_lit
		info_record['num_times_played'] = self.num_times_played
		info_record['lock_level'] = self.lock_level
		info_record['jackpot_collected'] = self.jackpot_collected
		return info_record

	def pause(self):
		self.paused = 1
		if self.lock_enabled:
			self.disable_lock()

	def resume(self):
		self.paused = 0
		if self.lock_enabled:
			self.enable_lock()

	def disable_lock(self):
		self.game.deadworld.disable_lock()
		self.lock_enabled = 0
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, False)

	def enable_lock(self):
		self.game.deadworld.enable_lock()
		self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)
		self.lock_enabled = 1
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, True)
		

	def sw_leftRampToLock_active(self, sw):
		if self.lock_enabled:
			self.game.coils.flasherGlobe.schedule(schedule=0xAAAAAAAA, cycle_seconds=2, now=True)
			self.num_balls_locked += 1
			self.display_text("Ball " + str(self.num_balls_locked) + " Locked!")
			if self.num_balls_locked == 3:
				# Tell ball tracker 3 more balls are in play (2 from locks and 1 from launch
				self.game.ball_tracker.num_balls_in_play += 3
				self.disable_lock()
				ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']
				if self.deadworld_mod_installed:
					# Tell the ball tracker 2 balls are being unlocked.
					# This 3rd one is never logged as physically locked.
					self.game.ball_tracker.num_balls_locked -= 2
					self.game.deadworld.eject_balls(3)
					self.game.ball_save.start(num_balls_to_save=4, time=ball_save_time, now=False, allow_multiple_saves=True)
					self.launch_balls([1,4,ball_save_time,False,True])
				else:
					self.launch_balls([3,4,ball_save_time,False,True])
					self.delay(name='stop_globe', event_type=None, delay=7.0, handler=self.stop_globe)
				self.start_multiball()
			elif self.num_balls_locked == self.num_locks_lit:
				self.disable_lock()
				if self.deadworld_mod_installed:
					# Tell the ball tracker another ball is physically locked
					self.game.ball_tracker.num_balls_locked += 1
					self.launch_balls([1,0,0,False,False])
				
			# When not yet multiball, launch a new ball each time
			# one is locked.
			elif self.deadworld_mod_installed:
				# Tell the ball tracker another ball is physically locked
				self.game.ball_tracker.num_balls_locked += 1
				self.launch_balls([1,0,0,False,False])

		else:
			if self.deadworld_mod_installed:
				self.game.deadworld.eject_balls(1)
		self.lock_lamps()

	def possibly_light_lock(self, mode):
		if self.state == 'load' and not self.paused:
			# Prepare to lock
			if self.num_locks_lit < 3:
				for target in self.targets:
					self.targets[target] = 'up'
					self.game.lamps['dropTarget' + target].pulse(0)
					
				if self.lock_level == 1:
					self.num_locks_lit = 3
				else:
					self.num_locks_lit += 1
				# Don't enable locks if doing virtual locks.
				if self.virtual_locks_needed == 0:
					self.enable_lock()
					self.display_text("Lock is Lit!")

			self.lock_lamps()

	def sw_leftRampExit_active(self,sw):
		if self.state == 'load':
			if self.virtual_locks_needed > 0:
				self.num_balls_locked += 1
				self.virtual_locks_needed -= 1

			self.lock_lamps()
		elif self.state == 'multiball':
			if not self.jackpot_lit:
				self.num_left_ramp_shots_hit += 1
				if self.num_left_ramp_shots_hit == self.num_left_ramp_shots_needed:
					self.jackpot_lit = True
					self.game.lamps.multiballJackpot.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
				if self.game.switches.dropTargetD.is_inactive():
					self.game.coils.tripDropTarget.pulse(50)
				self.lock_lamps()

	def lock_lamps(self):
		if self.state == 'load':
			for i in range(1,4):
				lampname = 'lock' + str(i)
				if self.num_locks_lit >= i and not self.paused:
					if self.num_balls_locked >= i:
						self.game.lamps[lampname].pulse(0)
					elif self.num_balls_locked < i:
						self.game.lamps[lampname].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
					else:
						self.game.lamps[lampname].disable()
				else:
					self.game.lamps[lampname].disable()
	
		elif self.state == 'multiball' and not self.jackpot_lit:
			self.game.lamps.lock1.schedule(schedule=0x000f000f, cycle_seconds=0, now=False)
			self.game.lamps.lock2.schedule(schedule=0x003c003c, cycle_seconds=0, now=False)
			self.game.lamps.lock3.schedule(schedule=0x00f000f0, cycle_seconds=0, now=False)
			
		else:
			self.game.lamps.lock1.disable()
			self.game.lamps.lock2.disable()
			self.game.lamps.lock3.disable()

	def how_many_balls_locked(self):
		return self.num_balls_locked

	def stop_globe(self):
		self.game.deadworld.mode_stopped()
		
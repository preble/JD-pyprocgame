import procgame
import locale
import time
from procgame import *

class UltimateChallenge(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(UltimateChallenge, self).__init__(game, priority)
		self.completed = False
		self.name = 'Ultimate Challenge'
		self.modes = ['fire','fear','mortis','death']
		self.mode_fire = Fire(game, self.priority+1)
		self.mode_fear = Fire(game, self.priority+1)
		self.mode_mortis = Fire(game, self.priority+1)
		self.mode_death = Fire(game, self.priority+1)

	def mode_started(self):
		self.active_mode = 'fire'
		self.mode_list = {}
		self.mode_list['fire'] = self.mode_fire
		self.mode_list['fear'] = self.mode_fear
		self.mode_list['mortis'] = self.mode_mortis
		self.mode_list['death'] = self.mode_death

		self.mode_fire.complete_callback = self.level_complete_callback
		self.mode_fear.complete_callback = self.level_complete_callback
		self.mode_mortis.complete_callback = self.level_complete_callback
		self.mode_death.complete_callback = self.level_complete_callback

	def mode_stopped(self):
		self.game.modes.remove(self.mode_fire)
		self.game.modes.remove(self.mode_fear)
		self.game.modes.remove(self.mode_mortis)
		self.game.modes.remove(self.mode_death)

	def begin(self):
		self.game.modes.add(self.mode_list[self.active_mode])

	def register_callback_function(self, function):
		self.callback = function

	def get_instruction_layers(self):
		font = self.game.fonts['tiny7']
		instr_layer1 = dmd.TextLayer(128/2, 15, font, "center").set_text('This')
		instr_layer2 = dmd.TextLayer(128/2, 15, font, "center").set_text('is')
		instr_layer3 = dmd.TextLayer(128/2, 15, font, "center").set_text('the')
		instr_layer4 = dmd.TextLayer(128/2, 15, font, "center").set_text('Ultimate')
		instr_layer5 = dmd.TextLayer(128/2, 15, font, "center").set_text('Challenge')
		instruction_layers = [[instr_layer1],[instr_layer2],[instr_layer3],[instr_layer4],[instr_layer5]]
		return instruction_layers

	def timer_update(self, timer):
		self.countdown_layer.set_text(str(timer))

	def update_lamps(self):
		self.game.lamps['ultChallenge'].pulse(0)

	def sw_shooterL_active_for_200ms(self, sw):
		self.game.coils.shooterL.pulse()
		return True	

	def level_complete_callback(self):
		self.game.ball_save.disable()
		self.game.trough.drain_callback = self.complete_drain_callback

	def complete_drain_callback(self):
		if self.game.trough.num_balls_in_play == 0:
			if self.active_mode == 'fire':
				self.game.modes.remove(self.mode_fire)
				self.active_mode == 'fear'
				self.game.modes.add(self.mode_fear)
			self.game.trough.drain_callback = self.game.base_game_mode.ball_drained_callback
			self.game.enable_flippers(True)


class UltimateIntro(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(UltimateIntro, self).__init__(game, priority)
		self.frame_counter = 0
		self.num_intro_layers = {'fire':1, 'fear':1, 'mortis':1, 'death':1}

	def mode_started(self):
		self.frame_counter = 0
		self.next_frame()
		self.update_gi(False, 'all')
		# Disable the flippers
		self.game.enable_flippers(enable=False)

	def mode_stopped(self):
		self.cancel_delayed('intro')
		self.update_gi(True, 'all')
		# Enable the flippers
		self.game.enable_flippers(enable=True)

	def setup(self, stage, exit_function):
		self.exit_function = exit_function
		self.stage = stage

	def update_gi(self, on, num):
		for i in range(1,5):
			if num == 'all' or num == i:
				if on:
					self.game.lamps['gi0' + str(i)].pulse(0)
				else:
					self.game.lamps['gi0' + str(i)].disable()

	def next_frame(self):
		if self.frame_counter != self.num_intro_layers[self.stage]:
			time_delay = self.set_next_frame()
			self.delay(name='intro', event_type=None, delay=time_delay, handler=self.next_frame)
			self.frame_counter += 1
		else:
			self.exit_function()

	def set_next_frame(self):
		if self.stage == 'fire':
			if self.frame_counter == 0:
				layer1 = dmd.TextLayer(128/2, 15, self.game.fonts['jazz18'], "center").set_text('Go!')
				self.layer = dmd.GroupedLayer(128, 32, [layer1])
				#self.layer = layer1
				return 3



class Fire(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Fire, self).__init__(game, priority)
		self.complete = False
		self.mystery_lit = True

	def mode_started(self):
		self.mystery_lit = True
		self.game.coils.flasherFire.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.targets = [1,1,1,1,1]
		self.lamp_colors = ['G', 'Y', 'R', 'W']
		self.update_lamps()
		self.complete = False
		if self.game.deadworld.num_balls_locked == 1:
			balls_to_launch = 2
		elif self.game.deadworld.num_balls_locked == 2:
			balls_to_launch = 1
		else:
			balls_to_launch = 3
		if balls_to_launch != 3:
			self.game.deadworld.eject_balls(self.game.deadworld.num_balls_locked)
		self.game.trough.launch_balls(balls_to_launch, self.launch_callback)

	def launch_callback(self):
		#ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']
		#self.game.ball_save.start(num_balls_to_save=6, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.game.coils.flasherFire.disable()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f Pursuit calling callback" % (time.time())
			self.callback()

	def update_lamps(self):
		for i in range(0,5):
			for j in range(0,4):
				lampname = 'perp' + str(i+1) + self.lamp_colors[j]
				if self.targets[i]:
					print lampname + 'on'
					self.drive_mode_lamp(lampname, 'medium')
				else:
					print lampname + 'off'
					self.drive_mode_lamp(lampname, 'off')
		if self.complete:
			self.game.coils.flasherFire.disable()

		if self.mystery_lit:
			self.drive_mode_lamp('mystery', 'on')
		else:
			self.drive_mode_lamp('mystery', 'off')

			
	def drive_mode_lamp(self, lampname, style='on'):
		if style == 'slow':
			self.game.lamps[lampname].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		if style == 'medium':
			self.game.lamps[lampname].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
		if style == 'fast':
			self.game.lamps[lampname].schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		elif style == 'on':
			self.game.lamps[lampname].pulse(0)
		elif style == 'off':
			self.game.lamps[lampname].disable()

	def sw_mystery_active(self, sw):
		self.game.sound.play('mystery')
		if self.mystery_lit:
			self.mystery_lit = False
			self.game.set_status('Add 2 balls!')
			self.game.trough.launch_balls(2, self.launch_callback)
		return True

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return True


	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1:
			self.switch_hit(1)

		return True

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)
		return True

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.switch_hit(3)
		return True

	def sw_topCenterRollover_active(self, sw):
		#See if ball came around right loop 
		#Give it 2 seconds as ball trickles this way.  Might need to adjust.
		if self.game.switches.topRightOpto.time_since_change() < 2:
			self.switch_hit(3)
		return True

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)
		return True

	def switch_hit(self, num):
		if self.targets[num]:
			self.targets[num] = 0
			self.target_hit(num)
			if self.all_targets_hit():
				self.finish()
			self.update_lamps()
			

	def target_hit(self, num):
		pass

	def all_targets_hit(self):
		for i in range(0,5):
			if self.targets[i]:
				return False
		return True

	def finish(self):
		self.game.lamps.gi01.disable()
		self.game.lamps.gi02.disable()
		self.game.lamps.gi03.disable()
		self.game.lamps.gi04.disable()
		self.game.enable_flippers(False)
		self.update_lamps()
		self.complete = True
		self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.

class Fear(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Fear, self).__init__(game, priority)
		self.complete = False
		self.mystery_lit = True

	def mode_started(self):
		self.mystery_lit = True
		self.game.coils.flasherFire.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.targets = [1,1,1,1,1]
		self.lamp_colors = ['G', 'Y', 'R', 'W']
		self.update_lamps()
		self.complete = False
		if self.game.deadworld.num_balls_locked == 1:
			balls_to_launch = 4
		elif self.game.deadworld.num_balls_locked == 2:
			balls_to_launch = 3
		else:
			balls_to_launch = 5
		if balls_to_launch != 5:
			self.game.deadworld.eject_balls(self.game.deadworld.num_balls_locked)
		self.game.trough.launch_balls(balls_to_launch, self.launch_callback)

	def launch_callback(self):
		ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']
		self.game.ball_save.start(num_balls_to_save=6, time=ball_save_time, now=False, allow_multiple_saves=True)

	def mode_stopped(self):
		self.game.coils.flasherFire.disable()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f Pursuit calling callback" % (time.time())
			self.callback()

	def update_lamps(self):
		for i in range(0,5):
			for j in range(0,4):
				lampname = 'perp' + str(i+1) + self.lamp_colors[j]
				if self.targets[i]:
					print lampname + 'on'
					self.drive_mode_lamp(lampname, 'medium')
				else:
					print lampname + 'off'
					self.drive_mode_lamp(lampname, 'off')
		if self.complete:
			self.game.coils.flasherFire.disable()

		if self.mystery_lit:
			self.drive_mode_lamp('mystery', 'on')
		else:
			self.drive_mode_lamp('mystery', 'off')

			
	def drive_mode_lamp(self, lampname, style='on'):
		if style == 'slow':
			self.game.lamps[lampname].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		if style == 'medium':
			self.game.lamps[lampname].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
		if style == 'fast':
			self.game.lamps[lampname].schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		elif style == 'on':
			self.game.lamps[lampname].pulse(0)
		elif style == 'off':
			self.game.lamps[lampname].disable()

	def sw_mystery_active(self, sw):
		self.game.sound.play('mystery')
		if self.mystery_lit:
			self.mystery_lit = False
			self.game.ball_save.start(num_balls_to_save=6, time=10, now=True, allow_multiple_saves=True)
			self.game.set_status('+10 second ball saver')
		return True

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return True


	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1:
			self.switch_hit(1)

		return True

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)
		return True

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.switch_hit(3)
		return True

	def sw_topCenterRollover_active(self, sw):
		#See if ball came around right loop 
		#Give it 2 seconds as ball trickles this way.  Might need to adjust.
		if self.game.switches.topRightOpto.time_since_change() < 2:
			self.switch_hit(3)
		return True

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)
		return True

	def switch_hit(self, num):
		if self.targets[num]:
			self.targets[num] = 0
			self.target_hit(num)
			if self.all_targets_hit():
				self.finish()
			self.update_lamps()
			

	def target_hit(self, num):
		pass

	def all_targets_hit(self):
		for i in range(0,5):
			if self.targets[i]:
				return False
		return True

	def finish(self):
		self.game.lamps.gi01.disable()
		self.game.lamps.gi02.disable()
		self.game.lamps.gi03.disable()
		self.game.lamps.gi04.disable()
		self.game.enable_flippers(False)
		self.update_lamps()
		self.complete = True
		self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.

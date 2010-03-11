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
		self.modes = ['fire','fear','mortis','death','celebration']
		self.mode_fire = Fire(game, self.priority+1)
		self.mode_fear = Fear(game, self.priority+1)
		self.mode_mortis = Mortis(game, self.priority+1)
		self.mode_death = Death(game, self.priority+1)
		self.mode_celebration = Celebration(game, self.priority+1)
		self.active_mode = 'fire'
		self.mode_list = {}
		self.mode_list['fire'] = self.mode_fire
		self.mode_list['fear'] = self.mode_fear
		self.mode_list['mortis'] = self.mode_mortis
		self.mode_list['death'] = self.mode_death
		self.mode_list['celebration'] = self.mode_celebration

		self.mode_fire.complete_callback = self.level_complete_callback
		self.mode_fear.complete_callback = self.level_complete_callback
		self.mode_mortis.complete_callback = self.level_complete_callback
		self.mode_death.complete_callback = self.level_complete_callback
		self.mode_celebration.complete_callback = self.level_complete_callback

	def mode_started(self):
		self.game.coils.resetDropTarget.pulse(40)

	def mode_stopped(self):
		self.game.modes.remove(self.mode_fire)
		self.game.modes.remove(self.mode_fear)
		self.game.modes.remove(self.mode_mortis)
		self.game.modes.remove(self.mode_death)

	def get_info_record(self):
		info_record = {}
		info_record['active_mode'] = self.active_mode
		return info_record

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.active_mode = info_record['active_mode']

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
		pass

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
				self.active_mode = 'mortis'
				self.game.modes.add(self.mode_mortis)
			elif self.active_mode == 'mortis':
				self.game.modes.remove(self.mode_mortis)
				self.active_mode = 'fear'
				self.game.modes.add(self.mode_fear)
			elif self.active_mode == 'fear':
				self.game.modes.remove(self.mode_fear)
				self.active_mode = 'death'
				self.game.modes.add(self.mode_death)
			elif self.active_mode == 'death':
				self.completed = True
				self.game.modes.remove(self.mode_death)
				self.active_mode = 'celebration'
				self.game.modes.add(self.mode_celebration)
			self.game.enable_flippers(True)
			self.game.trough.drain_callback = self.game.base_game_mode.ball_drained_callback
		elif self.game.trough.num_balls_in_play == 1:
			if self.active_mode == 'celebration':
				self.game.trough.drain_callback = self.game.base_game_mode.ball_drained_callback
				self.callback()


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
		self.game.lamps.rightStartFeature.disable()
		self.game.lamps.ultChallenge.pulse(0)
		# Leave GI off for Ultimate Challenge
		#self.game.lamps.gi01.disable()
		#self.game.lamps.gi02.disable()
		#self.game.lamps.gi03.disable()
		#self.game.lamps.gi04.disable()
		self.game.lamps.dropTargetJ.disable()
		self.game.lamps.dropTargetU.disable()
		self.game.lamps.dropTargetD.disable()
		self.game.lamps.dropTargetG.disable()
		self.game.lamps.dropTargetE.disable()

	def mode_stopped(self):
		self.cancel_delayed('intro')
		# Leave GI off for Ultimate Challenge
		# self.update_gi(True, 'all')
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

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.coils.resetDropTarget.pulse(40)
		return True

	def target_hit(self, num):
		pass

	def all_targets_hit(self):
		for i in range(0,5):
			if self.targets[i]:
				return False
		return True

	def finish(self):
		self.layer = dmd.TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Fire Defeated!')
		self.game.coils.flasherFire.disable()
		self.game.lamps.ultChallenge.disable()
		self.game.enable_flippers(False)
		self.mystery_lit = False
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
		self.countdown_layer = dmd.TextLayer(127, 1, self.game.fonts['tiny7'], "right")
		self.name_layer = dmd.TextLayer(1, 1, self.game.fonts['tiny7'], "left").set_text('Fear')
		self.score_layer = dmd.TextLayer(128/2, 10, self.game.fonts['num_14x10'], "center")
		self.status_layer = dmd.TextLayer(128/2, 26, self.game.fonts['tiny7'], "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

	def mode_started(self):
		self.state = 'ramps'
		self.ramp_shots_required = 4
		self.ramp_shots_hit = 0
		self.active_ramp = 'left'
		self.timer = 20
		self.mystery_lit = True
		self.update_lamps()
		self.complete = False
		self.game.trough.launch_balls(1, self.launch_callback)
		self.game.coils.flasherFear.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.already_collected = False
		self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)

	def launch_callback(self):
		ball_save_time = 10
		self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.game.coils.flasherFire.disable()

	def update_lamps(self):
		if self.mystery_lit:
			self.drive_mode_lamp('mystery', 'on')
		else:
			self.drive_mode_lamp('mystery', 'off')

		if self.state == 'finished':
			self.game.coils.flasherFear.disable()
			self.game.coils.flasherPursuitR.disable()
			self.game.coils.flasherPursuitL.disable()
			self.game.lamps.pickAPrize.disable()
			self.game.lamps.awardSafecracker.disable()
			self.game.lamps.awardBadImpersonator.disable()
			self.game.lamps.multiballJackpot.disable()
		elif self.state == 'ramps':
			if self.active_ramp == 'left':
				self.game.coils.flasherPursuitL.schedule(schedule=0x00030003, cycle_seconds=0, now=True)
				self.game.coils.flasherPursuitR.disable()
			else:
				self.game.coils.flasherPursuitR.schedule(schedule=0x00030003, cycle_seconds=0, now=True)
				self.game.coils.flasherPursuitL.disable()
		else:
			if self.game.switches.dropTargetD.is_inactive():
				self.game.lamps.dropTargetD.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
			else:
				self.game.lamps.dropTargetD.disable()
				self.game.lamps.pickAPrize.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
				self.game.lamps.awardSafecracker.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
				self.game.lamps.awardBadImpersonator.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
				self.game.lamps.multiballJackpot.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
			

			
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
			self.timer = 20
			self.mystery_lit = False
		return True

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return True


	def sw_leftRampExit_active(self, sw):
		if self.state == 'ramps':
			if self.active_ramp == 'left':
				self.ramp_shots_hit += 1
				self.ramp_shot_hit()

		return True

	def sw_rightRampExit_active(self, sw):
		if self.state == 'ramps':
			if self.active_ramp == 'right':
				self.ramp_shots_hit += 1
				self.ramp_shot_hit()
		return True

	def sw_popperR_active_for_300ms(self, sw):
		return True

	def ramp_shot_hit(self):
		if self.ramp_shots_hit == self.ramp_shots_required:
			self.state = 'subway'
		else:
			self.switch_ramps()
		self.timer = 20
		self.update_lamps()

	def switch_ramps(self):
		if self.active_ramp == 'left':
			self.active_ramp = 'right'
		else:
			self.active_ramp = 'left'

	def sw_dropTargetD_inactive_for_400ms(self, sw):
		self.game.coils.tripDropTarget.pulse(60)

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		if self.state == 'ramps':
			self.drop_targets()
		else:
			self.update_lamps()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.coils.resetDropTarget.pulse(40)
		return True

	def sw_subwayEnter1_closed(self, sw):
		self.finish()
		self.cancel_delayed(['grace', 'countdown'])
		self.already_collected = True
		return True
	
	# Ball might jump over first switch.  Use 2nd switch as a catchall.
	def sw_subwayEnter2_closed(self, sw):
		if not self.already_collected:
			self.banner_layer.set_text('Well Done!')
			self.finish()
			self.cancel_delayed(['grace', 'countdown'])
		return True
	

	def finish(self, success = True):
		self.layer = dmd.TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Fear Defeated!')
		self.state = 'finished'
		self.game.enable_flippers(False)
		self.update_lamps()
		self.game.lamps.ultChallenge.disable()
		if success:
			self.complete = True
			self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.

	def mode_tick(self):
		score = self.game.current_player().score
		if score == 0:
			self.score_layer.set_text('00')
		else:
			self.score_layer.set_text(locale.format("%d",score,True))

	def decrement_timer(self):
		if self.timer > 0:
			self.timer -= 1
			self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
			self.countdown_layer.set_text(str(self.timer))
		else:
			self.finish(False)

class Mortis(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Mortis, self).__init__(game, priority)
		self.complete = False

	def mode_started(self):
		self.state = 'ramps'
		self.shots_required = [2, 2, 2, 2, 2]
		self.update_lamps()
		self.complete = False
		self.game.trough.launch_balls(2, self.launch_callback)
		self.game.coils.flasherMortis.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.already_collected = False

	def launch_callback(self):
		ball_save_time = 20
		self.game.ball_save.start(num_balls_to_save=2, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.game.coils.flasherMortis.disable()

	def update_lamps(self):
		self.drive_shot_lamp(0, 'mystery')
		self.drive_shot_lamp(1, 'perp1W')
		self.drive_shot_lamp(1, 'perp1R')
		self.drive_shot_lamp(1, 'perp1Y')
		self.drive_shot_lamp(1, 'perp1G')
		self.drive_shot_lamp(2, 'perp3W')
		self.drive_shot_lamp(2, 'perp3R')
		self.drive_shot_lamp(2, 'perp3Y')
		self.drive_shot_lamp(2, 'perp3G')
		self.drive_shot_lamp(3, 'perp5W')
		self.drive_shot_lamp(3, 'perp5R')
		self.drive_shot_lamp(3, 'perp5Y')
		self.drive_shot_lamp(3, 'perp5G')
		self.drive_shot_lamp(4, 'stopMeltdown')

	def drive_shot_lamp(self, index, lampname):
		if self.shots_required[index] > 1:
			self.game.lamps[lampname].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
		elif self.shots_required[index] > 0:
			self.game.lamps[lampname].schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		else:
			self.game.lamps[lampname].disable()
			

			
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
		self.switch_hit(0)
		return True

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(1)
		return True

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)
		return True

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(3)
		return True

	def sw_captiveBall3_active(self, sw):
		self.switch_hit(4)
		return True

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return True


	def switch_hit(self, index):
		if self.shots_required[index] > 0:
			self.shots_required[index] -= 1
			self.update_lamps()
			self.check_for_completion()

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.coils.resetDropTarget.pulse(40)
		return True

	def check_for_completion(self):
		for i in range(0,5):
			if self.shots_required[i] > 0:
				return False
		self.finish()

	def finish(self, success = True):
		self.layer = dmd.TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Mortis Defeated!')
		self.state = 'finished'
		self.game.enable_flippers(False)

		self.game.lamps.perp1W.disable()
		self.game.lamps.perp1R.disable()
		self.game.lamps.perp1Y.disable()
		self.game.lamps.perp1G.disable()
		self.game.lamps.perp3W.disable()
		self.game.lamps.perp3R.disable()
		self.game.lamps.perp3Y.disable()
		self.game.lamps.perp3G.disable()
		self.game.lamps.perp5W.disable()
		self.game.lamps.perp5R.disable()
		self.game.lamps.perp5Y.disable()
		self.game.lamps.perp5G.disable()
		self.game.lamps.mystery.disable()
		self.game.lamps.stopMeltdown.disable()
		self.game.coils.flasherMortis.disable()
		self.game.lamps.ultChallenge.disable()

		if success:
			self.complete = True
			self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.

class Death(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Death, self).__init__(game, priority)
		self.complete = False
		self.countdown_layer = dmd.TextLayer(127, 1, self.game.fonts['tiny7'], "right")
		self.name_layer = dmd.TextLayer(1, 1, self.game.fonts['tiny7'], "left").set_text('Death')
		self.score_layer = dmd.TextLayer(128/2, 10, self.game.fonts['num_14x10'], "center")
		self.status_layer = dmd.TextLayer(128/2, 26, self.game.fonts['tiny7'], "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

	def mode_started(self):
		self.current_shot_index = 0
		self.total_timer = 180
		self.timer = 10
		self.active_shots = [1, 1, 1, 1, 1]
		self.shot_order = [4,2,0,3,1]
		self.update_lamps()
		self.complete = False
		self.game.trough.launch_balls(1, self.launch_callback)
		self.game.coils.flasherDeath.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
		self.already_collected = False
		self.game.coils.resetDropTarget.pulse(40)

	def launch_callback(self):
		ball_save_time = 20
		self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.game.coils.flasherDeath.disable()

	def update_lamps(self):
		self.drive_shot_lamp(0, 'perp1W')
		self.drive_shot_lamp(0, 'perp1R')
		self.drive_shot_lamp(0, 'perp1Y')
		self.drive_shot_lamp(0, 'perp1G')
		self.drive_shot_lamp(1, 'perp2W')
		self.drive_shot_lamp(1, 'perp2R')
		self.drive_shot_lamp(1, 'perp2Y')
		self.drive_shot_lamp(1, 'perp2G')
		self.drive_shot_lamp(2, 'perp3W')
		self.drive_shot_lamp(2, 'perp3R')
		self.drive_shot_lamp(2, 'perp3Y')
		self.drive_shot_lamp(2, 'perp3G')
		self.drive_shot_lamp(3, 'perp4W')
		self.drive_shot_lamp(3, 'perp4R')
		self.drive_shot_lamp(3, 'perp4Y')
		self.drive_shot_lamp(3, 'perp4G')
		self.drive_shot_lamp(4, 'perp5W')
		self.drive_shot_lamp(4, 'perp5R')
		self.drive_shot_lamp(4, 'perp5Y')
		self.drive_shot_lamp(4, 'perp5G')

	def drive_shot_lamp(self, index, lampname):
		if self.active_shots[index] >= 1:
			self.game.lamps[lampname].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
		else:
			self.game.lamps[lampname].disable()
			

			
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
		self.switch_hit(0)
		return True

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1.5:
			self.switch_hit(1)

		return True

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)
		return True

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.switch_hit(3)

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)
		return True

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return True


	def switch_hit(self, index):
		if self.active_shots[index]:
			self.active_shots[index] = 0
			self.timer += 10
			self.check_for_completion()
			self.update_lamps()

	def add_shot(self):
		for i in range(0, 5):
			if not self.active_shots[self.shot_order[i]]:
				self.active_shots[self.shot_order[i]] = 1
				break
		self.update_lamps()

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.coils.resetDropTarget.pulse(40)
		return True

	def check_for_completion(self):
		for i in range(0,5):
			if self.active_shots[i]:
				return False
		self.finish()

	def finish(self, success = True):
		self.layer = dmd.TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Death Defeated!')
		self.cancel_delayed('countdown')
		self.game.enable_flippers(False)

		self.game.lamps.perp1W.disable()
		self.game.lamps.perp1R.disable()
		self.game.lamps.perp1Y.disable()
		self.game.lamps.perp1G.disable()
		self.game.lamps.perp3W.disable()
		self.game.lamps.perp3R.disable()
		self.game.lamps.perp3Y.disable()
		self.game.lamps.perp3G.disable()
		self.game.lamps.perp5W.disable()
		self.game.lamps.perp5R.disable()
		self.game.lamps.perp5Y.disable()
		self.game.lamps.perp5G.disable()
		self.game.lamps.mystery.disable()
		self.game.lamps.stopMeltdown.disable()
		self.game.coils.flasherDeath.disable()
		self.game.lamps.ultChallenge.disable()

		if success:
			self.complete = True
			self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.

	def mode_tick(self):
		score = self.game.current_player().score
		if score == 0:
			self.score_layer.set_text('00')
		else:
			self.score_layer.set_text(locale.format("%d",score,True))

	def decrement_timer(self):
		if self.total_timer == 0:
			self.finish(False)
		elif self.timer > 0:
			self.timer -= 1
			self.total_timer -= 1
			self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
			self.countdown_layer.set_text(str(self.total_timer))
		else:
			self.add_shot()
			self.timer = 10
			self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)

class Celebration(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Celebration, self).__init__(game, priority)

	def mode_started(self):
		self.layer = dmd.TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Celebration Multiball!', 3)

		# Call callback now to set up drain callback, which will decide
		# when multiball should end... probably when 1 ball is left.
		self.complete_callback()

		if self.game.deadworld.num_balls_locked == 1:
			balls_to_launch = 5
		elif self.game.deadworld.num_balls_locked == 2:
			balls_to_launch = 4
		else:
			balls_to_launch = 6
		if balls_to_launch != 6:
			self.game.deadworld.eject_balls(self.game.deadworld.num_balls_locked)
		self.game.trough.launch_balls(balls_to_launch, self.launch_callback)

	def launch_callback(self):
		ball_save_time = 30
		self.game.ball_save.start(num_balls_to_save=6, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.game.coils.flasherDeath.disable()

	def update_lamps(self):
		pass

			
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
		self.game.score(5000)
		return True

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.game.score(5000)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1.5:
			self.game.score(5000)

		return True

	def sw_popperR_active_for_300ms(self, sw):
		self.game.score(1000)
		return True

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.game.score(5000)

	def sw_rightRampExit_active(self, sw):
		self.game.score(1000)
		return True

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return True

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.score(1000)
		self.game.coils.resetDropTarget.pulse(40)
		return True


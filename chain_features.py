import procgame
import locale
import time
from procgame import *
import os.path

class ModeCompletedHurryup(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ModeCompletedHurryup, self).__init__(game, priority)
		self.countdown_layer = dmd.TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.banner_layer = dmd.TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.countdown_layer, self.banner_layer])
	
	def mode_started(self):
		self.banner_layer.set_text("HURRY-UP!", 3)
		self.seconds_remaining = 13
		self.update_and_delay()
		self.update_lamps()
		self.game.coils.tripDropTarget.pulse(40)
		self.already_collected = False

	def sw_dropTargetD_inactive_for_400ms(self, sw):
		self.game.coils.tripDropTarget.pulse(40)

	def update_lamps(self):
		self.game.lamps.pickAPrize.schedule(schedule=0x33333333, cycle_seconds=0, now=True)

	def mode_stopped(self):
		#self.drop_target_mode.animated_reset(1.0)
		self.game.lamps.pickAPrize.disable()
		#if self.game.switches.popperL.is_open():
		#	self.game.coils.popperL.pulse(40)
	
	def sw_subwayEnter1_closed(self, sw):
		self.collected()
		self.cancel_delayed(['grace', 'countdown'])
		self.already_collected = True
		self.banner_layer.set_text('Well Done!')
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
	
	# Ball might jump over first switch.  Use 2nd switch as a catchall.
	def sw_subwayEnter2_closed(self, sw):
		if not self.already_collected:
			self.banner_layer.set_text('Well Done!')
			self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
			self.collected()
			self.cancel_delayed(['grace', 'countdown'])
	
	def update_and_delay(self):
		self.countdown_layer.set_text("%d seconds" % (self.seconds_remaining))
		self.delay(name='countdown', event_type=None, delay=1, handler=self.one_less_second)
		
	def one_less_second(self):
		self.seconds_remaining -= 1
		if self.seconds_remaining >= 0:
			self.update_and_delay()
		else:
			self.delay(name='grace', event_type=None, delay=2, handler=self.delayed_removal)
			
	def delayed_removal(self):
		self.expired()


class ChainFeature(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, name):
		super(ChainFeature, self).__init__(game, priority)
		self.completed = False
		self.name = name
		self.countdown_layer = dmd.TextLayer(127, 1, self.game.fonts['tiny7'], "right")
		self.name_layer = dmd.TextLayer(1, 1, self.game.fonts['tiny7'], "left").set_text(name)
		self.score_layer = dmd.TextLayer(128/2, 10, self.game.fonts['num_14x10'], "center")
		self.status_layer = dmd.TextLayer(128/2, 26, self.game.fonts['tiny7'], "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])
		

	def register_callback_function(self, function):
		self.callback = function

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(name)
		instruction_layers = [[layer1]]
		return instruction_layers

	def mode_tick(self):
		score = self.game.current_player().score
		if score == 0:
			self.score_layer.set_text('00')
		else:
			self.score_layer.set_text(locale.format("%d",score,True))

	def timer_update(self, timer):
		self.countdown_layer.set_text(str(timer))

class Pursuit(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Pursuit, self).__init__(game, priority, 'Pursuit')
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if difficulty == 'easy':
			self.shots_required_for_completion = 3
		elif difficulty == 'medium':
			self.shots_required_for_completion = 4
		else:
			self.shots_required_for_completion = 5

	def mode_started(self):
		self.game.coils.flasherPursuitL.schedule(schedule=0x00030003, cycle_seconds=0, now=True)
		self.game.coils.flasherPursuitR.schedule(schedule=0x03000300, cycle_seconds=0, now=True)
		self.shots = 0
		self.update_status()

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()
		self.game.coils.flasherPursuitR.disable()

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f Pursuit calling callback" % (time.time())
			self.callback()

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot " + str(self.shots_required_for_completion) + " L/R ramp shots")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers
	
class Blackout(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Blackout, self).__init__(game, priority, 'Blackout')
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if difficulty == 'easy':
			self.shots_required_for_completion = 1
		elif difficulty == 'medium':
			self.shots_required_for_completion = 1
		else:
			self.shots_required_for_completion = 2

	def mode_started(self):
		self.game.lamps.gi01.disable()
		self.game.lamps.gi02.disable()
		self.game.lamps.gi03.disable()
		self.game.lamps.gi04.disable()
		self.game.lamps.blackoutJackpot.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots = 0
		self.update_status()
		filename = "./games/jd/dmd/blackout.dmd"
		if os.path.isfile(filename):
			anim = dmd.Animation().load(filename)
			self.game.base_game_mode.jd_modes.play_animation(anim, 'high', repeat=False, hold=False, frame_time=3)

	def update_status(self):
		if self.shots > self.shots_required_for_completion:
			extra_shots = self.shots - self.shots_required_for_completion
			status = 'Shots made: ' + str(extra_shots) + ' extra'
		else:
			status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.lamps.blackoutJackpot.disable()
		self.game.coils.flasherBlackout.disable()
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)
		self.game.lamps.gi04.pulse(0)

	def update_lamps(self):
		self.game.lamps.blackoutJackpot.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

	def sw_centerRampExit_active(self, sw):
		self.completed = True
		self.game.coils.flasherBlackout.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots += 1
		self.game.score(10000)
		print "% 10.3f Blackout calling callback" % (time.time())
		self.check_for_completion()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot center ramps " + str(self.shots_required_for_completion) + " times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers

class Sniper(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Sniper, self).__init__(game, priority, 'Sniper')

	def mode_started(self):
		self.game.lamps.awardSniper.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0
		self.update_status()

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(2)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.lamps.awardSniper.disable()

	def update_lamps(self):
		self.game.lamps.awardSniper.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_popperR_active_for_300ms(self, sw):
		self.shots += 1
		self.game.score(10000)
		filename = "./games/jd/dmd/dredd_shoot_at_sniper.dmd"
		if os.path.isfile(filename):
			anim = dmd.Animation().load(filename)
			self.game.base_game_mode.jd_modes.play_animation(anim, 'high', repeat=False, hold=False, frame_time=5)
		self.check_for_completion()

	def check_for_completion(self):
		self.update_status()
		if self.shots == 2:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f Sniper calling callback" % (time.time())
			self.callback()

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot Sniper Tower 2 times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class BattleTank(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(BattleTank, self).__init__(game, priority, 'Battle Tank')

	def mode_started(self):
		self.game.lamps.tankCenter.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.game.lamps.tankLeft.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.game.lamps.tankRight.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = {'left':False,'center':False,'right':False}
		self.update_status()

	def update_status(self):
		num_shots = 0
		for shot in self.shots:
			if self.shots[shot]:
				num_shots += 1
		status = 'Shots made: ' + str(num_shots) + '/' + str(len(self.shots))
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.lamps.tankCenter.disable()
		self.game.lamps.tankLeft.disable()
		self.game.lamps.tankRight.disable()

	def update_lamps(self):
		if not self.shots['center']:
			self.game.lamps.tankCenter.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		if not self.shots['left']:
			self.game.lamps.tankLeft.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		if not self.shots['right']:
			self.game.lamps.tankRight.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_topRightOpto_active(self, sw):
		if not self.shots['left']:
			if self.game.switches.leftRollover.time_since_change() < 1:
				self.game.lamps.tankLeft.disable()
				self.shots['left'] = True
				self.check_for_completion()
				self.game.score(10000)

	def sw_centerRampExit_active(self, sw):
		if not self.shots['center']:
			self.game.lamps.tankCenter.disable()
			self.shots['center'] = True
			self.check_for_completion()
			self.game.score(10000)

	def sw_threeBankTargets_active(self, sw):
		if not self.shots['right']:
			self.game.lamps.tankRight.disable()
			self.shots['right'] = True
			self.check_for_completion()
			self.game.score(10000)

	def check_for_completion(self):
		self.update_status()
		if self.shots['right'] and self.shots['left'] and self.shots['center']:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f BattleTank calling callback" % (time.time())
			self.callback()

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot all 3 battle tank shots")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class Meltdown(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Meltdown, self).__init__(game, priority, 'Meltdown')
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if difficulty == 'easy':
			self.shots_required_for_completion = 3
		elif difficulty == 'medium':
			self.shots_required_for_completion = 5
		else:
			self.shots_required_for_completion = 7

	def mode_started(self):
		self.game.lamps.stopMeltdown.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0
		self.update_status()

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.lamps.stopMeltdown.disable()

	def update_lamps(self):
		self.game.lamps.stopMeltdown.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_captiveBall1_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_captiveBall2_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_captiveBall3_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		self.update_status()
		if self.shots >= self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f Meltdown calling callback" % (time.time())
			self.callback()

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Activate " + str(self.shots_required_for_completion) + " captive ball switches")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class Impersonator(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Impersonator, self).__init__(game, priority, 'Impersonator')
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if difficulty == 'easy':
			self.shots_required_for_completion = 3
		elif difficulty == 'medium':
			self.shots_required_for_completion = 5
		else:
			self.shots_required_for_completion = 7

	def mode_started(self):
		self.game.lamps.awardBadImpersonator.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0
		self.timer = 0
		self.delay(name='moving_target', event_type=None, delay=1, handler=self.moving_target)
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active(): 
			self.game.coils.resetDropTarget.pulse(40)
		self.update_status()

	def update_status(self):
		if self.shots > self.shots_required_for_completion:
			extra_shots = self.shots - self.shots_required_for_completion
			status = 'Shots made: ' + str(extra_shots) + ' extra'
		else:
			status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.lamps.awardBadImpersonator.disable()
		self.game.lamps.dropTargetJ.disable()
		self.game.lamps.dropTargetU.disable()
		self.game.lamps.dropTargetD.disable()
		self.game.lamps.dropTargetG.disable()
		self.game.lamps.dropTargetE.disable()
		self.cancel_delayed('moving_target')

	def update_lamps(self):
		self.game.lamps.awardBadImpersonator.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)

	def sw_dropTargetJ_active(self,sw):
		if self.timer%6 == 0:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetU_active(self,sw):
		if self.timer%6 == 0 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetD_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 4 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetG_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 3 or self.timer%6 == 4:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetE_active(self,sw):
		if self.timer%6 == 3:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def moving_target(self):
		self.timer += 1
		self.game.lamps.dropTargetJ.disable()
		self.game.lamps.dropTargetU.disable()
		self.game.lamps.dropTargetD.disable()
		self.game.lamps.dropTargetG.disable()
		self.game.lamps.dropTargetE.disable()
		if self.timer%6 == 0:
			self.game.lamps.dropTargetJ.pulse(0)
			self.game.lamps.dropTargetU.pulse(0)
		elif self.timer%6 == 1 or self.timer%6==5:
			self.game.lamps.dropTargetU.pulse(0)
			self.game.lamps.dropTargetD.pulse(0)
		elif self.timer%6 == 2 or self.timer%6==4:
			self.game.lamps.dropTargetD.pulse(0)
			self.game.lamps.dropTargetG.pulse(0)
		elif self.timer%6 == 3:
			self.game.lamps.dropTargetG.pulse(0)
			self.game.lamps.dropTargetE.pulse(0)
		self.delay(name='moving_target', event_type=None, delay=1, handler=self.moving_target)

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot " + str(self.shots_required_for_completion) + " lit drop targets")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers

		

class Safecracker(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Safecracker, self).__init__(game, priority, 'Safe Cracker')
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if difficulty == 'easy':
			self.shots_required_for_completion = 2
		elif difficulty == 'medium':
			self.shots_required_for_completion = 3
		else:
			self.shots_required_for_completion = 4

	def mode_started(self):
		self.game.lamps.awardSafecracker.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active():
			self.game.coils.resetDropTarget.pulse(40)
		self.delay(name='trip_target', event_type=None, delay=2, handler=self.trip_target)
		self.update_status()

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.lamps.awardSafecracker.disable()
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active():
			self.game.coils.resetDropTarget.pulse(40)

	def update_lamps(self):
		self.game.lamps.awardSafecracker.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_subwayEnter2_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_dropTargetD_inactive_for_400ms(self, sw):
		self.game.coils.tripDropTarget.pulse(30)

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f Safecracker calling callback" % (time.time())
			self.callback()

	def trip_target(self):
		self.game.coils.tripDropTarget.pulse(30)

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot the subway " + str(self.shots_required_for_completion) + " times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class ManhuntMillions(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ManhuntMillions, self).__init__(game, priority, 'Manhunt')
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if difficulty == 'easy':
			self.shots_required_for_completion = 2
		elif difficulty == 'medium':
			self.shots_required_for_completion = 3
		else:
			self.shots_required_for_completion = 4

	def mode_started(self):
		self.game.coils.flasherPursuitL.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots = 0
		self.update_status()

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			print "% 10.3f Manhunt calling callback" % (time.time())
			self.callback()

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot the left ramp " + str(self.shots_required_for_completion) + " times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class Stakeout(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Stakeout, self).__init__(game, priority, 'Stakeout')
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if difficulty == 'easy':
			self.shots_required_for_completion = 2
		elif difficulty == 'medium':
			self.shots_required_for_completion = 3
		else:
			self.shots_required_for_completion = 4

	def mode_started(self):
		self.game.coils.flasherPursuitR.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots = 0
		self.update_status()

	def update_status(self):
		if self.shots > self.shots_required_for_completion:
			extra_shots = self.shots - self.shots_required_for_completion
			status = 'Shots made: ' + str(extra_shots) + ' extra'
		else:
			status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		

	def mode_stopped(self):
		self.game.coils.flasherPursuitR.disable()

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = dmd.TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = dmd.TextLayer(128/2, 24, font_small, "center").set_text("Shoot the right ramp " + str(self.shots_required_for_completion) + " times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers

	
class ModeTimer(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ModeTimer, self).__init__(game, priority)
		self.timer = 0;
		self.timer_update_callback = 'None'


	def mode_stopped(self):
		self.stop()

	def start(self, time):
		# Tell the mode how much time it gets, if it cares.
		if (self.timer_update_callback != 'None'):
			self.timer_update_callback(time)
		self.timer = time
		self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)
	def stop(self):
		self.timer = 0
		self.cancel_delayed('decrement timer')

	def add(self,adder):
		self.timer += adder 

	def pause(self, pause_unpause=True):
		if pause_unpause:
			self.cancel_delayed('decrement timer')
		elif self.timer > 0:
			self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)

	def decrement_timer(self):
		if self.timer > 0:
			self.timer -= 1
			self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)
			if (self.timer_update_callback != 'None'):
				self.timer_update_callback(self.timer)
		else:
			print "% 10.3f Timer calling callback" % (time.time())
			self.callback()

class PlayIntro(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(PlayIntro, self).__init__(game, priority)
		self.frame_counter = 0

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

	def setup(self, mode, exit_function, exit_function_param, instruction_layers):
		self.exit_function = exit_function
		self.exit_function_param = exit_function_param
		self.mode = mode
		self.instruction_layers = instruction_layers
		self.layer = dmd.GroupedLayer(128, 32, self.instruction_layers[0])

	def update_gi(self, on, num):
		for i in range(1,5):
			if num == 'all' or num == i:
				if on:
					self.game.lamps['gi0' + str(i)].pulse(0)
				else:
					self.game.lamps['gi0' + str(i)].disable()

	def sw_flipperLwL_active(self, sw):
		if self.game.switches.flipperLwR.is_active():
			self.cancel_delayed('intro')
			self.exit_function(self.exit_function_param)	

	def sw_flipperLwR_active(self, sw):
		if self.game.switches.flipperLwL.is_active():
			self.cancel_delayed('intro')
			self.exit_function(self.exit_function_param)	

	def next_frame(self):
		if self.frame_counter != len(self.instruction_layers):
			self.delay(name='intro', event_type=None, delay=2, handler=self.next_frame)
			self.layer = dmd.GroupedLayer(128, 32, self.instruction_layers[self.frame_counter])
			self.frame_counter += 1
		else:
			self.exit_function(self.exit_function_param)	


import procgame
from procgame import *

class ModeCompletedHurryup(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, font):
		super(ModeCompletedHurryup, self).__init__(game, priority)
		self.countdown_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.banner_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.countdown_layer, self.banner_layer])
	
	def mode_started(self):
		self.banner_layer.set_text("HURRY-UP!", 3)
		self.seconds_remaining = 13
		self.update_and_delay()
		self.game.lamps.multiballJackpot.schedule(schedule=0x33333333, cycle_seconds=0, now=True)
		if self.game.switches.dropTargetD.is_inactive():
			self.game.coils.tripDropTarget.pulse(30)

	def sw_dropTargetD_inactive_for_200ms(self, sw):
		self.game.coils.tripDropTarget.pulse(30)
			

	def mode_stopped(self):
		#self.drop_target_mode.animated_reset(1.0)
		self.game.lamps.multiballJackpot.disable()
		#if self.game.switches.popperL.is_open():
		#	self.game.coils.popperL.pulse(40)
	
	def sw_subwayEnter1_closed(self, sw):
		self.collected()
		self.cancel_delayed(['grace', 'countdown'])
		#self.delay(name='end_of_mode', event_type=None, delay=3.0, handler=self.delayed_removal)
		#Don't allow the popper to kick the ball back out until the mode is reset.
	
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
	def __init__(self, game, priority):
		super(ChainFeature, self).__init__(game, priority)
		self.completed = False

	def register_callback_function(self, function):
		self.callback = function

class Pursuit(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Pursuit, self).__init__(game, priority)
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
		print "Pursuit Started"

	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()
		self.game.coils.flasherPursuitR.disable()
		print "Pursuit Stopped"

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def check_for_completion(self):
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()
	
class Blackout(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Blackout, self).__init__(game, priority)
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

	def mode_stopped(self):
		self.game.lamps.blackoutJackpot.disable()
		self.game.coils.flasherBlackout.disable()
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)
		self.game.lamps.gi04.pulse(0)

	def sw_centerRampExit_active(self, sw):
		self.completed = True
		self.game.coils.flasherBlackout.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def check_for_completion(self):
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.set_status('Great job!')
			self.game.score(50000)

class Sniper(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Sniper, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.awardSniper.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0

	def mode_stopped(self):
		self.game.lamps.awardSniper.disable()

	def sw_popperR_active_for_300ms(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def check_for_completion(self):
		if self.shots == 2:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

class BattleTank(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(BattleTank, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.tankCenter.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.game.lamps.tankLeft.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.game.lamps.tankRight.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = {'left':False,'center':False,'right':False}

	def mode_stopped(self):
		self.game.lamps.tankCenter.disable()
		self.game.lamps.tankLeft.disable()
		self.game.lamps.tankRight.disable()

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
		if self.shots['right'] and self.shots['left'] and self.shots['center']:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

class Meltdown(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Meltdown, self).__init__(game, priority)
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

	def mode_stopped(self):
		self.game.lamps.stopMeltdown.disable()

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
		if self.shots >= self.shots_required_for_completion:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

class Impersonator(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Impersonator, self).__init__(game, priority)
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

	def mode_stopped(self):
		self.game.lamps.awardBadImpersonator.disable()
		self.game.lamps.dropTargetJ.disable()
		self.game.lamps.dropTargetU.disable()
		self.game.lamps.dropTargetD.disable()
		self.game.lamps.dropTargetG.disable()
		self.game.lamps.dropTargetE.disable()
		self.cancel_delayed('moving_target')

	def check_for_completion(self):
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.set_status('Great Job!')
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
		

class Safecracker(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Safecracker, self).__init__(game, priority)
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

	def mode_stopped(self):
		self.game.lamps.awardSafecracker.disable()
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active():
			self.game.coils.resetDropTarget.pulse(40)

	def sw_subwayEnter2_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

	def trip_target(self):
		self.game.coils.tripDropTarget.pulse(50)


class ManhuntMillions(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ManhuntMillions, self).__init__(game, priority)
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

	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.set_status('Great Job!')
			self.game.score(50000)
			self.callback()

class Stakeout(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Stakeout, self).__init__(game, priority)
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

	def mode_stopped(self):
		self.game.coils.flasherPursuitR.disable()

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.set_status('Great Job!')
			self.game.score(50000)

	
class ModeTimer(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ModeTimer, self).__init__(game, priority)
		self.timer = 0;

	def mode_stopped(self):
		self.timer = 0;

	def start(self, time):
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
		else:
			self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)

	def decrement_timer(self):
		if self.timer > 0:
			self.timer -= 1
			self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)
			self.game.set_status('Mode Timer: ' + str(self.timer))
		else:
			self.callback()

class PlayIntro(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, mode, exit_function, exit_function_param, font):
		super(PlayIntro, self).__init__(game, priority)
		self.abort = 0
		self.exit_function = exit_function
		self.exit_function_param = exit_function_param
		self.banner_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.countdown_layer = dmd.TextLayer(128/2, 20, font, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer, self.countdown_layer])
		self.mode = mode
	
	def mode_started(self):
		self.frame_counter = 5
		self.delay(name='intro', event_type=None, delay=1, handler=self.next_frame)
		self.banner_layer.set_text(str(self.mode) + ' intro')
		self.update_gi(False, 'all')

	def mode_stopped(self):
		if self.abort:
			self.cancel_delayed('intro')
		self.update_gi(True, 'all')

	def update_gi(self, on, num):
		for i in range(1,5):
			if num == 'all' or num == i:
				if on:
					self.game.lamps['gi0' + str(i)].pulse(0)
				else:
					self.game.lamps['gi0' + str(i)].disable()

	def sw_flipperLwL_active(self, sw):
		if self.game.switches.flipperLwR.is_active():
			self.exit_function(self.exit_function_param)	
			self.abort = 1

	def sw_flipperLwR_active(self, sw):
		if self.game.switches.flipperLwL.is_active():
			self.exit_function(self.exit_function_param)	
			self.abort = 1

	def next_frame(self):
		if self.frame_counter > 0:
			self.delay(name='intro', event_type=None, delay=1, handler=self.next_frame)
			self.countdown_layer.set_text(str(self.frame_counter))
			self.frame_counter -= 1
		else:
			self.exit_function(self.exit_function_param)	



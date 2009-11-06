from procgame import *
from chain_features import *
from multiball import *
from crimescenes import *
from missile_award import *

class JD_Modes(modes.Scoring_Mode):
	"""docstring for JD_Modes"""
	def __init__(self, game, priority, font_small, font_big):
		super(JD_Modes, self).__init__(game, priority)
		self.reset()
		self.mode_timer = ModeTimer(game, priority+1)
		self.mode_pursuit = Pursuit(game, priority+1)
		self.mode_blackout = Blackout(game, priority+1)
		self.mode_sniper = Sniper(game, priority+1)
		self.mode_battleTank = BattleTank(game, priority+1)
		self.mode_impersonator = Impersonator(game, priority+1)
		self.mode_meltdown = Meltdown(game, priority+1)
		self.mode_safecracker = Safecracker(game, priority+1)
		self.mode_manhunt = ManhuntMillions(game, priority+1)
		self.mode_stakeout = Stakeout(game, priority+1)
		self.font = font_small
		self.crimescenes = Crimescenes(game, priority+1)
		self.crimescenes.crimescenes_completed = self.crimescenes_completed
		self.missile_award_mode = Missile_Award_Mode(game, priority+1, font_small)
		self.missile_award_mode.callback = self.award_missile_award
		self.mode_completed_hurryup = ModeCompletedHurryup(game, priority+1, font_small)
		self.mode_completed_hurryup.collected = self.hurryup_collected
		self.mode_completed_hurryup.expired = self.hurryup_expired
		self.multiball = Multiball(self.game, priority + 1, self.game.user_settings['Machine']['deadworld_mod_installed'], font_big)
		self.multiball.start_callback = self.multiball_started
		self.multiball.end_callback = self.multiball_ended

	def reset(self):
		self.state = 'idle'
		self.judges_attempted = []
		self.judges_not_attempted = ['Fear', 'Mortis', 'Death', 'Fire']
		self.modes_attempted = []
		self.modes_not_attempted = ['pursuit', 'blackout', 'sniper', 'battleTank', 'impersonator', 'meltdown', 'safecracker', 'manhunt', 'stakeout']
		self.modes_just_attempted = []
		self.active_mode_pointer = 0
		self.multiball_active = False
		self.modes_not_attempted_ptr = 0
		self.mode_active = False
		self.mode_list = {}
		self.mode = 0
		self.extra_balls_lit = 0
		self.total_extra_balls_lit = 0
		self.mystery_lit = False
		self.missile_award_lit = False
		self.missile_award_lit_save = False
		self.num_modes_completed = 0
		self.modes_completed = []
		self.hold_bonus_x = 0
		self.num_hurryups_collected = 0
		self.num_extra_mode_balls = 0
		for mode in self.modes_not_attempted:
			self.drive_mode_lamp(mode, 'off')
		self.drive_mode_lamp('mystery', 'off')
		for judge in self.judges_not_attempted:
			self.game.coils['flasher' + judge].disable()

		# disable auto-plunging for the start of ball - Force player to hit the
		# right Fire button.
		self.auto_plunge = 0

	def reset_modes(self):
		self.modes_attempted = []
		self.modes_not_attempted = ['pursuit', 'blackout', 'sniper', 'battleTank', 'impersonator', 'meltdown', 'safecracker', 'manhunt', 'stakeout']
		self.modes_just_attempted = []
		self.active_mode_pointer = 0

	def mode_started(self):
		self.mode_timer.callback = self.mode_over
		self.mode_list['pursuit'] = self.mode_pursuit
		self.mode_list['blackout'] = self.mode_blackout
		self.mode_list['sniper'] = self.mode_sniper
		self.mode_list['battleTank'] = self.mode_battleTank
		self.mode_list['impersonator'] = self.mode_impersonator
		self.mode_list['meltdown'] = self.mode_meltdown
		self.mode_list['safecracker'] = self.mode_safecracker
		self.mode_list['manhunt'] = self.mode_manhunt
		self.mode_list['stakeout'] = self.mode_stakeout
		self.multiball.launch_balls = self.launch_balls
		for mode in self.mode_list:
			self.mode_list[mode].callback = self.mode_over
		self.crimescenes.light_extra_ball_function = self.light_extra_ball
		self.game.modes.add(self.mode_timer)
		self.game.modes.add(self.crimescenes)
		self.game.modes.add(self.multiball)

	def mode_stopped(self):
		self.game.modes.remove(self.mode_timer)
		self.game.modes.remove(self.crimescenes)
		self.game.modes.remove(self.multiball)
		if self.mode_active:
			this_mode = self.mode_list[self.mode]
			self.game.modes.remove(self.mode_list[self.mode])
		for coil in self.game.coils:
			if coil.name.find('flasher', 0) != -1:
				coil.disable()
			

	def get_info_record(self):
		info_record = {}
		info_record['state'] = self.state
		info_record['judges_attempted'] = self.judges_attempted
		info_record['judges_not_attempted'] = self.judges_not_attempted
		info_record['mode'] = self.mode
		info_record['modes_attempted'] = self.modes_attempted
		info_record['modes_completed'] = self.modes_completed
		info_record['modes_just_attempted'] = self.modes_just_attempted
		info_record['modes_not_attempted'] = self.modes_not_attempted
		info_record['modes_not_attempted_ptr'] = self.modes_not_attempted_ptr
		info_record['extra_balls_lit'] = self.extra_balls_lit
		info_record['total_extra_balls_lit'] = self.total_extra_balls_lit
		info_record['mystery_lit'] = self.mystery_lit
		info_record['missile_award_lit'] = self.missile_award_lit or self.missile_award_lit_save
		info_record['num_modes_completed'] = self.num_modes_completed
		info_record['crimescenes'] = self.crimescenes.get_info_record()
		info_record['missile_award_mode'] = self.missile_award_mode.get_info_record()
		info_record['multiball'] = self.multiball.get_info_record()
		info_record['num_hurryups_collected'] = self.num_hurryups_collected
		info_record['num_extra_mode_balls'] = self.num_extra_mode_balls
		if self.hold_bonus_x:
			info_record['bonus_x'] = self.bonus_x
		else:
			info_record['bonus_x'] = 1
		return info_record

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.state = info_record['state']
			self.mode= info_record['mode']
			self.modes_attempted = info_record['modes_attempted']
			self.modes_completed = info_record['modes_completed']
			self.modes_just_attempted = info_record['modes_just_attempted']
			self.modes_not_attempted = info_record['modes_not_attempted']
			self.modes_not_attempted_ptr = info_record['modes_not_attempted_ptr']
			self.judges_attempted = info_record['judges_attempted']
			self.judges_not_attempted = info_record['judges_not_attempted']
			self.extra_balls_lit = info_record['extra_balls_lit']
			self.total_extra_balls_lit = info_record['total_extra_balls_lit']
			self.mystery_lit = info_record['mystery_lit']
			self.missile_award_lit = info_record['missile_award_lit']
			self.num_modes_completed = info_record['num_modes_completed']
			self.crimescenes.update_info_record(info_record['crimescenes'])
			self.missile_award_mode.update_info_record(info_record['missile_award_mode'])
			self.multiball.update_info_record(info_record['multiball'])
			self.bonus_x = info_record['bonus_x']
			self.num_hurryups_collected = info_record['num_hurryups_collected']
			self.num_extra_mode_balls = info_record['num_extra_mode_balls']
		else:	
			self.crimescenes.update_info_record({})
			self.missile_award_mode.update_info_record({})
		
		self.begin_processing()

	def end_multiball(self):
		if self.multiball_active:
			self.multiball.end_multiball()

	def award_missile_award(self, award):
		if award.find('Points', 0) != -1:
			award_words = award.rsplit(' ')
			self.game.score(int(award_words[0]))
			self.game.set_status(award)
		elif award == 'Light Extra Ball':
			self.light_extra_ball()
		elif award == 'Advance Crimescenes':
			self.crimescenes.level_complete()
		elif award == 'Bonus X+1':
			self.inc_bonus_x()
		elif award == 'Hold Bonus X':
			self.hold_bonus_x = True
		if self.state == 'mode':
			self.mode_timer.pause(False)

	def light_extra_ball(self):
		if self.total_extra_balls_lit == self.game.user_settings['Gameplay']['Max extra balls per game']:
			self.game.set_status('No more extras this game.')
		elif self.extra_balls_lit == self.game.user_settings['Gameplay']['Max extra balls lit']:
			self.game.set_status('Extra balls lit maxed.')
		else:
			self.extra_balls_lit += 1
			self.total_extra_balls_lit += 1
			self.enable_extra_ball()

	def enable_extra_ball(self):
		self.drive_mode_lamp('extraBall2','on')

	def get_bonus_base(self):
		# Add bonus info: 5000 bonus for attempting
		num_modes_completed_str = 'Modes Completed: ' + str(len(self.modes_completed))
		num_modes_attempted_str = 'Modes Attempted: ' + str(len(self.modes_attempted))
		bonus_base_elements = {}
		bonus_base_elements[num_modes_attempted_str] = len(self.modes_attempted)*4000
		bonus_base_elements[num_modes_completed_str] = len(self.modes_completed)*12000
		bonus_base_elements.update(self.crimescenes.get_bonus_base())
		return bonus_base_elements

	def get_bonus_x(self):
		return self.bonus_x

	def begin_processing(self):
		for mode in self.modes_attempted:
			self.drive_mode_lamp(mode, 'on')
		if self.is_ultimate_challenge_ready():
			self.setup_ultimate_challenge()
		elif self.state == 'idle':
			self.setup_next_mode()
		elif self.state == 'mode':
			self.mode_complete()
		elif self.state == 'ultimate_challenge':
			self.ultimate_challenge_complete()
		if self.extra_balls_lit > 0:
			self.enable_extra_ball()
		if self.mystery_lit:
			self.drive_mode_lamp('mystery', 'on')
		if self.missile_award_lit:
			self.drive_mode_lamp('airRade', 'medium')


	def rotate_modes(self, adder):
		self.disable_not_attempted_mode_lamps()
		self.active_mode_pointer += adder
		if len(self.modes_not_attempted) == 0:
			self.modes_not_attempted_ptr = 0
		else:
			self.modes_not_attempted_ptr = self.active_mode_pointer % len(self.modes_not_attempted)
		print "mode_ptr"
		print self.modes_not_attempted_ptr
		if self.state == 'idle':
			self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'slow')

	def disable_not_attempted_mode_lamps(self):
		for mode in self.modes_not_attempted:
			self.game.lamps[mode].disable()

	def drive_mode_lamp(self, lamp_name, style='on'):
		if style == 'slow':
			self.game.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		if style == 'medium':
			self.game.lamps[lamp_name].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
		if style == 'fast':
			self.game.lamps[lamp_name].schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		elif style == 'on':
			self.game.lamps[lamp_name].pulse(0)
		elif style == 'off':
			self.game.lamps[lamp_name].disable()

	def sw_captiveBall3_active(self, sw):
		self.inc_bonus_x()

	def inc_bonus_x(self):
		self.bonus_x += 1
		self.game.set_status("Bonus Multiplier at " + str(self.bonus_x))

	def sw_leftScorePost_active(self, sw):
		if self.extra_balls_lit > 0:
			self.award_extra_ball()

	def sw_rightTopPost_active(self, sw):
		if self.extra_balls_lit > 0:
			self.award_extra_ball()

	def sw_mystery_active(self, sw):
		if self.mystery_lit:
			self.mystery_lit = False
			self.drive_mode_lamp('mystery', 'off')
			if self.multiball_active:
				if self.game.ball_save.timer > 0:
					self.game.set_status('+10 second ball saver')
					self.game.ball_save.add(10)
				else:
					self.game.ball_save.start(num_balls_to_save=self.game.ball_tracker.num_balls_in_play, time=10, now=True, allow_multiple_saves=True)
				
			elif self.state == 'mode':
				self.mode_timer.add(10)
				self.game.set_status('Adding 10 seconds')
			else:
				self.game.ball_save.start(num_balls_to_save=1, time=10, now=True, allow_multiple_saves=True)
				self.game.set_status('+10 second ball saver')
				self.missile_award_lit = True
				self.drive_mode_lamp('airRade', 'medium')

	def award_extra_ball(self):
		self.game.extra_ball()
		self.extra_balls_lit -= 1
		print "extra balls_lit"
		print self.extra_balls_lit
		if self.extra_balls_lit == 0:
			self.drive_mode_lamp('extraBall2','off')
		self.game.set_status('Extra Ball!')

	def sw_shooterL_active_for_200ms(self, sw):
		if self.multiball_active:
			self.game.coils.shooterL.pulse()
		elif self.missile_award_lit:
			self.drive_mode_lamp('airRade', 'off')
			self.missile_award_lit = False
			self.game.modes.add(self.missile_award_mode)
			if self.state == 'mode':
				self.mode_timer.pause(True)
		else:
			self.game.coils.shooterL.pulse()
			self.missile_award_lit = True
			self.drive_mode_lamp('airRade', 'medium')
			

	def sw_fireR_active(self, sw):
		if self.game.switches.shooterR.is_inactive():
			self.rotate_modes(1)
		else:
			self.game.coils.shooterR.pulse(50)

	

	def sw_fireL_active(self, sw):
		if self.game.switches.shooterL.is_inactive():
			self.rotate_modes(-1)
		else:
			self.game.coils.shooterL.pulse(50)

	def sw_rightRampExit_closed(self, sw):
		self.game.set_status("Right ramp!")
		self.game.coils.flashersRtRamp.schedule(0x333, cycle_seconds=1, now=False)
		self.game.score(2000)
	
	def sw_slingL_active(self, sw):
		self.rotate_modes(-1)

	def sw_slingR_active(self, sw):
		self.rotate_modes(1)

	def sw_popperL_open_for_200ms(self, sw):
		self.flash_then_pop('flashersLowerLeft', 'popperL', 50)

	def popperR_eject(self):
		self.flash_then_pop('flashersRtRamp', 'popperR', 20)

	def flash_then_pop(self, flasher, coil, pulse):
		self.game.coils[flasher].schedule(0x00555555, cycle_seconds=1, now=True)
		self.delay(name='delayed_pop', event_type=None, delay=1.0, handler=self.delayed_pop, param=[coil, pulse])

	def delayed_pop(self, coil_pulse):
		self.game.coils[coil_pulse[0]].pulse(coil_pulse[1])	


	def sw_popperR_active_for_200ms(self, sw):
		if not self.multiball_active:
			if self.state == 'idle':
				self.game.lamps.rightStartFeature.disable()
				self.play_intro = PlayIntro(self.game, self.priority+1, self.modes_not_attempted[self.modes_not_attempted_ptr], self.activate_mode, self.modes_not_attempted[0], self.font)
				self.game.modes.add(self.play_intro)
			elif self.state == 'pre_ultimate_challenge':
				self.game.lamps.rightStartFeature.disable()
				self.play_intro = PlayIntro(self.game, self.priority+1, 'ultimate_challenge', self.activate_mode, 'ultimate_challenge', self.font)
				self.game.modes.add(self.play_intro)
			else:
				self.popperR_eject()
		else:
			self.popperR_eject()

	def sw_outlaneL_closed(self, sw):
		self.game.score(1000)
		#self.game.sound.play('outlane')

	def sw_outlaneR_closed(self, sw):
		self.game.score(1000)
		#self.game.sound.play('outlane')

	# Enable auto-plunge as soon as the new ball is launched (by the player).
	def sw_shooterR_open_for_2s(self,sw):
		self.auto_plunge = 1

	def sw_shooterR_closed_for_300ms(self,sw):
		if (self.auto_plunge):
			self.game.coils.shooterR.pulse(50)

	def activate_mode(self, mode):
		self.game.modes.remove(self.play_intro)
		self.popperR_eject()

		if self.state == 'idle':
			self.game.lamps[self.modes_not_attempted[self.modes_not_attempted_ptr]].schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
			self.mode = self.modes_not_attempted[self.modes_not_attempted_ptr]
			print "self.mode"
			print self.mode
			if self.mode == 'impersonator' or self.mode == 'safecracker':
				self.multiball.drops.paused = True
			self.modes_not_attempted.remove(self.mode)
			self.modes_attempted.append(self.mode)
			self.modes_just_attempted.append(self.mode)
			self.state = 'mode'
			self.game.modes.add(self.mode_list[self.mode])
			self.mode_timer.start(self.game.user_settings['Gameplay']['Time per chain feature'])
			self.mode_active = True
			self.drive_mode_lamp('mystery', 'on')
			self.mystery_lit = True
			if self.num_extra_mode_balls > 0:
				self.launch_balls([self.num_extra_mode_balls,0,0,False,False])
				self.game.ball_tracker.num_balls_in_play += self.num_extra_mode_balls
				self.num_extra_mode_balls = 0
			
		elif self.state == 'pre_ultimate_challenge':
			if self.missile_award_lit:
				self.missile_award_lit_save = True
				self.missile_award_lit = False
				self.drive_mode_lamp('airRade', 'off')
		
			self.game.set_status('challenge in progress')
			self.state = 'ultimate_challenge'
			self.drive_mode_lamp('mystery', 'on')
			self.mystery_lit = True

	def setup_next_mode(self):
		print "setup_next_mode"
		if not self.multiball_active:
			self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'slow')
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def setup_ultimate_challenge(self):
		self.state = 'pre_ultimate_challenge'
		if not self.multiball_active:
			self.game.lamps.ultChallenge.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def multiball_started(self):
		self.game.lamps.rightStartFeature.disable()
		self.multiball_active = True
		self.drive_mode_lamp('mystery', 'on')
		self.mystery_lit = True
		if self.missile_award_lit:
			self.drive_mode_lamp('airRade', 'off')
			self.missile_award_lit_save = True

	def multiball_ended(self):
		self.multiball_active = False
		if self.is_ultimate_challenge_ready():
			self.setup_ultimate_challenge()
		elif self.state == 'idle':
			self.setup_next_mode()
		if self.missile_award_lit_save:
			self.missile_award_lit = True
			self.drive_mode_lamp('airRade', 'medium')

	def mode_over(self):
		self.game.modes.remove(self.mode_list[self.mode])
		if self.mode_timer.timer > 0:
			self.mode_timer.stop()
		self.mode_active = False
		this_mode = self.mode_list[self.mode]
		success = this_mode.completed
		if self.state == 'mode':
			self.mode_complete(success)	
		elif self.state == 'ultimate_challenge':
			self.ultimate_challenge_complete()	

	def hurryup_collected(self):
		print "hurryup_collected"
		print self.num_hurryups_collected
		if self.num_hurryups_collected == 0:
			self.crimescenes.level_complete(3)
		elif self.num_hurryups_collected == 1:
			self.light_extra_ball()
		elif self.num_hurryups_collected == 2:
			self.num_extra_mode_balls = 1
		elif self.num_hurryups_collected == 3:
			self.num_extra_mode_balls = 2
		elif self.num_hurryups_collected == 4:
			self.num_extra_mode_balls = 3
		elif self.num_hurryups_collected == 5:
			self.light_extra_ball()
		elif self.num_hurryups_collected == 6:
			self.crimescenes.level_complete(3)
		elif self.num_hurryups_collected == 7:
			self.crimescenes.level_complete(3)
		elif self.num_hurryups_collected == 8:
			self.game.score(1000000)
		self.hurryup_expired()
		self.num_hurryups_collected += 1

	def hurryup_expired(self):
		self.game.modes.remove(self.mode_completed_hurryup)
		if not self.multiball_active:
			self.multiball.drops.animated_reset(.1)
			if self.is_ultimate_challenge_ready():
				self.setup_ultimate_challenge()
			if len(self.modes_not_attempted) > 0:
				self.rotate_modes(1)
				self.state = 'idle'
				self.setup_next_mode()

	def crimescenes_completed(self):
		if self.is_ultimate_challenge_ready():
			self.setup_ultimate_challenge()
		

	def is_ultimate_challenge_ready(self):
		return self.multiball.jackpot_collected and self.crimescenes.complete and len(self.modes_not_attempted) == 0

	def mode_complete(self, successful=False):
		self.multiball.drops.paused = False

		# Success: Add to success list and start hurryup
		if successful:
			self.game.modes.add(self.mode_completed_hurryup)
			self.modes_completed.append(self.mode)
			self.num_modes_completed += 1
		else:
			if self.is_ultimate_challenge_ready():
				self.setup_ultimate_challenge()
			if len(self.modes_not_attempted) > 0:
				self.rotate_modes(1)
				self.state = 'idle'
				self.setup_next_mode()

		# Turn on mode lamp to show it has been attempted
		self.drive_mode_lamp(self.mode, 'on')

		if self.mode == 'impersonator' or self.mode == 'safecracker':
			self.multiball.drops.animated_reset(.1)

	def ultimate_challenge_complete(self):
		self.reset_modes()
		self.crimescenes.reset_complete()
		self.multiball.reset_jackpot_collected()


from procgame import *
from chain_features import *
from multiball import *
from crimescenes import *
from missile_award import *

music_path = "./games/jd/sound/"

class JD_Modes(modes.Scoring_Mode):
	"""docstring for JD_Modes"""
	def __init__(self, game, priority, font_small, font_big):
		super(JD_Modes, self).__init__(game, priority)

		self.font = font_small

		# Reset member variables
		self.reset()
		
		# Instantiate sub-modes
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
		self.crimescenes = Crimescenes(game, priority+1)
		self.crimescenes.crimescenes_completed = self.crimescenes_completed
		self.missile_award_mode = Missile_Award_Mode(game, priority+1, font_small)
		self.missile_award_mode.callback = self.award_missile_award
		self.mode_completed_hurryup = ModeCompletedHurryup(game, priority+1)
		self.mode_completed_hurryup.collected = self.hurryup_collected
		self.mode_completed_hurryup.expired = self.hurryup_expired
		self.multiball = Multiball(self.game, priority + 1, self.game.user_settings['Machine']['Deadworld mod installed'], font_big)
		self.multiball.start_callback = self.multiball_started
		self.multiball.end_callback = self.multiball_ended

		#self.game.sound.register_music('background', music_path+"mainSongLoop.mp3")
		#self.game.sound.register_music('background', music_path+"mainSongDarkerSlower.mp3")
		#self.game.sound.register_music('background', music_path+"mainSongDarkerFaster.mp3")
		self.game.sound.register_music('background', music_path+"mainSongDarkerEvenFaster.mp3")
		self.game.sound.register_sound('ball_launch', music_path+"preBallLaunch.wav")


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
		self.tilt = False

	def reset_modes(self):
		self.modes_attempted = []
		self.modes_not_attempted = ['pursuit', 'blackout', 'sniper', 'battleTank', 'impersonator', 'meltdown', 'safecracker', 'manhunt', 'stakeout']
		self.modes_just_attempted = []
		self.active_mode_pointer = 0

	def mode_started(self):
		self.mode_timer.callback = self.mode_over

		# Set up a mode list dictionary using mode names as keys for easy access.
		self.mode_list['pursuit'] = self.mode_pursuit
		self.mode_list['blackout'] = self.mode_blackout
		self.mode_list['sniper'] = self.mode_sniper
		self.mode_list['battleTank'] = self.mode_battleTank
		self.mode_list['impersonator'] = self.mode_impersonator
		self.mode_list['meltdown'] = self.mode_meltdown
		self.mode_list['safecracker'] = self.mode_safecracker
		self.mode_list['manhunt'] = self.mode_manhunt
		self.mode_list['stakeout'] = self.mode_stakeout
		for mode in self.mode_list:
			self.mode_list[mode].callback = self.mode_over
		self.crimescenes.light_extra_ball_function = self.light_extra_ball

		# Add modes that are always active
		self.game.modes.add(self.mode_timer)
		self.game.modes.add(self.crimescenes)
		self.game.modes.add(self.multiball)

		# Set flag for switch events the do something unique the first time they
		# they are triggered.
		self.ball_starting = True

	def mode_stopped(self):

		# Remove modes from the mode Q
		self.game.modes.remove(self.mode_timer)
		self.game.modes.remove(self.crimescenes)
		self.game.modes.remove(self.multiball)
		if self.mode_active:
			this_mode = self.mode_list[self.mode]
			self.game.modes.remove(self.mode_list[self.mode])

		# Disable all flashers.
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

	def ball_drained(self):
		# Called as a result of a ball draining into the trough.
		# End multiball if there is now only one ball in play (and MB was active).
		if self.multiball_active and self.game.trough.num_balls_in_play == 1:
			self.multiball.end_multiball()

	# Award missile award indicated by award param.
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
	
	def light_extra_ball(self):
		if self.total_extra_balls_lit == self.game.user_settings['Gameplay']['Max extra balls per game']:
			self.game.set_status('No more extras this game.')
		elif self.extra_balls_lit == self.game.user_settings['Gameplay']['Max extra balls lit']:
			self.game.set_status('Extra balls lit maxed.')
		else:
			self.extra_balls_lit += 1
			self.total_extra_balls_lit += 1
			self.enable_extra_ball_lamp()

	def enable_extra_ball_lamp(self):
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
		self.mystery_lit = True
		self.update_lamps()
		if self.is_ultimate_challenge_ready():
			self.setup_ultimate_challenge()
		elif self.state == 'idle':
			self.setup_next_mode()
		elif self.state == 'mode':
			self.mode_complete()
		elif self.state == 'ultimate_challenge':
			self.ultimate_challenge_complete()

	def update_lamps(self):
		if self.state == 'idle' or self.state == 'mode':
			for mode in self.modes_attempted:
				self.drive_mode_lamp(mode, 'on')
			if self.state == 'mode':
				self.drive_mode_lamp(self.mode,'slow')
			else:
				if self.game.switches.popperR.is_inactive() and not self.multiball_active:
					self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
				self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'slow')
			self.drive_mode_lamp('ultChallenge','off') 
		elif self.state == 'ultimate_challenge':
			self.drive_mode_lamp('ultChallenge','slow') 
		elif self.state == 'pre_ultimate_challenge':
			self.drive_mode_lamp('ultChallenge','slow') 
			if not self.multiball_active:
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

		if self.mystery_lit:
			self.drive_mode_lamp('mystery', 'on')

		if self.missile_award_lit:
			self.drive_mode_lamp('airRade', 'medium')

		if self.extra_balls_lit > 0:
			self.enable_extra_ball_lamp()


	def rotate_modes(self, adder):

		# Start by turning off all lamps of not attempted modes
		self.disable_not_attempted_mode_lamps()
		# Increment the mode pointer
		self.active_mode_pointer += adder
		# Adjust the pointer based on the number of not attempted modes
		if len(self.modes_not_attempted) == 0:
			self.modes_not_attempted_ptr = 0
		else:
			self.modes_not_attempted_ptr = self.active_mode_pointer % len(self.modes_not_attempted)
		# Drive the lamp of the selected mode.
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
		self.drive_mode_lamp('mystery', 'on')
		self.mystery_lit = True
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
					self.game.ball_save.start(num_balls_to_save=self.game.trough.num_balls_in_play, time=10, now=True, allow_multiple_saves=True)
				
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

	def sw_shooterL_active_for_500ms(self, sw):
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

	def sw_shooterL_inactive_for_200ms(self, sw):
		self.mode_timer.pause(False)
			

	def sw_fireR_active(self, sw):
		if self.game.switches.shooterR.is_inactive():
			self.rotate_modes(1)
		else:
			self.game.coils.shooterR.pulse(50)
			if self.ball_starting:
				self.game.sound.stop('ball_launch')
				self.game.sound.play_music('background')

	

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
				self.mode = self.modes_not_attempted[self.modes_not_attempted_ptr]
				intro_instruction_layers = self.mode_list[self.mode].get_instruction_layers()
				self.play_intro = PlayIntro(self.game, self.priority+1, self.modes_not_attempted[self.modes_not_attempted_ptr], self.activate_mode, self.modes_not_attempted[0], intro_instruction_layers)
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
	def sw_shooterR_open_for_1s(self,sw):
		self.auto_plunge = 1

		if self.ball_starting and not self.tilt:
			ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
			self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=True, allow_multiple_saves=False)
		self.ball_starting = False
			
	def sw_shooterR_active(self,sw):
		if self.ball_starting: 
			self.game.sound.play('ball_launch',loops=-1)

	def sw_shooterR_closed_for_700ms(self,sw):
		if (self.auto_plunge):
			self.game.coils.shooterR.pulse(50)

	def activate_mode(self, mode):
		self.game.modes.remove(self.play_intro)

		# Put the ball back into play
		self.popperR_eject()

		if self.state == 'idle':
			# Get the active mode
			self.mode = self.modes_not_attempted[self.modes_not_attempted_ptr]
			# Drive lamp of the starting mode
			self.drive_mode_lamp(self.mode, 'slow')
			
			# Pause multibal drop target mode if this mode uses the drop targets.
			if self.mode == 'impersonator' or self.mode == 'safecracker':
				self.multiball.drops.paused = True

			# Update the mode lists.
			self.modes_not_attempted.remove(self.mode)
			self.modes_attempted.append(self.mode)
			self.modes_just_attempted.append(self.mode)

			# Change state to indicate a mode is in progress.
			self.state = 'mode'

			# Add the mode to the mode Q to activate it.
			self.game.modes.add(self.mode_list[self.mode])

			# Start the mode timer
			self.mode_timer.start(self.game.user_settings['Gameplay']['Time per chain feature'])
			self.mode_active = True

			# See if any extra mode balls need to be launched.
			if self.num_extra_mode_balls > 0:
				self.game.trough.launch_balls(self.num_extra_mode_balls, 'None')
				self.num_extra_mode_balls = 0
			
		elif self.state == 'pre_ultimate_challenge':
			# Disable missile award.  Save it so it can be reactivate later.
			if self.missile_award_lit:
				self.missile_award_lit_save = True
				self.missile_award_lit = False
				self.drive_mode_lamp('airRade', 'off')
		
			# Change state to indicate ultimate challenge is active
			self.game.set_status('challenge in progress')
			self.state = 'ultimate_challenge'

			# Light mystery to start the finale
			self.drive_mode_lamp('mystery', 'on')
			self.mystery_lit = True

			# Start ultimate challenge!
			# self.game.modes.add(self.ultimate_challenge)

	def setup_next_mode(self):
		# Don't setup a mode if in multiball.
		if not self.multiball_active:
			# Turn on lamps to tell player what's going on.
			self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'slow')
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def setup_ultimate_challenge(self):
		self.state = 'pre_ultimate_challenge'
		if not self.multiball_active:
			# Turn on lamps to tell player what's going on.
			self.game.lamps.ultChallenge.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def multiball_started(self):
		# No modes can be started when multiball is active
		self.game.lamps.rightStartFeature.disable()
		self.multiball_active = True
		# Light mystery once for free.
		self.drive_mode_lamp('mystery', 'on')
		self.mystery_lit = True
		# Disable missile award but save it for later if lit.
		if self.missile_award_lit:
			self.drive_mode_lamp('airRade', 'off')
			self.missile_award_lit_save = True

	def multiball_ended(self):
		self.multiball_active = False

		# See about starting the finale
		if self.is_ultimate_challenge_ready():
			self.setup_ultimate_challenge()
		# Otherwise see about setting up the next mode.
		elif self.state == 'idle':
			self.setup_next_mode()
		# Re-enable missile_award if it was lit before multiball started
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
		settings_key = 'Mode hurry-up award: ' + str(self.num_hurryups_collected)
		award = self.game.user_settings['Gameplay'][settings_key]
		if award == 'Advance 3 crimescenes':
			self.crimescenes.level_complete(3)
		elif award == 'Light extra ball':
			self.light_extra_ball()
		elif award == 'Add 1 ball for next mode':
			self.num_extra_mode_balls = 1
		elif award == 'Add 2 balls for next mode':
			self.num_extra_mode_balls = 2
		elif award == 'Add 3 balls for next mode':
			self.num_extra_mode_balls = 3
		elif award == '1,000,000 points':
			self.game.score(1000000)

		self.hurryup_expired()
		self.num_hurryups_collected += 1
		self.game.modes.remove(self.mode_completed_hurryup)

	def hurryup_expired(self):
		self.game.modes.remove(self.mode_completed_hurryup)
		if not self.multiball_active:
			self.multiball.drops.animated_reset(.1)
			# See if it's time for the finale!
			if self.is_ultimate_challenge_ready():
				self.setup_ultimate_challenge()
			# If more modes to do, rotate and setup the next one.
			elif len(self.modes_not_attempted) > 0:
				self.rotate_modes(1)
				self.state = 'idle'
				self.setup_next_mode()
			else:
				self.state = 'modes_complete'

	def crimescenes_completed(self):
		if self.is_ultimate_challenge_ready():
			self.setup_ultimate_challenge()
		

	def is_ultimate_challenge_ready(self):
			# 3 Criteria for finale: jackpot, crimescenes, all modes attempted.
		return self.multiball.jackpot_collected and \
                       self.crimescenes.complete and \
                       len(self.modes_not_attempted) == 0

	def mode_complete(self, successful=False):
		self.multiball.drops.paused = False

		# Success: Add to success list and start hurryup
		if successful:
			self.game.modes.add(self.mode_completed_hurryup)
			self.modes_completed.append(self.mode)
			self.num_modes_completed += 1
		else:
			# See if it's time for the finale!
			if self.is_ultimate_challenge_ready():
				self.setup_ultimate_challenge()
			# If more modes to do, rotate and setup the next one.
			elif len(self.modes_not_attempted) > 0:
				self.rotate_modes(1)
				self.state = 'idle'
				self.setup_next_mode()
			else:
				self.state = 'modes_complete'

		# Turn on mode lamp to show it has been attempted
		self.drive_mode_lamp(self.mode, 'on')

		# Reset the drop targes if the mode just ending used them.
		if self.mode == 'impersonator' or self.mode == 'safecracker':
			self.multiball.drops.animated_reset(.1)

	def ultimate_challenge_complete(self):
		self.reset_modes()
		self.crimescenes.reset_complete()
		self.multiball.reset_jackpot_collected()


import sys
sys.path.append(sys.path[0]+'/../..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame
import pinproc
from deadworld import *
from info import *
from bonus import *
from tilt import *
from jd_modes import *
from procgame import *
from threading import Thread
from random import *
import string
import time
import locale
import math
import copy
import yaml

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

machine_config_path = "../shared/config/JD.yaml"
settings_path = "./games/jd/config/settings.yaml"
game_data_path = "./games/jd/config/game_data.yaml"
game_data_template_path = "./games/jd/config/game_data_template.yaml"
settings_template_path = "./games/jd/config/settings_template.yaml"
fonts_path = "../shared/dmd/"
shared_sound_path = "../shared/sound/"
sound_path = "./games/jd/sound/FX/"
music_path = "./games/jd/sound/"
font_tiny7 = dmd.Font(fonts_path+"04B-03-7px.dmd")
font_jazz18 = dmd.Font(fonts_path+"Jazz18-18px.dmd")
font_14x10 = dmd.Font(fonts_path+"Font14x10.dmd")
font_18x12 = dmd.Font(fonts_path+"Font18x12.dmd")
font_07x4 = dmd.Font(fonts_path+"Font07x4.dmd")
font_07x5 = dmd.Font(fonts_path+"Font07x5.dmd")
font_09Bx7 = dmd.Font(fonts_path+"Font09Bx7.dmd")

#lampshow_files = ["./games/jd/lamps/attract_show_test.lampshow"]
lampshow_files = ["./games/jd/lamps/attract_show_horiz.lampshow", \
                  "./games/jd/lamps/attract_show_vert.lampshow" \
                 ]

class Attract(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(Attract, self).__init__(game, 1)
		self.display_order = [0,1,2,3,4,5,6,7,8,9]
		self.display_index = 0

#		commands = []
#		commands += [pinproc.aux_command_disable()]
#		for i in range(0,32):
#			commands += [pinproc.aux_command_output_primary(i,0)]
#		commands += [pinproc.aux_command_delay(1000)]
#		commands += [pinproc.aux_command_jump(1)]
#		self.game.proc.aux_send_commands(0,commands)
#		commands = []
#		commands += [pinproc.aux_command_jump(1)]
#		self.game.proc.aux_send_commands(0,commands)

	def mode_topmost(self):
		pass

	def mode_started(self):
		self.play_super_game = False
		self.ball_search_started = False
		self.emptying_deadworld = False
		if self.game.deadworld.num_balls_locked > 0:
			self.game.deadworld.eject_balls(self.game.deadworld.num_balls_locked)
			self.emptying_deadworld = True
			self.delay(name='deadworld_empty', event_type=None, delay=10, handler=self.check_deadworld_empty)

		# Blink the start button to notify player about starting a game.
		self.game.lamps.startButton.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
		# Blink the start button to notify player about starting a game.
		self.game.lamps.superGame.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
		# Turn on minimal GI lamps
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.disable()

		# Release the ball from places it could be stuck.
		for name in ['popperL', 'popperR', 'shooterL', 'shooterR']:
			if self.game.switches[name].is_active():
				self.game.coils[name].pulse()


		# Set up schedules for random lamp blinking
		#lamp_schedules = []
		#for i in range(0,32):
		#	lamp_schedules.append(0xffff0000 >> i)
		#	# Handle wrap condition.  This code keeps 16 consecutive bits set.
		#	if i > 16:
		#		lamp_schedules[i] = (lamp_schedules[i] | (0xffff << (32-(i-16)))) & 0xffffffff

		# Randomize the order of the lamp schedules
		#shuffle(lamp_schedules)
		#i = 0
		## Write the lamp schedules to the lamps.  Obviously don't want to include
		## the front cabinet buttons or GIs.
		#for lamp in self.game.lamps:
		#	if lamp.name.find('gi0', 0) == -1 and \
                #           lamp.name != 'startButton' and lamp.name != 'buyIn' and \
                #           lamp.name != 'superGame':
		#		lamp.schedule(schedule=lamp_schedules[i%32], cycle_seconds=0, now=False)
		#		i += 1

		self.change_lampshow()
		self.change_display(0)
		self.ball_search_started = False

	def mode_stopped(self):
		pass
		
	def mode_tick(self):
		pass

	def change_lampshow(self):
		shuffle(self.game.lampshow_keys)
		self.game.lampctrl.play_show(self.game.lampshow_keys[0], repeat=True)
		self.delay(name='lampshow', event_type=None, delay=10, handler=self.change_lampshow)

	def sw_flipperLwL_active(self, sw):
		self.change_display(offset=-1)

	def sw_flipperLwR_active(self, sw):
		self.change_display(offset=1)

	def change_display(self, index=None, offset=0):
		# Cancel delay just in case it is still active from earlier.
		if index != None:
			self.display_index = index

		self.display_index += offset
		if self.display_index >= len(self.display_order):
			self.display_index = 0
		elif self.display_index < 0:
			self.display_index = int(len(self.display_order) - 1)

		self.cancel_delayed('display')
		ret_delay = self.setup_display(self.display_order[self.display_index])
		if self.display_index == len(self.display_order) - 1:
			new_index = 0
		else:
			new_index = self.display_index + 1
		self.delay(name='display', event_type=None, delay=ret_delay, handler=self.change_display, param=new_index)

	def setup_display(self, index=0):
		if index < 5:
			ret_val = self.setup_intro_display(index)
		elif index < 7:
			ret_val = self.setup_score_display(index-5)
		elif index < 9:
			ret_val = self.setup_credits_display(index-7)
		else:
			ret_val = self.setup_judges_display()
		return ret_val

	def setup_intro_display(self, index=0):
		if index == 0:
			self.layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("Press Start",2)
		elif index == 1:
			self.layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("pyprocgame",2)
		elif index == 2:
			self.layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("Judge Dredd",2)
		elif index == 3:
			self.layer = dmd.FrameLayer(opaque=True, frame=dmd.Animation().load(fonts_path+'Splash.dmd').frames[0])
		elif index == 4:
			self.layer = None
		return 2

	def setup_score_display(self, index):
		
		if index == 0:
			self.layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("High Scores", 2)
		else:
			self.gc0 = dmd.TextLayer(128/2, 3, font_tiny7, "center").set_text("Grand Champion:", 2)
			self.gc1 = dmd.TextLayer(128/2, 12, font_tiny7, "center").set_text(self.game.game_data['High Scores']['Grand Champion']['name'], 2)
			self.gc2 = dmd.TextLayer(128/2, 21, font_tiny7, "center").set_text(str(self.game.game_data['High Scores']['Grand Champion']['score']), 2)
			self.layer = dmd.GroupedLayer(128, 32, [self.gc0, self.gc1, self.gc2])
		return 2

	def setup_credits_display(self, index):
		if index == 0:
			self.layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("Credits",2)
		else:
			self.credits_1 = dmd.TextLayer(1, 1, font_tiny7, "left").set_text("Rules: Gerry Stellenberg")
			self.credits_2 = dmd.TextLayer(1, 8, font_tiny7, "left").set_text("Tools/Framework: Adam Preble")
			self.credits_sound_0 = dmd.TextLayer(1, 15, font_tiny7, "left").set_text("Sound/Music: Rob Keller")
			self.credits_sound_1 = dmd.TextLayer(1, 22, font_tiny7, "left").set_text("Music: Jonathan Coultan")
			self.layer = dmd.GroupedLayer(128, 32, [self.credits_1, self.credits_2, self.credits_sound_0, self.credits_sound_1])
		return 2

	def setup_judges_display(self):
		filename = "./games/jd/dmd/judgesincrystals.dmd"
		if os.path.isfile(filename):
			anim = dmd.Animation().load(filename)
			self.layer = dmd.AnimatedLayer(frames=anim.frames, repeat=False, frame_time=3)
		return 4

	def setup_game_over_display(self):
		self.game_over_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("Game Over")
		self.layer = dmd.ScriptedLayer(128, 32, [{'seconds':3.0, 'layer':self.game_over_layer}, {'seconds':3.0, 'layer':None}])
		return 6

	# Eject any balls that get stuck before returning to the trough.
	def sw_popperL_active_for_500ms(self, sw): # opto!
		self.game.coils.popperL.pulse(40)

	def sw_popperR_active_for_500ms(self, sw): # opto!
		self.game.coils.popperR.pulse(40)

	def sw_shooterL_active_for_500ms(self, sw):
		self.game.coils.shooterL.pulse(40)

	def sw_shooterR_active_for_500ms(self, sw):
		self.game.coils.shooterR.pulse(40)

	# Enter service mode when the enter button is pushed.
	def sw_enter_active(self, sw):
		#self.game.modes.remove(self.show)
		self.cancel_delayed(name='lampshow')
		self.cancel_delayed(name='display')
		self.game.lampctrl.stop_show()
		for lamp in self.game.lamps:
			lamp.disable()
		#self.game.load_settings(settings_template_path, settings_path)
		del self.game.service_mode
		self.game.service_mode = procgame.service.ServiceMode(self.game,100,font_tiny7,[self.game.deadworld_test])
		self.game.modes.add(self.game.service_mode)
		return True

	def sw_exit_active(self, sw):
		return True

	# Outside of the service mode, up/down control audio volume.
	def sw_down_active(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return True

	def sw_up_active(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return True


	# Start button starts a game if the trough is full.  Otherwise it
	# initiates a ball search.
	# This is probably a good place to add logic to detect completely lost balls.
	# Perhaps if the trough isn't full after a few ball search attempts, it logs a ball
	# as lost?	
	def sw_startButton_active(self, sw):
		if self.game.trough.is_full:
			self.game.lampctrl.save_state('temp')
			# Stop the attract mode lampshows
			self.cancel_delayed(name='lampshow')
			self.game.lampctrl.stop_show()
			# Remove attract mode from mode queue - Necessary?
			self.game.modes.remove(self)
			# Initialize game	
			self.game.start_game()
			# Add the first player
			self.game.add_player()
			# Start the ball.  This includes ejecting a ball from the trough.
			self.game.start_ball()
			self.ball_search_started = False
		else: 
			if not self.ball_search_started and not self.emptying_deadworld:
				self.delay(name='search_delay', event_type=None, delay=8.0, handler=self.search_delay)
				self.ball_search_started = True
				self.game.set_status("Ball Search!")
				self.game.ball_search.perform_search(5)
				self.game.deadworld.perform_ball_search()
		return True

	def sw_superGame_active(self, sw):
		if self.game.trough.is_full:
			self.play_super_game = True
			self.game.lampctrl.save_state('temp')
			# Stop the attract mode lampshows
			self.cancel_delayed(name='lampshow')
			self.game.lampctrl.stop_show()
			# Remove attract mode from mode queue - Necessary?
			self.game.modes.remove(self)
			# Initialize game	
			self.game.start_game()
			# Add the first player
			self.game.add_player()
			# Start the ball.  This includes ejecting a ball from the trough.
			self.game.start_ball()
			self.ball_search_started = False
		else: 
			if not self.ball_search_started and not self.emptying_deadworld:
				self.delay(name='search_delay', event_type=None, delay=8.0, handler=self.search_delay)
				self.ball_search_started = True
				self.game.set_status("Ball Search!")
				self.game.ball_search.perform_search(5)
				self.game.deadworld.perform_ball_search()
		return True

	def search_delay(self):
		self.ball_search_started = False

	def check_deadworld_empty(self):
		if self.game.deadworld.num_balls_locked > 0:
			self.delay(name='deadworld_empty', event_type=None, delay=10, handler=self.check_deadworld_empty)
		else:
			self.emptying_deadworld = False
			

class BaseGameMode(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(BaseGameMode, self).__init__(game, 2)
		self.tilt = Tilt(self.game, 1000, font_jazz18, font_tiny7, 'tilt', 'slamTilt')

	def mode_started(self):

		# Disable any previously active lamp
		for lamp in self.game.lamps:
			lamp.disable()

		# Do a quick lamp show
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)

		# Turn on the GIs
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)
		self.game.lamps.gi04.pulse(0)

		# Enable the flippers
		self.game.enable_flippers(enable=True)

		# Create jd_modes, which handles all of the game rules
		self.jd_modes = JD_Modes(self.game, 8, font_tiny7, font_jazz18)

		# Create mode to check for replay
		self.replay = procgame.modes.Replay(self.game, 18)
		self.game.modes.add(self.replay)
		self.replay.replay_callback = self.jd_modes.replay_callback
		self.jd_modes.replay = self.replay


		# Start modes
		self.game.modes.add(self.jd_modes)
		self.tilt.tilt_callback = self.tilt_callback
		self.tilt.slam_tilt_callback = self.slam_tilt_callback
		self.tilt.num_tilt_warnings = self.game.user_settings['Gameplay']['Number of tilt warnings']
		self.game.modes.add(self.tilt)

		# Load the player data saved from the previous ball.
		# It will be empty if this is the first ball.
		self.jd_modes.update_info_record(self.game.get_player_record('JD_MODES'))
		if self.game.attract_mode.play_super_game:
			self.jd_modes.multiball.jackpot_collected = True
			self.jd_modes.crimescenes.complete = True
			self.jd_modes.modes_not_attempted = []
		self.jd_modes.begin_processing()

		# Set up ball save params to be passed into launch_balls.
		ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
		ball_save_repeats = self.game.user_settings['Gameplay']['New ball repeating ballsave']
		ball_save_start_now = False # Ball save should start when the ball is plunged.

		# Put the ball into play and start tracking it.
		# self.game.coils.trough.pulse(40)
		self.game.trough.launch_balls(1, self.ball_launch_callback)

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Reset tilt warnings and status
		self.times_warned = 0;
		self.tilt_status = 0

		# In case a higher priority mode doesn't install it's own ball_drained
		# handler.
		self.game.trough.drain_callback = self.ball_drained_callback

	def ball_launch_callback(self):
		self.game.ball_save.start_lamp()
	
	def mode_stopped(self):
		
		# Ensure flippers are disabled
		self.game.enable_flippers(enable=False)

		# Deactivate the ball search logic so it won't search due to no 
		# switches being hit.
		self.game.ball_search.disable()

	def ball_drained_callback(self):
		if self.game.trough.num_balls_in_play == 0:
			# Give jd_modes a chance to do any any of ball processing
			self.jd_modes.ball_drained()
			# End the ball
			if self.tilt_status:
				self.tilt_delay()
			else:
				self.finish_ball()
		else:
			# Tell jd_modes a ball has drained (but not the last ball).
			self.jd_modes.ball_drained()

	def tilt_delay(self):
		# Make sure tilt switch hasn't been hit for at least 2 seconds before
		# finishing ball to ensure next ball doesn't start with tilt bob still
		# swaying.
		if self.game.switches.tilt.time_since_change() < 2:
			self.delay(name='tilt_bob_settle', event_type=None, delay=2.0, handler=self.tilt_delay)
		else:
			self.finish_ball()


	def finish_ball(self):

		self.game.sound.fadeout_music()

		# Make sure the motor isn't spinning between balls.
		self.game.coils.globeMotor.disable()

		# Remove the rules logic from responding to switch events.
		self.game.modes.remove(self.jd_modes)
		self.game.modes.remove(self.tilt)

		# Get and save the player's data
		jd_modes_info_record = self.jd_modes.get_info_record()
		self.game.update_player_record('JD_MODES', jd_modes_info_record)

		# Create the bonus mode so bonus can be calculated.
		self.bonus = Bonus(self.game, 8, font_jazz18, font_tiny7)
		self.game.modes.add(self.bonus)

		# Only compute bonus if it wasn't tilted away.
		if not self.tilt_status:
			self.bonus.compute(self.jd_modes.get_bonus_base(), self.jd_modes.get_bonus_x(), self.end_ball)
		else:
			self.end_ball()

	# Final processing for the ending ball.  If bonus was calculated, it is finished
	# by now.
	def end_ball(self):
		self.game.modes.remove(self.replay)
		# Remove the bonus mode since it's finished.
		self.game.modes.remove(self.bonus)
		# Tell the game object it can process the end of ball
		# (to end player's turn or shoot again)
		self.game.end_ball()

		# Start the next ball - I think this is redundant as the ball should launch when
		# base_game_mode is restarted.
		#if self.game.switches.trough6.is_active() and \
                #   self.game.switches.shooterR.is_inactive() and self.game.ball != 0:
			#self.game.coils.trough.pulse(20)
		#	self.launch_balls(1)
		# TODO: What if the ball doesn't make it into the shooter lane?
		#       We should check for it on a later mode_tick() and possibly re-pulse.

	def sw_startButton_active(self, sw):
		if self.game.ball == 1:
			p = self.game.add_player()
			self.game.set_status(p.name + " added!")
		else:
			self.game.set_status("Hold for 2s to reset.")

	def sw_startButton_active_for_2s(self, sw):
		if self.game.ball > 1 and self.game.user_settings['Gameplay']['Allow restarts']:
			self.game.set_status("Reset!")

			# Need to build a mechanism to reset AND restart the game.  If one ball
			# is already in play, the game can restart without plunging another ball.
			# It would skip the skill shot too (if one exists). 

			# Currently just reset the game.  This forces the ball(s) to drain and
			# the game goes to AttractMode.  This makes it painfully slow to restart,
			# but it's better than nothing.
			self.game.reset()
			return True

	# Allow service mode to be entered during a game.
	def sw_enter_active(self, sw):
		del self.game.service_mode
		self.game.service_mode = procgame.service.ServiceMode(self.game,100,font_tiny7,[self.game.deadworld_test])
		self.game.modes.add(self.game.service_mode)
		return True

	# Outside of the service mode, up/down control audio volume.
	def sw_down_active(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return True

	def sw_up_active(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return True


	# Reset game on slam tilt
	def slam_tilt_callback(self):
		self.game.sound.fadeout_music()
		# Need to play a sound and show a slam tilt screen.
		# For now just popup a status message.
		self.game.reset()
		return True

	def tilt_callback(self):
		# Process tilt.
		# First check to make sure tilt hasn't already been processed once.
		# No need to do this stuff again if for some reason tilt already occurred.
		if self.tilt_status == 0:

			self.game.sound.fadeout_music()
			
			# Tell the rules logic tilt occurred
			self.jd_modes.tilt = True

			# Disable flippers so the ball will drain.
			self.game.enable_flippers(enable=False)

			# Make sure ball won't be saved when it drains.
			self.game.ball_save.disable()
			#self.game.modes.remove(self.ball_save)

			# Make sure the ball search won't run while ball is draining.
			self.game.ball_search.disable()

			# Ensure all lamps are off.
			for lamp in self.game.lamps:
				lamp.disable()

			# Kick balls out of places it could be stuck.
			if self.game.switches.shooterR.is_active():
				self.game.coils.shooterR.pulse(50)
			if self.game.switches.shooterL.is_active():
				self.game.coils.shooterL.pulse(20)
			self.tilt_status = 1
			#play sound
			#play video
	
	def sw_slingL_active(self, sw):
		self.game.score(100)
		return False
	def sw_slingR_active(self, sw):
		self.game.score(100)
		return False

class JDPlayer(game.Player):
	def __init__(self, name):
		super(JDPlayer, self).__init__(name)
		self.info_record = {}

class Game(game.BasicGame):
	"""docstring for Game"""
	def __init__(self, machineType):
		super(Game, self).__init__(machineType)
		self.sound = procgame.sound.SoundController(self)
		self.lampctrl = procgame.lamps.LampController(self)
	
	def create_player(self, name):
		return JDPlayer(name)
	
	def save_settings(self):
		self.write_settings(settings_path)

	def save_game_data(self):
		self.write_game_data(game_data_path)
		
	def setup(self):
		"""docstring for setup"""
		self.load_config(machine_config_path)
		self.load_settings(settings_template_path, settings_path)
		self.sound.music_volume_offset = self.user_settings['Machine']['Music volume offset']
		self.sound.set_volume(self.user_settings['Machine']['Initial volume'])
		self.load_game_data(game_data_template_path, game_data_path)
		print "Stats:"
		print self.game_data
		print "Settings:"
		print self.settings
		print("Initial switch states:")
		for sw in self.switches:
			print("  %s:\t%s" % (sw.name, sw.state_str()))

		self.balls_per_game = self.user_settings['Gameplay']['Balls per game']

		self.setup_ball_search()

		self.score_display.set_left_players_justify(self.user_settings['Display']['Left side score justify'])

		# Instantiate basic game features
		self.attract_mode = Attract(self)
		self.base_game_mode = BaseGameMode(self)
		self.deadworld = Deadworld(self, 20, self.settings['Machine']['Deadworld mod installed'])
		self.ball_save = procgame.modes.BallSave(self, self.lamps.drainShield, 'shooterR')

		trough_switchnames = []
		for i in range(1,7):
			trough_switchnames.append('trough' + str(i))
		early_save_switchnames = ['outlaneR', 'outlaneL']
		self.trough = procgame.modes.Trough(self,trough_switchnames,'trough6','trough', early_save_switchnames, 'shooterR', self.drain_callback)

		# Link ball_save to trough
		self.trough.ball_save_callback = self.ball_save.launch_callback
		self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
		self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save

		self.deadworld_test = DeadworldTest(self,200,font_tiny7)

		# Setup and instantiate service mode
		self.service_mode = procgame.service.ServiceMode(self,100,font_tiny7,[self.deadworld_test])
		#self.sound.register_sound('service_enter', shared_sound_path+"menu_in.wav")
		#self.sound.register_sound('service_exit', shared_sound_path+"menu_out.wav")
		#self.sound.register_sound('service_next', shared_sound_path+"next_item.wav")
		#self.sound.register_sound('service_previous', shared_sound_path+"previous_item.wav")
		#self.sound.register_sound('service_switch_edge', shared_sound_path+"switch_edge.wav")
		#self.sound.register_sound('service_save', shared_sound_path+"save.wav")
		#self.sound.register_sound('service_cancel', shared_sound_path+"cancel.wav")
		
		#self.sound.register_sound('slingL', shared_sound_path+'exp_smoother.wav')
		#self.sound.register_sound('slingR', shared_sound_path+'exp_smoother2.wav')
		
		#self.sound.register_sound('bonus', shared_sound_path+'coin.wav') # Used as bonus is counting up.
		#self.sound.register_sound('bonus', shared_sound_path+'exp_smoother.wav') # Used as bonus is counting up.
		self.sound.register_sound('bonus', sound_path+'DropTarget.wav') # Used as bonus is counting up.
		
		# Setup fonts
		self.fonts = {}
		self.fonts['tiny7'] = font_tiny7
		self.fonts['jazz18'] = font_jazz18
		self.fonts['num_14x10'] = font_14x10
		self.fonts['18x12'] = font_18x12
		self.fonts['num_07x4'] = font_07x4
		self.fonts['07x5'] = font_07x5
		self.fonts['num_09Bx7'] = font_09Bx7

		# Register lampshow files
		self.lampshow_keys = []
		key_ctr = 0
		for file in lampshow_files:
			key = 'attract' + str(key_ctr)
			self.lampshow_keys.append(key)
			self.lampctrl.register_show(key, file)
			key_ctr += 1

		# Instead of resetting everything here as well as when a user
		# initiated reset occurs, do everything in self.reset() and call it
		# now and during a user initiated reset.
		self.reset()

	def reset(self):
		# Reset the entire game framework
		super(Game, self).reset()

		# Add the basic modes to the mode queue
		self.modes.add(self.attract_mode)
		self.modes.add(self.ball_search)
		self.modes.add(self.deadworld)
		self.modes.add(self.ball_save)
		self.modes.add(self.trough)


		self.ball_search.disable()
		self.ball_save.disable()
		self.trough.drain_callback = self.drain_callback

		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)

	# Empty callback just incase a ball drains into the trough before another
	# drain_callback can be installed by a gameplay mode.
	def drain_callback(self):
		pass

	def ball_starting(self):
		super(Game, self).ball_starting()
		self.modes.add(self.base_game_mode)

	def end_ball(self):
		super(Game, self).end_ball()

		self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
		self.game_data['Audits']['Balls Played'] += 1

	def calc_time_average_string(self, prev_total, prev_x, new_value):
		prev_time_list = prev_x.split(':')
		prev_time = (int(prev_time_list[0]) * 60) + int(prev_time_list[1])
		avg_game_time = int((int(prev_total) * int(prev_time)) + int(new_value)) / (int(prev_total) + 1)
		avg_game_time_min = avg_game_time/60
		avg_game_time_sec = str(avg_game_time%60)
		if len(avg_game_time_sec) == 1:
			avg_game_time_sec = '0' + avg_game_time_sec

		return_str = str(avg_game_time_min) + ':' + avg_game_time_sec
		return return_str

	def calc_number_average(self, prev_total, prev_x, new_value):
		avg_game_time = int((prev_total * prev_x) + new_value) / (prev_total + 1)
		return int(avg_game_time)
		
	def ball_ended(self):
		self.modes.remove(self.base_game_mode)
		super(Game, self).ball_ended()

	def start_game(self):
		super(Game, self).start_game()
		self.game_data['Audits']['Games Started'] += 1
		
	def game_ended(self):
		super(Game, self).game_ended()
		# Make sure nothing unexpected happens if a ball drains
		# after a game ends (due possibly to a ball search).
		self.trough.drain_callback = self.drain_callback
		self.modes.remove(self.base_game_mode)
		#self.modes.add(self.attract_mode)
		self.deadworld.mode_stopped()
		# Restart attract mode lampshows
		self.modes.add(self.attract_mode)

		#self.attract_mode.change_display(99)
		# Change to game_over index
		self.attract_mode.change_display(0)

		# Handle stats for last ball here
		self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
		self.game_data['Audits']['Balls Played'] += 1
		# Also handle game stats.
		for i in range(0,len(self.players)):
			game_time = self.get_game_time(i)
			self.game_data['Audits']['Avg Game Time'] = self.calc_time_average_string( self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Game Time'], game_time)
			self.game_data['Audits']['Games Played'] += 1

		for i in range(0,len(self.players)):
			self.game_data['Audits']['Avg Score'] = self.calc_number_average(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Score'], self.players[i].score)
		self.save_game_data()
		
	def set_status(self, text):
		self.dmd.set_message(text, 3)
		print(text)
	
	def extra_ball(self):
		p = self.current_player()
		p.extra_balls += 1

	def update_player_record(self, key, record):
		p = self.current_player()
		p.info_record[key] = record

	def get_player_record(self, key):
		p = self.current_player()
		if key in p.info_record:
			return p.info_record[key]
		else:
			return []

	def setup_ball_search(self):

		# Currently there are no special ball search handlers.  The deadworld
		# could be one, but running it while balls are locked would screw up
		# the multiball logic.  There is already logic in the multiball logic
		# to eject balls that enter the deadworld when lock isn't lit; so it 
		# shouldn't be necessary to search the deadworld.  (unless a ball jumps
		# onto the ring rather than entering through the feeder.)
		special_handler_modes = []
		self.ball_search = procgame.modes.BallSearch(self, priority=100, \
                                     countdown_time=10, coils=self.ballsearch_coils, \
                                     reset_switches=self.ballsearch_resetSwitches, \
                                     stop_switches=self.ballsearch_stopSwitches, \
                                     special_handler_modes=special_handler_modes)
		
def main():
	config = yaml.load(open(machine_config_path, 'r'))
	machineType = config['PRGame']['machineType']
	config = 0
	game = None
	try:
	 	game = Game(machineType)
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()

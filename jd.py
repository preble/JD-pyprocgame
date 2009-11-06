import sys
sys.path.append(sys.path[0]+'/../..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame
import pinproc
from deadworld import *
from bonus import *
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
user_settings_path = "./games/jd/config/user_settings.yaml"
fonts_path = "../shared/dmd/"
sound_path = "../shared/sound/"
font_tiny7 = dmd.Font(fonts_path+"04B-03-7px.dmd")
font_jazz18 = dmd.Font(fonts_path+"Jazz18-18px.dmd")

class Attract(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(Attract, self).__init__(game, 1)
		self.press_start = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("Press Start")
		self.proc_banner = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("pyprocgame")
		self.game_title = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("Judge Dredd")
		self.splash = dmd.FrameLayer(opaque=True, frame=dmd.Animation().load(fonts_path+'Splash.dmd').frames[0])
		self.layer = dmd.ScriptedLayer(128, 32, [{'seconds':2.0, 'layer':self.splash}, {'seconds':2.0, 'layer':self.proc_banner}, {'seconds':2.0, 'layer':self.game_title}, {'seconds':2.0, 'layer':self.press_start}, {'seconds':2.0, 'layer':None}])
		self.layer.opaque = True

	def mode_topmost(self):
		pass

	def mode_started(self):
		# Blink the start button to notify player about starting a game.
		self.game.lamps.startButton.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
		# Turn on minimal GI lamps
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.disable()

		# Release the ball from places it could be stuck.
		for name in ['popperL', 'popperR', 'shooterL', 'shooterR']:
			if self.game.switches[name].is_active():
				self.game.coils[name].pulse()

		# Set up schedules for random lamp blinking
		lamp_schedules = []
		for i in range(0,32):
			lamp_schedules.append(0xffff0000 >> i)
			# Handle wrap condition.  This code keeps 16 consecutive bits set.
			if i > 16:
				lamp_schedules[i] = (lamp_schedules[i] | (0xffff << (32-(i-16)))) & 0xffffffff

		# Randomize the order of the lamp schedules
		shuffle(lamp_schedules)
		i = 0
		# Write the lamp schedules to the lamps.  Obviously don't want to include
		# the front cabinet buttons or GIs.
		for lamp in self.game.lamps:
			if lamp.name.find('gi0', 0) == -1 and \
                           lamp.name != 'startButton' and lamp.name != 'buyIn' and \
                           lamp.name != 'superGame':
				lamp.schedule(schedule=lamp_schedules[i%32], cycle_seconds=0, now=False)
				i += 1

		# TODO: Change the pattern every once in a while.  Possibly integrate
		# predefined lamp shows.

	def mode_stopped(self):
		pass
		
	def mode_tick(self):
		pass

	# Eject any balls that get stuck before returning to the trough.
	def sw_popperL_active_for_500ms(self, sw): # opto!
		self.game.coils.popperL.pulse(20)

	def sw_popperR_active_for_500ms(self, sw): # opto!
		self.game.coils.popperR.pulse(20)

	def sw_shooterL_active_for_500ms(self, sw):
		self.game.coils.shooterL.pulse(20)

	def sw_shooterR_active_for_500ms(self, sw):
		self.game.coils.shooterR.pulse(20)

	# Enter service mode when the enter button is pushed.
	def sw_enter_active(self, sw):
		for lamp in self.game.lamps:
			lamp.disable()
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
		if self.game.trough.is_full():
			if self.game.switches.trough6.is_active():
				self.game.modes.remove(self)
				self.game.start_game()
				self.game.add_player()
				self.game.start_ball()
		else: 
			self.game.set_status("Ball Search!")
			self.game.ball_search.perform_search(5)
			self.game.deadworld.perform_ball_search()
		return True


class BaseGameMode(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(BaseGameMode, self).__init__(game, 2)
		self.tilt_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("TILT!")
		self.layer = None # Presently used for tilt layer

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

		# Link helper modes
		self.jd_modes.launch_balls = self.launch_balls

		# Start modes
		self.game.modes.add(self.jd_modes)

		# Load the player data saved from the previous ball.
		# It will be empty if this is the first ball.
		self.jd_modes.update_info_record(self.game.get_player_record('JD_MODES'))

		# Set up ball save params to be passed into launch_balls.
		ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
		ball_save_repeats = self.game.user_settings['Gameplay']['New ball repeating ballsave']
		ball_save_start_now = False # Ball save should start when the ball is plunged.

		# Put the ball into play and start tracking it.
		# self.game.coils.trough.pulse(40)
		self.launch_balls([1,1,ball_save_time,ball_save_start_now,ball_save_repeats])
		self.game.ball_tracker.num_balls_in_play += 1

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Reset tilt warnings and status
		self.times_warned = 0;
		self.tilt_status = 0
	
	def mode_stopped(self):
		
		# Ensure flippers are disabled
		self.game.enable_flippers(enable=False)

		# Deactivate the ball search logic so it won't search due to no 
		# switches being hit.
		self.game.ball_search.disable()
	
	def sw_trough1_active_for_500ms(self, sw):
		self.trough_check();

	def sw_trough2_active_for_500ms(self, sw):
		self.trough_check();

	def sw_trough3_active_for_500ms(self, sw):
		self.trough_check();

	def sw_trough4_active_for_500ms(self, sw):
		self.trough_check();

	def sw_trough5_active_for_500ms(self, sw):
		self.trough_check();
		
	def trough_check(self):
		# Ask the ball tracker how to handle this drained ball.
		action = self.game.ball_tracker.ball_drain_action()
		if action == 'save':
			self.game.ball_save.saving_ball()
			self.launch_balls([1,0,0,False,False])
			self.game.set_status("Ball Saved!")
		elif action == 'end_multiball':
			self.game.ball_tracker.num_balls_in_play -= 1
			self.jd_modes.end_multiball()
		elif action == 'end_ball':
			self.game.ball_tracker.num_balls_in_play -= 1
			self.finish_ball()
		elif action == 'ball_out_of_play':
			self.game.ball_tracker.num_balls_in_play -= 1
		return True

	def finish_ball(self):

		# Make sure the motor isn't spinning between balls.
		self.game.coils.globeMotor.disable()

		# Remove the rules logic from responding to switch events.
		self.game.modes.remove(self.jd_modes)

		# Turn off tilt display (if it was on) now that the ball has drained.
		if self.tilt_status and self.layer == self.tilt_layer:
			self.layer = None

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

	# This helper function can/should be used wheneve one or more new balls need to be launched.
	# If more than one ball is being launched, it delays 2 seconds between balls.  If after 2 
	# seconds there is still a ball in the shooter lane, it doesn't kick out a new ball.  Rather,
	# it reschedules the launch.
	# TODO: Add some logic to make sure the ball got into the shooter lane.  Otherwise, the count
	# could get screwed up and the ball may never get into play. 

	# Also, set up ball save according to params.
	# Note, params are in a list so the function can be called recursively using the delay 
	# feature if more than one ball is being launched. Delayed functions take 1 param.
	def launch_balls(self, params = [1, 0, 10, False, False]):
		num = params[0]
		num_balls_to_save = params[1]
		ball_save_time = params[2]
		ball_save_start_now = params[3]
		ball_save_allow_multiple = params[4]
		self.game.coils.trough.pulse(40)
		num -= 1
		params[0] = num
		if num > 0:
			self.delay(name='launch', event_type=None, delay=2.0, handler=self.launch_balls, param=params)
		else:
			if num_balls_to_save > 0:
				self.game.ball_save.start(num_balls_to_save=num_balls_to_save, time=ball_save_time, now=ball_save_start_now, allow_multiple_saves=ball_save_allow_multiple)
			
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
		self.game.modes.add(self.game.service_mode)
		return True

	# Reset game on slam tilt
	def sw_slamTilt_active(self_sw):
		# Need to play a sound and show a slam tilt screen.
		# For now just popup a status message.
		self.game.set_status("Slam Tilt!")
		self.game.reset()
		return True

	def sw_tilt_active(self, sw):
		if self.times_warned == self.game.user_settings['Gameplay']['Number of Tilt Warnings']:
			self.tilt()
		else:
			self.times_warned += 1
			#play sound
			#add a display layer and add a delayed removal of it.
			self.game.set_status("Tilt Warning " + str(self.times_warned) + "!")

	def tilt(self):
		# Process tilt.
		# First check to make sure tilt hasn't already been processed once.
		# No need to do this stuff again if for some reason tilt already occurred.
		if self.tilt_status == 0:
			
			# Display the tilt graphic
			self.layer = self.tilt_layer

			# Disable flippers so the ball will drain.
			self.game.enable_flippers(enable=False)

			# Make sure ball won't be saved when it drains.
			self.ball_save.disable()
			self.game.modes.remove(self.ball_save)

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



class Game(game.GameController):
	"""docstring for Game"""
	def __init__(self, machineType):
		super(Game, self).__init__(machineType)
		self.sound = procgame.sound.SoundController(self)
		self.dmd = dmd.DisplayController(self, width=128, height=32, message_font=font_tiny7)
		self.keyboard_handler = procgame.keyboard.KeyboardHandler()
		self.keyboard_events_enabled = True
		self.get_keyboard_events = self.keyboard_handler.get_keyboard_events

	def save_settings(self):
		self.write_settings(user_settings_path)
		
	def setup(self):
		"""docstring for setup"""
		self.load_config(machine_config_path)
		self.load_settings(settings_path, user_settings_path)
		print("Initial switch states:")
		for sw in self.switches:
			print("  %s:\t%s" % (sw.name, sw.state_str()))

		self.setup_ball_search()

		self.score_display = scoredisplay.ScoreDisplay(self, 0)
		self.score_display.set_left_players_justify(self.user_settings['Display']['Left side score justify'])

		# Instantiate basic game features
		self.attract_mode = Attract(self)
		self.base_game_mode = BaseGameMode(self)
		self.deadworld = Deadworld(self, 20, self.settings['Machine']['Deadworld mod installed'])
		self.ball_save = procgame.ballsave.BallSave(self, self.lamps.drainShield)
		self.ball_tracker = procgame.balltracker.BallTracker(self, self.num_balls_total)
		self.trough = procgame.balltracker.Trough(self)

		# Setup and instantiate service mode
		self.sound.register_sound('service_enter', sound_path+"menu_in.wav")
		self.sound.register_sound('service_exit', sound_path+"menu_out.wav")
		self.sound.register_sound('service_next', sound_path+"next_item.wav")
		self.sound.register_sound('service_previous', sound_path+"previous_item.wav")
		self.sound.register_sound('service_switch_edge', sound_path+"switch_edge.wav")
		self.sound.register_sound('service_save', sound_path+"save.wav")
		self.sound.register_sound('service_cancel', sound_path+"cancel.wav")
		self.service_mode = procgame.service.ServiceMode(self,100,font_tiny7)

		# Instead of resetting everything here as well as when a user
		# initiated reset occurs, do everything in self.reset() and call it
		# now and during a user initiated reset.
		self.reset()

	def reset(self):
		# Reset the entire game framework
		super(Game, self).reset()

		# Add the basic modes to the mode queue
		self.modes.add(self.score_display)
		self.modes.add(self.attract_mode)
		self.modes.add(self.ball_search)
		self.modes.add(self.deadworld)
		self.modes.add(self.ball_save)
		self.modes.add(self.trough)

		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)
		
	def ball_starting(self):
		super(Game, self).ball_starting()
		self.modes.add(self.base_game_mode)
		
	def ball_ended(self):
		self.modes.remove(self.base_game_mode)
		super(Game, self).ball_ended()
		
	def game_ended(self):
		super(Game, self).game_ended()
		self.modes.remove(self.base_game_mode)
		#self.modes.add(self.attract_mode)
		self.deadworld.mode_stopped()
		self.set_status("Game Over")
		
	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		self.dmd.update()

	def set_status(self, text):
		self.dmd.set_message(text, 3)
		print(text)
	
	def score(self, points):
		p = self.current_player()
		p.score += points

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
		self.ball_search = procgame.ballsearch.BallSearch(self, priority=100, countdown_time=10, coils=self.ballsearch_coils, reset_switches=self.ballsearch_resetSwitches, stop_switches=self.ballsearch_stopSwitches,special_handler_modes=special_handler_modes)
		
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

import procgame
from procgame import *
from random import *

class Crimescenes(modes.Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Crimescenes, self).__init__(game, priority)
		self.total_levels = 0
		self.level = 0
		self.mode = 'idle'
		self.targets = [1,0,0,0,0]
		self.target_award_order = [1,3,0,2,4]
		self.lamp_colors = ['G', 'Y', 'R', 'W']
		difficulty = self.game.user_settings['Gameplay']['Crimescene shot difficulty']
		if difficulty == 'easy':
			self.level_templates = [ [2,4], [2,4], 
                                                 [2,4], [2,4], 
                                                 [0,2,4], [0,2,4], 
                                                 [0,2,4], [0,2,4], 
                                                 [0,2,4], [0,2,4], 
                                                 [0,2,3,4], [0,2,3,4], 
                                                 [0,2,3,4], [0,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4] ]
			self.level_nums = [ 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5 ]
		elif difficulty == 'medium':
			self.level_templates = [ [2,4], [2,4], 
                                                 [2,4], [2,4], 
                                                 [0,2,4], [0,2,4], 
                                                 [0,2,4], [0,2,4], 
                                                 [0,2,3,4], [0,2,3,4], 
                                                 [0,2,3,4], [0,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4] ]
			self.level_nums = [ 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ]
		else:
			self.level_templates = [ [0,2,4], [0,2,4], 
                                                 [0,2,4], [0,2,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4], 
                                                 [0,1,2,3,4], [0,1,2,3,4] ]
			self.level_nums = [ 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ]
		self.bonus_num = 1
		self.extra_ball_levels = 2
		self.complete = False

		self.game.lampctrl.register_show('advance_level', "./games/jd/lamps/crimescene_advance_level.lampshow")

	def mode_stopped(self):
		if self.mode == 'bonus':
			self.cancel_delayed('moving_target')
		for i in range(1,6):
			for j in range(0,4):
				lampname = 'perp' + str(i) + self.lamp_colors[j]
				self.drive_mode_lamp(lampname, 'off')
		for i in range(1,5):
			lampname = 'crimeLevel' + str(i)
			self.drive_mode_lamp(lampname, 'off')

	def get_info_record(self):
		info_record = {}
		info_record['level'] = self.level
		info_record['total_levels'] = self.total_levels
		info_record['mode'] = self.mode
		info_record['targets'] = self.targets
		info_record['complete'] = self.complete
		return info_record

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.total_levels = info_record['total_levels']
			self.level = info_record['level']
			self.mode = info_record['mode']
			self.targets = info_record['targets']
			self.complete = info_record['complete']

		if self.mode == 'bonus':
			self.mode = 'complete'
		self.num_advance_hits = 0
		self.update_lamps()

	def get_bonus_base(self):
		# Add bonus info: 5000 bonus for attempting
		num_levels_str = 'Crimescene Levels: ' + str(self.total_levels)
		bonus_base_elements = {}
		bonus_base_elements[num_levels_str] = self.total_levels*2000
		return bonus_base_elements


	def update_lamps(self):
		if self.mode == 'idle':
			self.init_level(0)
		elif self.mode == 'levels':
			lampname = 'advanceCrimeLevel'
			if self.num_advance_hits == 0:
				self.drive_mode_lamp(lampname, 'on')
			elif self.num_advance_hits == 1:
				self.drive_mode_lamp(lampname, 'slow')
			elif self.num_advance_hits == 2:
				self.drive_mode_lamp(lampname, 'fast')
			else:
				self.drive_mode_lamp(lampname, 'off')
				
			for i in range(0,5):
				lamp_color_num = self.level%4
				for j in range(0,4):
					lampname = 'perp' + str(i+1) + self.lamp_colors[j]
					if self.targets[i] and lamp_color_num == j:
						self.drive_mode_lamp(lampname, 'medium')
					else:
						self.drive_mode_lamp(lampname, 'off')
			# Use 4 center crimescene lamps as a binary representation
			# of the level.
			for i in range (1,5):
				lampnum = self.level%4 + 1
				lampname = 'crimeLevel' + str(i)
				if i == lampnum:
					self.drive_mode_lamp(lampname, 'on')
				else:
					self.drive_mode_lamp(lampname, 'off')
		elif self.mode == 'bonus':
			lampname = 'advanceCrimeLevel'
			self.drive_mode_lamp(lampname, 'off')
			for i in range(0,5):
				for j in range(0,4):
					lampname = 'perp' + str(i+1) + self.lamp_colors[j]
				self.drive_mode_lamp(lampname, 'off')
		elif self.mode == 'complete':
			for i in range(0,5):
				if self.targets[i]:
					for j in range(0,4):
						lampname = 'perp' + str(i+1) + self.lamp_colors[j]
						self.drive_mode_lamp(lampname, 'off')

	def sw_threeBankTargets_active(self, sw):
		if self.mode == 'levels':
			if self.num_advance_hits == 2:	
				self.award_hit()
				self.num_advance_hits = 0
				self.update_lamps()
			else:
				self.num_advance_hits += 1
				self.update_lamps()

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		print "time"
		print self.game.switches.leftRollover.time_since_change()

		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1:
			self.switch_hit(1)

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1:
			self.switch_hit(3)

	def sw_topCenterRollover_active(self, sw):
		#See if ball came around right loop 
		#Give it 2 seconds as ball trickles this way.  Might need to adjust.
		if self.game.switches.topRightOpto.time_since_change() < 2:
			self.switch_hit(3)

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)

	def award_hit(self):
		for i in range(0,5):
			award_switch = self.target_award_order[i]
			if self.targets[award_switch]:
				self.switch_hit(award_switch)
				return True

	def switch_hit(self, num):
		if self.mode == 'levels':
			if self.targets[num]:
				self.game.score(1000)
			self.targets[num] = 0
			print 'self.targets'
			print self.targets
			if self.all_targets_off():
				self.level_complete()
			else:
				self.update_lamps()
		elif self.mode == 'bonus':
			if num+1 == self.bonus_num:
				self.cancel_delayed('bonus_target')
				self.drive_bonus_lamp(self.bonus_num, 'off')
				self.game.score(500000)
				self.level_complete()
				#Play sound, lamp show, etc

	def level_complete(self, num_levels = 1):
		self.num_levels_to_advance = num_levels
		self.game.lampctrl.play_show('advance_level', False, self.finish_level_complete)

	def finish_level_complete(self):
		self.game.score(10000)
		if self.mode == 'bonus':
			self.complete = True
			self.crimescenes_completed()
			self.level = 0
			self.mode = 'idle'
			self.init_level(self.level)
		else:
			for number in range(0,self.num_levels_to_advance):
				if self.level + number == self.extra_ball_levels:
					self.light_extra_ball_function()
					break
			if (self.level + self.num_levels_to_advance) > (self.game.user_settings['Gameplay']['Crimescene levels for finale']-1):
				self.mode = 'bonus'
				self.update_lamps()
				#Play sound, lamp show, etc
				self.bonus_num = 1
				self.bonus_dir = 'up'
				self.delay(name='bonus_target', event_type=None, delay=3, handler=self.bonus_target)
				self.drive_bonus_lamp(self.bonus_num, 'on')
				for i in range(1,5):
					lampname = 'crimeLevel' + str(i)
					self.drive_mode_lamp(lampname, 'slow')
				
			else:
				self.level += self.num_levels_to_advance
				self.total_levels += self.num_levels_to_advance
				self.init_level(self.level)
				#Play sound, lamp show, etc

	def bonus_target(self):
		self.drive_bonus_lamp(self.bonus_num, 'off')
		if self.bonus_num == 5:
			self.bonus_dir = 'down'

		if self.bonus_dir == 'down' and self.bonus_num == 1:
			self.level_complete()
			for i in range(1,5):
				lampname = 'crimeLevel' + str(i)
				self.drive_mode_lamp(lampname, 'off')
		else:
			if self.bonus_dir == 'up':
				self.bonus_num += 1
			else:
				self.bonus_num -= 1
			self.drive_bonus_lamp(self.bonus_num, 'on')
			self.delay(name='bonus_target', event_type=None, delay=3, handler=self.bonus_target)
			

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

	def drive_bonus_lamp(self, lamp_num, style='on'):
		for i in range(1,len(self.lamp_colors)):
			lamp_name = 'perp' + str(lamp_num) + self.lamp_colors[i]
			if style == 'slow':
				self.game.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			elif style == 'on':
				self.game.lamps[lamp_name].pulse(0)
			elif style == 'off':
				self.game.lamps[lamp_name].disable()
		

	def all_targets_off(self):
		for i in range(0,5):
			if self.targets[i]:
				return False
		return True

	def init_level(self, level):
		self.mode = 'levels'
		level_template = self.level_templates[level]
		print "level template"
		print level_template
		shuffle(level_template)
		print "shuffled_level template"
		print level_template
		# First initialize targets (redundant?)
		for i in range(0,5):
			self.targets[i] = 0
		# Now fill targets according to shuffled template
		for i in range(0,5):
			print "len(self.level_templates[level])"
			print len(self.level_templates[level])
			print self.level_nums
			if i < self.level_nums[level] and i < len(self.level_templates[level]):
				self.targets[level_template[i]] = 1
		print "targets"
		print self.targets
		self.update_lamps()

	def complete(self):
		return self.complete

	def reset_complete(self):
		self.complete = False


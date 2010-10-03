import sys
import os
sys.path.append(sys.path[0]+'/../..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
import procgame
from procgame import *
import time
import yaml
import random

voice_path = "./games/jd/sound/Voice/shooting_gallery/"

class ShootingGallery(game.Mode):
	def __init__(self, game, priority, gallery_filename, cows_filename, scope_filename, cow_mode):
		super(ShootingGallery, self).__init__(game, priority)
		self.gallery_images_anim = dmd.Animation().load(gallery_filename)
		self.cow_images_anim = dmd.Animation().load(cows_filename)
		#self.image_frames = dmd.GroupedFrameToList( self.gallery_images_anim.frames[0], 6, 2 )
		self.cow_mode = cow_mode
		self.image_frames = self.gallery_images_anim.frames[0].create_frames_from_grid( 6, 2 )
		self.cow_image_frames = self.cow_images_anim.frames[0].create_frames_from_grid( 4, 1 )

		self.scope_and_shot_anim = dmd.Animation().load(scope_filename)
		self.on_complete = None

		keyname = 'bad guy shot'
		for i in range(1,6):
			filename = 'man shot ' + str(i) + '.wav'
			self.game.sound.register_sound(keyname, voice_path+filename)

		keyname = 'good guy shot'
		for i in range(1,3):
			filename = 'mother ' + str(i) + '.wav'
			self.game.sound.register_sound(keyname, voice_path+filename)

	def mode_started(self):
		self.gallery_index = 0
		self.scope_pos = 0
		self.states = ['empty', 'empty', 'empty', 'empty']
		self.num_enemies = 0
		self.num_enemies_old = 0
		self.num_enemies_shot = 0
		self.speed_factor = 1

		self.mode = 'active'
		self.success = False

		self.intro_active = True
		self.intro()

	def intro(self):
		print "hi"
		self.game.enable_flippers(enable=False)
		print "hi2"
		self.status_layer = dmd.TextLayer(128/2, 7, self.game.fonts['jazz18'], "center", opaque=False).set_text("Video Mode")
#		self.status_layer.composite_op = 'blacksrc'
		self.intro_layer_0 = dmd.GroupedLayer(128, 32, [self.status_layer])

		if self.cow_mode:
			enemy_text = "Shoot mean cows"
			friend_text = "Do NOT shoot nice cows"
		else:
			enemy_text = "Shoot enemies"
			friend_text = "Do NOT shoot friends"

		self.instruction_layer_1 = dmd.TextLayer(128/2, 7, self.game.fonts['07x5'], "center").set_text(enemy_text)
		self.instruction_layer_2 = dmd.TextLayer(128/2, 17, self.game.fonts['07x5'], "center").set_text(friend_text)
		self.intro_layer_1 = dmd.GroupedLayer(128, 32, [self.instruction_layer_1, self.instruction_layer_2])
		

		self.instruction_layer_21 = dmd.TextLayer(128/2, 7, self.game.fonts['07x5'], "center").set_text("Flipper buttons aim")
		self.instruction_layer_22 = dmd.TextLayer(128/2, 17, self.game.fonts['07x5'], "center").set_text("Fire buttons shoot")
		self.intro_layer_2 = dmd.GroupedLayer(128, 32, [self.instruction_layer_21, self.instruction_layer_22])

		anim = dmd.Animation().load("games/jd/dmd/gun_powerup.dmd")
		self.anim_layer = dmd.AnimatedLayer(frames=anim.frames, frame_time=5)
		self.anim_layer.composite_op = 'blacksrc'

		self.intro_layer_4 = dmd.TextLayer(128/2, 7, self.game.fonts['jazz18'], "center", opaque=False).set_text("Video Mode").set_text("Ready...")

		self.status_layer_5 = dmd.TextLayer(128/2, 7, self.game.fonts['jazz18'], "center", opaque=False).set_text("Video Mode").set_text("Begin!")
		self.intro_layer_5 = dmd.GroupedLayer(128, 32, [self.anim_layer, self.status_layer_5])

		self.layer = dmd.ScriptedLayer(128, 32, [\
			{'seconds':3.0, 'layer':self.intro_layer_0},
			{'seconds':3.0, 'layer':self.intro_layer_1},
			{'seconds':3.0, 'layer':self.intro_layer_2},
			{'seconds':3.0, 'layer':self.intro_layer_4},
			{'seconds':3.0, 'layer':self.intro_layer_5}])

		self.layer.on_complete = self.start

	def start(self):

		self.intro_active = False
		self.status_layer.set_text("")

		# Create the layers for each target
		self.pos_layers = []
		self.transitions = []

		for i in range(0,4):
			#new_transition = dmd.PushLayerTransition
			new_transition = dmd.ExpandTransition
			self.transitions += [new_transition]
			new_layer = dmd.FrameLayer()
			new_layer.composite_op = 'blacksrc'
			new_layer.transition = self.transitions[i]()
			self.pos_layers += [new_layer]

		# Create the layer for the gun scope.
		self.scope_layer = dmd.FrameLayer()
		self.scope_layer.composite_op = 'blacksrc'

		# Create the layer for each bullet hole position.
		self.shot_layers = []
		for i in range(0,4):
			new_layer = dmd.FrameLayer()
			new_layer.composite_op = 'blacksrc'
			self.shot_layers += [new_layer]

		self.result_layer = dmd.TextLayer(128/2, 26, self.game.fonts['07x5'], "center", opaque=True)
		#self.result_layer.composite_op = 'blacksrc'

		# Add all of the layers to a GroupedLayer.
		self.layer = dmd.GroupedLayer(128, 32, [self.pos_layers[0], self.pos_layers[1], self.pos_layers[2], self.pos_layers[3], self.scope_layer, self.shot_layers[0], self.shot_layers[1],self.shot_layers[2], self.shot_layers[3], self.status_layer, self.result_layer])

		# Add the first target after 1 second.
		self.delay(name='add', event_type=None, delay=1, handler=self.add_target)
		self.update_scope_pos()

	def add_target(self):
		if self.num_enemies == 15:
			self.delay(name='finish', event_type=None, delay=2.0, handler=self.finish)
		else:
			if self.speed_factor < 5 and self.num_enemies % 4 == 3 and self.num_enemies != self.num_enemies_old:
				self.speed_factor += 1
				self.num_enemies_old = self.num_enemies
			if self.mode == 'active':
				target_index = random.randint(0,3)
				target_type = random.randint(0,1)
		
				# Find the first empty position starting with the random target_index.
				for i in range(0,3):
					position = (i+target_index)%4
					if self.states[position] == 'empty':
						if target_type:
							self.show_enemy(position, -1)
						else:
							self.show_friend(position, -1)
						self.delay(name='remove', event_type=None, delay=3.0-(self.speed_factor*0.4), handler=self.remove_target, param=position)
						break
		
				# Add a new target every 2 seconds.
				self.delay(name='add', event_type=None, delay=2.0-(self.speed_factor*0.3), handler=self.add_target)

	def finish(self):
		self.mode = 'complete'
		self.status_layer.set_text("Completed!")
		self.instruction_layer_21.set_text("Completion Bonus:")
		self.instruction_layer_22.set_text(str(100000))
		self.layer = self.intro_layer_2
		self.delay(name='show_num_shot', event_type=None, delay=2.0, handler=self.show_num_shot)

	def show_num_shot(self):
		self.instruction_layer_21.set_text("Enemies Shot:")
		self.instruction_layer_22.set_text(str(self.num_enemies_shot) + " of " + str(self.num_enemies))
		self.success = self.num_enemies_shot == self.num_enemies
		if self.success:
			self.delay(name='perfect', event_type=None, delay=3.0, handler=self.perfect)
		else:
			self.delay(name='wrap_up', event_type=None, delay=3.0, handler=self.wrap_up)

	def perfect(self):
		self.status_layer.set_text("Perfect!")
		self.layer = self.status_layer
		self.layer.opaque = True
		self.delay(name='wrap_up', event_type=None, delay=2.0, handler=self.wrap_up)
	
	def wrap_up(self):
		self.game.enable_flippers(True)
		if self.on_complete != None:
			self.on_complete(self.success)

	def remove_target(self, position):
		# Only remove if it hasn't been shot.  
		# If it has been shot, it will be removed later.
		if self.states[position] != 'shot' and self.mode == 'active':
			self.states[position] = 'empty'
			self.pos_layers[position].transition.in_out = 'out'
			self.pos_layers[position].transition.start()
			#self.pos_layers[position].frame = None

	def show_friend(self, position, target_index=-1):
		if target_index == -1:
			if self.cow_mode:
				target_index = 0
			else:
				target_index = random.randint(6,11)

		self.show_target(position, target_index)
		self.states[position] = 'friend'
	
	def show_enemy(self, position, target_index=-1):
		self.num_enemies += 1
		if target_index == -1:
			if self.cow_mode:
				target_index = 1
			else:
				target_index = random.randint(0,5)

		self.show_target(position, target_index)
		self.states[position] = 'enemy'

	def show_target(self, position, target_index):
		new_frame = dmd.Frame(128,32)		
		if self.cow_mode:
			dmd.Frame.copy_rect(dst=new_frame, dst_x=position*32, dst_y=0, src=self.cow_image_frames[target_index], src_x=0, src_y=0, width=32, height=32, op='blacksrc')
		else:
			dmd.Frame.copy_rect(dst=new_frame, dst_x=position*32, dst_y=0, src=self.image_frames[target_index], src_x=0, src_y=0, width=32, height=32, op='blacksrc')
		self.pos_layers[position].frame = new_frame
		self.pos_layers[position].transition.in_out = 'in'
		self.pos_layers[position].transition.start()

	def sw_flipperLwL_active(self, sw):
		if self.intro_active:
			if self.game.switches.flipperLwR.is_active():
				self.layer.force_next(True)
		elif self.mode == 'active':
			if self.scope_pos != 0:
				self.scope_pos -= 1
			self.update_scope_pos()

	def sw_flipperLwR_active(self, sw):
		if self.intro_active:
			if self.game.switches.flipperLwL.is_active():
				self.layer.force_next(True)	
		elif self.mode == 'active':
			if self.scope_pos != 3:
				self.scope_pos += 1
			self.update_scope_pos()

	def sw_fireL_active(self, sw):
		if not self.intro_active:
			self.shoot()

	def sw_fireR_active(self, sw):
		if not self.intro_active:
			self.shoot()

	def update_scope_pos(self):
		self.scope_layer.frame = self.scope_and_shot_anim.frames[self.scope_pos]

	def shoot(self):
		self.shot_layers[self.scope_pos].frame = self.scope_and_shot_anim.frames[self.scope_pos + 4]
		if self.states[self.scope_pos] == 'enemy':
			self.delay(name='enemy_shot', event_type=None, delay=1.5, handler=self.enemy_shot, param=self.scope_pos)
			self.states[self.scope_pos] = 'shot'
			self.result_layer.set_text("Good Shot",1)
			self.num_enemies_shot += 1
			self.game.sound.play('bad guy shot')
		elif self.states[self.scope_pos] == 'empty':
			self.delay(name='empty_shot', event_type=None, delay=0.5, handler=self.empty_shot, param=self.scope_pos)
		elif self.states[self.scope_pos] == 'friend':
			self.friend_shot(self.scope_pos)

	def enemy_shot(self, position):
		self.pos_layers[position].blink_frames = 2
		self.shot_layers[position].blink_frames = 2
		self.delay(name='enemy_remove', event_type=None, delay=1, handler=self.enemy_remove, param=position)

	def enemy_remove(self, position):
		self.states[position] = 'empty'
		self.pos_layers[position].frame = None
		self.shot_layers[position].frame = None
		self.pos_layers[position].blink_frames = 0
		self.shot_layers[position].blink_frames = 0

	def friend_shot(self, position):
		self.game.sound.play('good guy shot')
		self.mode = 'complete'
		self.status_layer.set_text("Failed!")
		self.cancel_delayed('empty_shot')
		self.cancel_delayed('enemy_shot')
		self.cancel_delayed('enemy_remove')
		self.cancel_delayed('friend_shot')
		self.cancel_delayed('add')
		self.cancel_delayed('finish')
		self.delay(name='wrap_up', event_type=None, delay=2.0, handler=self.wrap_up)
		self.success = False

	def empty_shot(self, position):
		# Make sure it's still empty
		if self.states[position] == 'empty':
			self.shot_layers[position].frame = None

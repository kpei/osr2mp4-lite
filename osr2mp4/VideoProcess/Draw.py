import copy
import sys

import time
import traceback

from PIL import Image
from osr2mp4.osrparse.replay import Replay

from osr2mp4 import logger
from osr2mp4.ImageProcess import imageproc
from osr2mp4.Utils.skip import skip
from osr2mp4.InfoProcessor import Updater
from osr2mp4.VideoProcess.AFrames import *
from osr2mp4.CheckSystem.Judgement import DiffCalculator
from osr2mp4.EEnum.EReplay import Replays
from osr2mp4.VideoProcess.smoothing import smoothcursor
from osr2mp4.VideoProcess.Setup import FrameInfo, CursorEvent, get_buffer
from osr2mp4.VideoProcess.calc import check_break, check_key, add_followpoints, add_hitobjects, nearer
from osr2mp4.CheckSystem.mathhelper import getunstablerate


class Drawer:
	def __init__(self, shared, beatmap, frames, replay_info, resultinfo, videotime, settings):
		self.shared = shared
		self.beatmap = beatmap
		self.frames = frames
		self.replay_info = replay_info
		self.replay_event = replay_info.play_data
		self.hasfl = Mod.Flashlight in replay_info.mod_combination
		self.resultinfo = resultinfo
		self.start_index = videotime[0]
		self.end_index = videotime[1]
		self.settings = settings

		self.updater = None
		self.frame_info = None
		self.component = None
		self.preempt_followpoint = None
		self.cursor_event = None
		self.img = None
		self.time_preempt = None
		self.np_img, self.pbuffer = None, None
		self.key_queue = []

		self.setup_draw()

	def setup_draw(self):
		replay_event = self.replay_info.play_data
		old_cursor_x = int(replay_event[0][Replays.CURSOR_X] * self.settings.playfieldscale) + self.settings.moveright
		old_cursor_y = int(replay_event[0][Replays.CURSOR_Y] * self.settings.playfieldscale) + self.settings.moveright

		diffcalculator = DiffCalculator(self.beatmap.diff)
		self.time_preempt = diffcalculator.ar()

		map_time = (self.beatmap.start_time, self.beatmap.end_time)
		light_replay_info = Replay()
		light_replay_info.set(self.replay_info.get())

		self.component = FrameObjects(self.frames, self.settings, self.beatmap.diff, light_replay_info, self.beatmap.meta, self.beatmap.hash, map_time)

		self.component.cursor_trail.set_cursor(old_cursor_x, old_cursor_y, replay_event[0][Replays.TIMES])
		self.component.flashlight.set_pos(old_cursor_x, old_cursor_y)

		self.preempt_followpoint = 800

		self.updater = Updater(self.resultinfo, self.component, self.settings, self.replay_info.mod_combination, self.beatmap.path)

		self.component.strain_graph.set_strain_graph(self.settings.temp + "strain.png")
		self.component.strain_graph.set_beatmap(self.resultinfo)

		to_time = replay_event[self.start_index][Replays.TIMES]
		self.frame_info = FrameInfo(*skip(to_time, self.resultinfo, replay_event, self.beatmap, self.time_preempt, self.component))

		self.cursor_event = CursorEvent(replay_event[self.frame_info.osr_index], old_cursor_x, old_cursor_y)

		self.updater.info_index = self.frame_info.info_index

		self.img = Image.new("RGB", (1, 1))
		self.np_img, self.pbuffer = get_buffer(self.shared, self.settings)

	def render_draw(self):

		if self.frame_info.osr_index >= self.start_index:
			if self.img.size[0] == 1:
				self.img = self.pbuffer

		in_break = check_break(self.beatmap, self.component, self.frame_info, self.updater, self.settings)
		cur_key = None
		if self.key_queue:
			cur_key = self.key_queue.pop(0)
			check_key(self.component, cur_key, self.frame_info.cur_time, in_break)
		add_followpoints(self.beatmap, self.component, self.frame_info, self.preempt_followpoint)
		add_hitobjects(self.beatmap, self.component, self.frame_info, self.time_preempt, self.settings)

		self.updater.update(self.frame_info.cur_time)

		cx, cy = smoothcursor(self.replay_event, self.frame_info.osr_index, self.frame_info.cur_time)

		cursor_x = int(cx * self.settings.playfieldscale) + self.settings.moveright
		cursor_y = int(cy * self.settings.playfieldscale) + self.settings.movedown

		self.component.background.add_to_frame(self.img, self.np_img, self.frame_info.cur_time, in_break)
		if not self.hasfl:
			self.component.scorebarbg.add_to_frame(self.img, self.frame_info.cur_time, in_break)

		self.component.hitresult.add_to_frame(self.img)
		self.component.followpoints.add_to_frame(self.img, self.frame_info.cur_time)
		self.component.hitobjmanager.add_to_frame(self.img, self.frame_info.cur_time)
		self.component.hitresult.add_to_frame(self.img)
		self.component.flashlight.add_to_frame(self.img, in_break, cursor_x, cursor_y)

		# we don't want the flashlight black screen to overlay the scorebarbg
		if self.hasfl:
			self.component.scorebarbg.add_to_frame(self.img, self.frame_info.cur_time, in_break)

		self.component.timepie.add_to_frame(self.np_img, self.img, self.frame_info.cur_time,self.component.scorebarbg.h,self.component.scorebarbg.alpha, in_break)
		self.component.playinggrade.add_to_frame(self.img, self.updater.info.accuracy, self.frame_info.cur_time)
		self.component.arrowwarning.add_to_frame(self.img, self.frame_info.cur_time)
		self.component.inputoverlayBG.add_to_frame(self.img, self.settings.width - self.component.inputoverlayBG.w() // 2, int(320 * self.settings.scale))
		self.component.urbar.add_to_frame_bar(self.img)
		self.component.key1.add_to_frame(self.img, self.settings.width - int(24 * self.settings.scale), int(350 * self.settings.scale), self.frame_info.cur_time)
		self.component.key2.add_to_frame(self.img, self.settings.width - int(24 * self.settings.scale), int(398 * self.settings.scale), self.frame_info.cur_time)
		self.component.mouse1.add_to_frame(self.img, self.settings.width - int(24 * self.settings.scale), int(446 * self.settings.scale), self.frame_info.cur_time)
		self.component.mouse2.add_to_frame(self.img, self.settings.width - int(24 * self.settings.scale), int(492 * self.settings.scale), self.frame_info.cur_time)
		self.component.spinbonus.add_to_frame(self.img)
		self.component.combocounter.add_to_frame(self.img, in_break)
		self.component.scorecounter.add_to_frame(self.img, self.cursor_event.event[Replays.TIMES], in_break)
		self.component.accuracy.add_to_frame(self.img, in_break)
		self.component.urbar.add_to_frame(self.img)
		self.component.cursor_trail.add_to_frame(self.img, cursor_x, cursor_y, self.frame_info.cur_time)
		self.component.cursor.add_to_frame(self.img, cursor_x, cursor_y)
		self.component.cursormiddle.add_to_frame(self.img, cursor_x, cursor_y)
		self.component.playingmodicons.add_to_frame(self.img)
		self.component.ppcounter.add_to_frame(self.img)
		self.component.strain_graph.add_to_frame(self.img, self.frame_info.cur_time)
		self.component.hitresultcounter.add_to_frame(self.img)
		self.frame_info.cur_time += self.settings.timeframe / self.settings.fps

		tt, keys = nearer(self.frame_info.cur_time, self.replay_info, self.frame_info.osr_index)
		if self.key_queue:
			while keys and keys[0] == self.key_queue[-1]:
				keys = keys[1:]
		self.key_queue.extend(keys)
		self.frame_info.osr_index += tt
		self.cursor_event.event = copy.copy(self.replay_event[self.frame_info.osr_index])
		return self.img.size[0] != 1
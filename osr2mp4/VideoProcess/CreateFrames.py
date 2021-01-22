import cv2
from multiprocessing import Process, Pipe
from osr2mp4 import logger
from osr2mp4.VideoProcess.Draw import Drawer
from osr2mp4.VideoProcess.FrameWriter import getwriter
from osr2mp4.VideoProcess.AFrames import PreparedFrames
from osr2mp4.CheckSystem.mathhelper import getunstablerate
import numpy as np
import os
import traceback

def create_frame(ur, frames, settings, beatmap, replay_info, resultinfo, videotime, filename = None):
	if(filename is None):
		filename = settings.output

	logger.debug("process start")

	shared = np.zeros((settings.height * settings.width * 4), dtype=np.uint8)
	drawer = Drawer(shared, beatmap, frames, replay_info, resultinfo, videotime, settings)

	writer = getwriter(filename, settings)
	buf = np.zeros((settings.height + int(settings.height/2.0), settings.width), dtype=np.uint8)

	logger.debug("setup done")

	while drawer.frame_info.osr_index < videotime[1]:
		status = drawer.render_draw()
		if status:
			cv2.cvtColor(drawer.np_img, cv2.COLOR_BGRA2YUV_YV12, dst=buf)
			writer.write_frame(buf)

	writer.release()
	logger.debug("\nprocess done")

	return None, None, None, None


def create_frame_process(ur, frames, settings, beatmap, replay_info, resultinfo, videotime, filename = None):
	try:
		create_frame(ur, frames, settings, beatmap, replay_info, resultinfo, videotime, filename)
	except Exception as e:
		tb = traceback.format_exc()
		logger.error("{} from {}\n{}\n\n\n".format(tb, videotime, repr(e)))
		raise

def create_frame_mp(settings, beatmap, replay_info, resultinfo, videotime):

	start_index, end_index = videotime
	osr_interval = int((end_index - start_index) / settings.process)
	start = start_index

	my_file = open(os.path.join(settings.temp, "listvideo.txt"), "w")
	drawers = []
	for i in range(settings.process):

		if i == settings.process - 1:
			end = end_index
		else:
			end = start + osr_interval

		vid = (start, end)

		_, file_extension = os.path.splitext(settings.output)
		f = os.path.join(settings.temp, f"outputf{i}{file_extension}")

		ur = getunstablerate(resultinfo)
		frames = PreparedFrames(settings, beatmap.diff, replay_info.mod_combination, ur=ur, bg=beatmap.bg)
		drawer = Process(target=create_frame_process, args=(ur, frames, settings, beatmap, replay_info, resultinfo, vid, f))
		drawer.start()
		drawers.append(drawer)

		my_file.write("file '{}'\n".format(f))

		start += osr_interval
	my_file.close()

	return drawers, None, None, None
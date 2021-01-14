import os
import time
import traceback
import numpy as np
from osr2mp4 import logger
from osr2mp4.global_var import videoextensions
from osr2mp4.Exceptions import CannotCreateVideo, FourccIsNotExtension, WrongFourcc, LibAvNotFound
from osr2mp4 import log_stream
from osr2mp4.VideoProcess.FFMpegWriter import FFMpegWriter

def getwriter(filename, videotime, settings):
	videoerror = None
	if settings.settings["FFmpeg codec"] == "":
		settings.settings["FFmpeg codec"] = "libx264"
	ffmpegcodec = settings.settings["FFmpeg codec"]
	ffmpegargs = settings.settings["FFmpeg custom commands"]
	writer = FFMpegWriter(settings.ffmpeg, filename, (settings.width, settings.height), settings.fps, ffmpegcodec, 
		None, settings.audiocodec, "ultrafast", str(settings.settings["Audio bitrate"]) + "k", 
		logfile = log_stream(), threads = 0, pixel_format="yuv420p", audiotime = videotime)
	return writer

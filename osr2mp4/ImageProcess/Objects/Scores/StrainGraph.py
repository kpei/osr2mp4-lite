from osr2mp4.ImageProcess.Objects.FrameObject import FrameObject
from osr2mp4.ImageProcess import imageproc
from osr2mp4.ImageProcess.PrepareFrames.YImage import YImage
from PIL import Image

class StrainGraph(FrameObject):
	def __init__(self, settings, start_time, end_time):
		self.settings = settings
		if(settings.settings["Enable Strain Graph"]):
			self.scale = settings.scale * settings.strainsettings["Size"]/20
			self.x = settings.strainsettings["x"] * self.scale
			self.y = settings.strainsettings["y"] * self.scale
			self.alpha = settings.strainsettings["Alpha"]
			self.graph = None
			self.graph_pixel_access = None
			self.last_position = 0
			self.width, self.height = (0,0)
			self.start_time = start_time
			self.end_time = end_time
			self.beatmap = None
			self.object_index = 0

	def set_beatmap(self, beatmap):
		self.beatmap = beatmap
		print(self.beatmap)

	def set_strain_graph(self, filename):
		if(self.settings.settings["Enable Strain Graph"]):
			strain_graph = Image.open(filename).convert("RGBA")
			self.graph = imageproc.change_size(strain_graph, self.scale, self.scale)
			self.graph_pixel_access = self.graph.load()
			self.width, self.height = self.graph.size
			return True

	def get_closest_object_time(self, cur_time):
		if self.object_index >= len(self.beatmap) or self.beatmap[self.object_index].time >= cur_time:
			return cur_time
		while self.object_index < len(self.beatmap) and self.beatmap[self.object_index].time < cur_time:
			result = self.beatmap[self.object_index].time
			self.object_index += 1
			return result

	def update_progress(self, cur_time):
		time = self.get_closest_object_time(cur_time)
		ratio = (time-self.start_time)/max(self.end_time-self.start_time, 1)
		progress = min(self.width, int(ratio*self.graph.size[0]))
		if( (progress >= 0) & (progress > self.last_position) ):
			self.set_graph_progress_opacity(self.last_position, progress, self.settings.strainsettings["ProgressAlpha"])
			self.last_position = progress

	def set_graph_progress_opacity(self, x0, x1, opacity_ratio):
		for y in range(self.height):
			for x in range(x0,x1):
				if self.graph_pixel_access[x, y][-1] > 0:
					pix = self.graph_pixel_access[x, y]
					self.graph_pixel_access[x, y] = (pix[0], pix[1], pix[2], int(pix[3]*opacity_ratio))

	def add_to_frame(self, background, cur_time):
		if(self.settings.settings["Enable Strain Graph"]):
			self.update_progress(cur_time)
			imageproc.add(self.graph, background, self.x, self.y, alpha=self.alpha)
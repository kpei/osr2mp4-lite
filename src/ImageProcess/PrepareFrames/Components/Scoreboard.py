from ImageProcess import imageproc
from ImageProcess.PrepareFrames.YImage import YImage


scoreboard = "menu-button-background"


def prepare_scoreboard(scale):
	"""
	:param scale: float
	:return: [PIL.Image]
	"""
	img = YImage(scoreboard, scale).img
	img = img.crop((int(img.size[0] * 2/3), 0, img.size[0], img.size[1]))
	img = imageproc.change_size(img, 0.6, 0.6)
	imageproc.changealpha(img, 0.3)

	playerimg = imageproc.add_color(img, [80, 80, 80])
	img = imageproc.add_color(img, [60, 70, 120])
	return [img, playerimg]


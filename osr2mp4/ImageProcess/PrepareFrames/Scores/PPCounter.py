import numpy
from PIL import Image, ImageFont, ImageDraw
from osr2mp4.ImageProcess import imageproc
from osr2mp4 import logger

def round_corner(radius, fill):
	"""Draw a round corner"""
	corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
	draw = ImageDraw.Draw(corner)
	draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
	return corner


def round_rectangle(size, radius, fill):
	"""Draw a rounded rectangle"""
	width, height = size
	rectangle = Image.new('RGBA', size, fill)
	corner = round_corner(radius, fill)
	rectangle.paste(corner, (0, 0))
	rectangle.paste(corner.rotate(90), (0, height - radius))  # Rotate the corner and paste it
	rectangle.paste(corner.rotate(180), (width - radius, height - radius))
	rectangle.paste(corner.rotate(270), (width - radius, 0))
	return rectangle

def get_font(name, size=10):
	try:
		font = ImageFont.truetype(name, size=size)
	except Exception as e:
		font = ImageFont.load_default()
		logger.error(f"Error while loading beatmap font at {name}: {repr(e)}")
	return font

def prepare_pp_counter(settings, bg, beatmap):
	PP_CARD_WIDTH = 550
	PP_CARD_HEIGHT = 300
	PP_CARD_LOWER_HEIGHT = 75
	PP_CARD_SIZE = (PP_CARD_WIDTH, PP_CARD_HEIGHT)
	FONT_BIG = get_font(settings.ppsettings["Font"], size = 50)
	FONT_HEADER = get_font(settings.ppsettings["Font"], size = 25)
	FONT_DEFAULT_TITLE = get_font(settings.ppsettings["Font"], size = 20)

	try:
		bg = Image.open(bg).convert("RGBA")
		bg = bg.resize(PP_CARD_SIZE, Image.ANTIALIAS)
		imageproc.changealpha(bg, 0.8)
	except Exception as e:
		logger.error("Error while loading beatmap BG: " + repr(e))
		bg = Image.new("RGBA", PP_CARD_SIZE, (0, 0, 0, 205))

	# create mask
	mask = round_rectangle((PP_CARD_WIDTH*5, PP_CARD_HEIGHT*5), 150, (0,0,0,255))
	mask = mask.resize(PP_CARD_SIZE, Image.ANTIALIAS)

	# create counter in card
	counter = Image.new('RGBA', (PP_CARD_WIDTH,PP_CARD_LOWER_HEIGHT), "#222f3e")
	bg.paste(counter, box = (0,PP_CARD_HEIGHT - PP_CARD_LOWER_HEIGHT))
	text_draw = ImageDraw.Draw(bg)

	# title
	title_font = FONT_DEFAULT_TITLE
	beatmap_title = f'{beatmap.meta["Artist"]} - {beatmap.meta["Title"]}'
	for fs in range(15,50):
	    f = get_font(settings.ppsettings["Font"], size=fs)
	    title_size = text_draw.textsize(beatmap_title, f)
	    if (title_size[0] >= PP_CARD_WIDTH*0.85) or (title_size[1] >= PP_CARD_HEIGHT*0.12):
	        title_font = f
	        logger.info(f"PP Counter Title size: {fs}")
	        break
	text_draw.text((int((PP_CARD_WIDTH-title_size[0])/2),10), beatmap_title, "white", font=title_font)

	# pp
	text_draw.text((int(PP_CARD_WIDTH*0.25), int(PP_CARD_HEIGHT - PP_CARD_LOWER_HEIGHT/1.2)), "pp", "#c8d6e5", font=FONT_BIG)

	# hit counter
	text_draw.text((int(PP_CARD_WIDTH*0.47), int(PP_CARD_HEIGHT - PP_CARD_LOWER_HEIGHT/1.2)), "100", "#1dd1a1", font=FONT_HEADER)
	text_draw.text((int(PP_CARD_WIDTH*0.67), int(PP_CARD_HEIGHT - PP_CARD_LOWER_HEIGHT/1.2)), "50", "#54a0ff", font=FONT_HEADER)
	text_draw.text((int(PP_CARD_WIDTH*0.84), int(PP_CARD_HEIGHT - PP_CARD_LOWER_HEIGHT/1.2)), "miss", "#ff6b6b", font=FONT_HEADER)

	# round corners
	mask.paste(bg, mask = mask)
	mask.save(settings.temp + "pptemplate.png")

	return mask

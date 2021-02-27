import os
from osr2mp4.osr2mp4 import Osr2mp4
from PIL import ImageFont

def lambda_handler(event, context):
	os.system('cp ./local/bin/ffmpeg /tmp/ffmpeg')
	os.system('chmod 755 /tmp/ffmpeg')

	osr2mp4 = Osr2mp4(filedata="data.json", filesettings="settings.json", filepp="ppsettings.json", filestrain="strainsettings.json", logtofile=False)
	osr2mp4.startaudio()
	osr2mp4.startvideo()
	osr2mp4.cleanup()


if __name__ == '__main__':
	lambda_handler(None, None)
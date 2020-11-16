from osr2mp4.AudioProcess.Hitsound import Hitsound
from osr2mp4.EEnum.EAudio import Sound


def overlay(time, song, hitsound, volume=1.0):
	index = int(time / 1000 * song.rate)
	endindex = min(index + len(hitsound.audio), len(song.audio))
	song.audio[index:endindex] += hitsound.audio[:endindex - index] * 0.5 * volume


def overlays(time, song, sounds, volume=1.0):
	overlay(time, song, Hitsound.hitsounds[sounds[0]], volume=volume)
	for f in sounds[1:]:
		overlay(time, song, Hitsound.hitsounds[f], volume=volume * 0.5)


def getcirclehitsound(n):
	whistle = n & 2 == 2
	finish = n & 4 == 4
	clap = n & 8 == 8
	normal = False  #  not (whistle or finish or clap)
	return normal, whistle, finish, clap


def getsliderhitsound(n):
	whistle = n & 2 == 2
	slide = not whistle
	return slide, whistle


def gethitsounds(n, objtype):
	n = int(n)
	if objtype == "circle":
		return getcirclehitsound(n)
	else:
		return getsliderhitsound(n)


def getfilename(timing, soundinfo, sampleset, hitsound, hitsoundset, objtype):
	hitsound_names = []
	objname = {"circle": "hit", "slider": "slider"}
	for key, i in enumerate(gethitsounds(hitsound, objtype)):
		if i:
			hitsound_names.append(hitsoundset[str(key)])

	index_name = "0"
	if len(soundinfo) > Sound.index:
		index_name = soundinfo[Sound.index]
	if index_name == "0":
		index_name = timing["SampleIndex"]

	if soundinfo[Sound.normalset] != "0":
		samplekey = soundinfo[Sound.normalset]
	else:
		samplekey = timing["SampleSet"]

	samplekey = str(int(samplekey) % len(sampleset))  # in case out of range
	sample_name = sampleset[samplekey]

	additional_name = sampleset[soundinfo[Sound.additionalset]]
	if objtype == "slider" or soundinfo[Sound.additionalset] == "0":
		additional_name = sample_name

	filenames = []
	if len(soundinfo) > 4 and soundinfo[Sound.filename] != '':
		filenames = [soundinfo[Sound.filename]]
	else:
		filenames.append(sample_name + "-" + objname[objtype] + "normal")
		if index_name != "0" and index_name != "1":
			filenames[-1] += index_name
		for x in range(len(hitsound_names)):
			if objtype == "circle":
				filenames.append(additional_name + "-" + objname[objtype] + hitsound_names[x])
				if index_name != "0" and index_name != "1":
					filenames[-1] += index_name
	return filenames


def addfilename(beatmapsound, skinsound, soundinfo, timing, filenames, hitobjects, key):
	hitobjects[key] = []
	for i in filenames:
		index_name = "0"
		if len(soundinfo) > Sound.index:
			index_name = soundinfo[Sound.index]
		if index_name == "0":
			index_name = timing["SampleIndex"]

		if index_name == "0":
			skinsound[i] = None
		else:
			beatmapsound[i] = None
		hitobjects[key].append(i)


def getfilenames(beatmap, ignore):
	beatmapsound = {}
	for i in range(len(beatmap.hitobjects)-1):
		my_dict = beatmap.hitobjects[i]
		if "spinner" in my_dict["type"]:
			continue

		if my_dict["hitSample"] == "":
			soundinfo = []
		else:
			soundinfo = my_dict["hitSample"].split(":")
		if len(soundinfo) < 4:
			soundinfo += (4 - len(soundinfo)) * ["0"]

		my_dict["hitSample"] = soundinfo
		my_dict["soundcircle"] = ["normal-hitnormal"]
		if "slider" in my_dict["type"]:
			my_dict["soundhead"] = ["normal-hitnormal"]
			for arrowi in range(1, my_dict["repeated"]):
				my_dict["soundarrow{}".format(arrowi)] =  ["normal-hitnormal"]
			my_dict["soundtick"] = ["normal-slidertick"]
			my_dict["soundend"] = ["normal-hitnormal"]

	beatmapsound = ["normal-hitnormal", "normal-slidertick"]
	return beatmapsound, {}


def nextpowerof2(n):
	n -= 1
	n |= n >> 1
	n |= n >> 2
	n |= n >> 4
	n |= n >> 8
	n |= n >> 16
	n += 1
	return n

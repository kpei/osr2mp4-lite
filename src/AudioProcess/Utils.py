from EEnum.EAudio import Sound


def overlay(time, song, hitsound, volume=1):
	index = int(time / 1000 * song.rate)
	song.audio[index:index + len(hitsound.audio)] += hitsound.audio * 0.5 * volume


def getcirclehitsound(n):
	whistle = n & 2 == 2
	finish = n & 4 == 4
	clap = n & 8 == 8
	normal = n & 0 == 0  #  not (whistle or finish or clap)
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

	# samplekey = str(int(samplekey) % len(sampleset))  # in case out of range
	sample_name = sampleset[samplekey]

	additional_name = sampleset[soundinfo[Sound.additionalset]]
	if objtype == "slider":
		additional_name = sample_name

	filenames = []
	if len(soundinfo) > 4 and soundinfo[Sound.filename] != '':
		filenames = [soundinfo[Sound.filename]]
	else:
		for x in range(len(hitsound_names)):
			filenames.append(sample_name + "-" + objname[objtype] + hitsound_names[x])
			if index_name != "0":
				filenames[-1] += index_name
			if objtype == "circle":
				filenames.append(additional_name + "-" + objname[objtype] + hitsound_names[x])
				# filenames[-1] += index_name  # so we can have the same name for both
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


def getfilenames(beatmap):
	# also change hitsample and edgesample of beatmap

	timingpoint_i = 0
	beatmapsound = {}
	skinsound = {}
	hitsoundset = {"0": "normal", "1": "whistle", "2": "finish", "3": "clap"}
	sliderset = {"0": "slide", "1": "whilstle"}
	sampleset = {"0": "normal", "1": "normal", "2": "soft", "3": "drum"}

	for i in range(len(beatmap.hitobjects)-1):
		my_dict = beatmap.hitobjects[i]
		if "spinner" in my_dict["type"]:
			continue

		# use next off_set or not
		while my_dict["time"] >= beatmap.timing_point[timingpoint_i + 1]["Offset"]:
			timingpoint_i += 1
		soundinfo = my_dict["hitSample"].split(":")

		hitsound = my_dict["hitSound"]

		if "slider" in my_dict["type"]:
			sampleset_name = sampleset[beatmap.timing_point[timingpoint_i]["SampleSet"]]

		objtype = "circle"
		soundset = hitsoundset
		if "slider" in my_dict["type"]:
			soundset = sliderset
			objtype = "slider"

			slidersoundinfo = my_dict["edgeSets"].split("|")
			slidersoundinfo[0] = slidersoundinfo[0].split(":")
			slidersoundinfo[1] = slidersoundinfo[1].split(":")

			sliderhitsound = my_dict["edgeSounds"].split("|")


			f = getfilename(beatmap.timing_point[timingpoint_i], slidersoundinfo[0], sampleset, sliderhitsound[0], hitsoundset, "circle")
			addfilename(beatmapsound, skinsound, slidersoundinfo[0], beatmap.timing_point[timingpoint_i], f, my_dict, "soundhead")

			end_index = timingpoint_i
			while my_dict["time"] >= beatmap.timing_point[end_index + 1]["Offset"]:
				end_index += 1
			f = getfilename(beatmap.timing_point[timingpoint_i], slidersoundinfo[1], sampleset, sliderhitsound[1], hitsoundset, "circle")
			addfilename(beatmapsound, skinsound, slidersoundinfo[0], beatmap.timing_point[end_index], f, my_dict, "soundend")

			slidertickname = [sampleset[soundinfo[Sound.normalset]] + "-slidertick"]
			addfilename(beatmapsound, skinsound, soundinfo, beatmap.timing_point[timingpoint_i], slidertickname, my_dict, "soundtick")

			my_dict["edgeSets"] = slidersoundinfo
			my_dict["edgeSounds"] = sliderhitsound

		f = getfilename(beatmap.timing_point[timingpoint_i], soundinfo, sampleset, hitsound, soundset, objtype)
		addfilename(beatmapsound, skinsound, soundinfo, beatmap.timing_point[timingpoint_i], f, my_dict, "sound" + objtype)

		my_dict["hitSample"] = soundinfo
	return beatmapsound, skinsound




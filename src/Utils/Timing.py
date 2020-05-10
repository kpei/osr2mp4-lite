from CheckSystem.Judgement import DiffCalculator
from Utils.skip import search_time, search_osrindex


def get_offset(beatmap, start_index, end_index, replay_event):
	start_time = replay_event[start_index][3]
	diffcalculator = DiffCalculator(beatmap.diff)
	timepreempt = diffcalculator.ar()
	hitobjectindex = search_time(start_time, beatmap.hitobjects)
	to_time = min(beatmap.hitobjects[hitobjectindex]["time"] - timepreempt, start_time)
	osr_index = search_osrindex(to_time, replay_event)
	print(replay_event[start_index][3], replay_event[osr_index][3])
	index = max(osr_index, start_index)
	# print(replay_event[osr_index][Replays.TIMES], replay_event[start_index][Replays.TIMES], replay_event[index][Replays.TIMES])
	offset = replay_event[index][3]
	endtime = replay_event[end_index][3] + 100
	print("\n\nOFFSET:", offset)
	return offset, endtime


def find_time(starttime, endtime, replay, replay_start):

	starttime *= 1000
	starttime += replay_start

	if endtime != -1:
		endtime *= 1000
		endtime += replay_start

	startindex = None
	endindex = len(replay) - 3
	if endtime == -1:
		endindex = len(replay) - 3
	for index, x in enumerate(replay):
		if x[3] >= starttime and startindex is None:
			startindex = index
		if x[3] >= endtime + 1000 and endtime != -1:
			endindex = index
			break

	return startindex, endindex

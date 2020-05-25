import json

import cv2
import requests
from recordclass import recordclass
import re
from ImageProcess import imageproc
from ImageProcess.Objects.FrameObject import FrameObject
from Parser.scoresparser import getscores
from global_var import Settings, Paths, GameplaySettings

BoardInfo = recordclass("BoardInfo", "score maxcombo intscore intcombo playername x y alpha id")


def getsummods(mods):
	if mods == "*":
		return "*"
	modidct = {
		"NM": 0,
		"NF": 1,
		"EZ": 2,
		"HD": 8,
		"HR": 16,
		"SD": 32,
		"DT": 64,
		"RX": 128,
		"HT": 256,
		"NC": 576,
		"FL": 1024,
		"AT": 2048,
		"SO": 4096,
		"AP": 8192,
		"PF": 16384
	}

	summod = 0

	for i in mods:
		summod += modidct[i]

	return summod


def getmods(mods):
	if mods == "*":
		return "*"
	return re.findall('..', mods)


class Scoreboard(FrameObject):
	def __init__(self, frames, scorenetryframes, effectframes, replay_info, beatmap):
		FrameObject.__init__(self, frames)

		self.score = scorenetryframes[0]
		self.rank = scorenetryframes[1]
		self.combo = scorenetryframes[2]

		self.effecteclipse = effectframes[0]
		self.effectcircle = effectframes[1]
		self.effectx, self.effecty, self.effectalpha = 0, 0, 0

		self.scoreboards = []
		self.posboards = []
		self.alphaboards = None
		self.origposboards = []
		self.playerboard = None
		self.curscore = 0
		self.maxcombo = 0
		self.oldrankid = None
		self.falling = False

		self.nboard = 6
		self.height = (660 - 313) / self.nboard * Settings.scale
		self.beatmaphash = replay_info.beatmap_hash
		self.beatmapid = beatmap.meta["BeatmapID"]
		self.getscores()
		self.scoreboards.append(BoardInfo("", "", self.curscore, self.maxcombo, replay_info.player_name, None, None, None, -1))
		self.shows = max(0, len(self.scoreboards)-self.nboard+1)
		_, self.currank = self.sortscore()

		self.setuppos()

		self.animate = False

	def setuppos(self):
		x = 0
		y = 313 * Settings.scale
		self.nboard = min(self.nboard, len(self.scoreboards))
		for i in range(self.nboard):
			self.origposboards.append([x, y])
			y += self.height
		self.alphaboards = [1] * self.nboard

		for i in range(len(self.scoreboards)-1, -1, -1):
			if i <= len(self.scoreboards) - self.nboard and len(self.scoreboards) - self.nboard >= 0 and len(self.origposboards) > 1:
				x, y = self.origposboards[1]
				alpha = 0
			else:
				index = i - len(self.scoreboards) + self.nboard
				x, y = self.origposboards[index]
				alpha = 1
			self.scoreboards[i].x = x
			self.scoreboards[i].y = y
			self.scoreboards[i].alpha = alpha
		self.scoreboards[0].x = self.origposboards[0][0]
		self.scoreboards[0].y = self.origposboards[0][1]
		self.scoreboards[0].alpha = 1

	def getscores(self):
		mods = getmods(GameplaySettings.settings["Mods leaderboard"])

		if GameplaySettings.settings["Global leaderboard"]:
			self.getglobalscores(mods)
		else:
			self.getlocalscores(mods)

	def getglobalscores(self, mods):
		k = GameplaySettings.settings["api key"]
		if k is None:
			print("\n\n YOU DID NOT ENTERED THE API KEY. GET THE API HERE https://osu.ppy.sh/p/api/\n\n")
			self.getlocalscores(mods)
			return


		if mods == "*":
			data = {'k': k, 'b': self.beatmapid}
		else:
			summods = getsummods(mods)
			data = {'k': k, 'b': self.beatmapid, 'mods': summods}


		r = requests.post("https://osu.ppy.sh/api/get_scores", data=data)
		data = json.loads(r.text)

		if "error" in data:
			print("\n\n {} \n\n".format(data["error"]))
			self.getlocalscores(mods)
			return

		for i in range(len(data)):
			score = data[i]
			strscore = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(score["score"]))  # add dot to every 3 digits
			strcombo = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(score["maxcombo"]))
			self.scoreboards.append(BoardInfo(strscore, strcombo, int(score["score"]), int(score["maxcombo"]), score["username"], None, None, None, i))
		self.oldrankid = None


	def getlocalscores(self, mods):
		scores = getscores(self.beatmaphash, Paths.osu + "scores.db")
		for i in range(len(scores["scores"])):
			score = scores["scores"][i]

			summods = getsummods(mods)
			if summods != score["mods"]["modFlags"] and summods != "*":
				continue

			strscore = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(score["score"]))  # add dot to every 3 digits
			strcombo = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(score["max_combo"]))
			self.scoreboards.append(BoardInfo(strscore, strcombo, score["score"], score["max_combo"], score["player"], None, None, None, i))
		self.oldrankid = None

	def sortscore(self):
		self.scoreboards.sort(key=lambda x: x.intscore, reverse=True)
		playerrank = [i for i in range(len(self.scoreboards)) if self.scoreboards[i].id == -1][0]

		if self.oldrankid == playerrank:
			return False, playerrank
		self.oldrankid = playerrank
		return True, playerrank

	def setscore(self, score, combo=None):
		self.curscore = score
		curinfo = self.scoreboards[self.currank]
		if combo is not None:
			combo = max(combo, curinfo.intcombo)
		else:
			combo = curinfo.intcombo
		strscore = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(score))  # add dot to every 3 digits
		strcombo = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(combo))
		self.scoreboards[self.currank] = BoardInfo(strscore, strcombo, score, combo, curinfo.playername, curinfo.x, curinfo.y, curinfo.alpha, -1)
		animating = self.animate
		prevrank = self.currank
		self.animate, self.currank = self.sortscore()
		if self.animate and not animating:
			self.setranktoanimate(prevrank=prevrank)
			if self.effectalpha <= 0:
				self.effectalpha = 2.5
				self.effectx = -500 * Settings.scale
				self.effecty = self.scoreboards[self.currank].y

	def setsetscore(self, score, combo):
		self.curscore = score
		curinfo = self.scoreboards[self.currank]
		if combo is not None:
			combo = max(combo, curinfo.intcombo)
		else:
			combo = curinfo.intcombo
		strscore = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(score))  # add dot to every 3 digits
		strcombo = re.sub(r'(?<!^)(?=(\d{3})+$)', r'.', str(combo))
		self.scoreboards[self.currank] = BoardInfo(strscore, strcombo, score, combo, curinfo.playername, curinfo.x, curinfo.y, curinfo.alpha, -1)
		self.animate, self.currank = self.sortscore()
		if self.animate:
			self.setranktoanimate()
			if self.effectalpha <= 0:
				self.effectalpha = 2.5
				self.effectx = -500 * Settings.scale
				self.effecty = self.scoreboards[self.currank].y

	def getrange(self):
		if self.currank < self.nboard - 1:
			return min(0, self.currank), self.currank
		return self.currank - 4, self.currank

	def setranktoanimate(self, prevrank=None):
		start, end = self.getrange()
		self.scoreboards[0].y = self.origposboards[0][1]
		count = 0
		for i in range(start+1, end):
			count += 1
			if i == self.currank:
				continue
			self.scoreboards[i].y = self.origposboards[count][1]
		if prevrank is None:
			prevrank = self.currank+1
		rank = max(prevrank-1, self.currank)
		rank = min(self.nboard - 2, rank)
		if self.currank < self.nboard - 1:
			self.scoreboards[self.currank].y = self.origposboards[rank+1][1]
			for i in range(0, self.nboard):
				self.scoreboards[i].alpha = 1

	def drawnumber(self, background, x_offset, y_offset, number, frames, alpha):
		number = number
		x_start = x_offset
		for digit in number:
			if digit == "x":
				digit = 10
			elif digit == ".":
				digit = 11
			else:
				digit = int(digit)
			imageproc.add(frames[digit], background, x_start, y_offset + self.height * 0.8, alpha=alpha)
			x_start += frames[digit].size[0]

	def drawscore(self, background, y_offset, number, alpha):
		self.drawnumber(background, 5 * Settings.scale, y_offset, number, self.score, alpha)

	def drawcombo(self, background, y_offset, number, alpha):
		number = number + "x"
		n = len(number)
		x_start = self.frames[0].size[0] - int(n * self.combo[0].size[0])
		self.drawnumber(background, x_start, y_offset, number, self.combo, alpha)

	def drawname(self, background, y_offset, text, alpha):
		cv2.putText(background, text, (0, int(y_offset + self.height * 0.4)), cv2.QT_FONT_NORMAL, Settings.scale * 0.5, (alpha * 255, alpha * 255, alpha * 255, alpha * 150), 1, cv2.LINE_AA)

	def add_to_frame(self, np_img, background, in_break):
		if not GameplaySettings.settings["Show scoreboard"]:
			return

		shows = max(1, self.currank - self.nboard + 2)
		ranktoclimb = self.nboard - 1
		for x in range(len(self.scoreboards)-1, -1, -1):
			if shows <= x < self.currank:
				boardindex = x - shows + 1
				if self.scoreboards[x].y >= self.origposboards[boardindex][1] and self.scoreboards[x].alpha >= 1:
					self.scoreboards[x].y = self.origposboards[boardindex][1]
				else:
					self.scoreboards[x].y = min(self.origposboards[boardindex][1], self.scoreboards[x].y + 5)
					self.scoreboards[x].alpha = min(1, self.scoreboards[x].alpha + 0.02)

			if self.currank < ranktoclimb and self.currank < x < self.nboard:
				self.scoreboards[x].y = min(self.scoreboards[x].y + 5, self.origposboards[x][1])

			if x > self.currank and self.scoreboards[x].alpha > 0:
				if self.currank >= ranktoclimb:
					self.scoreboards[x].alpha -= 0.01
					self.scoreboards[x].y += 5
					self.falling = True

			if self.scoreboards[x].alpha <= 0 or (ranktoclimb <= self.currank < x) or (self.currank < ranktoclimb < x):
				continue

			if x == self.currank:
				self.frame_index = 1
				boardindex = min(ranktoclimb, self.currank)
				self.scoreboards[x].y = max(self.scoreboards[x].y - 5, self.origposboards[boardindex][1])
			else:
				self.frame_index = 0

			if GameplaySettings.settings["In-game interface"] or in_break:
				super().add_to_frame(background, self.scoreboards[x].x, self.scoreboards[x].y, topleft=True, alpha=self.scoreboards[x].alpha)
				self.drawscore(background, self.scoreboards[x].y, self.scoreboards[x].score, self.scoreboards[x].alpha)
				self.drawcombo(background, self.scoreboards[x].y, self.scoreboards[x].maxcombo, self.scoreboards[x].alpha)
				self.drawname(np_img, self.scoreboards[x].y, self.scoreboards[x].playername, self.scoreboards[x].alpha)

		alpha = max(0, min(1, self.effectalpha))
		if GameplaySettings.settings["In-game interface"] or in_break:
			imageproc.add(self.effecteclipse, background, self.effectx, self.effecty, alpha=alpha)
			imageproc.add(self.effectcircle, background, 0, self.effecty, alpha=alpha)

		self.effectalpha -= 0.1
		self.effectx = min(0 * Settings.scale, self.effectx + 30 * Settings.scale)


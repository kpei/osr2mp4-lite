from Objects.abstracts import *


hitprefix = "hit"
scoreprefix = "score-"
score_x = "score-x.png"


class HitResult(Images):
	def __init__(self, path, scale):
		self.scores_images = {}
		self.scores_frames = {}
		self.divide_by_255 = 1/255.0
		self.hitresults = []
		self.interval = 1000/60
		self.time = 600
		for x in [0, 50, 100]:
			self.scores_images[x] = Images(path+hitprefix+str(x)+".png", scale)
			if x == 0:
				self.to_square(self.scores_images[x])
			self.scores_images[x].to_3channel()
			self.scores_frames[x] = []
		self.prepare_frames()

	def to_square(self, image):
		max_length = int(np.sqrt(image.img.shape[0]**2 + image.img.shape[1]**2) + 2)  # round but with int
		square = np.zeros((max_length, max_length, image.img.shape[2]))
		y1, y2 = int(max_length / 2 - image.orig_rows / 2), int(max_length / 2 + image.orig_rows / 2)
		x1, x2 = int(max_length / 2 - image.orig_cols / 2), int(max_length / 2 + image.orig_cols / 2)
		square[y1:y2, x1:x2, :] = image.img[:, :, :]
		image.orig_img = square
		image.orig_rows, image.orig_cols = max_length, max_length

	def rotate_image(self, image, angle):
		image_center = tuple(np.array(image.shape[1::-1]) / 2)
		rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
		result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
		return result

	def to_3channel(self, image):
		# convert 4 channel to 3 channel, so we can ignore alpha channel, this will optimize the time of add_to_frame
		# where we needed to do each time alpha_s * img[:, :, 0:3]. Now we don't need to do it anymore
		alpha_s = image[:, :, 3] * self.divide_by_255
		for c in range(3):
			image[:, :, c] = image[:, :, c] * alpha_s

	def prepare_frames(self):
		for x in self.scores_images:
			end = 150
			start = 100
			if x != 0:
				end = 90
				start = 70
				for y in range(start, end, -5):
					self.scores_images[x].change_size(y/100, y/100)
					self.scores_frames[x].append(self.scores_images[x].img)

			for y in range(end, start, -2):
				self.scores_images[x].change_size(y/100, y/100)
				img = self.scores_images[x].img
				if x == 0:
					img = self.rotate_image(img, -10)
				self.scores_frames[x].append(img)

	def add_result(self, scores, x, y):
		if scores == 300:
			return
		# [score, x, y, index, alpha, time, go down]
		self.hitresults.append([scores, x, y, 0, 20, 0, 7])

	def add_to_frame(self, background):
		i = len(self.hitresults)
		while i > 0:
			i -= 1
			if self.hitresults[i][5] >= self.time:
				del self.hitresults[i]
				break

			score = self.hitresults[i][0]
			self.img = self.scores_frames[score][self.hitresults[i][3]][:, :, :] * (self.hitresults[i][4] / 100)

			x, y = self.hitresults[i][1], self.hitresults[i][2]
			super().add_to_frame(background, x, y)

			if score == 0:
				self.hitresults[i][2] += int(self.hitresults[i][6])
				self.hitresults[i][6] = max(2, self.hitresults[i][6] - 0.5)
			self.hitresults[i][3] = min(len(self.scores_frames[score]) - 1, self.hitresults[i][3] + 1)
			self.hitresults[i][5] += self.interval
			if self.hitresults[i][5] >= self.time - self.interval * 10:
				self.hitresults[i][4] = max(0, self.hitresults[i][4] - 10)
			else:
				self.hitresults[i][4] = min(100, self.hitresults[i][4] + 20)


class ScoreNumbers:
	def __init__(self, path, scale):
		self.score_images = []
		for x in range(10):
			self.score_images.append(Images(path + scoreprefix+str(x)+".png", scale))
			self.score_images[-1].to_3channel()
		self.score_x = Images(path + score_x, scale)
		self.score_x.to_3channel()


class SpinBonusScore(Images):
	def __init__(self, scale, gap, scorenumbers):
		self.score_frames = []
		self.spinbonuses = ["0", None, None, 10]
		self.score_images = scorenumbers.score_images
		self.gap = gap * scale
		self.gap += self.score_images[0].orig_cols
		self.divide_by_255 = 1 / 255.0

		self.prepare_scores()


	def prepare_scores(self):
		for image in self.score_images:
			self.score_frames.append([])
			size = 2.5
			for x in range(15, 5, -1):
				image.change_size(size, size)
				self.score_frames[-1].append(image.img[:, :, :] * (x/15))
				size -= 0.1

	def set_bonusscore(self, rotated_bonus, x, y):
		if rotated_bonus*1000 == int(self.spinbonuses[0]):
			return
		print(rotated_bonus)
		self.spinbonuses = [str(rotated_bonus*1000), x, y, 0]

	def xstart(self, n, x, size):
		digits = len(n)
		return int(x - size * (digits-1)/2)

	def add_to_frame(self, background):
		if self.spinbonuses[3] >= 10:
			self.spinbonuses = ["0", None, None, 10]
			return

		index = int(self.spinbonuses[3])
		x = self.xstart(self.spinbonuses[0], self.spinbonuses[1], self.gap * (2.5 - index/10))
		y = self.spinbonuses[2]

		for digit in self.spinbonuses[0]:
			digit = int(digit)
			self.img = self.score_frames[digit][index]
			super().add_to_frame(background, x, y)
			x += int(self.gap * (2.5 - index/10))

		self.spinbonuses[3] += 0.75


class ComboCounter(Images):
	def __init__(self, scorenumbers, width, height, gap):
		self.height = height
		self.width = width
		self.score_images = scorenumbers.score_images
		self.score_images.append(scorenumbers.score_x)

		self.score_frames = []
		self.score_fadeout = []

		self.score_index = 0
		self.index_step = 1
		self.fadeout_index = 0

		self.combofadeout = 0
		self.combo = 0
		self.breaking = False
		self.adding = False
		self.animate = False

		self.gap = gap

		self.divide_by_255 = 1/255

		self.prepare_combo()

	def prepare_combo(self):
		for digit in range(len(self.score_images)):
			self.score_frames.append([])
			self.score_fadeout.append([])
			for x in range(10, 15):
				self.score_images[digit].change_size(x/10, x/10)
				normal = self.score_images[digit].img
				self.score_frames[-1].append(normal)

			for x in range(20, 10, -1):
				self.score_images[digit].change_size(x/10, x/10)
				fadeout = self.score_images[digit].img[:, :, :] * (x/60)
				self.score_fadeout[-1].append(fadeout)

	def breakcombo(self):
		self.breaking = True
		self.adding = False
		self.animate = False
		self.combofadeout = 0

	def add_combo(self):
		if self.breaking:
			self.combo = 0
		if self.adding:
			self.combo = self.combofadeout
			self.score_index = 0
			self.index_step = 1
			self.animate = True

		self.breaking = False
		self.adding = True

		self.fadeout_index = 0
		self.combofadeout += 1

	def get_combo(self):
		return max(0, self.combofadeout-1)

	def add_to_frame(self, background):

		if self.fadeout_index == 10:
			self.combo = self.combofadeout
			self.score_index = 0
			self.index_step = 1
			self.fadeout_index = 0
			self.animate = True
			self.adding = False

		if self.breaking:
			self.combo = max(0, self.combo - 1)

		if self.score_index == 4:
			self.index_step = -1

		if self.score_index == 0 and self.animate and self.index_step == -1:
			self.animate = False

		if self.adding:
			x = 0
			y = self.height - self.score_fadeout[0][self.fadeout_index].shape[0]
			for digit in str(self.combofadeout):
				digit = int(digit)
				self.img = self.score_fadeout[digit][self.fadeout_index]
				x += self.img.shape[1] + self.gap
				x_offset = x - self.img.shape[1]//2
				y_offset = y + self.img.shape[0]//2
				super().add_to_frame(background, x_offset, y_offset)


			self.img = self.score_fadeout[10][self.fadeout_index]
			x += self.img.shape[1] + self.gap
			x_offset = x - self.img.shape[1] // 2
			y_offset = y + self.img.shape[0] // 2
			super().add_to_frame(background, x_offset, y_offset)

			self.fadeout_index += 1

		x = 0
		y = self.height - self.score_frames[0][self.score_index].shape[0]
		for digit in str(self.combo):
			digit = int(digit)
			self.img = self.score_frames[digit][self.score_index]
			x += self.img.shape[1] + self.gap
			x_offset = x - self.img.shape[1]//2
			y_offset = y + self.img.shape[0]//2
			super().add_to_frame(background, x_offset, y_offset)


		self.img = self.score_frames[10][self.score_index]
		x += self.img.shape[1] + self.gap
		x_offset = x - self.img.shape[1] // 2
		y_offset = y + self.img.shape[0] // 2
		super().add_to_frame(background, x_offset, y_offset)

		if self.animate:
			self.score_index += self.index_step


class ScoreCounter(Images):
	def __init__(self, scorenumbers, diff, width, height, gap):
		self.score_images = scorenumbers.score_images
		self.prepare_number()
		self.diff = diff
		self.diff_multiplier = self.difficulty_multiplier()
		self.showscore = 0
		self.score = 0
		self.width = width
		self.height = height
		self.gap = gap + self.score_images[0].img.shape[1]
		self.divide_by_255 = 1 / 255.0

	def prepare_number(self):
		for image in self.score_images:
			image.change_size(0.75, 0.75)

	def difficulty_multiplier(self):
		points = self.diff["OverallDifficulty"] + self.diff["HPDrainRate"] + self.diff["CircleSize"]
		if points in range(0, 6):
			return 2
		if points in range(6, 13):
			return 3
		if points in range(13, 18):
			return 4
		if points in range(18, 25):
			return 5
		return 6

	def update_score(self, combo, hitvalue, mod=1):
		self.score += int(hitvalue + (hitvalue * ((combo * self.diff_multiplier * mod) / 25))+0.5)
		self.showscore += hitvalue * ((combo * self.diff_multiplier * mod) / 25)

	def add_to_frame(self, background):
		score_string = str(int(self.showscore))
		score_string = "0" * (8 - len(score_string)) + score_string
		x = self.width - self.gap * len(score_string) - self.score_images[0].img.shape[1]//2
		y = self.score_images[0].img.shape[0]//2
		for digit in score_string:
			digit = int(digit)
			self.img = self.score_images[digit].img
			super().add_to_frame(background, x, y)
			x += self.gap


		add_up = min(19.0, (self.score - self.showscore)/30)
		if self.showscore + add_up > self.score:
			self.showscore = max(self.score - 1, self.showscore + 0.2)
		else:
			self.showscore += add_up
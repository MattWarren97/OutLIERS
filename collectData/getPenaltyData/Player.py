class Player:
	def __init__(self, id):
		self.id = id
		self.takerRating = 1500
		self.keeperRating = 1500
		self.takeCount = 0
		self.keeperCount = 0

	def deltaTakerRating(self, rating):
		self.takerRating += rating
	def deltaKeeperRating(self, rating):
		self.keeperRating += rating

	def incrTakeCount(self):
		self.takeCount += 1
	def incrKeeperCount(self):
		self.keeperCount += 1

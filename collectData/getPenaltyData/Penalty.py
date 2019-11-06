class Penalty:

	def __init__(self, takerID, keeperID, scored, year, gameweek, matchID):
		self.takerID = takerID
		self.keeperID = keeperID
		self.scored = scored
		self.year = year
		self.gw = gameweek
		self.matchID = matchID

	def getResult(self):
		if self.scored:
			return "SCORED"
		else:
			return "MISSED"

	def __repr__(self):
		return "Penalty; date:" + str(self.year) + ",gw:" + str(self.gw) + "; " + str(self.takerID) + " vs. " + str(self.keeperID) + " - " + self.getResult()

	def toList(self):
		return [self.takerID, self.keeperID, self.scored, self.year, self.gw, self.matchID]

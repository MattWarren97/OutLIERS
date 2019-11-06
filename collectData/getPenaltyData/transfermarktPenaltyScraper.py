from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from time import sleep
import csv
import re
from Penalty import Penalty

driver = webdriver.Chrome()
playerNames = {}
penaltyResultsCSV = "penaltyResults.csv"
playerIdentityCSV = "playerIdentities.csv"

"""
A transfermarkt page for the penalties taken in a league in one year/
Contains: A table listing all the scored penalties in that year/
And a Table listing all the missed penalties in that year.

Each of these tables shows only 10 penalties at a time.

We have to find the correct URL (one for each year for each league)/
Then find the two tables/
Then read all the Penalties in that table/
(Including multiple pages in the table).

All these data points are read into a single array: shotData
I don't care about whether the shot misses or is scores, except/
to note this as a variable.

The outputs are written to a CSV. One line per penalty kick.
"""



def getPenalties(leagueCode, year):
	#construct the URL for the penalty data for a given league in a given year
	#load this, find the number of penalty pages, and read each one.

	shotData = []

	url = "https://www.transfermarkt.com/X/elfmeterstatistik/wettbewerb/" + str(leagueCode) +"/saison_id/" + str(year) + "/plus/1"
	driver.get(url)
	sleep(0.25)

	html = driver.page_source
	soupSrc = BeautifulSoup(html)
	penaltiesMissed = soupSrc.find(text="Penalty taker and Club")
	print("For year: ", year, "\n")
	if penaltiesMissed is None:
		print("No result found for chosen year: ", year)
		return
	fulldata = str(penaltiesMissed.parent.parent.parent.parent.parent.parent.parent)

	#find the number of pages of records: (10 records per 'page', 
	#one 'pageCount' for missed penalties, one for scored penalties (very likely to be higher))
	pageCounts = getPageCounts(fulldata)

	missedPageCount = pageCounts[0]
	scoredPageCount = pageCounts[1]

	for page in range(1, max(missedPageCount, scoredPageCount)+1):
		shotData.extend(getPenaltyPage(leagueCode, year, page, missedPageCount >= page, scoredPageCount >= page))
		#print("hi")
	#print("ShotData is: \n", shotData)
	return shotData

def getPageCounts(src):
	#for a given URL with two tables, for scored, and missed penalties
	#find the values that denote the number of pages in both those tables
	#has to deal with the fact that/
	#there may not be a <div class="pager"> for single page tables

	tableEndLocater = "div class=\"keys\""
	pageCountLocater = "Go the last page (page "
	tableEndIndices = [m.start() for m in re.finditer(tableEndLocater, src)]
	if len(tableEndIndices) != 2:
		print("FOUND " + str(len(tableEndIndices)) + " table ends. ERROR, not 2.\n")
		return

	pageCount1Index = src[:tableEndIndices[0]].find(pageCountLocater) + len(pageCountLocater)
	if pageCount1Index -len(pageCountLocater) == -1:
		#did not find page count. Assume only 1 page.
		print("Didn't find page locater here for MISSES: setting page count to 1")
		pageCount1 = 1
	else:
		pageCount1End = src[pageCount1Index:].find(")") + pageCount1Index
		pageCount1 = src[pageCount1Index:pageCount1End]
	pageCount2Index = src[tableEndIndices[0]:tableEndIndices[1]].find(pageCountLocater) + len(pageCountLocater) + tableEndIndices[0]
	if pageCount2Index-len(pageCountLocater) == -1:
		pageCount2 = 1
		print("Didn't find page locater here for SCORED: setting page count to 1")
	else:
		pageCount2End = src[pageCount2Index:].find(")")+pageCount2Index
		pageCount2 = src[pageCount2Index:pageCount2End]

	print("pageCounts are", pageCount1, ",", pageCount2)
	return [int(pageCount1), int(pageCount2)]



def getPenaltyPage(leagueCode, year, page, collectMissed, collectScored):
	#load each page of the penalty tables 
	#collect data as Penalty objects, add them to shotData
	#return an array of all Penalty objects on this page

	shotData = []
	print("page: ", page, ", missed;scored: ", collectMissed, "; ", collectScored)
	
	url = "https://www.transfermarkt.com/X/elfmeterstatistik/wettbewerb/" + leagueCode +"/saison_id/" + str(year) + "/plus/1/page/" + str(page)

	driver.get(url)
	sleep(0.25)

	html = driver.page_source
	soupSrc = BeautifulSoup(html)
	penaltiesMissed = soupSrc.find(text="Penalty taker and Club")
	print("For year: ", year, ", page: ", page, "\n")
	if penaltiesMissed is None:
		print("No result found for chosen year,page, leagueCode: ", year, ",", page, ",", leagueCode)
		return
	fulldata = str(penaltiesMissed.parent.parent.parent.parent.parent.parent.parent)

	#print(fulldata)

	(missTable, fulldata) = getValueBetween(fulldata, "Penalty statistics: Missed", "Penalty statistics: Scored")
	(scoreTable, fulldata) = getValueBetween(fulldata, "Penalty statistics: Scored", -1)
	

	if(collectMissed):
		misses = findPenalties(missTable)
		for miss in misses:
			shot = Penalty(miss[0], miss[1], False, year, miss[2], miss[3])
			shotData.append(shot)
	if(collectScored):
		goals = findPenalties(scoreTable)
		for goal in goals:
			shot = Penalty(goal[0], goal[1], True, year, goal[2], goal[3])
			shotData.append(shot)
	return shotData

def findPenalties(table):
	#within a penaltyPage, there are two tables.
	#html writing one table will be passed to this function
	#this function splits the table into the individual shots,
	#and extracts the required information.

	shotData = []

	individualShots = str(table).split("<td class=\"zentriert\">") #this string appears twice per penalty

	for count, src in enumerate(individualShots[1::2]):

		#	first = True
		(gameweek, src) = getValueBetween(src, "", "</td>")

		(takerID, src) = getValueBetween(src, "/spieler/", "\"")

		(takerName, src) = getValueBetween(src, "\" id=\""+takerID+"\">", "<")
		addPlayer(int(takerID), takerName)

		(keeperID, src) = getValueBetween(src, "/spieler/", "\"")

		(keeperName, src) = getValueBetween(src, "\" id=\""+keeperID+"\">", "<")
		addPlayer(int(keeperID), keeperName)

		src2 = individualShots[count*2+2]
		(matchID, src2) = getValueBetween(src2, "spielbericht/index/spielbericht/", "\"")

		shotData.append([takerID, keeperID, gameweek, matchID])
		print("For this shot, takerID was : ", takerID, ", and keeperID was : ", keeperID, ".\n")
	
	return shotData
	
def addPlayer(ID, name):
	playerNames[ID] = name


def getValueBetween(src, beginMarker, endMarker):
	#within a long string (src),
	#find the String between the beginMarker and the endMarker

	beginIndex = src.find(beginMarker) + len(beginMarker)
	if (beginIndex - len(beginMarker) == -1):
		#then find returned -1, not found
		print("The marker ", beginMarker, " was not found in src:\n\n", src)
		return
	if endMarker == -1:
		endIndex = len(src)
	else:
		endIndex = beginIndex + src[beginIndex:].find(endMarker)
		if endIndex - beginIndex == -1:
			print("The end marker ", endMarker, " was not found after the beginMarker: ", beginMarker, " in src:\n\n", src)
			return
	val = src[beginIndex:endIndex]
	#print("The value : ", val, " was found!\n")
	#print("Src is: \t", src, "\n\n")
	return (val, src[endIndex:])


def sanitiseNumberString(s):
	return str(s.replace(',', ''))


def findPenaltiesFromLeague(leagueCode, startYear, endYear, append=False):
	#given a leagueCode, the start and end years, 
	#makes calls to getPenalties for the relevant years,
	#then writes the results into a CSV file in the data directory

	#can be used with append=True to not overwrite existing data for the 
	#selected league.

	resultCsv = "../../data/penaltyData/" + leagueCode+".csv"
	idCsv = "../../data/penaltyData/" + leagueCode+"ID.csv"
	penaltyResults = []
	for year in range(startYear, endYear):
		shotData = getPenalties(leagueCode, year)
		penaltyResults.extend(shotData)

	fileOperation = ''
	if append:
		fileOperation = 'a'
	else:
		fileOperation = 'w'


	with open(resultCsv, fileOperation) as output:
		writer = csv.writer(output, lineterminator='\n')
		for penalty in penaltyResults:
			print("row: ", penalty)
			writer.writerow(penalty.toList())

	with open(idCsv, fileOperation) as output:
		writer = csv.writer(output, lineterminator='\n')
		for player in playerNames.keys():
			print("Player: ", player, " - ", playerNames[player])
			writer.writerow([player, playerNames[player]])




def findPenaltyData():
	#with start year 2005, end year: 2005 - no data will be returned.
	#start year 2005, end year: 2006 will return data from the 2005/06 season
	#use "append=True" to not overwrite all existing data for this league.

	findPenaltiesFromLeague("NL1", 2007, 2020)
	findPenaltiesFromLeague("GB1", 2005, 2020)
	findPenaltiesFromLeague("ES1", 2005, 2020)
	findPenaltiesFromLeague("ES2", 2013, 2020)
	findPenaltiesFromLeague("L1", 2005, 2020)
	findPenaltiesFromLeague("L2", 2005, 2020)
	findPenaltiesFromLeague("GB2", 2007, 2020)
	findPenaltiesFromLeague("GB3", 2009, 2020)
	findPenaltiesFromLeague("FR1", 2014, 2020)

	#findPenaltiesFromLeague("L2", 2018, 2020, append=True)
	#findPenaltiesFromLeague("GB2", 2018, 2020, append=True)
	#findPenaltiesFromLeague("GB3", 2018, 2020, append=True)
	#findPenaltiesFromLeague("FR1", 2018, 2020, append=True)



findPenaltyData()


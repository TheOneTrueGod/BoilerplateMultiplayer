import sys, Globals, pygame, random, math
from twisted.spread import pb
from twisted.internet import reactor
from twisted.python import util
from pygame.locals import *

from Globals import *
from Abilities import AbilStruct
from Units import UnitStruct
frame = 0
for i in range(len(sys.argv)):
	if sys.argv[i] == "-d":
		DEBUGMODE = 1
		
pMax = -1

units = []
abils = []
class Player:
	def __init__(self):
		self.keys = Keys()
		self.lastActive = {}
		
	def getKeys(self):
		return self.keys.getKeys()
		
	def getLastActivity(self, type):
		if type in self.lastActive:
			return self.lastActive[type]
		return 0
	
	def setLastActivity(self, type, frame):
		self.lastActive[type] = frame
		
	def keyPressed(self, key):
		return self.keys.keyPressed(key)
		
	def buttonsDown(self):
		return self.keys.getMouseButtons()
		
	def getMousePos(self):
		p = self.keys.getMousePos()
		return p
		
	def handleEvent(self, ev):
		self.keys.handleEvent(ev)
		
class Players:
	def __init__(self):
		self.players = {}
		self.playerDropped = False
	
	def addPlayer(self):
		if len(self.players) not in self.players:
			self.players[len(self.players)] = Player()
			print "Creating new player:", len(self.players) - 1
			return len(self.players) - 1
		else:
			return -1
		
	def getNumPlayers(self):
		return len(self.players)
		
	def dropPlayer(self, num):
		print "Deleting player:", num
		if num in self.players:
			del self.players[num]
			self.playerDropped = True
			
	def everDroppedPlayer(self):
		return self.playerDropped
		
	def getPlayer(self, num):
		if num in self.players:
			return self.players[num]
		else:
			return None
		
	def handleEvent(self, id, ev):
		if id in self.players:
			self.players[id].handleEvent(ev)
		elif DEBUGMODE:
			print "***************"
			print "ERROR IN HANDLEEVENT:", id, "not a valid player."
			print self.players
			print "***************"

class Keys:
	def __init__(self):
		self.pressed = {}
		self.mousePos = [0, 0]
		self.mouseButtons = []

	def getMousePos(self):
		return self.mousePos
		
	def getMouseButtons(self):
		return self.mouseButtons
		
	def keyPressed(self, key):
		return key in self.pressed
		
	def getKeys(self):
		return self.pressed
	
	def handleEvent(self, ev):
		if ev['type'] == KEYDOWN:
			self.pressed[ev['key']] = True
		elif ev['type'] == KEYUP:
			if ev['key'] in self.pressed:
				del self.pressed[ev['key']]
		elif ev['type'] == MOUSEMOTION:
			self.mousePos = ev['pos']
		elif ev['type'] == MOUSEBUTTONDOWN:
			self.mousePos = ev['pos']
			self.mouseButtons += [ev['button']]
		elif ev['type'] == MOUSEBUTTONUP:
			self.mousePos = ev['pos']
			if ev['button'] in self.mouseButtons:
				self.mouseButtons.remove(ev['button'])

class RootOb(pb.Root):
	def remote_createNewPlayer(self):
		global players
		return players.addPlayer()
	
	def remote_updateEvents(self, playerID, ev):
		global players
		players.handleEvent(playerID, ev)
		
	def remote_dropPlayer(self, playerNum):
		global _done
		print "Player Dropped..."
		players.dropPlayer(playerNum)
		_done = True
		
	def remote_getCharDrawList(self, pID):
		global units, players, frame
		player = players.getPlayer(pID)
		if player and player.getLastActivity("abils") != frame:
			player.setLastActivity("abils", frame)
			return units.getDrawList(player)
		return ""
		
	def remote_getBulletDrawList(self, pID):
		global abils, players, frame
		player = players.getPlayer(pID)
		if player and player.getLastActivity("chars") != frame:
			player.setLastActivity("chars", frame)
			return abils.getDrawList(player)
		return ""
		
players = Players()
abils = AbilStruct()
units = UnitStruct()

started = True
_done = False

def mainLoop():
	global _done, handicap, frame
	frame = (frame + 1) % 5000
	if started:
		units.update(players, abils)
		abils.update(units)

	if False:#units.getWinner():
		print "WINNER!:", units.getWinner()
		reactor.stop()
		_done = True
	if players.everDroppedPlayer():
		_done = True
		reactor.stop()
	if not _done:
		reactor.callLater(0.005, mainLoop)
	
if __name__ == '__main__':
	reactor.listenTCP(8789, pb.PBServerFactory(RootOb()))
	reactor.callLater(0, mainLoop)
	print "Server Created."
	reactor.run()
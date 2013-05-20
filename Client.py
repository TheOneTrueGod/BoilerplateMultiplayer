print "Initializing..."
import sys, os, math, pygame, random
from twisted.spread import pb
from twisted.internet import reactor
from twisted.python import util
from pygame.locals import *

from Units import drawUnit
from Abilities import drawAbil

from Globals import *
print "  Initializing Pygame..."
pygame.init()
print "  Initializing Variables..."
surface = None
charsToDraw = ""
abilsToDraw = ""
gotPics = [True, True]
playerNum = -1
_done = False
finished = False
connected = False;
host = "localhost"
teamOn = 1

PICTURES = {1:{}, 2:{}}
BUILDINGPICS = {1:{}, 2:{}}
ICONS = {}
TOOLTIPS = {}
class ReconnectingClientFactory(pb.PBClientFactory):
	"""My clients auto-reconnect with an exponential back-off.

	Note that clients should call my resetDelay method after they have
	connected successfully.

	@ivar maxDelay: Maximum number of seconds between connection attempts.
	@ivar initialDelay: Delay for the first reconnection attempt.
	@ivar factor: a multiplicitive factor by which the delay grows
	@ivar jitter: percentage of randomness to introduce into the delay length
			to prevent stampeding.
	"""
	maxDelay = 5
	initialDelay = 0.5
	# Note: These highly sensitive factors have been precisely measured by
	# the National Institute of Science and Technology.  Take extreme care
	# in altering them, or you may damage your Internet!
	#factor = 2.7182818284590451 # (math.e)
	factor = 1.6180339887498948 # (Phi is acceptable for use as a
	# factor if e is too large for your application.)
	jitter = 0.11962656492 # molar Planck constant times c, Jule meter/mole

	delay = initialDelay
	retries = 0
	maxRetries = None
	_callID = None
	connector = None

	continueTrying = 1

	def clientConnectionFailed(self, connector, reason):
		if self.continueTrying:
			self.connector = connector
			self.retry()

	def clientConnectionLost(self, connector, unused_reason):
		global _done
		_done = True
		quit()
			
	def retry(self, connector=None):
		"""Have this connector connect again, after a suitable delay.
		"""
		if not self.continueTrying:
			if DEBUGMODE:
				print "Abandoning %s on explicit request" % (connector,)
			return

		if connector is None:
			if self.connector is None:
				raise ValueError("no connector to retry")
			else:
				connector = self.connector

		self.retries += 1
		if self.maxRetries is not None and (self.retries > self.maxRetries):
			if self.noisy:
				print "Abandoning %s after %d retries." % (connector, self.retries)
			return

		self.delay = min(self.delay * self.factor, self.maxDelay)
		if self.jitter:
			self.delay = random.normalvariate(self.delay,
																				self.delay * self.jitter)

		if self.noisy:
			print "%s will retry in %d seconds" % (connector, self.delay,)
			
		from twisted.internet import reactor
		
		def reconnector():
			self._callID = None
			global reactor, host, factory
			reactor.connectTCP(host, 8789, factory)
		self._callID = reactor.callLater(self.delay, reconnector)

	def stopTrying(self):
		"""I put a stop to any attempt to reconnect in progress.
		"""
		# ??? Is this function really stopFactory?
		if self._callID:
			self._callID.cancel()
			self._callID = None
		if self.connector:
			# Hopefully this doesn't just make clientConnectionFailed
			# retry again.
			try:
				self.connector.stopConnecting()
			except error.NotConnectingError:
				pass
		self.continueTrying = 0
	
	def resetDelay(self):
		"""Call me after a successful connection to reset.

		I reset the delay and the retry counter.
		"""
		self.delay = self.initialDelay
		self.retries = 0
		self._callID = None
		self.continueTrying = 1
	
def loadToolTips():
	global TOOLTIPS
	fileIn = open(os.path.join("Data", "ToolTips.txt"))
	line = fileIn.readline()
	while line:
		if len(line.strip()) and line.strip()[0] != "#":
			TOOLTIPS[line[:line.find(" ")].upper().strip()] = line[line.find(" ") + 1:].strip()
		line = fileIn.readline()
	
def getToolTip(name):
	global TOOLTIPS
	if name.find("_") != -1:
		return " ".join(name.split("_"))
	if name.upper() not in TOOLTIPS:
		TOOLTIPS[name.upper()] = "ERROR: ToolTip not found: '" + name + "'"
	return TOOLTIPS[name.upper()]
	


def drawLightning(start, end):
	d = dist(start, end)
	while d > 4:
		a = math.atan2(end[1] - start[1], end[0] - start[0])
		if d > 30 ** 2:
			a += random.uniform(-math.pi / 8.0, math.pi / 8.0)
			
		d = math.sqrt(d)
		last = [start[0], start[1]]
		start = [int(start[0] + math.cos(a) * min(max(d / 4.0, 20), d)), int(start[1] + math.sin(a) * min(max(d / 4.0, 20), d))]
		clr = [0, 255, 255]
		pygame.draw.line(surface, clr, start, last)
		d = dist(start, end)
		
def error(reason):
	print "ERROR DOING CALLBACK:", reason
		
def init(rootOb):
	global surface
	print "  Init Called."
	d = rootOb.callRemote("createNewPlayer")
	d.addCallbacks(setPNum, error)
	fs = pygame.FULLSCREEN
	if DEBUGMODE:
		fs = 0
	surface = pygame.display.set_mode(SCREENSIZE, fs)
	surface.fill([0] * 3)
	pygame.display.update()
	print "Initializing Complete"
	
def setPNum(pNum):
	global playerNum, connected
	playerNum = pNum
	connected = True
	
def getCharDrawList(rootOb):
	global playerNum
	info = rootOb.callRemote("getCharDrawList", playerNum)
	info.addCallbacks(setCharsToDraw, error)
	
def setCharsToDraw(chars):
	global charsToDraw, gotPics
	if chars:
		charsToDraw = chars
	gotPics[1] = True
	
def getBulletDrawList(rootOb):
	global playerNum
	info = rootOb.callRemote("getBulletDrawList", playerNum)
	info.addCallbacks(setBulletsToDraw, error)
	
def setBulletsToDraw(bullets):
	global abilsToDraw, gotPics
	if bullets:
		abilsToDraw = bullets
	gotPics[0] = True
	
def disconnectPlayer(rootOb):
	d = rootOb.callRemote("dropPlayer", playerNum)
	d.addCallbacks(stopReactor, error)
	
def stopReactor(args):
	reactor.stop()
	
def quit():
	global _done, finished
	if not finished:
		_done = True
		finished = True
		d = factory.getRootObject()
		d.addCallbacks(disconnectPlayer, error)
		
def mainLoop():
	global _done, gotPics, connected
	if _done:
		quit()
		return
	if not connected:
		if not _done:
			reactor.callLater(0, mainLoop)
		return
	
	for ev in pygame.event.get():
		if ev.type == QUIT:
			quit()
		elif ev.type in [KEYDOWN, KEYUP]:
			d = factory.getRootObject()
			d.addCallbacks(lambda object: object.callRemote("updateEvents", playerNum, {'type':ev.type, 'key':ev.key}), error)
		elif ev.type in [MOUSEMOTION]:
			d = factory.getRootObject()
			d.addCallbacks(lambda object: object.callRemote("updateEvents", playerNum, {'type':ev.type, 'pos':ev.pos}), error)
		elif ev.type in [MOUSEBUTTONDOWN, MOUSEBUTTONUP]:
			d = factory.getRootObject()
			d.addCallbacks(lambda object: object.callRemote("updateEvents", playerNum, {'type':ev.type, 'pos':ev.pos, 'button':ev.button}), error)
	if not gotPics[0] or not gotPics[1]:
		call = reactor.callLater(0, mainLoop)
		return
	
	for c in charsToDraw.split():
		drawUnit(surface, c)
	for a in abilsToDraw.split():
		drawAbil(surface, b)
	
	gotPics = [False, False]
	d = factory.getRootObject()
	d.addCallbacks(getCharDrawList, error)
	d = factory.getRootObject()
	d.addCallbacks(getBulletDrawList, error)
	
	pygame.display.update()
		
	surface.fill([0] * 3)
	if not _done:
		call = reactor.callLater(0, mainLoop)
	else:
		quit()
		
print "  Initializing Factory..."
factory = ReconnectingClientFactory()
if len(sys.argv) >= 2:
	host = sys.argv[1]
print "  Connecting to", host, "..."
reactor.connectTCP(host, 8789, factory)
print "  Connected"

#loadToolTips()
d = factory.getRootObject()
d.addCallbacks(init, error)
reactor.callLater(0, mainLoop)
reactor.run()
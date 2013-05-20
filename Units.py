import pygame, os
from Globals import *
def loadIcon(pic):
	path = os.path.join("Data", "Pics", "Icons", pic + ".PNG")
	if not os.path.exists(path):
		print "ERROR, file not found: '" + path + "'"
		return loadIcon("NoIcon")
	pic = pygame.image.load(path)
	pic.set_colorkey([255, 0, 255])
	return pic
	
def drawIcon(pic, pos):
	global ICONS, surface
	if pic in ICONS:
		toDraw = ICONS[pic]
		pos = [pos[0] - toDraw.get_width() / 2, pos[1] - toDraw.get_height() / 2]
		surface.blit(toDraw, pos)
	else:
		newIcon = loadIcon(pic)
		ICONS[pic] = newIcon
		drawIcon(folder, pic, pos)

def loadCharPic(pic):
	path = os.path.join("Data", "Pics", "Actors", pic + ".PNG")
	frames = 5
	#if "Tank" in pic:
	#	frames = 4
	if not os.path.exists(path):
		print "ERROR, file not found: '" + path + "'"
		return loadCharPic("NoChar")
	pic = pygame.image.load(path)
	pic.set_colorkey([255, 0, 255])
	width = pic.get_width() / frames
	toRet = []
	for x in xrange(frames):
		toRet += [[]]
		for y in xrange(pic.get_height() / width):
			toRet[x] += [pic.subsurface([x * width, y * width, width, width])]
	
	return toRet

def drawCharPic(surface, pic, pos, frame, angle):
	global CHARPICTURES
	if pic in CHARPICTURES:
		toDraw = pygame.transform.rotate(CHARPICTURES[pic][frame][0], 180 - angle + 90)
		pos = [pos[0] - toDraw.get_width() / 2, pos[1] - toDraw.get_height() / 2]
		surface.blit(toDraw, pos)
	else:
		CHARPICTURES[pic] = loadCharPic(pic)
		drawCharPic(surface, pic, pos, frame, angle)
		
class UnitStruct:
	def __init__(self):
		pass
		
	def update(self, players, abils):
		pass
		
	def getDrawList(self, player):
		return "Farmer|400|300"
		
class Unit:
	def __init__(self):
		pass

def drawUnit(surface, unitStr):
	s = unitStr.split("|")
	drawCharPic(surface, s[0], [int(s[1]), int(s[2])], 1, 0)
	
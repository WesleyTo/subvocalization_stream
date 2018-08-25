# -*- coding: utf-8 -*-
import argparse
import os
import time
import pygame
from random import randint
import random
import datetime
import sys
from collections import deque

# Pygame initialization
pygame.init()
screen = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()
done = False

# Parse args 1: CSV, 2: Words flash delay, 3: CVS write delay
parser = argparse.ArgumentParser()
parser.add_argument(
			'--csv',
			type=str,
			default='',
			help='Where to save the CSV file')
parser.add_argument(
			'--long_delay',
			type=str,
			default='',
			help='Time in milliseconds of words to appear')
parser.add_argument(
			'--short_delay',
			type=str,
			default='Time in milliseconds to write to CSV',
			help='')
FLAGS, unparsed = parser.parse_known_args()

# CSV filename/location to be stored
file=str(unparsed[0])
# Delay for words to flash 500-1000 millis recomended
delay=int(unparsed[1])
# Delay to write to csv file 50 millis recomended
newDelay=int(unparsed[2])

def nearest_500(n):
		return round(n / 500) * 500

def nearest_50(n):
		return round(n / 50) * 50

def tap_to_start():
	i = 0
	j = 0
	while i < 5:
		j = 0
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN and event.key < 300:
				j = 1 # handles keys that registers as two keypresses
				file.write("SENTINEL,NONE,{}\n".format(int(time.time() * 1000 - globalStart)))
				break
		i += j
path = file.replace(os.path.basename(file), "")
if not os.path.isdir(path):
	os.makedirs(path)
file = open( file ,'w')
file.write('keyPressed,wordSaid,timeStamp\n')
# Fonts/size
font = pygame.font.SysFont("comicsansms", 2*72)
font2 = pygame.font.SysFont("comicsansms", 90)
font3 = pygame.font.SysFont("comicsansms", 50)
#font4 = pygame.font.SysFont("comicsansms", 20)
font4 = pygame.font.SysFont("comicsansms", 80)
tmp = 128
text = font.render("", True, (0, tmp, 0))
text2 = font.render("", True, (0, tmp, 0))
text3 = font3.render("", True, (0, tmp, 0))
text4 = font4.render("", True, (0, tmp, 0))
# list of words for training data
#l=["yes","no","up", "down", "left", "right", "on", "off", "stop", "go"]
#l = ["yes", "no", "stop"]
l = ["yes", "no"]

silence = ""

# Create non repeating queue with 3 elems to be shown on screen
ltext_queue = deque()
ltext = random.sample(l, 1)[0]
prevWord = None
# 3 elems
newl = set(l)
newl.discard(prevWord)
ltext_queue.append(random.sample(newl, 1)[0])
prevWord = ltext_queue[-1]
newl = set(l)
newl.discard(prevWord)
ltext_queue.append(random.sample(newl, 1)[0])
prevWord = ltext_queue[-1]
newl = set(l)
newl.discard(prevWord)
ltext_queue.append(random.sample(newl, 1)[0])
prevWord = ltext_queue[-1]
# Set initial flags
flag = 0
last = 0
pause = False
next_word = False
nlast = 0
globalStart = int(time.time() * 1000)
keydown = None

#Touch any key 5 times to start
tap_to_start()

while not done:
	# Key events
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			done = True
		# Pause game key (Del on numpad, space, or q)
		if event.type == pygame.KEYDOWN and event.key in [32, 113, 266]:
			pause = not pause
		# Move to next word (enter on numpad)
		if event.type == pygame.KEYDOWN and event.key == 271:
			next_word = not next_word
		if event.type == pygame.KEYDOWN:
			# Uncomment below to see key values 
			# print(event.key)
			if (event.key >= 256 and event.key <= 265):
				keydown=str(event.key-256)
			elif (event.key == 256+15):
				keydown = 'enter'

	screen.fill((255, 255, 255))
	# Screen pygame every n milliseconds
	current = int(time.time() * 1000)-globalStart
	if (current-last > delay or next_word):
		last = current
		flag = (flag+1)%2
		if (flag):
			text = font.render(silence, True, (0, 128, 0))
			text2 = font.render(silence, True, (0, 128, 0))
			text3 = font3.render(silence, True, (0, 0, 0))
		else:
			# Pop first elem in queue
			ltext = ltext_queue.popleft()
			# Enqueue new unique elem
			newl = set(l)
			newl.discard(prevWord)
			ltext_queue.append(random.sample(newl, 1)[0])
			prevWord = ltext_queue[-1]
			# If not pause, set text to be shown on screen
			if pause:
				text = font.render("PAUSE", True, (0, 128, 0))
			else:
				text = font.render(ltext, True, (0, 128, 0))
				text2 = font2.render(ltext_queue[0], True, (0, 60, 0))
				text3 = font3.render(ltext_queue[1], True, (0, 0, 0))
				time1 = datetime.datetime.fromtimestamp(float((time.time() * 1000)-globalStart)/1000).strftime('%M:%S')#'%H:%M:%S'
				text4 = font4.render(str(time1), True, (0, 0, 0))
			next_word = False

	# CSV files every n milliseconds
	ncurrent=nearest_50(int(time.time() * 1000)-globalStart)
	if (ncurrent-nlast > newDelay):
		nlast = ncurrent
		if pause:
			file.write("PAUSE" + ',' + "PAUSE" + ',' + str(int(ncurrent)) + '\n')
		else:
			file.write((str(keydown)) + ',' + ltext + ',' + str(int(ncurrent)) + '\n')
		keydown = None

	# Put text to screen
	screen.blit(text,(320 - text.get_width() // 2, 200 - text.get_height() // 2))
	screen.blit(text2,(320 - text2.get_width() // 2, 305 - text2.get_height() // 2))
	screen.blit(text3,(320 - text3.get_width() // 2, 390 - text3.get_height() // 2))
	screen.blit(text4,(10, 10))
	pygame.display.flip()
	clock.tick(60)

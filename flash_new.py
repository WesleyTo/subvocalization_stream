import argparse
import os
from time import time
import pygame
from random import randint, choice, sample
from datetime import datetime
import sys
import json
from collections import deque

##########################################
#				PYGAME SETUP			 #
##########################################
pygame.init()
screen = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()
done = False

##########################################
#				ARG PARSING				 #
##########################################
parser = argparse.ArgumentParser()
parser.add_argument(
			'--csv',
			type=str,
			default='./outputs.csv',
			help='Where to save the CSV file')
parser.add_argument(
			'--delay',
			type=int,
			default=500,
			help='milliseconds that word appears on screen (500-1000 recommended)')
args = parser.parse_args()
file = args.csv
delay = args.delay
newDelay = 50

if not (file and delay):
	raise Exception("Missing required arguments. Run with '-h' for help")

##########################################
#			HELPER FUNCTIONS			 #
##########################################
def curr_ms():
	"""Returns the current time as milliseconds since the epoch"""
	return int(time() * 1000)

def nearest_nth(num, n):
	"""Rounds a number to the nearest multiple of n"""
	return round(num / n) * n

def pluralize(s, n):
	"""Naively pluralizes a singlular word based on the quantity.
		Dog, 0 => Dogs
		Dog, 1 => Dog
		Dog, 2 => Dogs
		Glass, 2 => Glasses
	Doesn't handle special cases, such as Goose -> Geese"""
	if n == 1:
		return s
	if s.endswith('s'):
		return s + 'es'
	return s + 's'

def tap_to_start():
	"""Tells the user how to proceed with the program"""
	global FILE
	j, limit, s = 0, 5, "Press ANY KEY {} {} To Start"
	while limit > 0:
		j = 0
		screen.fill((255, 255, 255))
		t = s.format(limit, pluralize("Time", limit))
		text = font3.render(t, True, (0, 128, 0))
		screen.blit(text,(300 - text.get_width() // 2, 200- text.get_height() // 2))
		pygame.display.flip()
		clock.tick(60)
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN and event.key < 300:
				j = 1 # handles buggy keys that registers as two keypresses
				FILE.write("SENTINEL,NONE,{}\n".format(int(curr_ms()) - GLOBALSTART))
				break
		limit -= j

def is_escape_condition(event):
	return ((event.type == pygame.QUIT) or
		(event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE))

def is_pause_condition(event, keys=[32, 113, 266]):
	return event.type == pygame.KEYDOWN and event.key in keys

def is_skip_condition(event, keys=[271]):
	return event.type == pygame.KEYDOWN and event.key in keys

def process_keypress(event):
	"""Returns the string representation of the key pressed"""
	if (event.key >= 256 and event.key <= 265):
		return str(event.key - 256)
	elif (event.key == 256 + 15):
		return 'enter'

##########################################
#				CSV SETUP				 #
##########################################
path = file.replace(os.path.basename(file), "")
if not os.path.isdir(path):
	os.makedirs(path)
FILE = open(file ,'w')
FILE.write('keyPressed,wordSaid,timeStamp\n')

##########################################
#				FONTS SETUP				 #
##########################################
R, G, B = 0, 128, 0 # text color (RGB-255)
font = pygame.font.SysFont("comicsansms", 2*72)
font2 = pygame.font.SysFont("comicsansms", 90)
font3 = pygame.font.SysFont("comicsansms", 50)
font4 = pygame.font.SysFont("comicsansms", 80)
text = font.render("", True, (R, G, B))
text2 = font.render("", True, (R, G, B))
text3 = font3.render("", True, (R, G, B))
text4 = font4.render("", True, (R, G, B))

##########################################
#			VOCABULARY SETUP			 #
##########################################
WORD_LIST = ["yes","no","up", "down", "left", "right", "on", "off", "stop", "go"]
if os.path.isfile("configuration.json"):
	with open("configuration.json", 'r') as file:
		config = json.load(file)
	WORD_LIST = config['words']
SILENCE = ""

##########################################
#			WORDS QUEUE SETUP			 #
##########################################
ltext_queue = deque()
ltext = choice(WORD_LIST)
newl = set(WORD_LIST)
ltext_queue.append(sample(newl, 1)[0])
prevWord = ltext_queue[-1]
newl = set(WORD_LIST)
newl.discard(prevWord)
ltext_queue.append(sample(newl, 1)[0])
prevWord = ltext_queue[-1]
newl = set(WORD_LIST)
newl.discard(prevWord)
ltext_queue.append(sample(newl, 1)[0])
prevWord = ltext_queue[-1]

##########################################
#			GENERAL VARIABLES SETUP		 #
##########################################
display_flag = True
last = 0
pause = False
next_word = False
nlast = 0
keydown = None
GLOBALSTART = curr_ms()

##########################################
#				MAIN LOOP				 #
##########################################
tap_to_start()
while not done:
	# Handle Keypress events
	for event in pygame.event.get():
		if is_escape_condition(event):
			print("File saved to {}".format(args.csv))
			done = True
		if is_pause_condition(event):
			pause = not pause
		if is_skip_condition(event):
			next_word = not next_word
		# All other keypresses
		if event.type == pygame.KEYDOWN:
			keydown = process_keypress(event)

	# Set up text for screen output
	current = curr_ms() - GLOBALSTART
	if (current-last > delay or next_word):
		last = current
		display_flag = not display_flag
		if display_flag:
			# Get a non-repeating word from the queue
			ltext = ltext_queue.popleft()
			newl = set(WORD_LIST)
			newl.discard(prevWord)
			ltext_queue.append(sample(newl, 1)[0])
			prevWord = ltext_queue[-1]
			if pause:
				text = font.render("PAUSE", True, (0, 128, 0))
			else:
				# Set various text to be shown on screen
				text = font.render(ltext, True, (0, 128, 0))
				text2 = font2.render(ltext_queue[0], True, (0, 60, 0))
				text3 = font3.render(ltext_queue[1], True, (0, 0, 0))
				time1 = datetime.fromtimestamp((curr_ms() - GLOBALSTART) / 1000).strftime('%M:%S')
				text4 = font4.render(str(time1), True, (0, 0, 0))
			next_word = False
		else:
			text = font.render(SILENCE, True, (0, 128, 0))
			text2 = font.render(SILENCE, True, (0, 128, 0))
			text3 = font3.render(SILENCE, True, (0, 0, 0))

	# Write to CSV file after appropriate amount of time
	ncurrent = nearest_nth(curr_ms() - GLOBALSTART, 50)
	if (ncurrent - nlast > newDelay):
		nlast = ncurrent
		if pause:
			s = "PAUSE,PAUSE,{}\n".format(ncurrent)
		else:
			s = "{},{},{}\n".format(keydown, ltext, ncurrent)
		FILE.write(s)
		keydown = None

	# Draw text to screen
	screen.fill((255, 255, 255))
	screen.blit(text,(320 - text.get_width() // 2, 200 - text.get_height() // 2))
	screen.blit(text2,(320 - text2.get_width() // 2, 305 - text2.get_height() // 2))
	screen.blit(text3,(320 - text3.get_width() // 2, 390 - text3.get_height() // 2))
	screen.blit(text4,(10, 10))
	pygame.display.flip()
	clock.tick(60)

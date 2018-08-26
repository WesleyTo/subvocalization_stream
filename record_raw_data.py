from datetime import datetime
from time import time, sleep
import serial
import serial.tools.list_ports
import wave
import os
from helpers import *

##########################################
#		UTILITY VARIABLES AND FUNCTIONS	 #
##########################################
SAMPLE_RATE = 1000
BUF_SIZE = 2000 #2KB
OUTPUT_DIR = "audio" + str(datetime.now()).replace(" ", "_").replace(":", "-")
OUTPUT = OUTPUT_DIR + "/{}.wav"
OUTPUT_LENGTH = 0.997 # seconds

##########################################
#				PORT SETUP				 #
##########################################
ports = list(serial.tools.list_ports.comports())
com_port = ''
for p in ports:
	if 'CP2102' in p[1] or 'Arduino' in p[1] or 'Generic' in p[1]:
		com_port = p[0]
if not com_port:
	raise Exception("Arduino device not found")
port = serial.Serial(com_port,115200,timeout = None)
print(">>> COM PORT: '{}'".format(com_port))

##########################################
#			FILE & DIRECTORY SETUP		 #
##########################################
if not os.path.isdir(OUTPUT_DIR):
	os.mkdir(OUTPUT_DIR)

##########################################
#			MAIN LOOP RECORDING			 #
##########################################
try:
	print(">>> (CTRL-C) to Stop Recording")
	buf = b''
	clip_counter = 0
	chunk = 0
	start = time()
	duration = time() - start
	sleep(1 - duration) # align to 1 second after doing initialization
	while(True):
		duration = time() - start
		print("\r{}\tReading chunk #{}".format(ms_to_strtime(duration * 1000), chunk), end='')
		clip_counter += 1
		chunk += 1

		# READ UP TO BUF_SIZE KB FROM ARDUINO STREAM
		rec_bytes = port.read(BUF_SIZE)
		buf += rec_bytes
		buf = buf[(SAMPLE_RATE * -2):]

		# SAVE LAST SECOND OF OUTPUT
		waveFile = wave.open(OUTPUT.format(clip_counter), 'wb')
		waveFile.setnchannels(1)
		waveFile.setsampwidth(2)
		waveFile.setframerate(SAMPLE_RATE)
		waveFile.writeframes(buf)
		waveFile.close()

		# DELAY UNTIL NEXT OUTPUT
		sleep(OUTPUT_LENGTH)
except KeyboardInterrupt:
	print("\nDone!")
except Exception as e:
	print(e)
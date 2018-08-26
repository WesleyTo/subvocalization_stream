from datetime import datetime
from time import time, sleep
import serial
import serial.tools.list_ports
import wave
import os

##########################################
#		UTILITY VARIABLES AND FUNCTIONS	 #
##########################################
TEMP = "temp.out"
SAMPLE_RATE = 1000
BUF_SIZE = 2000 #2KB
OUTPUT_DIR = "audio" + str(datetime.now()).replace(" ", "_").replace(":", "-")
OUTPUT = OUTPUT_DIR + "/{}.wav"
OUTPUT_LENGTH = 0.997 # seconds

def sec_to_str(sec):
	ms = str(sec % 1)[2:5]
	days = int(sec // (60 * 60 * 24))
	sec %= (60 * 60 * 24)
	hours = int(sec // (60 * 60))
	sec %= (60 * 60)
	minutes = int(sec // 60)
	sec %= 60
	sec = int(sec)
	return ("{:02}:{:02}:{:02}:{:02}.{}".format(days, hours, minutes, sec, ms))

##########################################
#			FILE & DIRECTORY SETUP		 #
##########################################
try:
	os.remove(TEMP)
except:
	pass
if not os.path.isdir(OUTPUT_DIR):
	os.mkdir(OUTPUT_DIR)

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
		print("\r{}\tReading chunk #{}".format(sec_to_str(duration), chunk), end='')
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
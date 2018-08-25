import pandas as pd
import sys, os, subprocess, threading, shutil
from multiprocessing import Queue, Process, Value, Lock
from functools import reduce
from helpers import *

VERBOSITY = 100
PER_WORD_DURATION = None # ms
# Input CSV and the expected column names
CSV = "outputs.csv"
TIME_NAME = "timeStamp"
KEY_NAME = "keyPressed"
WORD_NAME = "wordSaid"
# Audio paths to read/write
AUDIO_PATH = "original_audio"
SPLIT_PATH = "split_audio"

##########################################
#			General Helpers				 #
##########################################

def nearest_1000(n):
	return round(n / 1000) * 1000

##########################################
#			Multi-Threading				 #
##########################################

def run_command(command):
	NULL = open(os.devnull, 'w')
	subprocess.run(command, stdout=NULL, stderr=NULL)

def run_job(q, num_jobs, dryrun=False):
	while not q.empty():
		command = q.get()
		counter.increment()
		job_num = counter.value()
		progress_bar(job_num, num_jobs, 1, "Splitting ")
		if not dryrun:
			run_command(command)

def make_pool(q, num_jobs, num_threads=8, dryrun=False):
	threads = []
	for i in range(num_threads):
		threads.append(threading.Thread(target=run_job, args=(q, num_jobs, dryrun)))
	return threads

def run_jobs(pool):
	for thread in pool:
		thread.start()
		thread.join()

def del_threads(pool):
	for thread in pool:
		del(thread)

class Counter(object):
	""" A thread-safe counter """
	def __init__(self, initval=0):
		self.val = Value('i', initval)
		self.lock = Lock()

	def increment(self):
		with self.lock:
			self.val.value += 1

	def value(self):
		with self.lock:
			return self.val.value

##########################################
#		Dataframe IO and Manipulation	 #
##########################################

def read_inputs(file):
	return pd.read_csv(file, sep=',')

def first_signal(df):
	return df.iloc[0][TIME_NAME]

def postprocess_df(df):
	"""	Custom post-processing function.
		Add anything required for a particular dataset here """
	df = df.tail(df.shape[0] - 2) # drop the first 2 entries for rhythm reasons
	df = df.reset_index()
	return df

def make_start_end_df(df):
	""" Generate a dataframe with the word, start time, end time, and duration """
	idx = df.index[df[KEY_NAME] == "PAUSE"]
	df.loc[idx, WORD_NAME] = "PAUSE"
	prevWord = None
	startEnd = pd.DataFrame()
	prev = 0
	for i, row in df.iterrows():
		word = row[WORD_NAME]
		if prevWord != None and word != prevWord:
			start = prev
			end = row[TIME_NAME]
			duration = end - start
			if PER_WORD_DURATION == None:
				PER_WORD_DURATION = nearest_1000(duration)
			repeats = nearest_1000(duration) // PER_WORD_DURATION
			per_sample_time = int(duration / repeats) if repeats else 0
			for _ in range(repeats - 1):
				curr_start = int(start + _ * per_sample_time)
				curr_end = int(start + (_ + 1) * per_sample_time)
				startEnd = startEnd.append([pd.Series([prevWord, curr_start, curr_end, per_sample_time])])#, index=0)
			curr_start = int(start + (repeats - 1) * per_sample_time)
			curr_end = int(start + repeats * per_sample_time)
			startEnd = startEnd.append([pd.Series([word, curr_start, curr_end, per_sample_time])])#, index=0)
			prev = end
		prevWord = word
	startEnd.columns=["word", "start", "end", "duration"]
	startEnd.start = startEnd.start.shift(-1).fillna(0).astype(int)
	startEnd.end = startEnd.end.shift(-1).fillna(0).astype(int)
	startEnd.duration = startEnd.duration.shift(-1).fillna(0).astype(int)
	startEnd = startEnd[(startEnd.word != "PAUSE") & (startEnd.word != "NONE")]
	length = startEnd.shape[0]
	startEnd = startEnd.head(length - 2) # drop the last 2 for pause reasons
	if startEnd.iloc[0]["duration"] < 750:
		length = startEnd.shape[0]
		startEnd = startEnd.tail(length - 1) # drop the first one for pause reasons
	startEnd = startEnd.reset_index()
	startEnd = startEnd.drop(['index'], axis=1)
	return postprocess_df(startEnd)

def make_dirs(startEnd, numChannels=8, root='.'):
	""" Given a StartEnd DF, generate the directories
		required for the files the DF will generate """
	labels = startEnd["word"].unique()
	main_dir = os.path.join(root, SPLIT_PATH)
	if not os.path.isdir(main_dir):
		os.mkdir(main_dir)
	for label in labels:
		subdir = os.path.join(main_dir, label)
		if not os.path.isdir(subdir):
			os.mkdir(subdir)
		for i in range(numChannels):
			channel_path = os.path.join(subdir, "ch{}".format(i + 1))
			if not os.path.isdir(channel_path):
				os.mkdir(channel_path)

##########################################
#			Audio Processing			 #
##########################################

def split_audio(startEnd, audio_dir, numChannels=8, root='.'):
	labels = startEnd["word"].unique()
	q = Queue()
	num_jobs = 0
	for file in [f for f in os.listdir(audio_dir) if f.endswith(".wav")]:
		labels = {label:0 for label in labels}
		original_filepath = os.path.join(audio_dir, file)
		print("\tProcessing {}".format(original_filepath))
		channel = int(file[:2])
		for i, row in startEnd.iterrows():
			if (i + 1 % VERBOSITY == 0):
				print("\t\tAdded {}th clip to job queue".format(i))
			label = row["word"]
			startTime = ms_to_strtime(row["start"])
			endTime = ms_to_strtime(row["end"])
			subdir = "ch{}".format(channel)
			filename = "{:05}.wav".format(labels[label])
			labels[label] += 1
			new_filepath = os.path.join(root, SPLIT_PATH, label, subdir, filename)
			command = ["ffmpeg", "-i", original_filepath, "-ss", startTime, "-to", endTime, "-c", "copy", new_filepath]
			q.put(command)
			num_jobs += 1
	return q, num_jobs

def downsample(audio_path, sample_rate=8000):
	new_audio_path = os.path.join(audio_path + "_downsampled")
	if not os.path.isdir(new_audio_path):
		os.mkdir(new_audio_path)
	for wavfile in [f for f in os.listdir(audio_path) if f.endswith(".wav")]:
		original_filepath = os.path.join(audio_path, wavfile)
		new_filepath = os.path.join(new_audio_path, wavfile)
		command = ["ffmpeg", "-i", original_filepath, "-ar", str(sample_rate), new_filepath]
		print("\tDownsampling {} to {}Hz".format(original_filepath, sample_rate))
		run_command(command)
	return new_audio_path

def cleanup(d):
	for folder in d:
		shutil.rmtree(folder)

##########################################
#				Main Program			 #
##########################################

if __name__ == "__main__":
	if (len(sys.argv) == 2):
		counter = Counter(0)
		root = sys.argv[1]
		# Read in the CSV file and process it
		csv = os.path.join(root, CSV)
		outputs = read_inputs(csv)
		offset = first_signal(outputs)
		outputs[TIME_NAME] = outputs[TIME_NAME] - offset
		outputs = outputs[outputs.timeStamp > 0]
		outputs = make_start_end_df(outputs)
		print(outputs)
		make_dirs(outputs, root=root)
		# Prepare the audio for processing
		dryrun = False
		sample_rate = 8000
		downsampled_path = timer(downsample, os.path.join(root, AUDIO_PATH), sample_rate)
		# Create jobs to split the audio
		job_queue, num_jobs = timer(split_audio, outputs, downsampled_path, 8, root)
		pool = make_pool(job_queue, num_jobs, num_threads=4, dryrun=dryrun)
		# Run the audio jobs
		timer(run_jobs, pool)
		del_threads(pool)
		# Delete temporary folders/files created in the process
		cleanup([downsampled_path])
		print("Done!")
import sys, os, subprocess, random, getpass

""" Randomly samples a percentage (default 10%) of each label
	and plays back for manual verification"""

PERCENTAGE = 0.1

if __name__ == "__main__":
	if (len(sys.argv) == 2):
		incorrect = []
		root = sys.argv[1]
		audio_path = os.path.join(root, "split_audio")
		labels = os.listdir(audio_path)
		avg_samples = []
		for label in [x for x in labels if x != ".DS_Store"]:
			ch_path = os.path.join(audio_path, label, "ch4")
			num_items = len(os.listdir(ch_path))
			paths = [os.path.join(ch_path, file) for file in os.listdir(ch_path)]
			num_samples = int(num_items * PERCENTAGE)
			avg_samples.append(num_samples)
			samples = random.sample(paths, num_samples)
			print("LABEL:   [", label, "]")
			print("SAMPLES: [", num_samples, "]")
			print("PRESS:\n\t[Enter] To Continue\n\t[Q] to quit\n\t[ANY KEY] to mark sample as incorrect\n\t")
			for sample in samples:
				print("\t", sample)
				command = ["afplay", sample]
				subprocess.run(command)
				user_input = input()
				if len(user_input) != 0:
					if user_input.lower() == 'q':
						exit(0)
					incorrect.append(sample)
					print("\t\t'{}' marked as incorrect".format(sample))
		if (len(incorrect) > 0):
			print("Number of incorrectly labeled items: {}".format(len(incorrect)))
			print("Number of samples per label: {}".format(sum(avg_samples) / len(avg_samples)))
			for example in incorrect:
				print("\t", example)
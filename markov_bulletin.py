import urllib
import re
import random
import os.path

# Global character sets
sentence_endings = '.!?'
token_symbols = '.!\?",;:-'

# Test function for a ditc/dict/dict/num
def print_trigram_counts(trigram_counts):
	for one in trigram_counts.iterkeys():
		for two in trigram_counts[one].iterkeys():
			for three in trigram_counts[one][two].iterkeys():
				print one, two, three, trigram_counts[one][two][three]

# Use n-gram model (dictionary of weights) and word history to get a random next word

def next_token_unigram(unigram_weights):
	r = random.random()
	for one in unigram_weights.iterkeys():
		r -= unigram_weights[one]
		if r < 0:
			return one

def next_token_bigram(bigram_weights, last):
	r = random.random()
	for two in bigram_weights[last].iterkeys():
		r -= bigram_weights[last][two]
		if r < 0:
			return two

def next_token_trigram(trigram_weights, last, lastlast):
	r = random.random()
	for three in trigram_weights[lastlast][last].iterkeys():
		r -= trigram_weights[lastlast][last][three]
		if r < 0:
			return three

def next_token_ngram(n, ngram_weights, history):
	# History must be ordered as normal word order ex. (lastlastlast, lastlast, last)
	r = random.random()
	dictionary = ngram_weights
	for i in range(n-1):
		dictionary = ngram_weights[history[i]]
	for key in dictinoary.iterkeys():
		r -= dictionary[key]
		if r < 0:
			return key

# Use token n-gram next-word-generator to put together a sentence.

random_back_off = 0.01

def generate_sentence_unigram(unigram_weights):
	sentence = []
	while True:
		next_token = next_token_unigram(unigram_weights)
		sentence.append(next_token)
		if next_token in sentence_endings:
			break
	return sentence

def generate_sentence_bigram(unigram_weights, bigram_weights):
	sentence = ['.']
	while True:
		last = sentence[-1]
		if last in bigram_weights and not random.random() < random_back_off:
			next_token = next_token_bigram(bigram_weights, last)
		else: # Back off
			next_token = next_token_unigram(unigram_weights)
		sentence.append(next_token)
		if next_token in sentence_endings:
			break
	sentence = sentence[1:]
	return sentence

def generate_sentence_trigram(unigram_weights, bigram_weights, trigram_weights):
	sentence = ['.', '.']
	while True:
		last = sentence[-1]
		lastlast = sentence[-2]
		if (
			lastlast in trigram_weights and last in trigram_weights[lastlast] and
			not random.random() < random_back_off
			):
			next_token = next_token_trigram(trigram_weights, last, lastlast)
		elif last in bigram_weights and not random.random() < random_back_off: # Back off
			next_token = next_token_bigram(bigram_weights, last)
		else: # Back off
			next_token = next_token_unigram(unigram_weights)
		sentence.append(next_token)
		if next_token in sentence_endings:
			break
	sentence = sentence[2:]
	return sentence

def generate_sentence_trigram_modified(unigram_weights, bigram_weights, trigram_weights, history = ('.', '.')):
	sentence = [history[0], history[1]]
	average_in_quotes_length = 7.87
	in_quotes = False
	while True:
		last = sentence[-1]
		lastlast = sentence[-2]
		if in_quotes and last not in token_symbols and random.random() < 1 / average_in_quotes_length:
			next_token = '"'
			in_quotes = False
		else:
			if (
				lastlast in trigram_weights and last in trigram_weights[lastlast] and
				not random.random() < random_back_off
				):
				next_token = next_token_trigram(trigram_weights, last, lastlast)
			elif last in bigram_weights and not random.random() < random_back_off: # Back off
				next_token = next_token_bigram(bigram_weights, last)
			else: # Back off
				next_token = next_token_unigram(unigram_weights)
			if next_token is '"':
				in_quotes = not in_quotes
		if next_token in token_symbols and last in token_symbols and last != '"':
			continue # Don't allow two items of punctuation in a row.
		sentence.append(next_token)
		if next_token in sentence_endings:
			if in_quotes:
				sentence.append('"')
				in_quotes = False
			break
	sentence = sentence[2:]
	return sentence

# Join tokens into a sentence with spaces as appropriate.

def get_sentence_string(unigram_weights, bigram_weights, trigram_weights, history):
	tokens = generate_sentence_trigram_modified(unigram_weights, bigram_weights, trigram_weights, history)
	sentence = ''
	in_quotes = False
	for t in tokens:
		if sentence == '':
			sentence += t
			continue
		last = sentence[-1]
		space = True
		if last == '"' and in_quotes:
			space = False
		if t == '"':
			if in_quotes:
				space = False
				in_quotes = False
			else:
				in_quotes = True
		elif t in token_symbols:
			space = False
		elif (
				last == ':' and len(sentence) > 1 and
				ord(sentence[-2]) > 47 and ord(sentence[-2]) <= 57
			):
			space = False
		elif last == '-':
			space = False
		if space:
			sentence += ' '
		sentence += t
	return sentence

# Filtering

def get_good_sentence(unigram_weights, bigram_weights, trigram_weights, history):
	min_length = 3 # Min characters for a sentence.
	chance_capitalized = 0.65 # Chance of capitalizing a sentence.
	s = ''
	while len(s) < min_length:
		s = get_sentence_string(unigram_weights, bigram_weights, trigram_weights, history)
	if random.random() < chance_capitalized:
		s = s[0].upper() + s[1:]
	return s

# Tokenization

def tokenize(data):
	# A token is:
		# an alphanumeric word, including apostrophes, excluding hyphens
		# a piece of punctuation (see token_symbols)
	token_splitter = re.compile("([" + token_symbols + "])|[^a-zA-Z0-9'" + token_symbols + "]+")
	tokens = re.split(token_splitter, data)
	tokens = [t for t in tokens if t != '' and t != None]
	return tokens

# Build trigram model

def trigram_model(tokens):
	# Trigram model - get raw counts
		# trigram_counts is dict of dict of dict of num
		# counts_one is dict of dict of num
		# counts_two is dict of num
		# counts_three is num
	trigram_counts = {}
	for i in range(2, len(tokens)):
		# Call the token a proper noun if first char is uppercase letter,
			# rest of word is lowercase, token is not first in data and
			# token is not after a token whose first character is not a letter.
		is_proper = [
			tokens[i - j][0].isupper() and tokens[i - j][1:].islower() and
				i - j > 0 and tokens[i - j - 1][0].isalpha()
			for j in range(3)]
		trigram = [
			tokens[i - j] if is_proper[j] else tokens[i - j].lower()
			for j in range(3)]
		is_proper.reverse()
		trigram.reverse()
		one, two, three = trigram[0], trigram[1], trigram[2]
		one_low, two_low, three_low = one.lower(), two.lower(), three.lower()
		if not one in trigram_counts:
			if one_low in trigram_counts:
				trigram_counts[one] = trigram_counts[one_low]
				del trigram_counts[one_low]
			else:
				trigram_counts[one] = {}
		counts_one = trigram_counts[one]
		if not two in counts_one:
			if two_low in counts_one:
				counts_one[two] = counts_one[two_low]
				del counts_one[two_low]
			else:
				counts_one[two] = {}
		counts_two = counts_one[two]
		if not three in counts_two:
			if three_low in counts_two:
				counts_two[three] = counts_two[three_low]
				del counts_two[three_low]
			else:
				counts_two[three] = 0
		counts_two[three] += 1
	# Trigram model - normalize
		# Values in any dictionary sum to one
		# unigram_weights is *almost* a dict probabilities of tokens,
			# but in reality is a dict of probabilities of the starts of trigrams
	unigram_weights = {} # Dict of num
	bigram_weights = {} # Dict of dict of num
	trigram_weights = trigram_counts # Dict of dict of dict of num
	trigram_counts_sum = 0
	for one in trigram_counts.iterkeys():
		counts_one = trigram_counts[one]
		bigram_weights[one] = {} # Dict of num
		counts_one_sum = 0
		for two in counts_one.iterkeys():
			counts_two = trigram_counts[one][two] # Dict of dict
			counts_two_sum = 0
			for three in counts_two.iterkeys():
				counts_two_sum += counts_two[three]
			# Normalize counts''
			for three in counts_two.iterkeys():
				counts_two[three] = float(counts_two[three]) / counts_two_sum
			bigram_weights[one][two] = counts_two_sum
			counts_one_sum += counts_two_sum
		# Normalize counts'
		for two in counts_one.iterkeys():
			bigram_weights[one][two] = float(bigram_weights[one][two]) / counts_one_sum
		unigram_weights[one] = counts_one_sum
		trigram_counts_sum += counts_one_sum
	# Normalize counts
	for one in trigram_counts.iterkeys():
		unigram_weights[one] = float(unigram_weights[one]) / trigram_counts_sum
	return unigram_weights, bigram_weights, trigram_weights

# Generate

def generate(model, new_paragraph_chance):
	unigram_weights, bigram_weights, trigram_weights = model
	p = ''
	r = 1
	history = ('#', '.')
	while not r < new_paragraph_chance:
		s = get_good_sentence(unigram_weights, bigram_weights, trigram_weights, history) + ' '
		ending = s.split()[-1]
		history = (ending[:-1], ending[-1])
		p += s
		r = random.random()
	p = p[:-1]
	# NNB Caps
	split = p.split()
	split[0] = split[0].upper()
	if len(split) > 1: split[1] = split[1].upper()
	p = ' '.join(split)
	return p

# Main

def main():
	if False:
		# Read input file
		f = open('nnb_data.txt', 'r')
		data = f.read()
		f.close()

		tokens = tokenize(data)
		model = trigram_model(tokens)
		p = generate(model, 0.36)
		print p, '\n'

	categories = ['Today', 'GENERAL', 'WANTED', 'FOR SALE', 'LOST & FOUND',
		'HOUSING', 'RIDE SHARE', 'NOTICES']
	for c in categories:
		dir_path = 'parsed/' + c + '/'
		data = ''
		for file_name in os.listdir(dir_path):
			f = open(dir_path + file_name, 'r')
			s = f.read()
			f.close()
			data += s + '\n'
		if len(data) == 0:
			continue
		
		# Add huge nnb data set to every model
		f = open('nnb_data.txt', 'r')
		data += f.read()
		f.close()

		model = trigram_model(tokenize(data))
		output = open('generated/' + c + '.txt', 'w')
		for i in range(10):
			print >> output, generate(model, 0.36)
		output.close()

if __name__ == "__main__":
	main()
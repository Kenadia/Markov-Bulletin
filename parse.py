import re
import os.path

def blank(match_obj):
	return ''

def main():
	categories = ['Today', 'GENERAL', 'WANTED', 'FOR SALE', 'LOST & FOUND',
		'HOUSING', 'RIDE SHARE', 'NOTICES']
	for c in categories:
		dir_path = 'download/' + c + '/'
		for file_name in os.listdir(dir_path):
			print file_name
			f = open(dir_path + file_name, 'r')
			s = f.read()
			f.close()
			output = open('parsed/' + c + '/' + file_name, 'w')
			r = re.compile(r'<.*?>|&.*?;')
			parsed = re.sub(r, blank, s)
			print >> output, parsed
			output.close()

if __name__ == '__main__':
	main()
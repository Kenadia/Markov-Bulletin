import urllib
import re

# A date tuple contains year, month, day denoted as follows:
	# Year 2000 is 2000;
	# January is 0;
	# First of month is 0.
# Sunday is 0.
# Reference date is Sunday, December 31, 1899.

days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

def days_in_year(year):
	return 365 if (year & 3) else 366

def days_in_month(year, month):
	if month > 6:
		return 30 + (month & 1)
	elif month == 1:
		return 28 if (year & 3) else 29
	else:
		return 31 - (month & 1)

def day_of_week(date):
	year, month, day = date[0], date[1], date[2]
	days_since_year_start = day + sum([days_in_month(year, i) for i in range(month)])
	days_since_reference = days_since_year_start + sum([days_in_year(i) for i in range(1900, year)])
	return days_since_reference % 7

# Pass a date as normal (human) date notation, return date tuple.
def date(year, month, day):
	return (year, month - 1, day - 1)

# year(), mont(), day() give normal (human) date notation

def year(date):
	return date[0]

def month(date):
	return date[1] + 1

def day(date):
	return date[2] + 1

def to_string(date):
	return str(year(date)) + '_' + str(month(date)) + '_' + str(day(date))

def x_days_from(date, x):
	year, month, day = date[0], date[1], date[2]
	day += x
	while day >= days_in_month(year, month):
		day -= days_in_month(year, month)
		month += 1
		if month >= 12:
			month = 0
			year += 1
	return (year, month, day)

def date_is_before(date1, date2):
	if date1[0] < date2[0]:
		return True
	elif date1[0] == date2[0]:
		if date1[1] < date2[1]:
			return True
		elif date1[1] == date2[1]:
			if date1[2] < date2[2]:
				return True
	return False

def title_search(title):
	return re.compile(r'<BR><B><U>' + title + r'</U></B><BR>(.*?)</td></tr></table>', re.DOTALL)

def main():
	# Calculate day of the week on Matt's 21st birthday.
	# print days_of_week[day_of_week(x_days_from(date(1993, 2, 22), sum([days_in_year(i) for i in range(1993, 2014)])))]
	#start_11_12 = date(2011, 9, 12)
	#end_11_12 = date(2012, 6, 1)
	start_11_12 = date(2012, 1, 10)
	end_11_12 = date(2012, 1, 30)
	d = start_11_12
	week_day = day_of_week(d)
	while date_is_before(d, x_days_from(end_11_12, 1)):
		# Do something with d, week_day
		if week_day != 0 and week_day != 6:
			request = urllib.urlencode({'year' : year(d), 'month' : month(d), 'day' : day(d)})
			f = urllib.urlopen("https://apps.carleton.edu/campact/nnb/local/show.php3", request)
			s = f.read()
			f.close()
			# Event listings of the day
			match_obj = re.search(title_search("Today"), s)
			if match_obj != None:
				output = open('download/Today/' + to_string(d) + '.txt', 'w')
				print >> output, match_obj.group(1)
				output.close()
			# General, Wanted, For Sale, Lost and Found, Housing, Ride Share, Notices
			categories = ['GENERAL', 'WANTED', 'FOR SALE', 'LOST & FOUND',
				'HOUSING', 'RIDE SHARE', 'NOTICES']
			if (week_day & 1):
				for category in categories:
					match_obj = re.search(title_search(category), s)

					if match_obj != None:
						output = open('download/' + category + '/' + to_string(d) + '.txt', 'w')
						print >> output, match_obj.group(1)
						output.close()
		# End
		d = x_days_from(d, 1)
		week_day = (week_day + 1) % 7

if __name__ == '__main__':
	main()


def print_table(lines, separate_head=True):
	"""Prints a formatted table given a 2 dimensional array"""
	#Count the column width
	widths = []
	for line in lines:
			for i,size in enumerate([len(x) for x in line]):
					while i >= len(widths):
							widths.append(0)
					if size > widths[i]:
							widths[i] = size
	   
	#Generate the format string to pad the columns
	print_string = ""
	for i,width in enumerate(widths):
			print_string += "{" + str(i) + ":" + str(width) + "} | "
	if (len(print_string) == 0):
			return
	print_string = print_string[:-3]
	   
	#Print the actual data
	for i,line in enumerate(lines):
			print(print_string.format(*line))
			if (i == 0 and separate_head):
					print("-"*(sum(widths)+3*(len(widths)-1)))
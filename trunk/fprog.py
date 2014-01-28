from __future__ import generators

def sortF (seq):
	seq.sort()
	return seq
	
def group (isAssociated, seq, collapse=None):
	try:
		i = iter(seq)
	except:
		i = seq
	eof = False
	bof = True
	members = []
	while not eof:
		try:
			b = i.next()
			if bof or isAssociated (members, b):
				members.append (b)
				bof = False
			else:
				if collapse is not None:
					yield collapse (members)
				else:
					yield members
				members = [b]
			a = b
		except StopIteration:
			if not bof:
				if collapse is not None:
					yield collapse (members)
				else:
					yield members
			eof = True

if __name__ == '__main__':
	import sys
	import string
	def bothupper (a, b):
		result = a[0] in string.uppercase and b in string.uppercase
		return result
	sequence = sys.argv[1]
	print list(group(bothupper, sequence))
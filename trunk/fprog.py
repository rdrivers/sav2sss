# Copyright (c) 2014 Computable Functions Limited, UK

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

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
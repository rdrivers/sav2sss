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

# Python package to create XML rendition of Quantum data from the binaries

import exceptions
import struct
import datetime

def forceEncoding (text, encoding='ascii'):
	if type (text) != unicode:
		return str (text)
	try:
		return text.encode(encoding)
	except UnicodeError:
		lchars = []
		for char in text:
			try:
				lchars.append(char.encode(encoding))
			except UnicodeError, e:
				lchars.append("&#%d;" % ord(char))				
		return ''.join(lchars)

def setBig():
	global big, wordFormat, longFormat, signedLongFormat, floatFormat, endianity, endianityChar
	wordFormat = '>H'
	longFormat = '>L'
	signedLongFormat = '>l'
	floatFormat = '>d'
	big = True
	endianity = "big"
	endianityChar = '>'

def setLittle():
	global big, wordFormat, longFormat, signedLongFormat, floatFormat, endianity, endianityChar
	wordFormat = '<H'
	longFormat = '<L'
	signedLongFormat = '<l'
	floatFormat = '<d'
	big = False
	endianity = "little"
	endianityChar = '<'
setLittle ()

def adjustedValue (v):
	vOver11 = v/11.0
	if float(int(vOver11)) == vOver11:
		return vOver11
	else:
		return v
# Extraordinary fact that floats are scaled up by a factor of 11 (sometimes) !!!!

SPSSEpochalDelta = datetime.datetime.utcfromtimestamp (0.0) - datetime.datetime (1582, 10, 14)
SPSSEpochalDeltaSeconds = SPSSEpochalDelta.days*24*3600

def hexInterpretation (data):
	count = len(data)
	return (" %2X"*count) % struct.unpack('%dB' % count, data)
	# Read in reverse (declining address = declining significance)
	# to interpret as floating point at e.g.
	# http://babbage.cs.qc.edu/IEEE-754/IEEE-754hex64.html
	
def unpackFloat (data):
	value = struct.unpack(floatFormat, data) [0]
	#print value, hexInterpretation (data)
	return value

floatFormatCode = 5
dateFormatCode = 20
timeFormatCode = 21
datetimeFormatCode = 22
formatCodeMap = {
	1: "A",
	2: "AHEX",
	3: "COMMA",
	4: "DOLLAR",
	5: "F",
	6: "IB",
	7: "PIBHEX",
	8: "P",
	9: "PIB",
	10: "PK",
	11: "RB",
	12: "RBHEX",
	15: "Z",
	16: "N",
	17: "E",
	20: "DATE",
	21: "TIME",
	22: "DATETIME",
	23: "ADATE",
	24: "JDATE",
	25: "DTIME",
	26: "WKDAY",
	27: "MONTH",
	28: "MOYR",
	29: "QYR",
	30: "WKYR",
	31: "PCT",
	32: "DOT",
	33: "CCA",
	34: "CCB",
	35: "CCC",
	36: "CCD",
	37: "CCE",
	38: "EDATE",
	39: "SDATE"
}

def blankNone (t):
	if t is not None: return str (t)
	return ""
	
def alternativeText (t, alternative):
	if t == alternative: value = t
	else:
		value = "%s (%s)" % (t, alternative)
	return unicode (value).encode ("cp1252", "replace")

class SAVError (exceptions.Exception): pass

def requireByes (data, offset, length):
	if offset + length > len (data):
		raise SAVError, "Unexpected end of file, looking for %d bytes at offset %d" %\
			(length, offset)
	#return data [offset:offset+length]
			
class SPSSOutputFormat:
	def __init__ (self, bytes):
		self.dp = bytes [0]
		self.width = bytes [1]
		self.format_type = bytes [2]
		if not formatCodeMap.has_key (self.format_type):
			# raise SAVError, "Unknown format type %s" % self.format_type
			self.format_type_code = "D/k (%s)" % self.format_type
			# print "Unknown format type %s" % str (self)
		else:
			self.format_type_code = formatCodeMap [self.format_type]
	def __str__ (self):
		# format_type_code = formatCodeMap [self.format_type]
		return "Format #%s %s.%s" % (self.format_type_code, self.width, self.dp)

class SPSSLabelList:
	def __init__ (self, labels, variablesApplicable, nonInteger):
		self.labels = labels
		self.variablesApplicable = variablesApplicable
		self.nonInteger = nonInteger
				
class SAVVariable:
	def __init__ (self, dataset, data, offset):
		def nextInt32 (signed=False):
			if signed:
				format = signedLongFormat
			else:
				format = longFormat
			value = struct.unpack (format,
				data [offset + self.SAVSize: offset + self.SAVSize + 4])[0]
			self.SAVSize += 4
			return value
		def nextN (n):
			value = data [offset + self.SAVSize: offset + self.SAVSize + n]
			self.SAVSize += n
			return value
		def nextNBytes (n=1):
			value = struct.unpack ('%s%db' % (endianityChar, n),
				data [offset + self.SAVSize: offset + self.SAVSize + n])
			self.SAVSize += n
			return value
		def nextNFloat (n=1, adjust=False):
			# print "nextNFloat", n, adjust, self.SAVSize, offset
			values = [unpackFloat (data[offset + i:offset + i + 8])\
				for i in xrange (self.SAVSize, self.SAVSize + 8*n, 8)]
			#values = struct.unpack ('%s%dd' % (endianityChar, n),
			#		data [offset + self.SAVSize: offset + self.SAVSize + 8*n])
			self.SAVSize += 8*n
			if adjust:
				return [adjustedValue (v) for v in values]
			else:
				return values
		def alignTo4 ():
			self.SAVSize = (offset + self.SAVSize + 3)/4*4 - offset
			
		self.dataset = dataset
		self.SAVSize = 0
		self.type_ = nextInt32 (True)
		self.has_var_label = nextInt32 ()
		self.n_missing_values = nextInt32 (True)
		self.print_ = SPSSOutputFormat (nextNBytes (4))
		self.write_ = SPSSOutputFormat (nextNBytes (4))
		self.name = nextN (8).strip ()	# Won't strip correctly except for ASCII variants
		# print "New variable name", self.name
		# has to be stripped now to match with long-name entries.
		if self.has_var_label:
			self.label_len = nextInt32 ()
			self.label = nextN (self.label_len)
			alignTo4 ()
		else:
			self.label = None
		if abs (self.n_missing_values) > 0:
			self.missing_values = nextNFloat (abs (self.n_missing_values), False)
			#self.missing_values = nextNFloat (abs (self.n_missing_values), True)
		self.isDummy = False
		self.stringLength = self.type_
		self.extendedStringLength = None
		self.longName = self.name
		self.labelList = None
		self.measure = None
		self.width = None
		self.alignment = None
		self.fullPosition = None		
		
	def isValidMissingValue (self, value):
		if self.n_missing_values == 0: return False
		#print self.name, self.n_missing_values, self.missing_values, value
		if self.n_missing_values > 0:
			return value in self.missing_values
		if self.n_missing_values == -2:
			return (value >= self.missing_values [0] and
			       value <= self.missing_values [1])
		if self.n_missing_values == -3:
			return (value >= self.missing_values [0] and
			       value <= self.missing_values [1]) or\
			       value == self.missing_values [2]
			       
	def sensibleLabelCount (self):
		sensibleCount = 0
		if self.labelList is not None:
			labelList = self.dataset.labelLists [self.labelList]
			if not labelList.nonInteger:
				for code in labelList.labels.keys ():
					if not self.isValidMissingValue (code) and code >= 0:
					   sensibleCount += 1
		return sensibleCount
		
	def __str__ (self):
		if self.n_missing_values > 0:
			missingValuesText = " " + str(self.missing_values)
		else:
			missingValuesText = ""
		repn = """Variable %s: Type=%s; Label?=%s; Missing=%s%s; Print='%s'; Write='%s' List=%s Dummy=%s Length=%s Width=%s Measure=%s Align=%s""" %\
			(alternativeText (self.name, self.longName), 
			 self.type_, self.has_var_label, self.n_missing_values, missingValuesText,
			 self.print_, self.write_, blankNone (self.labelList), self.isDummy,
			 blankNone (self.extendedStringLength),
			 self.width, self.measure, self.alignment)
		if self.has_var_label: repn += "; Label=%s" % (forceEncoding (self.label))
		return repn
		
class SAVDataset:

	def __init__ (self, SAVFilename, sensibleStringLengths=True):
		self.lowest = 0
		self.highest = 0
		self.floating_point_rep = 1
		self.character_code = 3
		self.encoding = "ISO-8859-1"
		self.sysmis = 0
		self.n_lines = 0
	
		def getRecordType (required=None):
			return_type = None
			# print "getRecordType", self.offset, len (self.binData)
			if self.offset + 4 <= len (self.binData):
				record_type = struct.unpack(longFormat,
					self.binData[self.offset: self.offset+4])[0]
				if record_type == 7:
					self.offset += 4
					sub_type = struct.unpack(longFormat,
						self.binData[self.offset:self.offset+4])[0]
					return_type = "%d.%d" % (record_type, sub_type)
				else:
					return_type = "%d" % record_type
				if required is not None and return_type != required:
					raise SAVError, "Record type '%s' required at self.offset %d (X%x)" %\
					(required, self.offset, self.offset)
				self.offset += 4
				# print "Returning type: %s" % return_type
				return return_type
			if required is not None:
				raise SAVError, "Unexpected EOF looking for %s at self.offset %d (X%x)" %\
					(required, self.offset, self.offset)
					
		binFile = open(SAVFilename, 'rb')
		self.binData = binFile.read()
		binFile.close ()
		self.sensibleStringLengths = sensibleStringLengths

		rec_type = self.binData[:4]
		if rec_type != "$FL2": raise SAVError,\
			"Unknown file header record type %s" %  rec_type
		self.prod_name = self.binData[4:64]
		if struct.unpack('>L', self.binData [64:68])[0] in (2, 3):
		      setBig()
		elif struct.unpack('<L', self.binData[64:68])[0] in (2, 3):
		      setLittle()
		else:
		      raise QBError, "--Can't determine layout code and end-ianity"
		self.layout_code = struct.unpack(longFormat, self.binData[64:68])[0]
		self.nominal_case_size = struct.unpack(longFormat, self.binData[68:72])[0]
		self.compressed = struct.unpack(longFormat, self.binData[72:76])[0]
		self.weight_index = struct.unpack(longFormat, self.binData[76:80])[0]
		self.ncases = struct.unpack(longFormat, self.binData[80:84])[0]
		bias = struct.unpack(floatFormat, self.binData[84:92])[0]
		if float(int(bias)) != bias:
			raise SAVError, "Non-integer bias value %f" % bias
		self.bias = int (bias)
		self.creation_date = self.binData [92:101]
		self.creation_time = self.binData [101:109]
		self.file_label = self.binData [109:173]
		self.offset = 176	# End of header

		self.variables = []
		self.variableMap = {}
		self.fullVariableMap = {}
		self.totalVariables = 0
		variableIndex = 0
		while self.offset < len (self.binData) - 3:
			rec_type = getRecordType ()
			if rec_type != '2': break
			newVariable = SAVVariable (self, self.binData, self.offset)
			self.offset += newVariable.SAVSize
			dummyVariableCount = 0
			while self.offset < len (self.binData) - 7 and\
				struct.unpack(longFormat, self.binData[self.offset:self.offset+4])[0] == 2 and\
				struct.unpack(signedLongFormat, self.binData[self.offset+4:self.offset+8])[0]	 < 0:
				self.offset += 4
				dummyVariable = SAVVariable (self, self.binData, self.offset)
				dummyVariableCount += 1
				self.offset += dummyVariable.SAVSize
			newVariable.dummyVariables = dummyVariableCount
			newVariable.fullPosition = self.totalVariables
			self.variableMap [newVariable.name] = len (self.variables)
			self.fullVariableMap [self.totalVariables] = len (self.variables)
			self.variables.append (newVariable)
			self.totalVariables += newVariable.dummyVariables + 1
			# print "Variable", self.totalVariables, newVariable.name, newVariable.dummyVariables
		
		self.labelLists = []
		while rec_type == '3':
			labelList = {}
			label_count = struct.unpack(longFormat, self.binData[self.offset:self.offset+4])[0]
			self.offset += 4
			nonInteger = False
			for i in xrange (label_count):
				value = struct.unpack(floatFormat, self.binData [self.offset: self.offset + 8])[0]
				self.offset += 8
				label_length = struct.unpack ('%sb' % endianityChar, self.binData [self.offset: self.offset + 1]) [0]
				label = self.binData [self.offset+1: self.offset+1+label_length]
				if float (int (value)) != value:
					# raise SAVError, "Non-integer labelled value; %s: %s" % (value, label)
					print "--Non-integer labelled value; %s: %s" % (value, label)
					nonInteger = True
				self.offset += (label_length+1+7)/8*8
				# if value > 0: labelList [int (value)] = label	# Require +ve integer codes (for triple-S)
				if nonInteger:
					labelList [value] = label
				else:
					if labelList.has_key (int (value)):
						print "--Duplicated rounded code value: %s (%d) for label '%s'" %\
							(value, int (value), label)
					labelList [int (value)] = label	# 0 codes supported for triple-S level 2+
			getRecordType ("4")
			var_count = struct.unpack(longFormat, self.binData[self.offset:self.offset+4])[0]
			self.offset += 4
			format = "%s%dL" % (endianityChar, var_count)
			applicableVariables = struct.unpack (format, self.binData [self.offset:self.offset+4*var_count])
			self.offset += 4*var_count
			for variableIndex in applicableVariables:
				variable = self.variables [self.fullVariableMap [variableIndex-1]]
				variable.labelList = len (self.labelLists)
			self.labelLists.append (SPSSLabelList (labelList, applicableVariables, nonInteger))
			rec_type = getRecordType ()
			
		while rec_type is not None:
			if rec_type == "6":	# Document record
				self.n_lines = struct.unpack(longFormat, self.binData[self.offset:self.offset+4])[0]
				self.offset  += 4
				self.lines = [self.binData[self.offset:self.offset+80]
					for self.offset in xrange (self.offset, self.offset+80*(self.n_lines+1), 80)]
				# print "Document record", self.n_lines, self.lines
			
			elif rec_type == "7.3":
				self.floating_point_rep = struct.unpack(longFormat, self.binData[self.offset+24:self.offset+28])[0]
				if self.floating_point_rep != 1: raise SAVError, "Unsupported floating point format %s" %\
					self.floating_point_rep
				self.character_code = struct.unpack(longFormat, self.binData[self.offset+36:self.offset+40])[0]
				if self.character_code == 2:
					# self.encoding = "ascii" some files lie about being 7-bit
					self.encoding = "ISO-8859-1"
				elif self.character_code == 3:
					self.encoding = "ISO-8859-1"
				elif self.character_code < 5:
					raise SAVError, "Unsupported character set code %d" % self.character_code
				else:
					self.encoding = "CP%d" % self.character_code
				self.offset += 10 * 4	# Machine integer info				
			
			elif rec_type == "7.4":
				self.sysmis = struct.unpack (floatFormat,
					self.binData[self.offset+8:self.offset+16]) [0]
				self.highest = struct.unpack (floatFormat,
					self.binData[self.offset+16:self.offset+24]) [0]
				self.lowest = struct.unpack (floatFormat,
					self.binData[self.offset+24:self.offset+32]) [0]
				self.offset += 32
			
			elif rec_type == "7.11":
				self.offset += 4
				self.vdp_count = struct.unpack(longFormat,
					self.binData[self.offset:self.offset+4])[0]
				self.offset += 4
				vdpItemCount = self.vdp_count / len (self.variables)
				variableIndex = 0
				for vdpIndex in xrange (0, self.vdp_count, vdpItemCount):
					measure = struct.unpack (longFormat,
						self.binData[self.offset:self.offset+4]) [0]
					self.offset += 4
					width = struct.unpack (longFormat,
						self.binData[self.offset:self.offset+4]) [0]
					self.offset += 4
					if vdpItemCount > 2:
						alignment = struct.unpack (longFormat,
							self.binData[self.offset:self.offset+4]) [0]
						self.offset += 4
					else:
						alignment = None
					self.variables [variableIndex].measure = measure
					self.variables [variableIndex].width = width
					self.variables [variableIndex].alignment = alignment					
					variableIndex += 1
			
			elif rec_type == "7.13":
				self.offset += 4
				bytes = struct.unpack (longFormat,
					self.binData[self.offset:self.offset+4]) [0]
				self.offset += 4
				for name, longName in (pair.split ("=") for pair in
					self.binData [self.offset:self.offset+bytes].split ("\t")):
					self.variables [self.variableMap [name]].longName = longName
				self.offset += bytes
			
			elif rec_type == "7.14":
				self.offset += 4
				bytes = struct.unpack (longFormat,
					self.binData[self.offset:self.offset+4]) [0]
				self.offset += 4
				for name, stringLengthText in (pair.split ("=") for pair in
					self.binData [self.offset:self.offset+bytes].split ("\t") if len(pair) > 1):
					#print "..Extended string length: %s=%s" % (name, stringLengthText)
					if self.variableMap.has_key (name):
						variableIndex = self.variableMap [name]
						variable = self.variables [variableIndex]
						potentialStringLength =	int (stringLengthText.strip ("\0"))
						potentialSegmentCount = (potentialStringLength + 251) / 252
						variable.segmentCount = 0
						variable.extendedStringLength = variable.type_
						for i in xrange (1, potentialSegmentCount):
							potentialDummyVariable = self.variables [variableIndex + i]
							if potentialDummyVariable.label == variable.label:
								potentialDummyVariable.isDummy = True
								variable.extendedStringLength += potentialDummyVariable.type_
								variable.segmentCount += 1
							else:
								print "--Variable %s with extended string length %d has only %d segment(s)" %\
									(variable.name, potentialStringLength, i)
								break
						#if variable.stringLength != variable.type_ + variable.dummyVariables*8:
						#	print "--Variable %s has type value %d, %d dummy variables and string length %d" %\
						#		(variable.name, variable.type_, variable.dummyVariables, variable.stringLength)
					else:
						print "--Extended string length specified for undefined variable %s; ignored" % name
						#raise SAVError, "Extended string length specified for undefined variable %s" % name
				self.offset += bytes
				
			elif rec_type.startswith ("7"):
				size = struct.unpack (longFormat,
					self.binData[self.offset:self.offset+4]) [0]
				count = struct.unpack (longFormat,
					self.binData[self.offset+4:self.offset+8]) [0]
				self.offset += 8 + size * count
				
			elif rec_type == "999":
				self.offset += 4
				break
				
			else:
				raise SAVError, "Unknown record type %s at offset %d (X%x)" %\
					(rec_type, self.offset - 4, self.offset - 4)

			rec_type = getRecordType ()
		
		# Convert texts to Unicode using encoding declared in file
		
		self.prod_name = self.convertText (self.prod_name)
		self.creation_date = self.convertText (self.creation_date)
		self.creation_time = self.convertText (self.creation_time)
		self.prod_name = self.convertText (self.prod_name)
		

		for i, variable in enumerate (self.variables):
			variable.name = self.convertText (variable.name)
			variable.label = self.convertText (variable.label)
			variable.longName = self.convertText (variable.longName)

		# Now we know the longNames, let's use them as the variable names
		
		# Variables now may have two entries in the variable map
		for i, variable in enumerate (self.variables):
			if variable.longName and variable.longName != variable.name:
				if self.variableMap.has_key (variable.longName):
				  raise SAVError, "Long name '%s' for '%s' conflicts with existing short name" %\
				  	(variable.longName, variable.name)
				else:
					variable.name = variable.longName
					self.variableMap [variable.name] = variable
			
		for list_ in self.labelLists:
			for value, label in list_.labels.items ():
				list_.labels [value] = self.convertText (label)

		self.dataOffset = self.offset
		self.dataSize = len (self.binData) - self.dataOffset
		print "..Data section starts at offset %d (X%x), size %d byte(s)" %\
			(self.offset, self.offset, self.dataSize)

		self.sizeVariables ()
		
		for i, variable in enumerate (self.variables):
			if variable.labelList is not None:
				labelDictionary = self.labelLists [variable.labelList].labels
				for key in variable.valueDistribution:
					if not labelDictionary.has_key (key):
						#print "--No label for value %s of variable %s, list size: %d" %\
						#	(key, variable.name, len (labelDictionary))
						variable.partialCoding = True
						break
				else:
					variable.partialCoding = False
	
	def getCaseStream (self, errorTreatment="ignore"):
		errorTreatment = errorTreatment.lower ()
		if self.compressed == 0:
			raise SAVError, "Uncompressed data files not supported"
		else:	
			variablePosition = 0
			case = 0
			itemStream = self._getDataItemStream ()
		dataItem = itemStream.next ()
		variableValues = [None]* len (self.variables)
		try:
			while True:	
				variable = self.variables [variablePosition]
				#print variable.name, variable.type_, type (dataItem)
				if variable.type_ == 0:
					if type (dataItem) in (unicode, str):
						#value = adjustedValue (struct.unpack (floatFormat, dataItem) [0])
						value = struct.unpack (floatFormat, dataItem) [0]
						#print "%s: %016x%016x %f" %\
						#	(variable.name, struct.unpack (longFormat, dataItem[0:4]) [0],
						#	 struct.unpack (longFormat, dataItem[4:]) [0],
						#	 value)
						try:
							formatType = variable.write_.format_type
							if formatType in\
								(dateFormatCode, timeFormatCode, datetimeFormatCode):
								value = datetime.datetime.fromtimestamp (value - SPSSEpochalDeltaSeconds).isoformat ()
								if   formatType == dateFormatCode: value = value [0:10]
								elif formatType == timeFormatCode: value = value [11:19]
						except exceptions.Exception, e:
							t = self.et (value)
							if errorTreatment == "abort":
								raise SAVError, "Can't interpret time for %s (%s) at case %d" %\
								 	(variable.name, t, case)
							elif errorTreatment == "report":
								print "--Can't interpret time for %s (%s) at case %d" %\
									(variable.name, t, case)
							else:
								pass
					else:
						value = dataItem
						if value is not None:
							if variable.isValidMissingValue (value):
								value = None
							elif variable.labelList is not None:
								try:
									if value < 0 or float (int (value)) != value:
										if errorTreatment == "abort":
										 raise SAVError, "Only missing labelled values may be negative (variable %s, value %s)" %\
										 	(variable.name, value)
										elif errorTreatment == "report":
											print "--Only missing labelled values may be negative (variable %s, value %s) at case %d" %\
												(variable.name, value, case)
										else:
											pass
										value = None
								except exceptions.Exception, e:
									t = self.et (value)
									value = None
									if errorTreatment == "abort":
									 raise SAVError, "Exception interpreting '%s' (%s) at case %d; %s" %\
									 	(variable.name, t, case, e)
									elif errorTreatment == "report":
										print "--Exception interpreting '%s' (%s) at case %d; %s" %\
											(variable.name, t, case, e)
									else:
										pass
				else:
					#print variable.name, " string length ", variable.stringLength
					extensionBlocks = "".join ((itemStream.next ()
						for blockIndex in xrange ((variable.stringLength + 7) / 8 - 1)))
					value = dataItem + extensionBlocks
				variableValues [variablePosition] = value
				variablePosition += 1
				if variablePosition == len (self.variables):
					variablePosition = 0
					case = case + 1
					#for position, value in enumerate (variableValues):
					#	print case, position, self.variables [position].name, value
					#print ",".join ((self.encodeVariableCSVValue (index)
					#	for index in xrange (len (self.variables))
					#		if not self.variables [index].isDummy))
					yield self._combineDummies (variableValues, errorTreatment)
					variableValues = [None]* len (self.variables)
					#print "..Case %d completed" % case
				dataItem = itemStream.next ()
		except StopIteration, e:
			pass
			#print "Data loop ended: %s" % e
		#print "..End of data, case(s) %d" % case
		if variablePosition > 0:
			raise SAVError, "Incomplete case, before variable %s" %\
				(self.variables [variablePosition].name,)
		return
		
	def convertText (self, t, errorTreatment='ignore'):
		if t is not None:
			try:
				return t.decode (self.encoding).rstrip ()
			except exceptions.Exception, e:
				errorText = "Error '%s' converting '%s' to text" %\
					 	(e, t)
				if errorTreatment == "abort":
					raise SAVError, errorText
				elif errorTreatment == "report":
					#print errorText
					pass
				return str (t)
	def et (self, t):
		return self.convertText (t).encode ('ascii', 'replace')
		
	def printMetadata (self, verbose=False):
		print "..Product name is ", self.prod_name
		print "..Layout code is %s, %s-endian" % (self.layout_code, endianity)
		print "..Nominal case size is %s" % self.nominal_case_size
		print "..Compressed: %s" % self.compressed
		print "..Weight index: %s" % self.weight_index
		print "..Number of cases: %s" % self.ncases
		print "..Compression bias: %s" % self.bias
		print "..Creation date: %s" % self.creation_date
		print "..Creation time: %s" % self.creation_time
		print "..File label: %s" % self.file_label
		print "..Floating point format: ", self.floating_point_rep
		print "..Character code: ", self.character_code
		print "..Encoding: ", self.encoding
		print "..System missing value: ", self.sysmis
		print "..Highest value: ", self.highest
		print "..Lowest value: ", self.lowest
		if verbose:
			for i, variable in enumerate (self.variables):
				if not variable.isDummy:\
					print forceEncoding ("Variable %d (%s): %s" %\
						(i, variable.fullPosition+1, variable))
			for i, l in enumerate (self.labelLists):
				print "List: %d" % i, l.labels, l.variablesApplicable# , l.nonInteger
	
	def _getDataItemStream (self):
		def getDataByte (offset):
			byte = struct.unpack ('%sB' % endianityChar,
				self.binData [self.dataOffset + offset: self.dataOffset + offset + 1]) [0]
			#print "Byte @ %d=%s" % (offset, byte)
			return byte
		blockOffset = 0
		while blockOffset + 8 <= self.dataSize:
			#print "Block offset: ", blockOffset
			finalBlockOffset = blockOffset + 8
			for byteIndex in xrange (8):
				byte = getDataByte (blockOffset + byteIndex)
				if byte >= 1 and byte <= 251:
					value = byte - self.bias
					#print "Value %d (%s)" % (value, type (value))
				elif byte == 0:
					#print "Ignore"
					continue
				elif byte == 252:
					#print "EOF"
					continue
				elif byte == 253:
					value = self.binData [
						self.dataOffset + finalBlockOffset:
						self.dataOffset + finalBlockOffset + 8]
					#print "Extension value: %s" % value
					finalBlockOffset += 8
				elif byte == 254:
					value = "        "
					#print "Blank 8"
				elif byte == 255:
					value = None
					#print "Missing"
				else:
					raise SAVError, "Invalid compressed data value: %s" % byte
				yield value
			blockOffset = finalBlockOffset
			
	def _combineDummies (self, variableValues, errorTreatment):
		nonDummies = []
		for index, variable in enumerate (self.variables):
			if not variable.isDummy:
				if variable.isMultiple:
					value = []
					if variable.isSpread:
						for categoryIndex in xrange (variable.count):
							if variableValues [index + categoryIndex] == 0: break
							value.append (variableValues [index + categoryIndex])
					else:
						for categoryIndex in xrange (variable.length):
							if variableValues [index + categoryIndex] == variable.yesCode:
								value.append (categoryIndex + 1)
					nonDummies.append ((index, value))
				elif variable.type_ > 0:
					if variable.extendedStringLength:
						try:
							value = "".join ((value for value in variableValues
								[index:index+variable.segmentCount]))
						except exceptions.Exception, e:
							errorString =\
								"Exception '%s' caused by extended string value for variable '%s' composed of %s" %\
									(e, variable.name, str ([value for value in variableValues
								[index:index+variable.segmentCount]]))
							if errorTreatment == 'report':
								print errorString
								pass
							elif errorTreatment == 'abort':
								raise SAVError, errorString
							else:
								value = variableValues [index]
					else:
						value = variableValues [index]
					nonDummies.append ((index, self.convertText (value, errorTreatment)))
				else:
					nonDummies.append ((index, variableValues [index]))
		return nonDummies		
				
					
	def encodeVariableCSVValue (self, index):
		variable = self.variables [index]
		#print "encodeVariable", index, variable.name, self.variableValues [index]
		if variable.type_ > 0:
			if variable.extendedStringLength:
				value = "".join ((value for value in self.variableValues [index:index+variable.segmentCount]))
			value = self.variableValues [index]
			return self.convertText (value)
		value = self.variableValues [index]
		if value is None: return ""
		if variable.labelList is not None:
			#print "List value", variable.name, variable.labelList, value
			return self.labelLists [variable.labelList].labels [ int (value)]
		if variable.write_.format_type == floatFormatCode:
			if variable.write_.dp > 0:
				return "%0*.*f" % (variable.write_.width, variable.write_.dp, value)
			else:
				return "%0*d" % (variable.write_.width, int (value))
		if variable.write_.format_type == datetimeFormatCode:
			#return datetime.datetime.fromtimestamp (value/10.0 - 1264.*3600*24).isoformat ()
			return ""
		raise SAVError, "Value %s found with write format %s" %\
			(value, formatCodeMap [variable.write_.format_type])
			
	def sizeVariables (self):
		for variable in self.variables:
			variable.valueDistribution = {}
			if not variable.isDummy:
				variable.maxActualLength = 0
				if variable.type_ == 0:
					variable.min = self.highest
					variable.max = self.lowest
				variable.isMultiple = False
		stream = self.getCaseStream ("report")
		for case in stream:
			for (sequence, value) in case:
				if value is None: continue
				variable = self.variables [sequence]
				if variable.valueDistribution.has_key (value):
					variable.valueDistribution [value] += 1
				else:
					variable.valueDistribution [value] = 1
				if variable.extendedStringLength or variable.type_ == 255:
					thisLength = len (value.rstrip ())
					variable.maxActualLength =\
						max (variable.maxActualLength, thisLength)
				if variable.type_ == 0:
					variable.min = min (variable.min, value)
					variable.max = max (variable.max, value)
					# variable.max = 0
		for variable in self.variables:
			if not variable.isDummy:
				if variable.extendedStringLength or variable.type_ == 255:
					variable.sensibleLength = 1
					while variable.sensibleLength < variable.maxActualLength:
						variable.sensibleLength *= 2
						
if __name__ == "__main__":
	pass
import exceptions
import libxml2Util

from xml.sax.saxutils import escape, quoteattr
from schema import *
import re
import math

class SSSXMLError (exceptions.Exception): pass

def escapeCSVText (text):
	if text.find (',') >= 0 or text.find ('"') >= 0:
		return (True, text.replace ('"', '""'))
	else:
		return (False, text)
		
def escapedCSVText (text):
	quote, text = escapeCSVText (text)
	if quote:
		text = '"' + text + '"'
	return text
		
def pruneCSVNumber (text):
	if text.startswith ('-'):
		sign = '-'
		rump = text [1:]
	else:
		sign = ''
		rump = text
	rump = rump.lstrip ('0')
	if rump.startswith ('.'):
		rump = '0' + rump
	value = sign + rump
	# print "..Pruning %s as %s" % (text, value)
	return value
	
def toCSVField (vv, encoding="ascii", multipleDelimiter=""):
	quote = False
	variable = vv.variable
	if vv.value is None: text = ""
	elif multipleDelimiter and variable.type in ("single", "multiple"):
		answerList = variable.answerList
		if variable.type == 'single':
			text = forceEncoding (answerList.answerText (vv.value), encoding)
		else:
			texts = []
			for code in vv.value:
				texts.append (forceEncoding (answerList.answerText (code), encoding))
			text = multipleDelimiter.join (texts)
		quote, text = escapeCSVText (text)
	else:	
		text = vv.field.rstrip ()
		if variable.type == "multiple":
			quote = True	# Always quote multiples
		elif variable.type == "character":
			quote, text = escapeCSVText (text)
		else:
			text = pruneCSVNumber (text)
	if quote:
		text = '"' + text + '"'
	return text
		
def invertMap (map):
	result = {}
	for (key, value) in map.items():
		result[value] = key
	return result
	
len1Codes = ["%d" % i for i in xrange(0, 10)]
len2Codes = ["%02d" % i for i in xrange(0, 100)]

def magCeil (x):
	if x >= 0.0:
		return int (math.ceil (x))
	if int (x) == x:
		return int (x)
	return int (math.ceil (x))-1

def encodeBoolean (b):
	if b: return '1'
	else: return '0'
	
def encodeInt (i, width):
	if width == 1: return len1Codes[i]
	elif width == 2: return len2Codes[i]
	else:
		field = "%0*d" % (width, i)
		if len (field) > width: field = None
		return field
def encodeFloat (f, width, dp):
	field = "%0*.*f" % (width, dp, f)
	if len (field) > width: field = None
	return field
								
class SSSXMLSchema (SchemaRepresentation):

	def __init__ (self):
		SchemaRepresentation.__init__ (self)
		self.sssDate = None
		self.sssTime = None
		self.sssOrigin = None
		self.sssUser = None
		self.ident = "A"
		self.href = None
		
	def load (self, name, doc):
		#print "Loading SSSXMLSchema %s" % name
		self.schema = Schema()
		self.recordLength = 0
		xpc = libxml2Util.XPC (doc)
		survey = xpc.requireSingleNode("self::sss/survey", doc)
		self.schema.title = xpc.getTextNode ("title", survey)
		record = xpc.requireSingleNode("record", survey)
		self.schema.name = xpc.getAttribute("@ident", record)
		self.href = xpc.getAttribute ("@href", record)
		for variableDoc in xpc.eval("variable", record):
			type = xpc.getAttribute("@type", variableDoc).lower ()
			name = xpc.getTextNode("name", variableDoc)
			
			values = xpc.eval("values/value", variableDoc)
			if type in ("single", "multiple"):
				answerList = AnswerList(self.schema, name)
				for answerDoc in values:
					codeText = xpc.getAttribute("@code", answerDoc)
					if codeText is None:
						code = None
					else:
						code = int (codeText)
					Answer(answerList).makeNew\
						(None, code , xpc.getTextNode (".", answerDoc))
			else:
				answerList = None
				
			variable = Variable (self.schema, name, answerList)
			variable.start = int(xpc.getAttribute("position/@start", variableDoc))
			variable.finish = int(xpc.getAttribute("position/@finish", variableDoc, str(variable.start)))
			self.recordLength = max(self.recordLength, variable.finish)
			variable.id = xpc.getAttribute("@ident", variableDoc)
			variable.ttext = xpc.getTextNode("label", variableDoc)
			variable.qtext = None
			variable.type = type
			variable.count = 1
				
			use = xpc.getAttribute("@use", variableDoc)
			if use is not None:
				if use == 'serial':
					self.schema.serialVariableSequence = variable.index
				elif use == 'weight':
					self.schema.weightVariableSequence = variable.index
					
			filter = xpc.getAttribute("@filter", variableDoc)
			if filter is not None:
				variable.baseVariableIndex = self.schema.findVariable (filter)
				if variable.baseVariableIndex is not None:
					variable.baseVariableFilterValue = 1
								
			if type in ("single", "multiple"):
				variable.length = answerList.maxCode
				if type == "multiple":
					if xpc.hasSingleNode ("spread", variableDoc):
						variable.count = int(xpc.getAttribute("@subfields", variableDoc))
						variable.width = int(xpc.getAttribute("@width", variableDoc, '1'))
						variable.isSpread = True
					else:
						variable.count = variable.length
						variable.width = 1
						variable.isSpread = False

			elif type == "quantity":
				minText = xpc.getAttribute("values/range/@from", variableDoc)
				variable.dp = 0
				if minText.find('.') >= 0:
					variable.dp = len(minText)-minText.find('.')-1
				variable.min = float(minText)
				variable.max = float(xpc.getAttribute("values/range/@to", variableDoc))
				
			if xpc.hasSingleNode ("size", variableDoc):
				variable.length = int(xpc.getTextNode ("size", variableDoc))

	def allocate (self):
		import math
		recordLength = 0
		index = 0
		for variable in self.schema.variableSequence:
			#if variable.length is None:
			#	raise SSSXMLError, "Cannot allocate variable %s (%s)" % (variable.name, variable.type)
			index += 1
			variable.id = index
			variable.start = recordLength + 1
			if variable.type == "character":
				variable.finish = recordLength + variable.length
			elif variable.type == "logical":
				variable.finish = variable.start
			elif variable.type == "quantity":
				maxValue = magCeil (variable.max)
				minValue = magCeil (variable.min)
				width = max (codeLength (minValue), codeLength (maxValue))
				variable.finish = recordLength + width
				if variable.dp > 0:
					variable.finish += variable.dp + 1
			elif variable.type == "multiple":
				if variable.isSpread:
					variable.width = codeLength (variable.answerList.maxCode)
					spreadSize = variable.count * variable.width
					variable.finish = recordLength + spreadSize
				else:
					variable.width = 1
					variable.finish = recordLength + variable.length
			elif variable.type == "single":
				variable.finish = recordLength + codeLength (variable.answerList.maxCode)
			recordLength = variable.finish
		self.recordLength = recordLength
			
	def save (self, file, format="asc"):
		xmlDate = ""
		if self.sssDate and self.sssDate.strip ():
			xmlDate = "\n\t<date>%s</date>" % self.sssDate
		xmlTime = ""
		if self.sssTime and self.sssTime.strip ():
			xmlTime = "\n\t<time>%s</time>" % self.sssTime
		xmlOrigin= ""
		if self.sssOrigin and self.sssOrigin.strip ():
			xmlOrigin = "\n\t<origin>%s</origin>" % self.sssOrigin
		xmlUser = ""
		if self.sssUser and self.sssUser.strip ():
			xmlUser = "\n\t<user>%s</user>" % self.sssUser
		xmlName = ""
		if self.schema.name:
			xmlName = "\n\t\t<name>%s</name>" % forceEncoding(escape(self.schema.name))
		xmlTitle = ""
		if self.schema.title:
			xmlTitle = "\n\t\t<title>%s</title>" % forceEncoding(escape(self.schema.title))
		recordAttributes = " ident=\"%s\"" % self.ident
		print recordAttributes
		if self.href.strip ():
			recordAttributes += " href=\"%s\"" % forceEncoding(escape(self.href.strip ()))
		print recordAttributes
		if format == "csv":
			recordAttributes += " format=\"csv\" skip=\"1\""
		print recordAttributes
		file.write ("""<?xml version="1.0" encoding="ISO-8859-1"?>
<sss version="2.0">%s%s%s%s
	<survey>%s%s
		<record%s>\n""" %\
			(xmlDate, xmlTime, xmlOrigin, xmlUser,
			 xmlTitle,
			 xmlName,
			 recordAttributes))
		for index, variable in enumerate (self.schema.variableSequence):
			# if variable.length is None: break
			use = ""
			if self.schema.serialVariableSequence == variable.index:
				use = ' use="serial"'
			elif self.schema.weightVariableSequence == variable.index:
				use = ' use="weight"'
			filter = ""
			if variable.baseVariableIndex is not None:
				filter = ' filter="%s"' %\
					self.schema.variableSequence [variable.baseVariableIndex].name
			if format == "asc":
				positionAttributes = 'start="%d" finish="%d"' % (variable.start, variable.finish)
			else:
				positionAttributes = 'start="%d"' % (index+1,)
			file.write ("""			<variable ident="%s" type=%s%s%s>
				<name>%s</name>
				<label>%s</label>
				<position %s/>\n""" %\
					(variable.id, quoteattr(variable.type), use, filter,
					 escape(variable.name), forceEncoding(escape (variable.ttext)),
					 positionAttributes))
			if variable.type in ('single', 'multiple'):
				if variable.type == "multiple" and variable.isSpread:
					file.write ("""				<spread subfields="%d" width="%d"/>\n""" %\
						(variable.count, variable.width))
				file.write ("""				<values>\n""")
				for value in variable.answerList.answers():
					text = value.text
					if text is None:
						text = ""
					elif type (text) == int:
						text = str (text)
					else:
						text = forceEncoding(escape(text))
					file.write\
															("""					<value code="%s">%s</value>\n""" %\
															(value.code, text))
				file.write ("""				</values>\n""")
			elif variable.type == 'quantity':
				if variable.dp>0:
					file.write ("""				<values>
					<range from="%0*.*f" to="%0*.*f"/>
				</values>\n""" %\
						(variable.finish-variable.start+1, variable.dp, variable.min,
						 variable.finish-variable.start+1, variable.dp, variable.max))
				else:
					file.write ("""			 	<values>
					<range from="%d" to="%d"/>
				</values>\n""" %\
						(int(variable.min), int(variable.max)))
			elif variable.type == 'character':
				file.write ("""				<size>%s</size>\n""" %\
					variable.length)
			file.write ("""			</variable>\n""")
		file.write ("""		</record>
	</survey>
</sss>
""")
		
	# Create a schema in this representation based on an existing one
	def convert (self, aSchema, href=""):
		self.schema = aSchema
		self.href = href
		self.allocate()
		return self
			
class SSSVariableValue (VariableValue):

	def __init__ (self, dataset, index):
		VariableValue.__init__ (self, dataset, index)
		self.start0 = self.variable.start - 1
		self.finish0 = self.variable.finish - 1
		self.finish = self.variable.finish
		self.width = self.finish0 - self.start0 + 1
		self.emptyField = ' ' * self.width
		self.encoding = self.dataset.dataEncoding
		self.field = None
		
	def _prepareValue (self):
		self.value = None
		if self.finish0 <= len(self.dataset.record): # \n is not part of data
			self.field = self.dataset.record [self.start0: self.finish]
			if len(self.field.strip()) == 0: self.field = None
		else:
			self.field = None
			
	def _extractValue (self):
		self._prepareValue ()
		if self.field is not None:
			self.value = self.field.rstrip()	 

	def _insertValue (self):
		if self.value is not None:
			self._formatValue() 
		else:
			self.field = self.emptyField
			
	def _formatValue (self):
		value = self.value
		if type (value) in (str, unicode):
			value = value.replace ("\n", " ")
		# if self.field is not None:
		self.field = ("%-*s" % (self.width, value)).encode (self.encoding, "replace")
		if len(self.field) > self.width: self.field = self.field[0:self.width]
			
class SSSIntegerVariableValue (SSSVariableValue):
				
	def _extractValue (self):
		self._prepareValue()
		if self.field is not None:
			try:
				self.value = int (self.field)
			except exceptions.Exception, e:
				raise SSSXMLError, "Cannot extract integer variable %s from field '%s' at record %s column %s" %\
					(self.variable.name, self.field, self.dataset.recordNumber, self.variable.start)

	def _formatValue (self):
		try:
			self.field = encodeInt (int(self.value), self.width)
			if self.field is None: self.field = self.emptyField
		except exceptions.Exception, e:
				raise SSSXMLError, "Cannot encode value %s of integer variable %s into width %s at record %s" %\
					(self.value, self.variable.name, self.width, self.dataset.recordNumber)
			
class SSSFloatVariableValue (SSSVariableValue):

	def __init__ (self, dataset, index):
		SSSVariableValue.__init__ (self, dataset, index)
		#self.numberPart = self.width
		#if self.variable.dp > 0: self.numberPart -= (self.variable.dp + 1)
		
	def _extractValue (self):
		self._prepareValue()
		if self.field is not None:
			self.value =	float (self.field)

	def _formatValue (self):
		try:
			self.field = "%0*.*f" %\
				(self.width, self.variable.dp, self.value)
			if len (self.field) > self.width: self.field = self.emptyField
		except exceptions.Exception, e:
				raise SSSXMLError, "Cannot encode value %s of decimal variable %s into width %s.%s at record %s" %\
					(self.value, self.variable.name, self.width, self.dp, self.dataset.recordNumber)		
		#print "..Encoded variable %s with %d decimal place(s) as %s" %\
		#	(self.variable.name, self.variable.dp, self.field)
			
class SSSBooleanVariableValue (SSSVariableValue):
				
	def _extractValue (self):
		self._prepareValue()
		if self.field is not None:
			self.value = int (self.field)

	def _formatValue (self):
		if self.value:
			self.field = '1'
		else:
			self.field = '0'
		SSSVariableValue._formatValue (self)
			
class SSSMultipleVariableValue (SSSVariableValue):

	def __init__ (self, dataset, index):
		SSSVariableValue.__init__ (self, dataset, index)
		self.start0 = self.variable.start - 1
		self.finish0 = self.variable.finish - 1
		self.width = self.finish0 - self.start0 + 1
		self.fieldWidth = self.variable.width
		self.count = self.variable.count
			
class SSSSpreadVariableValue (SSSMultipleVariableValue):
				
	def _extractValue (self):
		self._prepareValue()
		if self.field is not None:
			result = []
			for offset in xrange(0, self.width, self.fieldWidth):
				fieldValue = int (self.field[offset:offset+self.fieldWidth])
				if fieldValue == 0: break
				result.append (fieldValue)
			self.value = result
		
	def _formatValue (self):
		fields = []
		if len(self.value) > self.count:
			raise SSSXMLError, "Variable %s has %d field(s) but %d values %s" %\
				(self.variable.name, self.count, len(self.value), self.value)
		for index in xrange(0, self.count):
			if index < len(self.value):
				fieldValue = self.value[index]
			else:
				fieldValue = 0
			#fields.append ("%*d" % (self.fieldWidth, int(fieldValue)))
			fields.append (encodeInt(int (fieldValue), self.fieldWidth))
		self.field = ''.join(fields)
			
class SSSBitstringVariableValue (SSSMultipleVariableValue):
				
	def _extractValue (self):
		self._prepareValue()
		if self.field is not None:
			result = []
			for index in xrange(0, self.width):
				if self.field[index] == '1':
				 result.append (index+1)
			self.value = result
		
	def _formatValue (self):
		fields = ['0']*self.width
		for aValue in self.value: fields[aValue-1] = '1'
		self.field = ''.join(fields)
						
class SSSDataset (Dataset):

	def __init__ (self, schemaRepresentation, filename, isInput=True,
		dataEncoding="ascii", format="asc", multipleDelimiter=""):
		if isInput:
			dataFile = file (filename)
		else:
			dataFile = file (filename, 'w')
		self.filename = filename
		self.hasBeenWritten = False
		self.hasBeenReopened = False
		self.dataEncoding = dataEncoding
		self.format = format
		self.multipleDelimiter = multipleDelimiter
		Dataset.__init__ (self, schemaRepresentation, dataFile, isInput)
		if self.format == "csv":
			if isInput:
				pass
			else:
				titles = []
				for vv in self.variableValueSequence:
					if self.multipleDelimiter:
						heading = vv.variable.ttext
					else:
						heading = vv.variable.name
					titles.append (escapedCSVText (forceEncoding (heading.strip ())))
				self.dataStore.write (",".join (titles))
				self.dataStore.write ("\n")

	def _assignVariableValue (self, index):
		variable = self.schema.variableSequence[index]
		if variable.type == 'character':
			return SSSVariableValue (self, index)
		elif variable.type == 'quantity' and variable.dp == 0:
			return SSSIntegerVariableValue (self, index)
		elif variable.type == 'quantity' and variable.dp > 0:
			return SSSFloatVariableValue (self, index)
		elif variable.type == 'single':
			return SSSIntegerVariableValue (self, index)
		elif variable.type == 'logical':
			return SSSBooleanVariableValue (self, index)
		elif variable.type == 'multiple' and variable.isSpread:
			return SSSSpreadVariableValue (self, index)
		elif variable.type == 'multiple' and not variable.isSpread:
			return SSSBitstringVariableValue (self, index)
		raise SSSXMLError, "Can't decode variable: (%s)" % (variable.name,)

	def read (self):
		self.record = self.dataStore.readline()
		if len(self.record) > 1:
			Dataset.read (self)
			return	True
		return False
		
	def reset1 (self):
		Dataset.reset1 (self)
		if self.hasBeenWritten:
			if not self.hasBeenReopened:
				self.dataStore.close ()
				self.dataStore = file (self.filename)
				self.hasBeenReopenend = True
		self.dataStore.seek (0)	
		
	def write (self):
		Dataset.write (self)
		if self.format == "asc":
			self.dataStore.write\
				(''.join([vv.field for vv in self.variableValueSequence]).rstrip())
		elif self.format == "csv":
			self.dataStore.write\
				(','.join ([toCSVField (vv, self.dataEncoding, self.multipleDelimiter)
					for vv in self.variableValueSequence]))
		self.dataStore.write ("\n")
		self.hasBeenWritten = True
		
	def close (self):
		self.dataStore.close ()

#if __name__=="__main__":
#	import sys
#	import libxml2
#	import urllib
#	import logger
#	
#	exitCode = 1
#	logger.open()
#	if len(sys.argv) >= 2:
#		try:
#			doc = libxml2.parseFile(sys.argv[1])
#		except:
#			logger.error ("Cannot load Triple-S XML document")
#			logger.logException()
#		else: 
#			try:
#				SSSschema = SSSXMLSchema ()
#				SSSschema.load (sys.argv[1], doc)
#				newSchema = SSSXMLSchema().convert (SSSschema.schema, "xx://yy")
#				logger.info ("..Schema %s loaded, %d variable(s), %d answer list(s)" %\
#					(sys.argv[1],
#					 len(SSSschema.schema.variableSequence),
#					 len(SSSschema.schema.answerListMap)))
#				exitCode = 0
#				newSchema.allocate()
#				newSchema.save (sys.stdout)
#			except:
#				logger.error ("Cannot process triple-s XML document")
#				logger.logException()
#	else:
#		logger.error ("Usage:	<XML-URL>")		 
#	logger.close()
#	sys.exit (exitCode)
#	

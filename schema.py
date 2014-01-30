#
# Copyright (c) 2005 Computable Functions Limited, GUILDFORD, UK
#
# All Rights Reserved.
#

import exceptions

__metaclass__ = type
		
interestingNumbers = (2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000,
	10000, 20000, 50000, 100000, 200000, 500000, 1000000)

class SchemaError (exceptions.Exception): pass

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
	
def codeLength (maxCode):
	if maxCode <0: return codeLength (-maxCode) + 1
	if maxCode < 10: return 1
	if maxCode < 100: return 2
	if maxCode < 1000: return 3
	if maxCode < 10000: return 4
	if maxCode < 100000: return 5
	if maxCode < 1000000: return 6
	if maxCode < 10000000: return 7
	if maxCode < 100000000: return 8
	if maxCode < 1000000000: return 9
	if maxCode < 10000000000: return 10 
	if maxCode < 100000000000: return 11 
	if maxCode < 1000000000000: return 12 
	if maxCode < 10000000000000: return 13 
	if maxCode < 100000000000000: return 14 
	if maxCode < 1000000000000000: return 15 
	if maxCode < 10000000000000000: return 16
	if maxCode < 100000000000000000: return 17
	if maxCode < 1000000000000000000: return 18
	if maxCode < 10000000000000000000: return 19
	if maxCode < 100000000000000000000: return 20
	if maxCode < 1000000000000000000000: return 21
	if maxCode < 10000000000000000000000: return 22
	if maxCode < 100000000000000000000000: return 23
	if maxCode < 1000000000000000000000000: return 24
	raise SchemaError, "More than 24 digits required for code %s" % maxCode

def lengthMaxCode (length):
	if length > 24 or length < 1:
		raise SchemaError, "Code lengths must be in range 1..24: %s" % length
	maxCode = (9, 99, 999, 9999, 99999, 999999, 9999999, 99999999, 999999999, 9999999999,
					99999999999, 999999999999, 9999999999999, 99999999999999,
					999999999999999, 9999999999999999, 99999999999999999,
					999999999999999999, 9999999999999999999, 99999999999999999999,
					999999999999999999999, 9999999999999999999999, 99999999999999999999999,
					999999999999999999999999)[length-1]
	return maxCode
	
class Schema:
	def __init__ (self):
		self.name = ""
		self.title = ""
		self.variableSequence = []
		self.variableMap = {}
		self.answerListMap = {}
		self.weightVariableSequence = None
		self.serialVariableSequence = None
		
	def findVariable (self, name):
		for (index, variable) in enumerate(self.variableSequence):
			if variable.name == name: return index
			
	# Copy a variable from another schema
	def copyVariable (self, variable):
		if variable.answerList is not None:
			# If named answer list already exists in this schema, use the existing one
			if variable.answerList.name is None or not\
			   self.answerListMap.has_key (variable.answerList.name):
				answerList = AnswerList (self, variable.answerList.name)
				for answer in variable.answerList.answers ():
					Answer (answerList).makeNew (answer.name, answer.code, answer.text)
			else:
				answerList = self.answerListMap [variable.answerList.name]
		else:
			answerList = None
		newVariable = Variable (self, variable.name, answerList)
		newVariable.ttext = variable.ttext
		newVariable.qtext = variable.qtext
		newVariable.type = variable.type
		if variable.baseVariableIndex is not None:
			raise SchemaError, "Can't copy based variable to new schema: %s" %\
				(variable.name,)
		newVariable.baseVariableIndex = None
		if newVariable.type in ('single', 'multiple', 'character'):
			newVariable.length = variable.length
		newVariable.count = variable.count
		if newVariable.type == 'quantity':
			newVariable.dp = variable.dp
			newVariable.min = variable.min
			newVariable.max = variable.max
			
	# Clone a complete schema
	# - only answer lists that are used
	# - don't reuse answer lists
	def copy (self, aSchema):
		self.name = aSchema.name
		self.title = aSchema.title
		for variable in aSchema.variableSequence:
			self.copyVariable (variable)

class SchemaRepresentation:

	# Initialise, either as empty or from an existing schema
	def __init__ (self, schema=None):
		pass
	
	# Load from an external file
	def load (self, name, file):
		return self
		
	# Save to an external file
	def save (self, file):
		assert False,\
			"Base 'save' method of SchemaRepresentation should not be called"
		
	# Assign an external representation.
	def allocate (self):
		assert False,\
			"Base 'allocate' method of SchemaRepresentation should not be called"
		
	# Create a schema in this representation based on an existing one
	def convert (self, aSchema):
		self.schema = aSchema
		self.allocate()
		return self

class VariableValue:

	def __init__ (self, dataset, index):
		self.dataset = dataset
		self.variable = dataset.schema.variableSequence[index]
		self.index = index
		self.enabled = False
		self.value = None
		
	def getType (self):
		return self.variable.type
		
	def _enable (self):
		self.enabled = True
		filter = self.variable.baseVariableIndex
		if filter is not None:
			self.dataset.variableValueSequence[filter]._enable()
					
	def _disable (self):
		self.enabled = False
		
	def _requireEnabled (self):
		if not self.enabled:
			raise SchemaError, "Access to disabled variable: %s" % self.variable.name
			
	def _checkBase (self):
		filter = self.variable.baseVariableIndex
		if filter is not None:
			return self.dataset.variableValueSequence[filter]._getValue() == self.variable.baseVariableFilterValue
		return True
				
	def _extractValue (self):
		pass		

	def _insertValue (self):
		pass
		
	def getValue (self):
		self._requireEnabled()
		if self._checkBase (): return self._getValue()
		
	def _getValue (self):
		return self.value
			
	def setValue (self, value):
		self._requireEnabled()
		self._setValue(value)
		
	def _setValue (self, value):
		self.value = value
		
	def reportValue (self):
		return "Variable %s at record %s (%s)" %\
			(self.variable.name, self.dataset.recordNumber,
			 self.variable.displayValue(self.value))
		
class Dataset:

	# Initialise, specifying a schema representation
	
	def __init__ (self, schemaRepresentation, dataStore, isInput=True):
		self.schemaRepresentation = schemaRepresentation
		self.schema = schemaRepresentation.schema
		self.dataStore = dataStore
		self.isInput = isInput
		self.variableValueSequence =\
			[self._assignVariableValue (index) for index in xrange(0,len(self.schema.variableSequence))]
		self.reset1 ()
		self.maxErrorCount = 100
		self.showTraceback = False
		
	# assign a VariableValue subclass instance appropriate to the dataset type and variable type
	def _assignVariableValue (self, index):
		return VariableValue (self, index)
			
	# Find the variable value instance corresponding to a particular variable name
	def getVariableValue (self, name):
		return self.variableValueSequence[self.schema.variableMap[name].index]
		
	# Prepare to make a pass over the dataset
	def reset1 (self):
		self.recordNumber = None
		for variableValue in self.variableValueSequence:
			variableValue._disable()
	
	# Make a variable value available during the next pass
	def enable (self, variableValue):
		variableValue._enable()
		
	# Begin pass making new value of each enabled variable available per advance
	def reset2 (self):
		self.enabledValues = []
		for variableValue in self.variableValueSequence:
			if variableValue is not None and variableValue.enabled:
				self.enabledValues.append (variableValue)
		self.recordNumber = 0
		self.errorCount = 0
		
	# Return True if new record available from the data store, False if not
	def read (self):
		self.recordNumber += 1
		for variableValue in self.enabledValues:
			try:
				variableValue._extractValue()
			except Exception, e:
				self.errorCount += 1
				self.errorReporter (variableValue, e)
		return True
		
	# Write the record to the data store
	def write (self):
		self.recordNumber += 1
		for variableValue in self.enabledValues:
			variableValue._insertValue ()
		
	def recordCount (self):
		self.reset1 ()
		self.reset2 ()
		recordsRead = 0
		moreData = self.read ()
		while moreData:
			recordsRead += 1
			moreData = self.read ()
		return recordsRead
		
	def close (self):
		pass
		
	def getDistributions (self):
		self.reset1 ()
		weightSequence = self.schema.weightVariableSequence
		if weightSequence is not None:
			weightvv = self.getVariableValue (self.schema.variableSequence[weightSequence])
			self.enable (weightvv)
		distributions = []
		for variable in self.schema.variableSequence:
			vv = self.getVariableValue (variable.name)
			self.enable (vv)
			distributions.append ((vv, {}))
		self.reset2 ()
		moreData = self.read()
		while moreData:
			for (vv, distribution) in distributions:
				if weightSequence is not None:
					weight = vv.getValue ()
				else:
					weight = 1.0
				value = vv.getValue()
				if type (value) == list:
					for individualValue in value:
						try:
							total = distribution[individualValue]
						except:
							total = Total()
							distribution[individualValue] = Total()
						total.increment(weight)
				else:
					try:
						total = distribution [value]
					except:
						total = Total()
						distribution [value] = total
					total.increment(weight)
			moreData = self.read()
		return distributions
		
	def convert (self, outputDataset, progressReporter = None):
		conversionSequence = []
		for variable in self.schema.variableSequence:
			vv = self.getVariableValue (variable.name)
			try:
				ovv = outputDataset.getVariableValue (variable.name)
				outputDataset.enable(ovv)
				self.enable (vv)
				conversionSequence.append ((vv, ovv))
			except Exception, e:
				raise SchemaError, "Can't enable variable %s in output dataset" % variable.name
		self.reset2()
		outputDataset.reset2()
		moreData = self.read()
		errorCount = 0
		while moreData:
			for (vv, ovv) in conversionSequence:
				ovv._setValue (vv._getValue())
			outputDataset.write()
					
			if progressReporter is not None:
				if self.recordNumber in interestingNumbers:
					progressReporter (self.recordNumber, 
						"%d record(s) processed" % self.recordNumber)
				else:		
					progressReporter (recordCount, self.recordNumber)

			moreData = self.read()
			
	def errorReporter (self, vv, e):
		import sys
		import traceback
		print >>sys.stderr, "--Error at record %d: %s" %\
			(self.recordNumber, e)
		if self.errorCount > self.maxErrorCount:
			print >>sys.stderr,\
				"--Maximum of %d conversion errors exceeded" %\
					self.maxErrorCount
			if self.showTraceback:
				traceback.print_exc ()
			sys.exit (1)
		
class Total:

	def __init__ (self):
		self.unweightedTotal = 0
		self.weightedTotal = 0.0
		
	def increment (self, weight=1.0):
		self.unweightedTotal += 1
		self.weightedTotal += weight
		
	def __str__ (self):
		return "%s\t%s"  % (self.unweightedTotal, self.weightedTotal)
		
class Variable:
	def __init__ (self, schema, name, answerList = None):
		self.name = name
		self.schema = schema
		self.answerList = answerList
		if answerList	is not None:
			self.answerList.useCount += 1 
		self.index = len(schema.variableSequence)
		schema.variableSequence.append (self)
		schema.variableMap[name] = self
		self.qtext = None
		self.baseVariableIndex = None
		# subclasses add attributes:
		# index: index in record
		# type: single/multiple/quantity/logical/character
		# ttext: Title for the variable
		# qtext: Associated question (if any)
		# length: Number of categories (categorical)
		#				 Number of characters (character string)
		# count: max number of values (1 unless multiple)
		# dp:		number of decimal places (if quantity)
		# min:	 minimum value (quantity)
		# max:	 maximum value (quantity)
		
	def displayValue (self, value):
		if value is None: return ""
		if self.type in ("single", "multiple"):
			return self.answerList.answerText (value)
		elif self.type == "quantity":
			if self.dp > 0: return "%0.*f" % (self.dp, value)
			else: return str (value)
		elif self.type== "logical":
			if value: return "Yes"
			else:		 return "No"
		else:
			return self.value		
	
	def displayValueRange (self, min, max):
		if self.type == 'logical':
			return self.ttext
		if min is None and max is None: return ""
		if min == max:
			return "%s: %s" % (self.ttext, self.displayValue (min))
		else:
			return "%s: %s...%s" % (self.ttext,
				self.displayValue (min),
				self.displayValue (max))
				
	def compareAnswers (self, other):
		if self.type in ("single", "multiple"):
			if other.type not in ("single", "multiple"):
				return False
			if self.length != other.length:
				return False
			otherAnswers = other.answerList.answers ()
			for answer in self.answerList.answers ():
				otherAnswer = otherAnswers. next ()
				if answer.code != otherAnswer.code or\
					 answer.name != otherAnswer.name or\
					 answer.text != otherAnswer.text:
					return False
			return True
		elif self.type != other.type:
			return False
		elif self.type == "logical":
			return True
		elif self.type == "quantity":
			return (self.dp == other.dp) and\
				(self.min == other.min) and\
				(self.max == other.max)
		elif self.type == "character":
			return self.length == other.length
		
class AnswerList:
	def __init__ (self, schema, name):
		self.name = name
		self.schema = schema
		if name is not None:
			schema.answerListMap[name] = self
		self.answerSequence = []
		self.answerMap = {}
		self.useCount = 0
		self.maxCode = None
		self.minCode = None
		self.simple = True
		
	def answers(self):
		nameMap = self.schema.answerListMap
		for item in self.answerSequence:
			if not item.isUse:
				yield item
			else:
				list = nameMap[item.name]
				for item in list.answers():
					yield item
					
	def findAnswerWithText (self, text):
		for answer in self.answers():
			if answer.text == text: return answer
					
	def findAnswerWithCode (self, code):
		for answer in self.answers():
			if answer.code == code: return answer
					
	def isSimpleList (self):
		return self.simple
		#currentCode = 0
		#for answer in self.answerSequence:
		#	currentCode += 1
		#	if answer.isUse or currentCode != answer.code:
		#		return False
		#return True
		
	def answerText (self, code):
		if self.simple:
			return self.answerSequence [code-1].text
		else:
			return "#%s" % code
				
class Answer:
	def __init__ (self, answerList):
		self.answerList = answerList
		answerList.answerSequence.append (self)
		
	def makeNew (self, name, code, text):
		self.isUse = False
		self.text = text
		self.name = name
		if code is None:
			if self.answerList.maxCode:
				proposedCode = self.answerList.maxCode + 1
			else:
				proposedCode = 1
		else:
			proposedCode = code
		if self.answerList.answerMap.has_key (code):
			raise SchemaError, "Duplicated code %s in answer list %s" %\
				(proposedCode, self.answerList.name)
		self.code = proposedCode
		self.answerList.answerMap [proposedCode] = self
		if self.answerList.maxCode:
			self.answerList.maxCode = max(self.answerList.maxCode, proposedCode)
		else:
			self.answerList.maxCode = proposedCode
		if self.answerList.minCode:
			self.answerList.minCode = min(self.answerList.minCode, proposedCode)
		else:
			self.answerList.minCode = proposedCode
		self.answerList.simple = self.answerList.simple and\
			proposedCode == len(self.answerList.answerSequence)
		
	def makeUse (self, name):
		self.isUse = True
		self.name = name
		usedList = self.answerList.schema.answerListMap[name]
		for usedAnswer in usedList.answers():
			self.answerList.answerMap [usedAnswer.code] = usedAnswer
		usedList.useCount += 1
		if self.answerList.maxCode is None:
			self.answerList.maxCode = usedList.maxCode
		else:
			self.answerList.maxCode = max(self.answerList.maxCode, usedList.maxCode)
		if self.answerList.minCode is None:
			self.answerList.minCode = usedList.minCode
		else:
			self.answerList.minCode = min(self.answerList.minCode, usedList.minCode)

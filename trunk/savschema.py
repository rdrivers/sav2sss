import exceptions
import savbinary
import re
import fprog
import difflib

from schema import *

class SavSchemaError (exceptions.Exception): pass
		
def invertMap (map):
	result = {}
	for (key, value) in map.items():
		result[value] = key
	return result
	
len1Codes = ["%d" % i for i in xrange(0, 10)]
len2Codes = ["%02d" % i for i in xrange(0, 100)]

identifierRE = re.compile ("[a-zA-Z][a-zA-Z0-9_]*")
 
def structuredNameIndex (aName):
	components = aName.split ("_")
	if len (components) > 1 and components [-1].isdigit ():
		return int (components [-1])
	else:
		return None

def structuredNameRoot (aName):
	return "_".join (aName.split ("_") [:-1])
		
# See if variable has yes/no answer list

def isYesNo (savVariable):
	if savVariable.labelList is None or\
	       len (savVariable.dataset.labelLists [savVariable.labelList].labels) <> 2:
	       	return False
	if yesLabel in savVariable.dataset.labelLists [savVariable.labelList].labels.values () and\
	   noLabel in savVariable.dataset.labelLists [savVariable.labelList].labels.values ():
	   	return True
	return False
		
# See if variable has 0/1 answer list

def is01 (savVariable):
	if savVariable.labelList is None or\
	       len (savVariable.dataset.labelLists [savVariable.labelList].labels) <> 2:
	       	return False
	if 0 in savVariable.dataset.labelLists [savVariable.labelList].labels.keys () and\
	   1 in savVariable.dataset.labelLists [savVariable.labelList].labels.keys ():
	   	return True
	return False
		
def findYesCode (savVariable):
	if savVariable.labelList is None or\
	       len (savVariable.dataset.labelLists [savVariable.labelList].labels) <> 2:
	       	return None
	for code, value in savVariable.dataset.labelLists [savVariable.labelList].labels.items ():
		if value == yesLabel: return code
	
# See if two answer lists are identical
def isSameAnswerList (savVariable1, savVariable2):
	if savVariable1.labelList is None or\
	   savVariable2.labelList is None or\
	   len (savVariable1.dataset.labelLists [savVariable1.labelList].labels) !=\
	   	len (savVariable2.dataset.labelLists [savVariable2.labelList].labels):
		return False
	for key, value in savVariable1.dataset.labelLists [savVariable1.labelList].labels.items ():
		if not savVariable1.dataset.labelLists [savVariable1.labelList].labels.has_key (key): return False
		if value != savVariable1.dataset.labelLists [savVariable2.labelList].labels [key]: return False
	return True

def getPrefix (text):
	if prefixDelimiterText == "": return ""
	fragments = text.split (prefixDelimiterText)
	if len (fragments) > 1:
		return prefixDelimiterText.join (fragments [:-1])
	else:
		return ""
def getSuffix (text):
	if suffixDelimiterText == "": return ""
	fragments = text.split (suffixDelimiterText)
	if len (fragments) > 1:
		return suffixDelimiterText.join (fragments [1:])
	else:
		return ""
	
# See if sequence of variables is potentially a multiple based on their names
def isPotentialMultiple (vList, next):
	return (structuredNameIndex (vList [0].name) == 1 or
		structuredNameIndex (vList [0].longName) == 1) and\
	       (structuredNameIndex (next.name) == len (vList) + 1 or
	        structuredNameIndex (next.longName) == len (vList) + 1)
# See if sequence of variables looks like a spread format multiple (and not a grid)	
def isPotentialSpread (vList, next):
	if vList [0].label.find (spreadMultipleAnswers [0]) >= 0:
		if len (spreadMultipleAnswers) < len (vList) + 1:
			raise SavSchemaError, "More spread responses than supplied answers: %s" %\
				(structuredNameRoot (vList [0].name))
		value = next.label.find (spreadMultipleAnswers [len (vList)]) >= 0
	else:
		value = False
	# print "isPotentialSpread", value, vList [0], next
	return value
def allAnswerListsSingleCategory (vList, next):
	value = vList [0].length == 1 and next.length == 1
	# print "allAnswerListsSingleCategory", value, vList [0], next
	return value
def allAnswerListsYesNo (vList, next):
	value = isYesNo (vList [0]) and isYesNo (next)
	# print "allAnswerListsYesNo", value, vList [0], next
	return value
def allAnswerLists01 (vList, next):
	value = is01 (vList [0]) and is01 (next)
	# print "allAnswerLists01", value, vList [0], next
	return value
def allAnswerListsSame (vList, next):
	value = isSameAnswerList (vList [0], next)
	# print "allAnswerListsSame", value, vList [0], next
	return value
def commonPrefix (vList, next):
	lastPrefix = getPrefix (next.label)
	if len (lastPrefix) == 0: return False
	for savVariable in vList:
		thisPrefix = getPrefix (savVariable.label)
		if thisPrefix != lastPrefix:
			value = False
	else:
		value = True
	# print "commonPrefix", value, vList [0], next
	return value
	
		
def commonSuffix (vList, next):
	lastSuffix = getSuffix (next.label)
	if len (lastSuffix) == 0: return False
	for savVariable in vList:
		thisSuffix = getSuffix (savVariable.label)
		if thisSuffix != lastSuffix:
			value = False
	else:
		value = len (firstSuffix) > 0 and firstSuffix == lastSuffix
	# print "commonSuffix", value, vList [0], next
	return value

def isSPSSBitstringMultiple (vList, next):
	return isPotentialMultiple (vList, next) and\
	   (allAnswerListsSingleCategory (vList, next) or
	    allAnswerListsYesNo (vList, next) or
	    allAnswerLists01 (vList, next)) and\
	   (commonPrefix (vList, next) or commonSuffix (vList, next))

def isSPSSSpreadMultiple (vList, next):
	return isPotentialMultiple (vList, next) and\
	       allAnswerListsSame (vList, next) and\
	       isPotentialSpread (vList, next)
		
def isSPSSMultiple (vList, next):
	# print "isSPSSMultiple", vList [0], next
	return isSPSSBitstringMultiple (vList, next) or\
	       isSPSSSpreadMultiple (vList, next)

class SAVSchema (SchemaRepresentation):

	def __init__ (self):
		SchemaRepresentation.__init__ (self)
		self.savDataset = None
		
	def load (self, savDataset):
		#print "Loading SavSchema %s" % name
		self.savDataset = savDataset
		self.schema = Schema()
		nonDummyCount = 0
		nonDummyMap = {}
		for index, savVariable in enumerate (savDataset.variables):
			if savVariable.isDummy: continue
			if savVariable.labelList is not None:
				savVariable.length =\
					len (savDataset.labelLists [savVariable.labelList].labels)
			else:
				savVariable.length = 0
			savVariable.labels = None
		revisedVariables = list (fprog.group (isSPSSMultiple, savDataset.variables))
		multipleCount = 0
		for variableGroup in revisedVariables:
			initialVariable = variableGroup [0]
			if len (variableGroup) <> 1:
				multipleCount = multipleCount + 1
				print "..SPSS-style multiple found: %s (%d categories)" %\
					(structuredNameRoot (variableGroup [0].name), len(variableGroup))
				if commonPrefix (variableGroup [:-1], variableGroup [-1]):
					prefixLength = len (getPrefix (initialVariable.label))
				else:
					prefixLength = 0
				if commonSuffix (variableGroup [:-1], variableGroup [-1]):
					suffixLength = len (getPrefix (initialVariable.label))
				else:
					suffixLength = 0
				
				initialVariable.isMultiple = True
				initialVariable.isSpread = isSPSSSpreadMultiple\
					(variableGroup [:-1], variableGroup [-1])
				if initialVariable.isSpread:
					for index, componentVariable in enumerate (variableGroup):
						componentVariable.isDummy = True
					initialVariable.isDummy = False
					initialVariable.count = len (variableGroup)
					initialVariable.label = initialVariable.label\
						[:-len (spreadMultipleAnswers[0])]
				else:
					initialVariable.isSingleCategory = allAnswerListsSingleCategory\
						(variableGroup [:-1], variableGroup [-1])
					initialVariable.labels = []
					for index, componentVariable in enumerate (variableGroup):
						if initialVariable.isSingleCategory:
							label = savDataset.labelLists [componentVariable.labelList].labels [1]
							initialVariable.yesCode = 1
						else:
							if prefixLength > 0:
								label = componentVariable.label\
									[prefixLength+len(prefixDelimiterText):]
							if suffixLength > 0:
								label = label\
									[:-suffixLength-len(suffixDelimiterText)]
							initialVariable.yesCode = findYesCode (componentVariable)
						initialVariable.labels.append\
							(label)
						if index > 0: componentVariable.isDummy = True
					initialVariable.labelList = None
					initialVariable.length = len (variableGroup)
					if prefixLength > 0:
						initialVariable.label = initialVariable.label [:prefixLength]
					if suffixLength > 0:
						initialVariable.label += initialVariable.label [-suffixLength:]
			else:
				initialVariable.isMultiple = False
				initialVariable.isSpread = False
		for index, savVariable in enumerate (savDataset.variables):
			if savVariable.isDummy: continue
			nonDummyMap [index] = nonDummyCount
			nonDummyCount += 1
			name = savVariable.name
			if savVariable.isMultiple:
				if savVariable.name == structuredNameRoot (savVariable.name):
					name = structuredNameRoot (savVariable.longName)
				else:
					name = structuredNameRoot (savVariable.name)
			if savVariable.labelList is not None:
				answerList = AnswerList (self.schema, name)
				labelList = savDataset.labelLists [savVariable.labelList]
				codes = [key for key in labelList.labels.keys ()]
				codes.sort ()
				for code in codes:
					Answer (answerList).makeNew\
						(None, code, labelList.labels [code])
			elif savVariable.labels is not None:
				answerList = AnswerList (self.schema, name)
				for index, label in enumerate (savVariable.labels):
					Answer (answerList).makeNew\
						(None, index+1, label)
			else:
				answerList = None
				
			variable = Variable (self.schema, name, answerList)
			variable.translatable = False
			if savVariable.label is None or len (savVariable.label) == 0:
				variable.ttext = savVariable.longName
				variable.qtext = ""
			else:
				variable.ttext = savVariable.label
				variable.qtext = savVariable.longName
			variable.count = 1
			if savVariable.labelList is not None and not savVariable.isSpread:
				variable.type = 'single'
				variable.length = answerList.maxCode
			elif savVariable.isMultiple:
				variable.type = 'multiple'
				variable.length = savVariable.length
				variable.isSpread = savVariable.isSpread
				if savVariable.isSpread:
					variable.count = savVariable.count
				else:
					variable.count = variable.length
			elif savVariable.type_ > 0:
				variable.type = 'character'
				if savVariable.extendedStringLength or savVariable.type_ == 255:
					if savDataset.sensibleStringLengths:
						variable.length = savVariable.sensibleLength
					else:
						variable.length = savVariable.extendedStringLength
				else:
					variable.length = savVariable.type_
			elif savVariable.write_.format_type == savbinary.datetimeFormatCode:
				variable.type = 'character'
				variable.length = 24
			else:
				variable.type = 'quantity'
				if savVariable.write_.format_type == savbinary.floatFormatCode:
					variable.translatable = True
				variable.dp = savVariable.write_.dp
				width = min (24, savVariable.write_.width)
				if variable.dp > 0: width = max (1, width - (variable.dp + 1))
				if width > 1:
					variable.min = min (savVariable.min, -lengthMaxCode (width-1))
				else:
					variable.min = min (savVariable.min, 0)
				variable.max = max (savVariable.max, lengthMaxCode (width))
				absMin = lengthMaxCode (codeLength (abs (variable.min)))
				if variable.min < 0.0:
					variable.min = -absMin
				else:
					variable.min = absMin
				variable.max = lengthMaxCode (codeLength (variable.max))
			
			# self.schema.weightVariableSequence = variable.index
			
class SAVVariableValue (VariableValue):

	def __init__ (self, dataset, index):
		VariableValue.__init__ (self, dataset, index)
		
	def _prepareValue (self):
		self.variableNumber, self.value = self.dataset.record [self.index]
			
	def _extractValue (self):
		self._prepareValue ()
		return self.value
			
class SAVSingleVariableValue (SAVVariableValue):
				
	def _extractValue (self):
		self._prepareValue()
		if self.value is not None:
			try:
				return int (self.value)
			except:
				raise SavSchemaError, "Can't extract code value %s" %\
					(self.reportValue (),)
			
class SAVQuantityVariableValue (SAVVariableValue):
		
	def _extractValue (self):
		self._prepareValue()
		if self.value is not None:
			try:
				return float (self.value)
			except:
				raise SavSchemaError, "Can't extract quantity value %s" %\
					(self.reportValue (),)
			
class SAVMultipleVariableValue (SAVVariableValue):
	pass
	
class SAVDataset (Dataset):

	def __init__ (self, schemaRepresentation, savDataset):
		Dataset.__init__ (self, schemaRepresentation, savDataset, True)
		self.savStream = None

	def _assignVariableValue (self, index):
		variable = self.schema.variableSequence[index]
		if variable.type == 'character':
			return SAVVariableValue (self, index)
		elif variable.type == 'quantity':
			return SAVQuantityVariableValue (self, index)
		elif variable.type == 'single':
			return SAVSingleVariableValue (self, index)
		elif variable.type == 'multiple':
			return SAVMultipleVariableValue (self, index)
		raise SavSchemaError, "Can't decode variable: %s" % variable.name

	def read (self):
		try:
			self.record = self.savStream.next ()
			Dataset.read (self)
			return True
		except StopIteration, e:
			return False
		
	def reset2 (self):
		Dataset.reset2 (self)
		self.savStream = self.dataStore.getCaseStream ()
		
	def close (self):
		pass

	
if __name__ == "__main__":
	import sys
	import os.path
	import getopt
	import sssxmlschema
	import datetime
			
	def logExceptionText (details=None):
		import traceback
		if details is None:
			details = sys.exc_info()
		(type, value, tb) = details
		return """Exception:	 %s
		Description: %s
		Traceback:	 %s""" %\
			(type, value, traceback.extract_tb (tb))
		
	def logException (details=None):
		print >>sys.stderr, logExceptionText (details)
	
	if len(sys.argv) < 2:
		print "--Usage: savschema [options] SAV-file-name"
		sys.exit(0)
		
	sensibleStringLengths = True
	full = False
	outputEncoding = "iso-8859-1"
	ident = "A"
	yesLabel = "Yes"
	noLabel = "No"
	suffixDelimiterText = ""
	prefixDelimiterText = ":"
	spreadMultipleAnswerList = ":1st answer,:2nd answer,:3rd answer,:4th answer,:5th answer,:6th answer,:7th answer,:8th answer"
	version = 0.3
	defaultMetadata = ("%s;%s;SAV2SSS %s (Windows) by Computable Functions (http://www.computable-functions.com);" %\
		("", "", version)).split (";")
	xmlMetadata = ""
	showVersion = False
	href = ""
	titleText = ""
	
	optlist, args = getopt.getopt(sys.argv[1:], 'vsfo:i:yna:b:m:x:h:t:')
	for (option, value) in optlist:
		if option == '-s':
			sensibleStringLengths = False
		if option == '-f':
			full = True
		if option == '-o':
			outputEncoding = value
		if option == '-i':
			ident = value				
		if option == '-y':
			yesLabel = value
		if option == "-n":
			noLabel = value
		if option == "-b":
			prefixDelimiterText = value.strip ()
		if option == "-a":
			suffixDelimiterText = value.strip ()
		if option == "-m":
			spreadMultipleAnswerList = value
		if option == "-x":
			xmlMetadata = value
		if option == "-v":
			showVersion = True
		if option == "-h":
			href = value
		if option == "-t":
			titleText = value

	nameTitle = titleText.split (";")
	if len (nameTitle) == 1:
		name = ""
		title = nameTitle [0]
	else:
		name, title = nameTitle [:2]
			
	metadataFields = xmlMetadata.split (";")
	if len (metadataFields) > 0 and len (metadataFields [0]):
		sssDate = metadataFields [0]
	else:
		sssDate = defaultMetadata [0]
	if len (metadataFields) > 1 and len (metadataFields [1]):
		sssTime = metadataFields [1]
	else:
		sssTime = defaultMetadata [1]
	if len (metadataFields) > 2 and len (metadataFields [2]):
		sssOrigin = metadataFields [2]
	else:
		sssOrigin = defaultMetadata [2]
	if len (metadataFields) > 3 and len (metadataFields [3]):
		sssUser = metadataFields [3]
	else:
		sssUser = defaultMetadata [3]
	
	spreadMultipleAnswers = spreadMultipleAnswerList.split (",")
	if len(spreadMultipleAnswers) < 2 or (len (prefixDelimiterText) > 0 and len (suffixDelimiterText) > 0):
		print "--Usage: savschema [options] SAV-file-name"
		sys.exit (0)
		
	if len (ident) == 1 and ident.isalpha ():
		ident = ident.upper ()
	else:
		print "--Invalid ident value: '%s'" % ident
		sys.exit (0)
				
	if showVersion:
		print "..sav2sss version %s" % version
				
	(root, savExt) = os.path.splitext (args [0])
	print "..Converting %s to %s.xml and %s.asc" %\
		(args [0], root, root)
	if not href:
		href = "%s.asc" % root
	if href.strip ():
		print "..href attribute will be '%s'" % href
		
	if len(args) == 1 and ident.isalpha () and len(ident) == 1:
		try:
			savData = savbinary.SAVDataset (args [0], sensibleStringLengths)
		except exceptions.Exception, e:
			print "Can't load SAV file (%s)" % e
			logException ()
		else:
			try:
				savSchema = SAVSchema ()
				savSchema.load (savData)
				print "..SAV file %s loaded, %d variable(s), %d answer list(s)" %\
					(args[0],
					 len(savSchema.schema.variableSequence),
					 len(savSchema.schema.answerListMap))
				if full: savData.printMetadata (True)
				newSchema = sssxmlschema.SSSXMLSchema().convert (savSchema.schema, href)
				if not sssDate and savData.creation_date:
					sssDate = savData.creation_date
				if not sssTime and savData.creation_time:
					sssTime = savData.creation_time
				if sssDate and sssDate.lower () == 'now':
					sssDate = str(datetime.date.today ())
				if sssTime and sssTime.lower () == 'now':
					sssTime = str(datetime.datetime.now ().time ()) [:5]
				newSchema.sssDate = sssDate
				newSchema.sssTime = sssTime
				newSchema.sssOrigin = sssOrigin
				newSchema.sssUser = sssUser
				newSchema.ident = ident
				newSchema.schema.name = name
				newSchema.schema.title = title
				newSchema.allocate()
				outputXMLFile = open (root + ".xml", 'w')
				newSchema.save (outputXMLFile)
				outputXMLFile.close ()
				SSSDataset = sssxmlschema.SSSDataset (newSchema, root + '.asc', False, outputEncoding)
				savDataset = SAVDataset (savSchema, savData)
				savDataset.convert (SSSDataset)
				print "..%d case(s) recovered from proprietary format" % savDataset.recordNumber
				distributions = SSSDataset.getDistributions ()
				if full:
					for vv, distribution in distributions:
						itemCount = len (distribution)
						others = 0
					 	print "Variable\t%s Distribution" % vv.variable.name
						for value, total in distribution.items ():
							if itemCount < 10 or total.unweightedTotal >  1:
								print "Value\t%s\t%s" % (value, total.unweightedTotal)
							else:
								others += 1
						if others > 0:
							print "Unlisted singleton values:", others
						
				SSSDataset.close ()
				outputXMLFile.close ()
				
			except exceptions.Exception, e:
				print "Cannot prepare triple-S XML dataset (%s)" % e
				logException ()
	else:
		print  "--Usage: savschema [-v] [-s] [-f] [-iIdent] [-oOutputEncoding] SAV-file-name"
import exceptions
import savbinary

from schema import *

class SavSchemaError (exceptions.Exception): pass
		
def invertMap (map):
	result = {}
	for (key, value) in map.items():
		result[value] = key
	return result
	
len1Codes = ["%d" % i for i in xrange(0, 10)]
len2Codes = ["%02d" % i for i in xrange(0, 100)]
								
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
			nonDummyMap [index] = nonDummyCount
			nonDummyCount += 1
			if savVariable.labelList is not None:
				answerList = AnswerList (self.schema, savVariable.name)
				labelList = savDataset.labelLists [savVariable.labelList]
				codes = [key for key in labelList.labels.keys ()]
				codes.sort ()
				for code in codes:
					Answer (answerList).makeNew\
						(None, code, labelList.labels [code])
			else:
				answerList = None
				
			variable = Variable (self.schema, savVariable.name, answerList)
			variable.translatable = False
			if savVariable.label is None or len (savVariable.label) == 0:
				variable.ttext = savVariable.longName
				variable.qtext = ""
			else:
				variable.ttext = savVariable.label
				variable.qtext = savVariable.longName
			if savVariable.labelList is not None:
				variable.type = 'single'
				variable.length = answerList.maxCode
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
				absMin = lengthMaxCode (codeLength (variable.min))
				if variable.min < 0.0:
					variable.min = -absMin
				else:
					variable.min = absMin
				variable.max = lengthMaxCode (codeLength (variable.max))
			
			variable.count = 1
			
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
		print "--Usage: savschema [-s] [-f] [-oOutputEncoding] SAV-file-name"
		sys.exit(0)
		
	sensibleStringLengths = True
	full = False
	outputEncoding = "iso-8859-1"
	ident = "A"
	optlist, args = getopt.getopt(sys.argv[1:], 'vsfo:i:')
	for (option, value) in optlist:
		if option == '-s':
			sensibleStringLengths = False
		if option == '-f':
			full = True
		if option == '-o':
			outputEncoding = value
		if option == '-i':
			ident = value.upper ()
			
	(root, savExt) = os.path.splitext (args [0])
	print "..Converting %s to %s.xml and %s.asc" %\
		(args [0], root, root)

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
				newSchema = sssxmlschema.SSSXMLSchema().convert (savSchema.schema, "xx://yy")
				newSchema.schema.name = ident
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
				
			except exceptions.Exception, e:
				print "Cannot prepare triple-S XML dataset (%s)" % e
				logException ()
	else:
		print  "--Usage: savschema [-v] [-s] [-f] [-iIdent] [-oOutputEncoding] SAV-file-name"

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

import exceptions
import traceback
import re
import fprog
import rdflib
import libxml2

import libxml2Util
import urllib
import urllib2

import rdfutil
		
from schema import *

class RDFUUIDs:
	@classmethod
	def initialise (__class__):
		__class__.rdfNS =\
			rdflib.Namespace ("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
		__class__.rdfsNS =\
			rdflib.Namespace ("http://www.w3.org/2000/01/rdf-schema#")
		__class__.xsdNS =\
			rdflib.Namespace ("http://www.w3.org/2001/XMLSchema#")
		__class__.rdfType = __class__.rdfNS ["type"]
		__class__.rdfsResource = __class__.rdfsNS ["Resource"]
		__class__.rdfsClass = __class__.rdfsNS ["Class"]
		__class__.rdfsSubClassOf = __class__.rdfsNS ["subClassOf"]
		__class__.xsdString = __class__.xsdNS ["string"]
		__class__.xsdPositiveInteger = __class__.xsdNS ["positiveInteger"]
		__class__.xsdDecimal = __class__.xsdNS ["decimal"]
		__class__.xsdDate = __class__.xsdNS ["date"]
		__class__.xsdTime = __class__.xsdNS ["time"]
		
SSS12nsURI = "http://www.triple-s.org/sw/2014-08-19/1.2#"
class SSSUUIDs:
	@classmethod
	def initialise (__class__):
	
		# Classes

		__class__.sss12NS = rdflib.Namespace (SSS12nsURI)
		__class__.sssObject = __class__.sss12NS ["object"]
		__class__.sss = __class__.sss12NS ["sss"]
		__class__.survey = __class__.sss12NS ["survey"]
		__class__.record = __class__.sss12NS ["record"]
		__class__.variable = __class__.sss12NS ["variable"]
		__class__.value = __class__.sss12NS ["value"]
		__class__.text = __class__.sss12NS ["text"]
		__class__.case = __class__.sss12NS ["case"]
		__class__.vV = __class__.sss12NS ["vV"]
		__class__.v = __class__.sss12NS ["v"]

		# relationship properties

		__class__.hasSurvey = __class__.sss12NS ["hasSurvey"]
		__class__.hasRecord = __class__.sss12NS ["hasRecord"]
		__class__.hasVariable = __class__.sss12NS ["hasVariable"]
		__class__.hasValues = __class__.sss12NS ["hasValues"]
		__class__.hasValue = __class__.sss12NS ["hasValue"]
		__class__.hasText = __class__.sss12NS ["hasText"]
		__class__.hasCase = __class__.sss12NS ["hasCase"]
		__class__.hasVV = __class__.sss12NS ["hasVV"]
		__class__.ofV = __class__.sss12NS ["ofV"]
		
		# scalar properties
		
		__class__.sssVersion = __class__.sss12NS ["sssVersion"]
		__class__.origin = __class__.sss12NS ["origin"]
		__class__.user = __class__.sss12NS ["user"]
		__class__.date = __class__.sss12NS ["date"]
		__class__.time = __class__.sss12NS ["time"]
		__class__.surveyTitle = __class__.sss12NS ["surveyTitle"]
		__class__.recordIdent = __class__.sss12NS ["recordIdent"]
		__class__.href = __class__.sss12NS ["href"]
		__class__.ident = __class__.sss12NS ["ident"]
		__class__.type = __class__.sss12NS ["type"]
		__class__.name = __class__.sss12NS ["name"]
		__class__.label = __class__.sss12NS ["label"]
		__class__.startLocation = __class__.sss12NS ["startLocation"]
		__class__.finishLocation = __class__.sss12NS ["finishLocation"]
		__class__.use = __class__.sss12NS ["use"]
		__class__.filter = __class__.sss12NS ["filter"]
		__class__.size = __class__.sss12NS ["size"]
		__class__.rangeStart = __class__.sss12NS ["rangeStart"]
		__class__.rangeFinish = __class__.sss12NS ["rangeFinish"]
		__class__.decimals = __class__.sss12NS ["decimals"]
		__class__.values = __class__.sss12NS ["values"]
		__class__.code = __class__.sss12NS ["code"]
		__class__.serial = __class__.sss12NS ["serial"]
		__class__.weight = __class__.sss12NS ["weight"]
		__class__.data = __class__.sss12NS ["data"]
		__class__.sequence = __class__.sss12NS ["sequence"]
		__class__.v = __class__.sss12NS ["v"]		

	@classmethod		
	def assertSchemaTriples (__class__, writer):
		triples = [
			(SSSUUIDs.sssObject, RDFUUIDs.rdfType, RDFUUIDs.rdfsResource), 
			(SSSUUIDs.sss, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject), 
			(SSSUUIDs.survey, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject), 
			(SSSUUIDs.record, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject), 
			(SSSUUIDs.variable, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject), 
			(SSSUUIDs.value, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject), 
			(SSSUUIDs.text, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject), 
			(SSSUUIDs.case, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject), 
			(SSSUUIDs.vV, RDFUUIDs.rdfsSubClassOf, SSSUUIDs.sssObject) 
		]
		for triple in triples: writer.add (triple)

class SSS2RDFError (exceptions.Exception): pass

def prepareMetadataTriples ():
	# survey and record properties
	surveyTriples = [
		(sssUUID, RDFUUIDs.rdfType, SSSUUIDs.sss),
		(surveyUUID, RDFUUIDs.rdfType, SSSUUIDs.survey),
		(recordUUID, RDFUUIDs.rdfType, SSSUUIDs.record),
		(sssUUID, SSSUUIDs.hasSurvey, surveyUUID),
		(surveyUUID, SSSUUIDs.hasRecord, recordUUID),
	]
	if SSSSchema.SSSVersion:
		surveyTriples.append (
			(sssUUID, SSSUUIDs.sssVersion,
			 rdflib.Literal (SSSSchema.SSSVersion))
		)		
	if SSSSchema.user:
		surveyTriples.append (
			(sssUUID, SSSUUIDs.user,
			 rdflib.Literal (SSSSchema.user))
		)		
	if SSSSchema.origin:
		surveyTriples.append (
			(sssUUID, SSSUUIDs.origin,
			 rdflib.Literal (SSSSchema.origin))
		)		
	if SSSSchema.date:
		surveyTriples.append (
			(sssUUID, SSSUUIDs.date,
			 rdflib.Literal (SSSSchema.date,
					 datatype=RDFUUIDs.xsdDate))
		)		
	if SSSSchema.time:
		surveyTriples.append (
			(sssUUID, SSSUUIDs.time,
			 rdflib.Literal (SSSSchema.time,
					 datatype=RDFUUIDs.xsdTime))
		)
	if not title: surveyTitle = schema.title
	else:
		surveyTitle = title
	if surveyTitle:
		surveyTriples.append (
			(surveyUUID, SSSUUIDs.surveyTitle,
			 rdflib.Literal (surveyTitle))
		)
	if schema.name:
		surveyTriples.append (
			(recordUUID, SSSUUIDs.recordIdent,
			 rdflib.Literal (schema.name))
		)
	if SSSSchema.href:
		surveyTriples.append (
			(recordUUID, SSSUUIDs.href,
			 rdflib.Literal (SSSSchema.href))
		)
	for triple in surveyTriples: writer.add (triple)

def prepareVariableTriples ():
	# variable properties
	variableUUIDTable = {}
	for variable in schema.variableSequence:
		variableUUID = nodeMaker.uuid ("#variable_%s" % variable.name)
		variableUUIDTable [variable.name] = variableUUID
		variableTriples = [
			(recordUUID, SSSUUIDs.hasVariable, variableUUID),
			(variableUUID, RDFUUIDs.rdfType, SSSUUIDs.variable),
			(variableUUID, SSSUUIDs.ident,
			 rdflib.Literal (variable.id)),
			(variableUUID, SSSUUIDs.type,
			 rdflib.Literal (variable.type)),
			(variableUUID, SSSUUIDs.name,
			 rdflib.Literal (variable.name)),
			(variableUUID, SSSUUIDs.label,
			 rdflib.Literal (variable.ttext)),
			(variableUUID, SSSUUIDs.startLocation,
			 rdflib.Literal (variable.start)),
			(variableUUID, SSSUUIDs.finishLocation,
			 rdflib.Literal (variable.finish)),
		]
		if variable.use:
			variableTriples.append (
				(variableUUID, SSSUUIDs.use,
				 rdflib.Literal (variable.use))
			)
		if variable.filter:
			variableTriples.append (
				(variableUUID, SSSUUIDs.filter,
				 rdflib.Literal (variable.filter))
			)
		if variable.length and variable.type == "character":
			variableTriples.append (
				(variableUUID, SSSUUIDs.size,
				 rdflib.Literal (variable.length))
			)
		for triple in variableTriples: writer.add (triple)
		if variable.type in ('single', 'multiple', 'quantity'):
			valuesUUID = nodeMaker.uuid ("#values_%s" % variable.name)
			valuesTriples = [
				(valuesUUID, RDFUUIDs.rdfType, SSSUUIDs.values),
				(variableUUID, SSSUUIDs.hasValues, valuesUUID)
			]
			if variable.min is not None:
				valuesTriples.append (
					(valuesUUID, SSSUUIDs.rangeStart,
					 rdflib.Literal (variable.min))
				)
			if variable.max is not None:
				valuesTriples.append (
					(valuesUUID, SSSUUIDs.rangeFinish,
					 rdflib.Literal (variable.max))
				)
			if variable.dp:
				valuesTriples.append (
					(valuesUUID, SSSUUIDs.decimals,
					 rdflib.Literal (variable.dp))
				)
			for triple in valuesTriples: writer.add (triple)
			answerList = variable.answerList
			if answerList:
				for answer in answerList.answerSequence:
					valueUUID = nodeMaker.uuid ("#value_%s_%s" % (variable.name, answer.code))
					valueTriples = [
						(valueUUID, RDFUUIDs.rdfType, SSSUUIDs.value),
						(valuesUUID, SSSUUIDs.hasValue, valueUUID),
						(valueUUID, SSSUUIDs.code,
						 rdflib.Literal (answer.code)),
						(valueUUID, SSSUUIDs.text,
						 rdflib.Literal (answer.text)),
					]
					for triple in valueTriples:
						writer.add (triple)
	return variableUUIDTable
	
def prepareCaseTriples (data, index, constructVariableValues):
	caseUUID = nodeMaker.uuid ("#case_%s" % (index,))
	caseTriples = [
		(recordUUID, SSSUUIDs.hasCase, caseUUID),
		(caseUUID, RDFUUIDs.rdfType, SSSUUIDs.case),
		(caseUUID, SSSUUIDs.data,
		 rdflib.Literal (data.rstrip ())),
		(caseUUID, SSSUUIDs.sequence,
		 rdflib.Literal (index)),
	]
	if constructVariableValues:
		for variable in schema.variableSequence:
			field = data [variable.start-1:variable.finish].rstrip ()
			values = []		
			if field:
				if variable.type == "quantity":
					if variable.dp > 0:
						values.append (float (field))
					else:
						values.append (int (field))
				elif variable.type == "boolean":
					values.append (field == "1")
				elif variable.type == "single":
					values.append (int (field))
				elif variable.type == "character":
					values.append (field)
				elif variable.type == "multiple":
					if variable.isSpread:
						for offset in xrange(variable.width - variable.codeWidth, len (field), variable.width):
							fieldValue = int (field[offset:offset+variable.codeWidth])
							if fieldValue: values.append (fieldValue)
					else:
						for index, subfield in enumerate (field):
							if subfield == "1": values.append (index+1)

			if len (values):
				vvUUID = nodeMaker.uuid ("#vV_%s_%s" % (index, variable.name))
				caseTriples.extend ([
					(caseUUID, SSSUUIDs.hasVV, vvUUID),
					(vvUUID, RDFUUIDs.rdfType, SSSUUIDs.vV),
					(vvUUID, SSSUUIDs.ofV, variableUUIDTable [variable.name]),
				])
				for value in values:
					caseTriples.extend ([
						(vvUUID, SSSUUIDs.v,
						 rdflib.Literal (value)),
					])
					if variable.use == "weight":
						caseTriples.append ((caseUUID, SSSUUIDs.weight, rdflib.Literal (value)))
					if variable.use == "serial":
						caseTriples.append ((caseUUID, SSSUUIDs.serial, rdflib.Literal (value)))

		for triple in caseTriples: writer.add (triple)
		
if __name__ == "__main__":
	import sys
	import os.path
	import getopt
	import sssxmlschema
	import datetime
		
	version = 0.1
	showVersion = False
	outputFilename = ""
	surveyURIBase = ""
	conversionPhase = 2
	dataFilename = None
	outputFormat = "n3"
	store = "file"
	contextURI = ""
	batchSize = 0
	title = ""
	endpoint = ""
	delete = False
	limit = None
	offset = None
	
	try:
		optlist, args = getopt.getopt(sys.argv[1:], 'f:vo:u:p:d:s:e:c:b:t:dxl:o:')
		for (option, value) in optlist:
			if option == "-f":
				outputFormat = value
			if option == "-v":
				showVersion = True
			if option == "-o":
				outputFilename = value
			if option == "-u":
				surveyURIBase = value
			if option == "-p":
				conversionPhase = int (value)
			if option == "-d":
				dataFilename = value
			if option == "-c":
				contextURI = value
			if option == "-b":
				batchSize = int (value)
			if option == "-t":
				title = value.strip ()
			if option == "-s":
				store = value.lower ()
			if option == "-e":
				endpoint = value
			if option == "-x":
				delete = True
			if option == "-l":
				limit = int (value)
			if option == "-o":
				offset = int (value)

		if showVersion:
			print "..sss2rdf version %s" % version

		if len (args) < 1 or len (args) > 2:
			raise SSS2RDFError, "Invalid arguments"

		(root, xmlExt) = os.path.splitext (args [0])
		if not outputFilename:
			outputFilename = root + "." + outputFormat

		if store == "file":
			print "..Converting %s to %s" %\
				(root, outputFilename)
		elif store == "bigdata":
			if not endpoint:
				endpoint = "http://localhost:8080/bigdata/sparql"
			print "..Uploading from %s to %s" %\
				(root, endpoint)
			# raise SSS2RDFError, "Support for bigdata store not yet implemented"
		elif store == "null":
			print "..Evaluating conversion of %s" % root
		else:
			raise SSS2RDFError, "Unknown store type '%s'" % store
			
	except exceptions.Exception, e:
			print "--sss2rdf error: %s" % e
			print "  sss2rdf [-v] [-e] [-cPhase] [-fFormat] [-oOutputFile] [-uBaseURI] sss-xml-file"
			sys.exit (0)
	try:
		RDFUUIDs.initialise ()
		SSSUUIDs.initialise ()

		if conversionPhase > 0:
			SSSSchema = sssxmlschema.SSSXMLSchema ()
			SSSSchema.load (args[0], libxml2.parseFile(args[0]))
			schema = SSSSchema.schema

		bindings = {
			"sss": SSS12nsURI,
		}
		if surveyURIBase:
			surveyNs = rdflib.Namespace (surveyURIBase)
			bindings ["survey"] = surveyURIBase
			nodeMaker = rdfutil.NodeUUIDMaker (surveyNs)
		else:
			nodeMaker = rdfutil.NodeUUIDMaker ()
		if store == "null":
			writer = rdfutil.NullTripleWriter (
				bindings = bindings,
				outputFormat = outputFormat,
				contextURI = contextURI,
				batchSize = batchSize
		)
		elif store == "file":
			writer = rdfutil.FileTripleWriter (outputFilename,
				bindings = bindings,
				outputFormat = outputFormat,
				contextURI = contextURI,
				batchSize = batchSize
		)
		elif store == "bigdata":
			writer = rdfutil.BigdataTripleWriter (endpoint, delete,
				bindings = bindings,
				outputFormat = outputFormat,
				contextURI = contextURI,
				batchSize = batchSize
		)
		if limit is not None or offset is not None:
			if limit: print "..Limit is %s record(s)" % limit
			if offset: print "..Offset is %s record(s)" % offset
			writer.setLimits (limit, offset)

		sssUUID = nodeMaker.uuid ('#sss')
		surveyUUID = nodeMaker.uuid ('#survey')
		recordUUID = nodeMaker.uuid ('#record')
		if conversionPhase > 0:
			SSSUUIDs.assertSchemaTriples (writer)
			prepareMetadataTriples ()
		if conversionPhase > 1:
			variableUUIDTable = prepareVariableTriples ()
		if conversionPhase > 2:
			if not dataFilename:
				dataFilename = root + ".asc"
			dataFile = open (dataFilename, 'r')
			caseCount = 0
			for case in dataFile.readlines ():
				caseCount += 1	
				prepareCaseTriples (case, caseCount, conversionPhase == 4)
			dataFile.close ()
			print "..%d case(s) converted to triples" % caseCount

		tripleCount = writer.tripleCount
		writer.close ()
		if store == "null":
			print "..%d triples prepared in total" % tripleCount
		elif store == "file":
			print "..%d triples written to file %s" %\
				(writer.addedCount, outputFilename)
		elif store == "bigdata":
			print "..%d triples uploaded to %s" %\
				(writer.addedCount, endpoint)
		print "..%d triples in entire dataset" % tripleCount
		
	except exceptions.Exception, e:
		print "Cannot prepare RDF dataset (%s)" % e
		raise

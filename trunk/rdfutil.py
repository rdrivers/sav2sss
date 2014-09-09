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
import json

import libxml2Util
import urllib
import urllib2

class RequestWithMethod(urllib2.Request):
	def __init__(self, method, *args, **kwargs):
		self._method = method
		urllib2.Request.__init__ (self, *args, **kwargs)

	def get_method(self):
		return self._method
		
from schema import *

class RDFUtilError (exceptions.Exception): pass

class NodeUUIDMaker (object):

	def __init__ (self, ns=None):
		self.ns = ns

	def uuid (self, suffix=None):
		if self.ns and suffix:
			uuid = self.ns [suffix]
		else:
			uuid = rdflib.BNode ()
		return uuid

class TripleWriter (object):
	def __init__ (self, bindings = {}, outputFormat="n3", contextURI="", batchSize=0):
		self.contextURI = contextURI
		self.tripleCount = 0
		self.batchSize = batchSize
		self.batchCount = 0
		self.bindings = bindings
		self.outputFormat = outputFormat
		self.limit = None
		self.offset = None
		self.addedCount = 0
		
	def setLimits (self, limit=None, offset=None):
		if limit is not None: self.limit = limit
		if offset is not None: self.offset = offset
		
	def _writeBatch (self):
		pass
		
	def add (self, triple):
		addThisTriple = not (
			(self.offset is not None and self.tripleCount < self.offset) or
		   	(self.limit is not None and self.addedCount >= self.limit))
		self.tripleCount += 1
		if addThisTriple:
			self.addedCount += 1
			if self.batchSize and self.batchCount == self.batchSize:
				self._writeBatch ()
				self.batchCount = 0
			if self.batchCount == 0:
				if self.contextURI:
					self.graph = rdflib.ConjunctiveGraph ("IOMemory",
						rdflib.URIRef (self.contextURI))
				else:
					self.graph = rdflib.ConjunctiveGraph ()
				for name, value in self.bindings.items ():
					self.graph.bind (name, value)
			self.graph.add (triple)
			self.batchCount += 1
			
	def close (self):
		if self.batchCount > 0:
			self._writeBatch ()
		
class FileTripleWriter (TripleWriter):
	def __init__ (self, outputFilename, bindings, outputFormat, contextURI="", batchSize=0):
		TripleWriter.__init__ (self, bindings, outputFormat, contextURI, batchSize)
		self.outputFile = open (outputFilename, 'w')
	
	def _writeBatch (self):
		print >> self.outputFile, self.graph.serialize (format=self.outputFormat)
		
	def close (self):
		TripleWriter.close (self)
		self.outputFile.close ()
		
class BigdataTripleWriter (TripleWriter):
	def __init__ (self, endpoint, delete, bindings, outputFormat, contextURI="", batchSize=0):
		TripleWriter.__init__ (self, bindings, outputFormat, contextURI, batchSize)
		self.endpoint = endpoint
		self.delete = delete
		print "..Uploading data for context %s to %s" % (contextURI, endpoint)
		if self.delete:
			print "..Purging context %s from %s" % (contextURI, endpoint)
			request = RequestWithMethod ("DELETE", endpoint + "?" +
				urllib.urlencode ({"c": "<" + contextURI + ">"}))
			request.add_header ("Accept", "application/xml")
			#request.add_data(urllib.urlencode ({"c": "<" + contextURI + ">"}))
			u = self._makeUpdateRequest (request)
			print "..Context purged, %s records(s) in %s milliseconds" %\
				(u ["modified"], u ["milliseconds"])
	
	def _writeBatch (self):
		request = RequestWithMethod ("POST", endpoint + "?" +
			urllib.urlencode ({"context-uri": contextURI}))
		#request = RequestWithMethod ("PUT", endpoint)
		request.add_header ("Accept", "application/xml")
		#request.add_header ("Content-Type", "text/x-nquads")
		#request.add_data(self.graph.serialize (format="nquads"))
		request.add_header ("Content-Type", "text/plain")
		request.add_data(self.graph.serialize (format="nt"))
		u = self._makeUpdateRequest (request)
		print "..Batch of %s records(s) uploaded in %s milliseconds" %\
			(u ["modified"], u ["milliseconds"])
			
	def _makeUpdateRequest (self, request):
		try:
			response = urllib2.urlopen (request)
			responseText = response.read ()
			xpc = libxml2Util.XPC (libxml2.parseDoc (responseText))
			return {
				"modified": xpc.getAttribute("self::data/@modified"),
				"milliseconds": xpc.getAttribute("self::data/@milliseconds")
			}
		except exceptions.Exception, error:
			print "--Server response: %s" % (error.read ())
			raise SSS2RDFError, "HTTP Update Error: %s" % error
		
class NullTripleWriter (TripleWriter):
	def __init__ (self, bindings, outputFormat, contextURI="", batchSize=0):
		TripleWriter.__init__ (self, bindings, outputFormat, contextURI, batchSize)

def makeQuery ():
		request = RequestWithMethod ("POST", endpoint + "?" +
			urllib.urlencode ({"query": queryArguments}))
		#request = RequestWithMethod ("PUT", endpoint)
		request.add_header ("Accept", "application/xml")
		#request.add_header ("Content-Type", "text/x-nquads")
		#request.add_data(self.graph.serialize (format="nquads"))
		request.add_header ("Content-Type", "text/plain")
		request.add_data(self.graph.serialize (format="nt"))
		u = self._makeUpdateRequest (request)
		print "..Batch of %s records(s) uploaded in %s milliseconds" %\
			(u ["modified"], u ["milliseconds"])

if __name__ == "__main__":
	import sys
	import os.path
	import getopt
	import sssxmlschema
	import datetime
		
	version = 0.1
	showVersion = False
	outputFilename = ""
	outputFormat = "json"
	store = "bigdata"
	endpoint = ""
	maxTime = None
	contextURI = None
	
	try:
		optlist, args = getopt.getopt(sys.argv[1:], 'e:f:q:o:s:vm:c:')
		for (option, value) in optlist:
			if option == "-e":
				endpoint = value
			if option == "-f":
				outputFormat = value
			if option == "-o":
				outputFilename = value
			if option == "-s":
				store = value
			if option == "-v":
				showVersion = True
			if option == "-m":
				maxTime = int (value)
			if option == "-c":
				contextURI = value

		if showVersion:
			print "..rdfutil version %s" % version

		if len (args) > 2:
			raise RDFUtilError, "Invalid arguments"
		if len (args):
			query = args [0]
			if query.startswith ("@"):
				query = open (query).readlines ()
		else:
			query = None
		if len (args) > 1:
			query = query % urllib.urldecode(queryArguments)

		if store == "bigdata":
			if not endpoint:
				endpoint = "http://localhost:8080/bigdata/sparql"
			print "..Accessing %s" %\
				(endpoint,)
			request = RequestWithMethod ("POST", endpoint)
			if outputFormat == "json":
				desiredType = "application/sparql-results+json"
			elif outputFormat == "n3":
				desiredType = "text/rdf+n3"
			else:
				raise RDFUtilError,\
					"Unsupported output format %s" % outputFormat
			request.add_header ("Accept", desiredType)
			if maxTime:
				request.add_header ("X-BIGDATA-MAX-QUERY-MILLIS",
					str (maxTime))
			data = {"query": query}
			if contextURI is not None:
				data ["default-graph-uri"] = contextURI
			request.add_data (urllib.urlencode(data))
			try:
				response = urllib2.urlopen (request)
				responseText = response.read ()
				if outputFilename:
					outputFile = open (outputFilename, 'w')
					print >>outputFile, responseText
					outputFile.close ()
				else:
					print responseText
			except exceptions.Exception, error:
				if error is urllib2.HTTPError:
					print "--HTTPError %d: %s" % (error.code, error.read ())
					raise SSS2RDFError, "SPARQL error: %s" % error
				else:
					print "--Exception accessing server: %s" % error
		else:
			raise RDFUtilError, "Unknown store type '%s'" % store
			
	except exceptions.Exception, e:
			print "--rdfutil error: %s" % e
			print "  rdfutil query query-args"
			sys.exit (0)

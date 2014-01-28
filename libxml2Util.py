import libxml2
import exceptions

class XMLError (exceptions.Exception): pass
			
def fromUTF (text):
	return unicode (text, "utf-8")
	
def toUTF (text):
	return text.encode ("utf-8")

class XMLFile:

	def __init__ (self, filename=None):
		self.filename = filename
		self.changed = False

	def load (self):
		import libxml2Util
		import libxml2
		doc = libxml2.parseFile(self.filename)		
		xpc = libxml2Util.XPC (doc)
		self.deserialise(xpc)
		doc.freeDoc()

	def save (self):
		import libxml2Util
		import libxml2
		outputDoc = libxml2.newDoc("1.0")
		self.serialise (outputDoc)
		result = outputDoc.serialize("ascii", 1)
		outputDoc.freeDoc()
		file = open(self.filename, "w")
		file.write (result)
		file.close ()
		print "..Updated", self.filename
		self.changed = False
		
	def isChanged (self):
		return self.changed

def forceEncoding (text, encoding='ascii'):
	try:
		text = unicode(text)
		return text.encode (encoding)
	except UnicodeError:
		lchars = []
		for char in text:
			try:
				lchars.append(char.encode(encoding))
			except UnicodeError:
				lchars.append("&#%d;" % ord(char))				
		return ''.join(lchars)
				
def wrapXML (object):
	outputDoc = libxml2.newDoc("1.0")
	object.XML (outputDoc)
	result = outputDoc.serialize(None, 1)
	outputDoc.freeDoc()
	return result
	
def intOrNone (text):
	if text is None or len(text) == 0: return None
	return int(text)
		
def booleanOrNone (text):
	if text is None or len(text) == 0: return None
	if text[0] in ('y', 'Y', 't', 'T'): return True
	if text[0] in ('n', 'N', 'f', 'F'): return False
	try:
		i = int(text)
		if i == 1: return True
		if i == 0: return False
	except:
		pass
		
class XPC:
	def __init__ (self, doc, namespaces={}):
		self.doc = doc
		self.xpc = doc.xpathNewContext()
		for name, value in namespaces.items():
			self.xpc.xpathRegisterNs (name, value)
		self.rootNode = doc.getRootElement()
		self.currentNode = self.rootNode
		self.xpc.setContextNode (self.rootNode)
		here = self.xpc.xpathEval ("/*") # seems to be necessary initially

	def __del__(self):
		self.xpc.xpathRegisteredNsCleanup()
		self.xpc.xpathFreeContext()
			
	def eval (self, path, node=None):
		if node is None:
			node = self.rootNode
		if node != self.currentNode:
			#print "setting current node to", node 
			self.xpc.setContextNode (node)
			self.currentNode = node
		#print "Evaluate '%s' at %s:%s" % (path, self.currentNode.type, self.currentNode.name)
		return self.xpc.xpathEval (path)

	def hasSingleNode (self, path, node=None):
		nodes = self.eval (path, node)
		return len(nodes) == 1
	
	def requireSingleNode (self, path, node=None):
		nodes = self.eval (path, node)
		if len(nodes) == 1:
			return nodes[0]
		elif len(nodes) == 0:
			raise XMLError, "XPath (%s) didn't return any nodes" % path
		else:
			raise XMLError, "XPath (%s) returned %d nodes" % (path, len(nodes))

	def getTextNode (self, path="text()", node=None):
		nodes = self.eval (path+"/text()", node)
		if len(nodes) == 0:
			return ""
		elif len(nodes) == 1:
			return fromUTF(nodes[0].content)
		else:
			raise XMLError, "XPath (%s) returned %d nodes" % (path, len(nodes))
			
	def requireTextNode (self, path, node=None):
		return fromUTF(self.requireSingleNode (path+"/text()", node).content.strip())
		
	def getIntNode (self, path, node=None):
		content = self.requireSingleNode (path, node).content
		try:
			return int(content)
		except:
			raise XMLError, "XPath (%s) returned non-integer value '%s'" %\
				(path, content)
		
	def getFloatNode (self, path, node=None):
		content = self.requireSingleNode (path, node).content
		try:
			return float(content)
		except:
			raise XMLError, "XPath (%s) returned non-float value '%s'" %\
				(path, content)
				
	def getIntNodes (self, path, node=None):
		try:
			return [int(n.content) for n in self.eval (path, node)]
		except:
			raise XMLError, "XPath (%s) returned non-integer" % path
				
	def getFloatNodes (self, path, node=None):
		try:
			return [float(n.content) for n in self.eval (path, node)]
		except:
			raise XMLError, "XPath (%s) returned non-float" % path
				
	def getTextNodes (self, path, node=None):
		for n in self.eval (path, node): print n
		return [fromUTF(n.content.strip())
				for n in self.eval (path + "/text()", node)]
	
	def getAttribute (self, path, node=None, default=None):
		attributes = self.eval (path, node)
		if len(attributes) == 1:
			return fromUTF(attributes[0].content)
		else:
			return default
			
	def requireAttribute (self, path, node=None):
		attribute = self.getAttribute (path, node, None)
		if attribute is None:
			raise XMLError, "XPath (%s) didn't return attribute" % path
		return attribute	
		
if __name__ == "__main__":
	doc = libxml2.parseDoc("""<?xml version="1.0" encoding="iso-8859-1"?>
<test name="xxx">
	<innertest seq="1">
		<innerinnertest>Hi!</innerinnertest>
	</innertest>
	<innertest seq="2">
	</innertest>
	<i>1</i><i>2</i><i>3</i><i>i</i>
</test>
""")
	xpc = XPC (doc, {})
	print xpc.requireSingleNode ("self::*")
	print xpc.requireAttribute ("@name")
	print xpc.getTextNode ("innertest[@seq='1']/innerinnertest")
	innertest = xpc.requireSingleNode ("innertest[@seq='1']")
	print xpc.getTextNode("innerinnertest", innertest)
	print xpc.getTextNodes("i[position() < 4]")
	print xpc.getIntNodes("i[position() < 4]")
	print xpc.getFloatNodes("i[position() < 4]")

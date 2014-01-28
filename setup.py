# setup.py for savschema

import sys

from distutils.core import setup
import py2exe
import os.path

includes = ['encodings', 'encodings.*']

options = {
	"py2exe": {
		'bundle_files': 1,
		'compressed': True,
		"includes": includes
	}
}

setup(
      console=["savschema.py"],
      author="Iain MacKay",
      author_email="iain@computable-functions.com",
      contact="Iain MacKay",
      options=options,
      contact_email="support@computable-functions.com",
      description="savschema - import .sav data into triple-S",
      name="sav2sss",
      zipfile=None,
      version="0.1")

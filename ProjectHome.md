Documentation and downloads may be found on the Wiki home page https://code.google.com/p/sav2sss/wiki/Usage.

The .sav file format has no publicly available specification so this software cannot be offered with any guarantee, either that it can convert any specific .sav file, or that any conversion is complete or accurate. All usage is entirely at the users risk. It is provided as open source with an MIT license in the hope that others with particular knowledge of the format may submit corrections or enhancements.

The distribution includes very lightly documented sources for:
schema: a Python abstraction of a survey data set and its metadata
sssxmlschema: a realisation of schema for triple-S XML (read and write)
savschema: a realisation of schema for .sav files (read only)

The source code provided is a platform for the Python developer to convert .sav files to other survey data formats, or to and from Triple-S XML data sets to other formats, as well as the primary purpose here to convert SPSS data to Triple-S. It is hoped but of course not required that any extensions to this software will be offered as open-source in the same spirit of open-ness and mutual benefit.

For instance an IBMSPSSSchema would be welcome, particularly if it were free of the restrictions inherent in http://pic.dhe.ibm.com/infocenter/spssdc/v7r0m0/index.jsp?topic=%2Fcom.spss.ddl%2Fmrpunch_write.htm
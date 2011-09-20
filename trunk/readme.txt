savchema - command line utility to convert SPSS (R) .sav files to triple-S XML

 Copyright (C) 2009 Computable Functions Limited, UK

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>

Purpose

The savschema utility converts an SPSS .sav file to triple-S XML metadata and data.
The utility is written based on the description of the .sav file format to be found at

http://cvs.savannah.gnu.org/viewvc/*checkout*/pspp/doc/dev/system-file-format.texi?root=pspp&revision=1.2&content-type=text%2Fplain

The description is unsupported and unendorsed by SPSS and so the results cannot be warranted in any way.
savschema with the ‘full’ option produces a frequency distribution of data values,
which may be checked against known totals for the dataset.

Running savschema

savschema must be executed from a command prompt:

\Path to CSV2SS installation folder\savschema [-ooutputEncoding] [-v] [-s] [-f] SAV-file

The -v switch if specified displays the savschema version number.

The -s switch disables "sensible string lengths". This is an option useful for data sets coming from Quancept (R) which may have extremely long string variable lengths. By default each long string variable is reduced to a length no greater than the next power of 2 greater than the maximum size found in the file.

The -f switch enables "full" output that includes:
-	A description of the information about each variable found in the file
-	A listing of the value labels found in the file
-	A frequency distribution for the variables in the file

The -o switch specifies the encoding to be used in the output data file, by default iso-8859-1
(which should be fine for English-speaking Windows users).
Sav files have the ability to store text in several different encodings internally.
This should be retrieved correctly by savschema but it has not been tested with a wide variety of character sets.
Characters from the sav file that are not representable in the specified output encoding are rendered
in the data file as ? and in the XML as entity references.

Known issues

-	Values marked as being in time/date format in the sav file are not translated.
        The timestamp values in the files seem to be well outside the Unix epoch.
        So time/date format values are translated as missing values. 
        NB: character strings recording time and/or date are not affected;only variables
        explicitly defined as time/date values.
-	The above may be an instance of a more general problem that some floating-point values
	in .sav files seem to be eleven times larger than one would expect,
	depending on the context in the sav file. 
-	Numeric fields are assigned digits and decimal places based on a combination of
        the information about formats in the sav file and the actual values found.

Using the source

-	savschema uses the XML library libxml2 (http://xmlsoft.org/python.html)
-	savschema uses the psyco accelerator (http://psyco.sourceforge.net/)

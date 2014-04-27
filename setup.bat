rem batch script to run setup.py with approprate options
set version=savschema-0.6

rem create initial distribution

rmdir .\%version% /s/q
rmdir .\build /s/q
c:\python26\python setup.py py2exe --dist-dir=%version% --packages encodings
rmdir .\build /s/q
rmdir .\output /s/q
mkdir .\output
copy readme.html .\output\*
move /y .\savschema-0.6\savschema.exe .\output\sav2sss.exe
rmdir .\savschema-0.6 /s/q

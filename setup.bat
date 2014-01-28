rem batch script to run setup.py with approprate options
set version=savschema-0.1

rem create initial distribution

del .\%version%\* /s/q
del .\build\* /s/q
c:\python26\python setup.py py2exe --dist-dir=%version% --packages encodings
del .\build\* /s/q
move /y .\savschema-0.1\savschema.exe .
ren .\savschema.exe sav2sss.exe
rmdir .\build /s/q
rmdir .\savschema-0.1 /s/q
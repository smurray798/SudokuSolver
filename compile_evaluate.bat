pyinstaller -F python\evaluate.py
copy dist\evaluate.exe evaluate.exe
del evaluate.spec
rmdir dist /Q /S
rmdir build /Q /S
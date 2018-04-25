PYTHON = python
PIP = pip3
PYINST = pyinstaller
INNOSETUP = "c:\Program Files (x86)\Inno Setup 5\ISCC.exe"

dependencies:
	python -m pip install --upgrade pip
	pip install PyQt5
	pip install PyYAML
	pip install reportlab
	pip install markdown
	pip install PyMySQL
	pip install ply
	pip install pyinstaller
	#pip install https://github.com/bjones1/pyinstaller/archive/pyqt5_fix.zip

binary:
	$(PYINST) --onefile --noconsole --icon resources/icons/olive.ico olive.py
	cp -r conf dist/
	cp -r resources dist/
	cp -r collections dist/
	mkdir dist/p2w
	mkdir dist/yacpdb
	mkdir dist/yacpdb/indexer
	cp yacpdb/indexer/indexer.md dist/yacpdb/indexer/indexer.md

inno: binary
	$(INNOSETUP) olive.iss

clean:
	rm -f dist/
	rm -f build/
    rm -f olive.spec
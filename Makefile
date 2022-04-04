PIP = pip3
PYINST = pyinstaller
INNOSETUP = "c:\Program Files (x86)\Inno Setup 6\ISCC.exe"
RCC = pyrcc5

dependencies:
	$(PIP) install PyQt5
	$(PIP) install PyYAML
	$(PIP) install reportlab
	$(PIP) install markdown
	$(PIP) install PyMySQL
	$(PIP) install ply
	$(PIP) install pyinstaller
	$(PIP) install jsonschema
	$(PIP) install Unidecode
	$(PIP) install requests
	$(PIP) install pystache

resources.py: resources/olive.qrc
	$(RCC) -o resources.py resources/olive.qrc

dist/olive.exe: clean resources.py
	$(PYINST) --onefile --noconsole --icon resources/icons/olive.ico olive.py

clean:
	rm -rf dist/
	rm -rf build/
	rm -f olive.spec
	rm -f resources.py

inno: dist/olive.exe olive.iss
	$(INNOSETUP) olive.iss


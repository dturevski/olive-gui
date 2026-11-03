PIP = pip3
PYINST = pyinstaller
INNOSETUP = "c:\Program Files (x86)\Inno Setup 6\ISCC.exe"
RCC = pyrcc5

.PHONY: dependencies build-dependencies clean inno

dependencies:
	$(PIP) install -r requirements.txt

build-dependencies:
	$(PIP) install -r requirements-build.txt

resources.py: resources/olive.qrc
	$(RCC) -o resources.py resources/olive.qrc

dist/olive.exe: clean resources.py
	$(PYINST) -p ./ --onefile --collect-data yacpdb --noconsole --icon resources/icons/olive.ico olive.py

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf __pycache__/
	rm -f olive.spec
	rm -f resources.py

inno: dist/olive.exe olive.iss
	$(INNOSETUP) olive.iss


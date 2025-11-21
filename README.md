## Synopsis

Olive is a free open source cross-platform graphical front-end for 
[Popeye](https://github.com/thomas-maeder/popeye) and
Chest with strong support for typesetting chess diagrams and solutions.


## Name
Olive is named after the fictional character Olive Oyl, girlfriend of Popeye the Sailor.

## Installation

### Installing from Git (Windows/Linux/MacOS)

The prerequisites are Python3 (with pip), git and make. Clone the repository and from the repository
root run

`sudo make dependencies`

`make resources.py`

Then olive can be started with

`python3 olive.py`

If you want to use Popeye/Chest with Olive (you probably do), then these programs
must be installed separately.

### Binaries

For single binary complilation pyrcc5 library for your distribution is required to manage Qt5 resources
Example for Ubuntu/Debian:
- pyqt5-dev-tools

#### Commands:
- (Optionally setup venv)
- pip install -r requirements.txt
- pyrcc5 -o resources.py resources/olive.qrc
- pyinstaller olive.unx.spec --clean
- pyinstaller olive.mac.spec --clean
- Place matching `py` popeye (Linux x86-64 ELF / Darwin ARM64) binary into the `build` directory: `build/py`


The binary packages for Windows are available under the
[Releases](https://github.com/dturevski/olive-gui/releases).
They already include the compiled windows version of Popeye and WinChest.

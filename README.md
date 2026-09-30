## Synopsis

Olive is a free, open-source, cross-platform graphical front end for
[Popeye](https://github.com/thomas-maeder/popeye) and
Chest with strong support for typesetting chess diagrams and solutions.


## Name

Olive is named after the fictional character Olive Oyl, the girlfriend of Popeye the Sailor.

## Installation

### Installing from Git (Windows/Linux/macOS)

The prerequisites are Python 3 (with pip), Git, and Make. Clone the repository and create a virtual environment:

```
git clone https://github.com/dturevski/olive-gui.git
cd olive-gui
python3 -m venv venv
source venv/bin/activate
```
Then run:

```
make dependencies
make resources.py
```
Start Olive with:

`python3 olive.py`

If you want to use Popeye or Chest with Olive (you probably do), these programs
must be installed separately.

### Binaries

To build a single binary, you need the `pyrcc5` tool for your distribution to manage Qt 5 resources.
For example, on Ubuntu/Debian, install `pyqt5-dev-tools`.

#### Commands

- Optionally, set up a virtual environment.
- `pip install -r requirements.txt`
- `pyrcc5 -o resources.py resources/olive.qrc`
- `pyinstaller olive.unx.spec --clean`
- `pyinstaller olive.mac.spec --clean`
- Place the matching Popeye binary named `py` (Linux x86-64 ELF / Darwin ARM64) in the `build` directory: `build/py`.


The binary packages for Windows are available on the
[Releases page](https://github.com/dturevski/olive-gui/releases).
They already include the compiled Windows versions of Popeye and WinChest.

## Editing configuration

Use **File → Configuration** to open `main.yaml`, `popeye.yaml`, or `chest.yaml`
in the application associated with YAML files. The same menu can open the
configuration folder or reload settings manually. In a packaged Windows build,
the files are under `%LOCALAPPDATA%/Olive/conf`; source builds use `conf`.

Saving a file automatically reloads its settings after a short delay. Fonts,
language, fairy pieces, toolbar options, and solver controls update without a
restart. Solver launch settings apply to the next run; an active Popeye run keeps
its existing output limit and communication log. Generated Popeye input follows
changes to sticky options; hand-edited input and solver output are preserved.

Invalid YAML or invalid settings leave the last valid configuration active. The
status bar shows the error; **Reload configuration** displays its full details.
Fix and save the file to retry. Invalid files are never overwritten at shutdown.

Olive merges GUI changes with external edits when reloading and again before
saving on exit. External edits win when both have changed the same setting;
unrelated GUI changes are retained. Files are only rewritten if GUI changes need
saving, so comments and formatting survive when no write is needed. A rewritten
file uses Olive's YAML formatting and does not preserve comments.

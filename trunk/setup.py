from distutils.core import setup
import py2exe
from glob import glob
import sys

sys.path.append("C:\\Users\\Dima\\Downloads\\test\\x86_Microsoft.VC90.CRT")

data_files = [("Microsoft.VC90.CRT", glob(r'C:\Users\Dima\Downloads\test\x86_Microsoft.VC90.CRT\*.*'))]
    
setup(data_files=data_files, windows=[{"script":"olive.py", "icon_resources": [(0, "olive.ico")]}], options={"py2exe":{"includes":["sip"]}})
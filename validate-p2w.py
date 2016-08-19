import base
import yaml


from p2w.parser import parser

s = """
a) 1.h2*g1=Q[+wBd8] Ra4-c4 2.Bc5-f8 Bd8*b6[+bPc1=Q] # b) bPg7-->g4 1.Sb2*a4[+wRg8] Bg1-e3 2.Re4-e7 Rg8*g4[+bPh1=S] #"""
x = parser.parse(s, debug=1)

# todo: print formatted
# todo: tests
# todo: git!
# todo Node.validate
# todo: validate script
# yacpdb
print yaml.dump(x)





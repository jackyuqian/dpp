#!/usr/local/bin/python3
import  sys, getopt
import  re

# Read Prototxt
context_str = open('t0.txt', 'r').read()
context_lst =re.split(r"([{:}\n\r ])", context_str)

# Build List
while '' in context_lst:
    context_lst.remove('')
while ' ' in context_lst:
    context_lst.remove(' ')
while '\n' in context_lst:
    context_lst.remove('\n')
while '\r' in context_lst:
    context_lst.remove('\r')
  
# Buile Dictionary
def build_dict(mlst, mdict):
    idx = 0
    while True:
        if len(mlst) == 0:
            return mlst, mdict
        elif mlst[0] == '}':
            mlst.pop(0)
            return mlst, mdict
        elif mlst[1] == ':':
            mdict[mlst[0] + '_' + str(idx)]  = mlst[2]
            del mlst[0:3]
        elif mlst[1] == '{':
            nlst, ndict  = build_dict(mlst[2:], {})
            mdict[mlst[0] + '_' + str(idx)]  = ndict
            mlst = nlst
        idx = idx + 1

# Parse Dictionary
def parse_dict(mdict):
    for key in mdict:
        print(key)
    # Find Data Layer

mlst, mdict   =build_dict(context_lst, {})
parse_dict(mdict)

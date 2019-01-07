#!/usr/local/bin/python3
from dpp import instrac
from dpp import prototxt
from dpp import analyze
import  sys, getopt

def usage():
    print('Please Contact Qian.(yuqian@xilinx.com)')

ddr_info    = {
        'bw'    : 19200,
        'eff'   : 0.9
        }

dpu_info    = {
        'bitwide'   : 512,
        'freq'      : 300,
        'ncore'     : 4,
        'ppxli'     : 8,
        'pchni'     : 16,
        'pchno'     : 16,
        'pmisc'     : 4
        }
instr_info  = {
        'LOAD'      : {'color' : '#000000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'LOADFM'    : {'color' : '#B1C914',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'LOADW'     : {'color' : '#B1C000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'SAVE'      : {'color' : '#206FA1',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'CONVINIT'  : {'color' : '#000000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'CONV'      : {'color' : '#A6325A',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'ELEWINIT'  : {'color' : '#000000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'ELEW'      : {'color' : '#FF9900',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'POOL'      : {'color' : '#48A742',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
        'END'       : {'color' : '#000000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10}
        }

opts, args  = getopt.getopt(sys.argv[1:], 'hipf:')
for op, value in opts:
    if op == '-f':
        fname   = value
    elif op == '-i':
        analyze_mode    = 'instrac'
    elif op == '-p':
        analyze_mode    = 'prototxt'
    elif op == '-h':
        usage()
        sys.exit()

if analyze_mode == 'instrac':
    iac = instrac.Instrac(fname, dpu_info)
    instructions_lst    = iac.parse()

    ia  = analyze.Analyze(dpu_info, instr_info, ddr_info)
    ia.analyze_instructions_lst(instructions_lst)
    ia.print_instructions_profile()
elif analyze_mode == 'prototxt':
    ptxt    = prototxt.Prototxt(fname)
    ptxt.parse()
    ptxt.print_info()

#!/usr/local/bin/python3
import  sys, getopt
import  math

# Global Definition
D_DDR_BW        = 19200 # MB/Hz
D_DDR_EFF       = 0.9
D_DPU_FREQ      = 300   # MHz
D_DPU_DATA_W    = 512   # Bits
D_CORE_NUM      = 4
D_WINDOW_IN     = 8
D_CHANNEL_IN    = 16
D_CHANNEL_OUT   = 16
D_MISC_PRLL     = 4
#D_CORE_NUM      = 10
#D_WINDOW_IN     = 4
#D_CHANNEL_IN    = 8
#D_CHANNEL_OUT   = 16
#D_MISC_PRLL     = 1
D_INSTRS        = {
        'LOAD'      : { 'IDX' : 0,  'COLOR' : '#B1C914',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10},
        'SAVE'      : { 'IDX' : 1,  'COLOR' : '#206FA1',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10},
        'CONVINIT'  : { 'IDX' : 2,  'COLOR' : '#000000',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10},
        'CONV'      : { 'IDX' : 2,  'COLOR' : '#A6325A',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10},
        'ELEWINIT'  : { 'IDX' : 3,  'COLOR' : '#000000',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10},
        'ELEW'      : { 'IDX' : 3,  'COLOR' : '#FF9900',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10},
        'POOL'      : { 'IDX' : 3,  'COLOR' : '#48A742',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10},
        'END'       : { 'IDX' : 1,  'COLOR' : '#000000',    'EFF' : 0.9, 'FOH' : 10, 'BOH' : 10}}

# Global Variable
instructions    = []

#Print Help
#
def usage():
    print('Please Contact Qian.(yuqian@xilinx.com)')

# Parse File "instr_ac.txt"
# Return Instructions Dictionary
#
def parse_instr_ac(fname):
    global instructions
    for line in open(fname, 'r'):
        instr_list  = line.strip().split(' ')
        if instr_list[0] in D_INSTRS:
            instr_dict   = {}
            instr_dict['name']  = instr_list.pop(0)
            instr_dict['dpdon'] = instr_list.pop(0)
            instr_dict['dpdby'] = instr_list.pop(0)
            instr_dict.update(dict(zip(instr_list[0::2], [int(x) for x in instr_list[1::2]])))
            instructions.append(instr_dict)

def calc_instr():
    global instructions
    convinit_vpp    = 0
    convinit_krnlh  = 0
    convinit_krnlw  = 0
    for instr in instructions:
        if instr['name'] == 'LOAD' and instr['mode'] == 0:
            instr['ops_exp']    = instr['channel'] * instr['length'] * D_CORE_NUM
            instr['ops_act']    = instr['jump_read'] * instr['length'] * D_CORE_NUM
            instr['time_exp']   = 1.0 * instr['ops_exp'] / (D_DPU_DATA_W * D_DPU_FREQ / 8)
            instr['time_act']   = 1.0 * instr['ops_act'] \
                                   / min(D_DPU_DATA_W * D_DPU_FREQ / 8, D_DDR_BW * D_DDR_EFF) \
                                   / D_INSTRS[instr['name']]['EFF'] # Load Engine Limit
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name'] == 'LOAD' and instr['mode'] == 1:
            instr['ops_exp']    = instr['channel'] * instr['length'] * D_CHANNEL_OUT
            instr['ops_act']    = instr['jump_read'] * instr['length'] * D_CHANNEL_OUT # Discard output channel isn't an integer number of D_CHANNEL_OUT
            instr['time_exp']   = 1.0 * instr['ops_exp'] / (D_DPU_DATA_W * D_DPU_FREQ / 8)
            instr['time_act']   = 1.0 * instr['ops_act'] \
                                   / min(D_DPU_DATA_W * D_DPU_FREQ / 8, D_DDR_BW * D_DDR_EFF) \
                                   / D_INSTRS[instr['name']]['EFF'] # Load Engine Limit
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name']  == 'SAVE':
            instr['ops_exp']    = instr['channel'] * instr['length'] * D_CORE_NUM
            instr['ops_act']    = instr['jump_read'] * instr['length'] * D_CORE_NUM
            instr['time_exp']   = 1.0 * instr['ops_exp'] / (D_DPU_DATA_W * D_DPU_FREQ / 8)
            instr['time_act']   = 1.0 * instr['ops_act'] \
                                   / min(D_DPU_DATA_W * D_DPU_FREQ / 8, D_DDR_BW * D_DDR_EFF) \
                                   / D_INSTRS[instr['name']]['EFF'] # SAVE Engine Limit
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name']  == 'CONVINIT':
            convinit_vpp        = instr['valid_pixel_parallel']
            convinit_krnlh      = instr['kernel_h']
            convinit_krnlw      = instr['kernel_w']
            instr['ops_exp']    = 0
            instr['ops_act']    = 0
            instr['time_exp']   = 1.0 / D_DPU_FREQ
            instr['time_act']   = 1.0 / D_DPU_FREQ
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name']  == 'CONV':
            instr['ops_exp']    = D_CHANNEL_OUT * instr['length'] * convinit_vpp * convinit_krnlw * convinit_krnlh * (D_CHANNEL_IN * instr['channel_group'] - instr['channel_offset']) * D_CORE_NUM * 2
            instr['ops_act']    = D_CHANNEL_OUT * instr['length'] * convinit_vpp * convinit_krnlw * convinit_krnlh * D_CHANNEL_IN * instr['channel_group'] * D_CORE_NUM * 2
            instr['time_exp']   = 1.0 * instr['ops_exp'] / (D_CHANNEL_IN * D_CHANNEL_OUT * D_WINDOW_IN * D_CORE_NUM * 2) / D_DPU_FREQ
            instr['time_act']   = 1.0 * instr['ops_act'] / (D_CHANNEL_IN * D_CHANNEL_OUT * D_WINDOW_IN * D_CORE_NUM * 2) / D_DPU_FREQ \
                                    / D_INSTRS[instr['name']]['EFF'] # CONV Engine Limit
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name']  == 'ELEWINIT':
            instr['ops_exp']    = 0
            instr['ops_act']    = 0
            instr['time_exp']   = 1.0 / D_DPU_FREQ
            instr['time_act']   = 1.0 / D_DPU_FREQ
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name']  == 'ELEW':
            instr['ops_exp']    = (instr['num'] - 1) * instr['width'] * instr['channel_group'] * D_CHANNEL_IN * instr['valid_pixel_parallel'] * D_CORE_NUM
            instr['ops_act']    = (instr['num'] - 1) * instr['width'] * instr['channel_group'] * D_CHANNEL_IN * instr['valid_pixel_parallel'] * D_CORE_NUM * 2
            instr['time_exp']   = 1.0 * instr['ops_exp'] / (D_CHANNEL_IN * D_MISC_PRLL * D_CORE_NUM) / D_DPU_FREQ 
            instr['time_act']   = 1.0 * instr['ops_act'] / (D_CHANNEL_IN * D_MISC_PRLL * D_CORE_NUM) / D_DPU_FREQ \
                                    / D_INSTRS[instr['name']]['EFF'] # MISC Engine Limit
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name']  == 'POOL':
            instr['ops_exp']    = instr['kernel_w'] * instr['kernel_h'] *  instr['length'] * instr['channel_group'] * D_CHANNEL_IN * instr['valid_pixel_parallel'] * D_CORE_NUM
            instr['ops_act']    = instr['kernel_w'] * instr['kernel_h'] *  instr['length'] * instr['channel_group'] * D_CHANNEL_IN * instr['valid_pixel_parallel'] * D_CORE_NUM
            instr['time_exp']   = 1.0 * instr['ops_exp'] / (D_CHANNEL_IN * D_MISC_PRLL * D_CORE_NUM) / D_DPU_FREQ 
            instr['time_act']   = 1.0 * instr['ops_act'] / (D_CHANNEL_IN * D_MISC_PRLL * D_CORE_NUM) / D_DPU_FREQ \
                                    / D_INSTRS[instr['name']]['EFF'] # MISC Engine Limit
            instr['eff']        = instr['time_exp'] / instr['time_act']
        elif instr['name']  == 'END':
            instr['ops_exp']    = 0
            instr['ops_act']    = 0
            instr['time_exp']   = 1.0 / D_DPU_FREQ
            instr['time_act']   = 1.0 / D_DPU_FREQ
            instr['eff']        = instr['time_exp'] / instr['time_act']

def analyse_perf():
    global instructions
    # dpdby_matrix[a][b] means: instr_a depend by instr_b, the value is runtime of instr_a
    # 0-LOAD, 1-SAVE, 2-CONV, 3-MISC
    dpdby_matrix    = [[[],[],[],[]],[[],[],[],[]],[[],[],[],[]],[[],[],[],[]]]
    time_line       = [0.0, 0.0, 0.0, 0.0]
    instr_num       = [0, 0, 0, 0]
    instr_ops       = [0, 0, 0, 0]
    instr_time      = [0.0, 0.0, 0.0, 0.0]
    for instr in instructions:
        #print(instr)
        # Can Execute?
        time_line_tmp   = time_line[D_INSTRS[instr['name']]['IDX']]
        for idx in range(4):
            if instr['dpdon'][idx] == '1':
                time_line_tmp   = max(time_line_tmp, dpdby_matrix[3-idx][D_INSTRS[instr['name']]['IDX']].pop(0))

        if instr['dpdon'] == '0000':
            instr['start']  = time_line[D_INSTRS[instr['name']]['IDX']] + D_INSTRS[instr['name']]['FOH'] / D_DPU_FREQ
        else:
            instr['start']  = time_line_tmp + D_INSTRS[instr['name']]['FOH'] / D_DPU_FREQ

        time_line[D_INSTRS[instr['name']]['IDX']]   = instr['start'] + instr['time_act'] + D_INSTRS[instr['name']]['BOH'] / D_DPU_FREQ

        # Execute Done!
        for idx in range(4):
            if instr['dpdby'][idx] == '1':
                dpdby_matrix[D_INSTRS[instr['name']]['IDX']][3-idx].append(time_line[D_INSTRS[instr['name']]['IDX']])
        
        if instr['name'] == 'END' and dpdby_matrix == [[[],[],[],[]],[[],[],[],[]],[[],[],[],[]],[[],[],[],[]]]:
            print("Execute Done!")
            break
        instr_num[D_INSTRS[instr['name']]['IDX']]   = instr_num[D_INSTRS[instr['name']]['IDX']] + 1
        instr_ops[D_INSTRS[instr['name']]['IDX']]   = instr_ops[D_INSTRS[instr['name']]['IDX']] + instr['ops_exp']
        instr_time[D_INSTRS[instr['name']]['IDX']]  = instr_time[D_INSTRS[instr['name']]['IDX']] + instr['time_act']

    print ('[%s]\t\tNumber\t\tOperations\t\tTime(us)' % cname)
    print ('[%s] LOAD\t%14d\t\t%10d\t\t%8.3f'  % (cname, instr_num[0], instr_ops[0], instr_time[0]))
    print ('[%s] SAVE\t%14d\t\t%10d\t\t%8.3f'  % (cname, instr_num[1], instr_ops[1], instr_time[1]))
    print ('[%s] CONV\t%14d\t\t%10d\t\t%8.3f'  % (cname, instr_num[2], instr_ops[2], instr_time[2]))
    print ('[%s] MISC\t%14d\t\t%10d\t\t%8.3f'  % (cname, instr_num[3], instr_ops[3], instr_time[3]))
    print ('---')
    print ('[%s] Runtime:\t%8.3f\n' % (cname, max(time_line[0], time_line[1], time_line[2], time_line[3])))


def print_prof():
    f   = open('dprof.js', 'w')
    print('function dprof() { return [', file = f)
    for instr in instructions:
        idx     = D_INSTRS[instr['name']]['IDX']
        color   = D_INSTRS[instr['name']]['COLOR']
        name    = instr['name']
        start   = instr['start']
        time    = instr['time_act']
        end     = start + time
        ops     = instr['ops_exp']
        eff     = instr['eff']
        print("{name:'%s',itemStyle:{normal: {color:'%s'}},value:[%d,%f,%f,%f,%d,%f]}," % (name, color, idx, start, end, time, ops, eff), file=f)
    print('];};', file = f)
    f.close()



#
# Main Function
#
opts, args  = getopt.getopt(sys.argv[1:], 'hf:c:')
fname   = "instr_ac.txt"
cname   = "default"
for op, value in opts:
    if op == '-f':
        fname   = value
    elif op == '-c':
        cname   = value
    elif op == '-h':
        usage()
        sys.exit()

parse_instr_ac(fname)
calc_instr()
analyse_perf()
print_prof()


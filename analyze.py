#!/usr/local/bin/python3
import  sys
import  getopt
import  math

# Global Definition
D_BANDWIDTH         = 19200 # MB/Hz
D_FREQUENCY         = 350   # MHz
D_CORE_NUM          = 10
D_WINDOW_IN         = 4
D_CHANNEL_IN        = 8
D_CHANNEL_OUT       = 16
D_LOAD_INTERVAL     = 20    # Cycles
D_SAVE_INTERVAL     = 35    # Cycles
D_CONV_INTERVAL     = 50    # Cycles
D_MISC_INTERVAL     = 10    # Cycles

#Print Help
#
def usage():
    print('Please Contact Qian.(yuqian@xilinx.com)')

def ddr_efficiency(ops):
    if ops > 40960:
        return 0.6
    elif ops > 20480:
        return 0.4
    elif ops > 10240:
        return 0.3
    else:
        return 0.2

# Parse File "instr_ac.txt"
# Return Instructions List
#
def parse_instr_ac(fname):
    instructions    = []
    convinit_krnlh  = 0
    convinit_krnlw  = 0
    convinit_pp     = 0

    for line in  open(fname, 'r'):
        instr_in    = line.strip().split(' ')
        if instr_in[0] == 'LOAD':
            instr_out   = {
                'NAME'  : None,
                'DPDON' : None,
                'DPDBY' : None,
                'MODE'  : None,
                'DJMP'  : None,
                'CHNL'  : None,
                'LEN'   : None,
                'DADDR' : None
                }
            instr_out['NAME']   = instr_in[0]
            instr_out['DPDON']  = instr_in[1]
            instr_out['DPDBY']  = instr_in[2]
            instr_out['MODE']   = int(instr_in[instr_in.index('mode')+1])
            instr_out['DJMP']   = int(instr_in[instr_in.index('jump_read')+1])
            instr_out['CHNL']   = int(instr_in[instr_in.index('channel')+1])
            instr_out['LEN']    = int(instr_in[instr_in.index('length')+1])
            instr_out['DADDR']  = int(instr_in[instr_in.index('ddr_addr')+1])
            instructions.append(instr_out)

        elif instr_in[0] == 'SAVE':
            instr_out   = {
                'NAME'  : None,
                'DPDON' : None,
                'DPDBY' : None,
                'DJMP'  : None,
                'CHNL'  : None,
                'LEN'   : None,
                'DADDR' : None
                }
            instr_out['NAME']   = instr_in[0]
            instr_out['DPDON']  = instr_in[1]
            instr_out['DPDBY']  = instr_in[2]
            instr_out['DJMP']   = int(instr_in[instr_in.index('jump_write')+1])
            instr_out['CHNL']   = int(instr_in[instr_in.index('channel')+1])
            instr_out['LEN']    = int(instr_in[instr_in.index('length')+1])
            instr_out['DADDR']  = int(instr_in[instr_in.index('ddr_addr')+1])
            instructions.append(instr_out)

        elif instr_in[0] == 'CONVINIT':
            convinit_krnlh  = int(instr_in[instr_in.index('kernel_h')+1])
            convinit_krnlw  = int(instr_in[instr_in.index('kernel_w')+1])
            convinit_pp     = int(instr_in[instr_in.index('valid_pixel_parallel')+1])

        elif instr_in[0] == 'CONV':
            instr_out   = {
                'NAME'  : None,
                'DPDON' : None,
                'DPDBY' : None,
                'KRNLH' : None,
                'KRNLW' : None,
                'PP'    : None,
                'CHNLG' : None,
                'CHNLO' : None,
                'LEN'   : None
                }
            instr_out['NAME']   = instr_in[0]
            instr_out['DPDON']  = instr_in[1]
            instr_out['DPDBY']  = instr_in[2]
            instr_out['KRNLH']  = convinit_krnlh 
            instr_out['KRNLW']  = convinit_krnlw
            instr_out['PP']     = convinit_pp 
            instr_out['CHNLG']  = int(instr_in[instr_in.index('channel_group')+1])
            instr_out['CHNLO']  = int(instr_in[instr_in.index('channel_offset')+1])
            instr_out['LEN']    = int(instr_in[instr_in.index('length')+1])
            instructions.append(instr_out)
            
        elif instr_in[0] == 'ELEW':
            instr_out   = {
                'NAME'  : None,
                'DPDON' : None,
                'DPDBY' : None,
                'NUM'   : None,
                'WIDTH' : None,
                'PP'    : None,
                'CHNLG' : None
                }
            instr_out['NAME']   = instr_in[0]
            instr_out['DPDON']  = instr_in[1]
            instr_out['DPDBY']  = instr_in[2]
            instr_out['NUM']    = int(instr_in[instr_in.index('num')+1])
            instr_out['WIDTH']  = int(instr_in[instr_in.index('width')+1])
            instr_out['PP']     = int(instr_in[instr_in.index('valid_pixel_parallel')+1])
            instr_out['CHNLG']  = int(instr_in[instr_in.index('channel_group')+1])
            instructions.append(instr_out)
    return instructions

# Calculate Number of Operations and Time of Execution
#
def calc_instruction(instr):
    if instr['NAME'] == 'LOAD' and instr['MODE'] == 2:
        ops_exp = instr['LEN'] * instr['CHNL']
        ops_act = math.ceil(((instr['LEN'] - 1) * instr['DJMP'] + instr['CHNL']) / 256.0) * 256
        cyc_exp = ops_exp / 8
        cyc_act = 1.0 * cyc_exp / \
                  0.667 / \
                  min(1, 1.0 * ops_exp / ops_act) + \
                  D_LOAD_INTERVAL
                    
    elif instr['NAME'] == 'LOAD':
        ops_exp = instr['LEN'] * instr['CHNL'] * D_CORE_NUM
        ops_act = math.ceil(((instr['LEN'] - 1) * instr['DJMP'] + instr['CHNL']) / 256.0) * 256 * D_CORE_NUM
        cyc_exp = ops_exp / 8 / D_CORE_NUM
        cyc_act = 1.0 * cyc_exp / \
                  0.667 / \
                  ddr_efficiency(ops_act) / \
                  min(1, 1.0 * ops_exp / ops_act) + \
                  D_LOAD_INTERVAL
    elif instr['NAME'] == 'SAVE':
        ops_exp = instr['LEN'] * instr['CHNL'] * D_CORE_NUM
        ops_act = math.ceil(((instr['LEN'] - 1) * instr['DJMP'] + instr['CHNL']) / 256.0) * 256 * D_CORE_NUM
        cyc_exp = ops_exp / 8 / D_CORE_NUM
        cyc_act = 1.0 * cyc_exp / \
                  0.8 / \
                  ddr_efficiency(ops_act) / \
                  min(1, 1.0 * ops_exp / ops_act) + \
                  D_SAVE_INTERVAL

    elif instr['NAME'] == 'CONV':
        ops_exp = D_CHANNEL_OUT * instr['LEN'] * instr['PP'] * instr['KRNLH'] * instr['KRNLW'] * (D_CHANNEL_IN * instr['CHNLG'] - instr['CHNLO']) * D_CORE_NUM * 2
        ops_act = D_CHANNEL_OUT * instr['LEN'] * instr['PP'] * instr['KRNLH'] * instr['KRNLW'] * D_CHANNEL_IN * D_CORE_NUM * 2
        cyc_exp = ops_exp / (D_CHANNEL_IN * D_CHANNEL_OUT * D_WINDOW_IN * 2) / D_CORE_NUM
        cyc_act = 1.0 * cyc_exp / \
                  min(1, 1.0 * ops_exp / ops_act) + \
                  instr['LEN'] * 4 + \
                  D_CONV_INTERVAL

    elif instr['NAME'] == 'ELEW':
        ops_exp = (instr['NUM'] - 1) * instr['WIDTH'] * instr['CHNLG'] * D_CHANNEL_IN * D_CORE_NUM
        ops_act = ops_exp
        cyc_exp = ops_exp / D_CHANNEL_IN / D_CORE_NUM
        cyc_act = 1.0 * cyc_exp / \
                  min(1, 1.0 * ops_exp / ops_act) / \
                  0.9 + \
                  D_MISC_INTERVAL
    return [ops_exp, ops_act, cyc_exp, cyc_act]

#
def analyse_performance(instructions, cname):
    runtime_load_dpdby_load = [] 
    runtime_load_dpdby_save = [] 
    runtime_load_dpdby_conv = [] 
    runtime_load_dpdby_elew = [] 
    runtime_save_dpdby_load = [] 
    runtime_save_dpdby_save = [] 
    runtime_save_dpdby_conv = [] 
    runtime_save_dpdby_elew = [] 
    runtime_conv_dpdby_load = [] 
    runtime_conv_dpdby_save = [] 
    runtime_conv_dpdby_conv = [] 
    runtime_conv_dpdby_elew = [] 
    runtime_misc_dpdby_load = [] 
    runtime_misc_dpdby_save = [] 
    runtime_misc_dpdby_conv = [] 
    runtime_misc_dpdby_elew = [] 
    
    runtime_load    = 0
    runtime_save    = 0
    runtime_conv    = 0
    runtime_misc    = 0

    num_loadw       = 0
    ops_loadw       = 0
    time_loadw      = 0
                    
    num_loada       = 0
    ops_loada       = 0
    time_loada      = 0
                    
    num_save        = 0
    ops_save        = 0
    time_save       = 0
                    
    num_conv        = 0
    ops_conv        = 0
    time_conv       = 0

    num_elew        = 0
    ops_elew        = 0
    time_elew       = 0

    for instr in instructions:
        [ops_exp, ops_act, cyc_exp, cyc_act] = calc_instruction(instr)
        ops     = ops_exp
        time    = 1.0 * cyc_act / D_FREQUENCY
        if instr['NAME'] == 'LOAD' and instr['MODE'] == 2:
            runtime_tmp = runtime_load
            if instr['DPDON'][3] == '1':
                runtime_tmp = max(runtime_tmp, runtime_load_dpdby_load.pop(0))
            if instr['DPDON'][2] == '1':
                runtime_tmp = max(runtime_tmp, runtime_save_dpdby_load.pop(0))
            if instr['DPDON'][1] == '1':
                runtime_tmp = max(runtime_tmp, runtime_conv_dpdby_load.pop(0))
            if instr['DPDON'][0] == '1':
                runtime_tmp = max(runtime_tmp, runtime_misc_dpdby_load.pop(0))
            if instr['DPDON'] == '0000':
                runtime_load    = runtime_load + time 
            else:
                runtime_load    = runtime_tmp + time 
            
            if instr['DPDBY'][3] == '1':
                runtime_load_dpdby_load.append(runtime_load)
            if instr['DPDBY'][2] == '1':
                runtime_load_dpdby_save.append(runtime_load)
            if instr['DPDBY'][1] == '1':
                runtime_load_dpdby_conv.append(runtime_load)
            if instr['DPDBY'][0] == '1':
                runtime_load_dpdby_elew.append(runtime_load)
            
            num_loadw       = num_loadw + 1
            ops_loadw       = ops_loadw + ops 
            time_loadw      = time_loadw + time 

        elif instr['NAME'] == 'LOAD':
            runtime_tmp = runtime_load
            if instr['DPDON'][3] == '1':
                runtime_tmp = max(runtime_tmp, runtime_load_dpdby_load.pop(0))
            if instr['DPDON'][2] == '1':
                runtime_tmp = max(runtime_tmp, runtime_save_dpdby_load.pop(0))
            if instr['DPDON'][1] == '1':
                runtime_tmp = max(runtime_tmp, runtime_conv_dpdby_load.pop(0))
            if instr['DPDON'][0] == '1':
                runtime_tmp = max(runtime_tmp, runtime_misc_dpdby_load.pop(0))
            if instr['DPDON'] == '0000':
                runtime_load    = runtime_load + time 
            else:
                runtime_load    = runtime_tmp + time 
            
            if instr['DPDBY'][3] == '1':
                runtime_load_dpdby_load.append(runtime_load)
            if instr['DPDBY'][2] == '1':
                runtime_load_dpdby_save.append(runtime_load)
            if instr['DPDBY'][1] == '1':
                runtime_load_dpdby_conv.append(runtime_load)
            if instr['DPDBY'][0] == '1':
                runtime_load_dpdby_elew.append(runtime_load)

            num_loada   = num_loada + 1
            ops_loada   = ops_loada + ops 
            time_loada  = time_loada + time 
        elif instr['NAME'] == 'SAVE':
            runtime_tmp = runtime_save
            if instr['DPDON'][3] == '1':
                runtime_tmp = max(runtime_tmp, runtime_load_dpdby_save.pop(0))
            if instr['DPDON'][2] == '1':
                runtime_tmp = max(runtime_tmp, runtime_save_dpdby_save.pop(0))
            if instr['DPDON'][1] == '1':
                runtime_tmp = max(runtime_tmp, runtime_conv_dpdby_save.pop(0))
            if instr['DPDON'][0] == '1':
                runtime_tmp = max(runtime_tmp, runtime_misc_dpdby_save.pop(0))
            if instr['DPDON'] == '0000':
                runtime_save    = runtime_save + time 
            else:
                runtime_save    = runtime_tmp + time 
            
            if instr['DPDBY'][3] == '1':
                runtime_save_dpdby_load.append(runtime_save)
            if instr['DPDBY'][2] == '1':
                runtime_save_dpdby_save.append(runtime_save)
            if instr['DPDBY'][1] == '1':
                runtime_save_dpdby_conv.append(runtime_save)
            if instr['DPDBY'][0] == '1':
                runtime_save_dpdby_elew.append(runtime_save)

            num_save    = num_save + 1
            ops_save    = ops_save + ops 
            time_save   = time_save + time 
        elif instr['NAME'] == 'CONV':
            runtime_tmp = runtime_conv
            if instr['DPDON'][3] == '1':
                runtime_tmp = max(runtime_tmp, runtime_load_dpdby_conv.pop(0))
            if instr['DPDON'][2] == '1':
                runtime_tmp = max(runtime_tmp, runtime_save_dpdby_conv.pop(0))
            if instr['DPDON'][1] == '1':
                runtime_tmp = max(runtime_tmp, runtime_conv_dpdby_conv.pop(0))
            if instr['DPDON'][0] == '1':
                runtime_tmp = max(runtime_tmp, runtime_misc_dpdby_conv.pop(0))
            if instr['DPDON'] == '0000':
                runtime_conv    = runtime_conv + time 
            else:
                runtime_conv    = runtime_tmp + time 
            
            if instr['DPDBY'][3] == '1':
                runtime_conv_dpdby_load.append(runtime_conv)
            if instr['DPDBY'][2] == '1':
                runtime_conv_dpdby_save.append(runtime_conv)
            if instr['DPDBY'][1] == '1':
                runtime_conv_dpdby_conv.append(runtime_conv)
            if instr['DPDBY'][0] == '1':
                runtime_conv_dpdby_elew.append(runtime_conv)

            num_conv    = num_conv + 1
            ops_conv    = ops_conv + ops 
            time_conv   = time_conv + time 
        elif instr['NAME'] == 'ELEW':
            runtime_tmp = runtime_misc
            if instr['DPDON'][3] == '1':
                runtime_tmp = max(runtime_tmp, runtime_load_dpdby_elew.pop(0))
            if instr['DPDON'][2] == '1':
                runtime_tmp = max(runtime_tmp, runtime_save_dpdby_elew.pop(0))
            if instr['DPDON'][1] == '1':
                runtime_tmp = max(runtime_tmp, runtime_conv_dpdby_elew.pop(0))
            if instr['DPDON'][0] == '1':
                runtime_tmp = max(runtime_tmp, runtime_misc_dpdby_elew.pop(0))
            if instr['DPDON'] == '0000':
                runtime_misc    = runtime_misc + time 
            else:
                runtime_misc    = runtime_tmp + time 
            
            if instr['DPDBY'][3] == '1':
                runtime_misc_dpdby_load.append(runtime_misc)
            if instr['DPDBY'][2] == '1':
                runtime_misc_dpdby_save.append(runtime_misc)
            if instr['DPDBY'][1] == '1':
                runtime_misc_dpdby_conv.append(runtime_misc)
            if instr['DPDBY'][0] == '1':
                runtime_misc_dpdby_elew.append(runtime_misc)

            num_elew    = num_elew + 1
            ops_elew    = ops_elew + ops 
            time_elew   = time_elew + time 

    print ('[%s]\t\t\tNumber\t\tOperations\t\tTime(us)' % cname)
    print ('[%s] LOADW\t%14d\t\t%10d\t\t%8.3f' % (cname, num_loadw, ops_loadw, time_loadw))
    print ('[%s] LOADA\t%14d\t\t%10d\t\t%8.3f' % (cname, num_loada, ops_loada, time_loada))
    print ('[%s] SAVE\t%14d\t\t%10d\t\t%8.3f'  % (cname, num_save,  ops_save,  time_save))
    print ('[%s] CONV\t%14d\t\t%10d\t\t%8.3f'  % (cname, num_conv,  ops_conv,  time_conv))
    print ('---')
    print ('[%s] Runtime:\t%8.3f' % (cname, max(runtime_load, runtime_save, runtime_conv, runtime_misc)))
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

instructions    = parse_instr_ac(fname)
analyse_performance(instructions, cname)


#!/usr/local/bin/python3

class Analyze:
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
            'LOADW'     : {'color' : '#B1C914',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
            'SAVE'      : {'color' : '#206FA1',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
            'CONVINIT'  : {'color' : '#000000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
            'CONV'      : {'color' : '#A6325A',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
            'ELEWINIT'  : {'color' : '#000000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
            'ELEW'      : {'color' : '#FF9900',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
            'POOL'      : {'color' : '#48A742',    'eff' : 0.9, 'foh' : 10, 'boh' : 10},
            'END'       : {'color' : '#000000',    'eff' : 0.9, 'foh' : 10, 'boh' : 10}
            }
    
    instructions_lst    = []

    def __init__(self, dpuinfo, instrinfo, ddrinfo):
        self.dpu_info   = dpuinfo
        self.instr_info = instrinfo
        self.ddr_info   = ddrinfo

    def analyze_instructions_lst(self, instructions_lst):
        # dpdby_matrix[a][b] means: instr_a depend by instr_b, the value is runtime of instr_a
        # 0-LOAD, 1-SAVE, 2-CONV, 3-MISC
        dpdby_matrix    = [[[],[],[],[]],[[],[],[],[]],[[],[],[],[]],[[],[],[],[]]]
        time_line       = [0.0, 0.0, 0.0, 0.0]
        instr_num       = [0, 0, 0, 0]
        instr_ops       = [0, 0, 0, 0]
        instr_time      = [0.0, 0.0, 0.0, 0.0]
        for instr in instructions_lst:
            # Can Execute?
            time_line_tmp   = time_line[instr['id']]
            for idx in range(4):
                if instr['dpdon'][3-idx] == '1':
                    time_line_tmp   = max(time_line_tmp, dpdby_matrix[idx][instr['id']].pop(0))

            instr['start']  = self.instr_info[instr['name']]['foh'] / self.dpu_info['freq'] + \
                    time_line[instr['id']] if instr['dpdon'] == '0000' else time_line_tmp

            # Executing
            if instr['name'] in ['LOADFM', 'LOADW', 'SAVE']:
                instr['eff']    = max(1.0, 1.0 * (self.dpu_info['bitwide'] * self.dpu_info['freq'] / 8) / (self.ddr_info['bw'] * self.ddr_info['eff'])) * \
                        self.instr_info[instr['name']]['eff']
            elif instr['name'] in ['CONVINIT', 'ELEWINIT', 'END']:
                instr['eff']    = 1.0
            elif instr['name'] == 'CONV':
                instr['eff']    = 1.0 * (self.dpu_info['pchni'] * instr['channel_group'] - instr['channel_offset']) / (self.dpu_info['pchni'] * instr['channel_group']) * \
                        self.instr_info[instr['name']]['eff']
            elif instr['name'] == 'ELEW':
                instr['eff']    = 1.0 * self.instr_info[instr['name']]['eff']
            elif instr['name'] == 'POOL':
                instr['eff']    = 1.0 * self.instr_info[instr['name']]['eff']
            
            instr['dur']    = instr['time_exp'] / instr['eff']
            instr['end']    = instr['start'] + instr['dur']

            # Done!
            time_line[instr['id']]  = instr['end'] + self.instr_info[instr['name']]['boh'] / self.dpu_info['freq']
            for idx in range(4):
                if instr['dpdby'][3-idx] == '1':
                    dpdby_matrix[instr['id']][idx].append(time_line[instr['id']])
            
            if instr['name'] == 'END' and dpdby_matrix == [[[],[],[],[]],[[],[],[],[]],[[],[],[],[]],[[],[],[],[]]]:
                print("Execute Done!")
                break
            instr_num[instr['id']]  += 1
            instr_ops[instr['id']]  += instr['ops_exp']
            instr_time[instr['id']] += instr['dur']
        self.instructions_lst   = instructions_lst

    def print_instructions_profile(self):
        f   = open('dprof.js', 'w')
        print('function dprof() { return [', file = f)
        for instr in self.instructions_lst:
            idx     = instr['id']
            color   = self.instr_info[instr['name']]['color']
            name    = instr['name']
            start   = instr['start']
            time    = instr['dur']
            end     = instr['end']
            ops     = instr['ops_exp']
            eff     = instr['eff']
            print("{name:'%s',itemStyle:{normal: {color:'%s'}},value:[%d,%f,%f,%f,%d,%f]}," % (name, color, idx, start, end, time, ops, eff), file=f)
        print('];};', file = f)
        f.close()





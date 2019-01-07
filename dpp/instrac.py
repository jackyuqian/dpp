class Instrac:

    instructions_lst  = []
    dpu_info          = {
            'bitwide'   : 512,
            'freq'      : 300,
            'ncore'     : 4,
            'ppxli'     : 8,
            'pchni'     : 16,
            'pchno'     : 16,
            'pmisc'     : 4
            }

    def __init__(self, fname, dpuinfo):
        self.dpu_info   = dpuinfo
        for line in open(fname, 'r'):
            instr_lst  = line.strip().split(' ')
            if instr_lst[0] in ['LOAD', 'SAVE', 'CONVINIT', 'CONV', 'ELEWINIT', 'ELEW', 'POOL', 'END']:
                instr_dict   = {}
                instr_dict['name']  = instr_lst.pop(0)
                instr_dict['dpdon'] = instr_lst.pop(0)
                instr_dict['dpdby'] = instr_lst.pop(0)
                instr_dict.update(dict(zip(instr_lst[0::2], [int(x) for x in instr_lst[1::2]])))
                self.instructions_lst.append(instr_dict)

    def __calc_instr(self):
        convinit_krnl   = 0
        load_prll       = self.dpu_info['bitwide'] / 8
        save_prll       = self.dpu_info['bitwide'] / 8
        conv_prll       = self.dpu_info['pchni'] * self.dpu_info['pchno'] * self.dpu_info['ppxli'] * self.dpu_info['ncore'] * 2
        pool_prll       = self.dpu_info['pchni'] * self.dpu_info['ncore'] * self.dpu_info['pmisc']
        elew_prll       = self.dpu_info['pchni'] * self.dpu_info['ncore'] * self.dpu_info['pmisc']
        for instr in self.instructions_lst:
            if instr['name'] == 'LOAD' and instr['mode'] in [0, 1]:
                instr['name']       = 'LOADFM'
                instr['id']         = 0
                instr['ops_exp']    = instr['channel'] * instr['length'] * self.dpu_info['ncore'] 
                instr['time_exp']   = 1.0 * instr['ops_exp'] / load_prll / self.dpu_info['freq']
            elif instr['name'] == 'LOAD' and instr['mode'] in [2]:
                instr['name']       = 'LOADW'
                instr['id']         = 0
                instr['ops_exp']    = instr['channel'] * instr['length'] * self.dpu_info['pchno'] 
                instr['time_exp']   = 1.0 * instr['ops_exp'] / load_prll / self.dpu_info['freq']
            elif instr['name']  == 'SAVE':
                instr['id']         = 1
                instr['ops_exp']    = instr['channel'] * instr['length'] * self.dpu_info['ncore']
                instr['time_exp']   = 1.0 * instr['ops_exp'] / save_prll / self.dpu_info['freq']
            elif instr['name']  == 'CONVINIT':
                instr['id']         = 2
                convinit_krnl      = instr['kernel_h'] * instr['kernel_w'] * instr['valid_pixel_parallel']
                instr['ops_exp']    = 0
                instr['time_exp']   = 1.0 / self.dpu_info['freq']
            elif instr['name']  == 'CONV':
                instr['id']         = 2
                instr['ops_exp']    = self.dpu_info['pchno'] * instr['length'] * convinit_krnl * \
                        (self.dpu_info['pchni'] * instr['channel_group'] - instr['channel_offset']) * \
                        self.dpu_info['ncore'] * 2
                instr['time_exp']   = 1.0 * instr['ops_exp'] / conv_prll / self.dpu_info['freq']
            elif instr['name']  == 'ELEWINIT':
                instr['id']         = 3
                instr['ops_exp']    = 0
                instr['time_exp']   = 1.0 / self.dpu_info['freq']
            elif instr['name']  == 'ELEW':
                instr['id']         = 3
                instr['ops_exp']    = (instr['num'] - 1) * instr['width']  * \
                        instr['channel_group'] * instr['valid_pixel_parallel'] * self.dpu_info['pchni'] * self.dpu_info['ncore']
                instr['time_exp']   = 1.0 * instr['ops_exp'] / elew_prll / self.dpu_info['freq']
            elif instr['name']  == 'POOL':
                instr['id']         = 3
                instr['ops_exp']    = instr['kernel_w'] * instr['kernel_h'] * instr['length'] * \
                        instr['channel_group'] * instr['valid_pixel_parallel'] * self.dpu_info['pchni'] * self.dpu_info['ncore']
                instr['time_exp']   = 1.0 * instr['ops_exp'] / pool_prll / self.dpu_info['freq']
            elif instr['name']  == 'END':
                instr['id']         = 1
                instr['ops_exp']    = 0
                instr['time_exp']   = 1.0 / self.dpu_info['freq']

    def parse(self):
        self.__calc_instr()
        return self.instructions_lst

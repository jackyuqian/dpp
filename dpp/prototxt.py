import  re, math

class Prototxt:

    layers_lst  = []  
    layers_dict = {}

    # Convert Prototxt to a List
    def __init__(self, fname):
        txt = open(fname, 'r').read()
        lst = re.split(r"([{:}\n\r ])", txt)
        while '' in lst:
            lst.remove('')
        while ' ' in lst:
            lst.remove(' ')
        while '\n' in lst:
            lst.remove('\n')
        while '\r' in lst:
            lst.remove('\r')
        self.layers_lst   = self.__build_layers_list(lst, [])[1]

    # Buile Layers List
    #
    def __build_layers_list(self, txt_lst, layers_lst):
        while True:
            if len(txt_lst) == 0:
                return [txt_lst, layers_lst]
            elif txt_lst[0] == '}':
                txt_lst.pop(0)
                return [txt_lst, layers_lst]
            elif txt_lst[1] == ':':
                layers_lst.append({txt_lst[0] : txt_lst[2]})
                txt_lst = txt_lst[3:]
            elif txt_lst[1] == '{':
                layers_lst.append({txt_lst[0] : self.__build_layers_list(txt_lst[2:], [])[1]})
                txt_lst = self.__build_layers_list(txt_lst[2:], [])[0]

    # Merge Dict from List
    # [{'xxx' : n}, {'yyy', m}] -> {'xxx' : n, 'yyy', m}
    #
    def __list2dict(self, lst):
        d   = {}
        for ele in lst:
            d   = dict(d, **ele)
        return d
    
    # Build Layers Dictionary
    # http://caffe.berkeleyvision.org/tutorial/layers.html
    #
    def __build_layers_dict(self):
        for layer in self.layers_lst:
            # Build Layer Dictionary
            layer_dict  = {
                    'name'      : '',
                    'type'      : '', 
                    'bottom'    : [], 
                    'top'       : '', 
                    'params'    : {}
                    }

            # Fill Basic Info
            for ele in layer['layer']:
                if 'name' in ele:
                    layer_dict['name']  = ele['name'].strip('"')
                elif 'type' in ele:
                    layer_dict['type']  = ele['type'].strip('"')
                elif 'top' in ele:
                    layer_dict['top']   = ele['top'].strip('"')
                elif 'bottom' in ele:
                    layer_dict['bottom'].append(ele['bottom'].strip('"'))
    
            # Fill Params
            for ele in layer['layer']:
                if 'input_param' in ele:
                    params  = self.__list2dict(ele['input_param'])
                    # Required
                    layer_dict['params']['channel_out'] = int(params['shape'][1]['dim'])
                    layer_dict['params']['height_out']  = int(params['shape'][2]['dim'])
                    layer_dict['params']['width_out']   = int(params['shape'][3]['dim'])
    
                elif 'convolution_param' in ele:
                    params  = self.__list2dict(ele['convolution_param'])
                    # Required
                    layer_dict['params']['channel_out'] = int(params['num_output'])
                    layer_dict['params']['kernel_h']    = int(params['kernel_h'] if 'kernel_h' in params else params['kernel_size'])
                    layer_dict['params']['kernel_w']    = int(params['kernel_w'] if 'kernel_w' in params else params['kernel_size'])
                    # Optional
                    if 'pad' in params or ('pad_h' in params and 'pad_w' in params):
                        layer_dict['params']['pad_h']   = int(params['pad_h'] if 'pad_h' in params else params['pad'])
                        layer_dict['params']['pad_w']   = int(params['pad_w'] if 'pad_w' in params else params['pad'])
                    else:
                        layer_dict['params']['pad_h']   = 0 
                        layer_dict['params']['pad_w']   = 0
                    if 'stride' in params or ('stride_h' in params and 'stride_w' in params):
                        layer_dict['params']['stride_h']= int(params['stride_h'] if 'stride_h' in params else params['stride'])
                        layer_dict['params']['stride_w']= int(params['stride_w'] if 'stride_w' in params else params['stride'])
                    else:
                        layer_dict['params']['stride_h']= 1
                        layer_dict['params']['stride_w']= 1
    
                elif 'pooling_param' in ele:
                    params  = self.__list2dict(ele['pooling_param'])
                    # Required
                    layer_dict['params']['kernel_h']    = int(params['kernel_h'] if 'kernel_h' in params else params['kernel_size'])
                    layer_dict['params']['kernel_w']    = int(params['kernel_w'] if 'kernel_w' in params else params['kernel_size'])
                    # Optional
                    if 'pool' in params:
                        layer_dict['params']['pool']    = params['pool']
                    else:
                        layer_dict['params']['pool']    = 'MAX'
                    if 'pad' in params or ('pad_h' in params and 'pad_w' in params):
                        layer_dict['params']['pad_h']       = int(params['pad_h'] if 'pad_h' in params else params['pad'])
                        layer_dict['params']['pad_w']       = int(params['pad_w'] if 'pad_w' in params else params['pad'])
                    else:
                        layer_dict['params']['pad_h']   = 0 
                        layer_dict['params']['pad_w']   = 0
                    if 'stride' in params or ('stride_h' in params and 'stride_w' in params):
                        layer_dict['params']['stride_h']= int(params['stride_h'] if 'stride_h' in params else params['stride'])
                        layer_dict['params']['stride_w']= int(params['stride_w'] if 'stride_w' in params else params['stride'])
                    else:
                        layer_dict['params']['stride_h']= 1
                        layer_dict['params']['stride_w']= 1
    
                elif 'inner_product_param' in ele:
                    params  = self.__list2dict(ele['inner_product_param'])
                    # Required
                    layer_dict['params']['channel_out'] = int(params['num_output'])
    
            # Add layer_dict to layers_dict
            self.layers_dict = dict(self.layers_dict, ** {layer_dict['name']: layer_dict})
                
            
    # Calculate Layer Dictionary
    # NOT SUPPORT: top != name
    #
    def __calc_layers_dict(self):
        uncalced_lst= list(self.layers_dict.keys())
        calced_lst  = []
    
        while len(uncalced_lst) != 0:
            for layer in uncalced_lst:
                if set(self.layers_dict[layer]['bottom']).issubset(calced_lst):
                    calced_lst.append(layer)
                    uncalced_lst.remove(layer)
                    if self.layers_dict[layer]['type'] == 'Input':
                        pass
                    elif self.layers_dict[layer]['type'] in ['ReLU', 'Softmax']:
                        self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['post'].append(self.layers_dict[layer]['type'])
                    elif self.layers_dict[layer]['type'] == 'Convolution':
                        ci  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['channel_out']
                        hi  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['height_out']
                        wi  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['width_out']
                        co  = self.layers_dict[layer]['params']['channel_out']
                        ph  = self.layers_dict[layer]['params']['pad_h']
                        pw  = self.layers_dict[layer]['params']['pad_w']
                        kh  = self.layers_dict[layer]['params']['kernel_h']
                        kw  = self.layers_dict[layer]['params']['kernel_w']
                        sh  = self.layers_dict[layer]['params']['stride_h']
                        sw  = self.layers_dict[layer]['params']['stride_w']
                        ho  = math.floor((hi + ph * 2 - kh) / sh) + 1
                        wo  = math.floor((wi + pw * 2 - kw) / sw) + 1
                        self.layers_dict[layer]['params']['channel_in'] = ci
                        self.layers_dict[layer]['params']['height_in']  = hi
                        self.layers_dict[layer]['params']['width_in']   = wi
                        self.layers_dict[layer]['params']['height_out'] = ho
                        self.layers_dict[layer]['params']['width_out']  = wo
                        self.layers_dict[layer]['params']['ops']        = ci * co * ho * wo * kh * kw * 2
                        self.layers_dict[layer]['params']['post']       = []
                    elif self.layers_dict[layer]['type'] == 'Pooling':
                        ci  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['channel_out']
                        hi  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['height_out']
                        wi  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['width_out']
                        ph  = self.layers_dict[layer]['params']['pad_h']
                        pw  = self.layers_dict[layer]['params']['pad_w']
                        kh  = self.layers_dict[layer]['params']['kernel_h']
                        kw  = self.layers_dict[layer]['params']['kernel_w']
                        sh  = self.layers_dict[layer]['params']['stride_h']
                        sw  = self.layers_dict[layer]['params']['stride_w']
                        ho  = math.ceil((hi + ph * 2 - kh) / sh) + 1
                        wo  = math.ceil((wi + pw * 2 - kw) / sw) + 1
                        self.layers_dict[layer]['params']['channel_in'] = ci
                        self.layers_dict[layer]['params']['channel_out']= ci
                        self.layers_dict[layer]['params']['height_in']  = hi
                        self.layers_dict[layer]['params']['width_in']   = wi
                        self.layers_dict[layer]['params']['height_out'] = ho
                        self.layers_dict[layer]['params']['width_out']  = wo
                        self.layers_dict[layer]['params']['ops']        = co * ho * wo * kh * kw 
                        self.layers_dict[layer]['params']['post']       = []
                    elif self.layers_dict[layer]['type'] == 'Eltwise':
                        ci  = 0
                        for bottom in self.layers_dict[layer]['bottom']:
                            ci  = self.layers_dict[bottom]['params']['channel_out'] + ci
                            co  = self.layers_dict[bottom]['params']['channel_out']
                            hi  = self.layers_dict[bottom]['params']['height_out']
                            wi  = self.layers_dict[bottom]['params']['width_out']
                            ho  = self.layers_dict[bottom]['params']['height_out']
                            wo  = self.layers_dict[bottom]['params']['width_out']
                        self.layers_dict[layer]['params']['channel_in'] = ci
                        self.layers_dict[layer]['params']['channel_out']= co
                        self.layers_dict[layer]['params']['height_in']  = hi
                        self.layers_dict[layer]['params']['width_in']   = wi
                        self.layers_dict[layer]['params']['height_out'] = ho
                        self.layers_dict[layer]['params']['width_out']  = wo
                        self.layers_dict[layer]['params']['ops']        = ci * ho * wo
                        self.layers_dict[layer]['params']['post']       = []
                    elif self.layers_dict[layer]['type'] == 'Concat':
                        ci  = 0
                        co  = 0
                        for bottom in self.layers_dict[layer]['bottom']:
                            ci  = self.layers_dict[bottom]['params']['channel_out'] + ci
                            co  = self.layers_dict[bottom]['params']['channel_out'] + co
                            hi  = self.layers_dict[bottom]['params']['height_out']
                            wi  = self.layers_dict[bottom]['params']['width_out']
                            ho  = self.layers_dict[bottom]['params']['height_out']
                            wo  = self.layers_dict[bottom]['params']['width_out']
                        self.layers_dict[layer]['params']['channel_in'] = ci
                        self.layers_dict[layer]['params']['channel_out']= ci
                        self.layers_dict[layer]['params']['height_in']  = hi
                        self.layers_dict[layer]['params']['width_in']   = wi
                        self.layers_dict[layer]['params']['height_out'] = ho
                        self.layers_dict[layer]['params']['width_out']  = wo
                        self.layers_dict[layer]['params']['ops']        = ci * ho * wo
                        self.layers_dict[layer]['params']['post']       = []
                    elif self.layers_dict[layer]['type'] == 'InnerProduct':
                        ci  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['channel_out']
                        hi  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['height_out']
                        wi  = self.layers_dict[self.layers_dict[layer]['bottom'][0]]['params']['width_out']
                        co  = self.layers_dict[layer]['params']['channel_out']
                        self.layers_dict[layer]['params']['channel_in'] = ci
                        self.layers_dict[layer]['params']['height_in']  = hi
                        self.layers_dict[layer]['params']['width_in']   = wi
                        self.layers_dict[layer]['params']['height_out'] = 1
                        self.layers_dict[layer]['params']['width_out']  = 1
                        self.layers_dict[layer]['params']['ops']        = ci * co * hi * wi * 2
                        self.layers_dict[layer]['params']['post']       = []
                    break

    def parse(self):
        self.__build_layers_dict()
        self.__calc_layers_dict()
        return self.layers_dict

    def print_info(self):
        print('%-25s%-15s%-30s%-30s%-30s%-20s' % ('Layer', 'Type', 'Input_Size', 'Output_Size', 'Kernel_size', 'Operations'))
        print(150*'-')
        for key, val in self.layers_dict.items():
            if val['type'] not in ['Input', 'ReLU', 'Softmax']:
                Layer       = key
                if val['type']  == 'Convolution':
                    Type        = 'CONV'
                    Kernel_Size = str(val['params']['kernel_h']) + ' x ' + str(val['params']['kernel_w']) + \
                            '(Stride=' + str(val['params']['stride_h']) + 'x' + str(val['params']['stride_w']) + ')'
                elif val['type'] == 'Pooling':
                    Type        = 'POOL'
                    Kernel_Size = str(val['params']['kernel_h']) + ' x ' + str(val['params']['kernel_w']) + \
                            '(Stride=' + str(val['params']['stride_h']) + 'x' + str(val['params']['stride_w']) + ')'
                elif val['type'] == 'Eltwise':
                    Type        = 'ELEW'
                    Kernel_Size = '-'
                elif val['type'] == 'Concat':
                    Type        = 'CCAT'
                    Kernel_Size = '-'
                elif val['type'] == 'InnerProduct':
                    Type        = 'FC'
                    Kernel_Size = '-'
                for p in val['params']['post']:
                    Type    = Type + '_' + p
                Input_Size  = str(val['params']['channel_in']) + ' x ' + str(val['params']['height_in']) + ' x ' + str(val['params']['width_in']) + ' = ' \
                            + str(val['params']['channel_in'] * val['params']['height_in'] * val['params']['width_in']) 
                Output_Size = str(val['params']['channel_out']) + ' x ' + str(val['params']['height_out']) + ' x ' + str(val['params']['width_out']) + ' = ' \
                            + str(val['params']['channel_out'] * val['params']['height_out'] * val['params']['width_out'])
                Operations  = str(val['params']['ops'])
                print('%-25s%-15s%-30s%-30s%-30s%-20s' % (Layer, Type, Input_Size, Output_Size,Kernel_Size, Operations))



    
    

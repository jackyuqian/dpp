#!/usr/local/bin/python3
import  sys, getopt
import  re
import  math
import  time

# TODO:
# top != name

# Print Help
#
def usage():
    print('Please Contact Qian.(yuqian@xilinx.com)')

# Merge Dict from List
# [{'xxx' : n}, {'yyy', m}] -> {'xxx' : n, 'yyy', m}
#
def list2dict(lst):
    d   = {}
    for ele in lst:
        d   = dict(d, **ele)
    return d


# Build Context List
#
def build_context_list(fname):
    context_lst =re.split(r"([{:}\n\r ])", open(fname, 'r').read())
    while '' in context_lst:
        context_lst.remove('')
    while ' ' in context_lst:
        context_lst.remove(' ')
    while '\n' in context_lst:
        context_lst.remove('\n')
    while '\r' in context_lst:
        context_lst.remove('\r')
    return context_lst

# Buile Layer List
#
def build_layer_list(txt_lst, layer_lst):
    while True:
        if len(txt_lst) == 0:
            return [txt_lst, layer_lst]
        elif txt_lst[0] == '}':
            txt_lst.pop(0)
            return [txt_lst, layer_lst]
        elif txt_lst[1] == ':':
            layer_lst.append({txt_lst[0] : txt_lst[2]})
            txt_lst = txt_lst[3:]
        elif txt_lst[1] == '{':
            layer_lst.append({txt_lst[0] : build_layer_list(txt_lst[2:], [])[1]})
            txt_lst = build_layer_list(txt_lst[2:], [])[0]

# Build Layer Dictionary
# http://caffe.berkeleyvision.org/tutorial/layers.html
#
def build_layer_dict(layer_lst):
    layers_dict = {}
    for layer in layer_lst:
        layer_dict  = {}
        layer_name  = ''
        # Name
        for ele in layer['layer']:
            if 'name' in ele:
                layer_name  = ele['name'].strip('"')
                layer_dict[layer_name]  = {
                        'type'      : '', 
                        'bottom'    : [], 
                        'top'       : '', 
                        'params'    : {}
                        }
        # Basic Info
        for ele in layer['layer']:
            if 'type' in ele:
                layer_dict[layer_name]['type']  = ele['type'].strip('"')
            elif 'bottom' in ele:
                layer_dict[layer_name]['bottom'].append(ele['bottom'].strip('"'))
            elif 'top' in ele:
                layer_dict[layer_name]['top']   = ele['top'].strip('"')

        # Params
        for ele in layer['layer']:
            if layer_dict[layer_name]['type'] == 'Input' and 'input_param' in ele:
                params  = list2dict(ele['input_param'])
                # Required
                layer_dict[layer_name]['params']['channel_out'] = int(params['shape'][1]['dim'])
                layer_dict[layer_name]['params']['height_out']  = int(params['shape'][2]['dim'])
                layer_dict[layer_name]['params']['width_out']   = int(params['shape'][3]['dim'])

            elif layer_dict[layer_name]['type'] == 'Convolution' and 'convolution_param' in ele:
                params  = list2dict(ele['convolution_param'])
                # Required
                layer_dict[layer_name]['params']['channel_out'] = int(params['num_output'])
                layer_dict[layer_name]['params']['kernel_h']    = int(params['kernel_h'] if 'kernel_h' in params else params['kernel_size'])
                layer_dict[layer_name]['params']['kernel_w']    = int(params['kernel_w'] if 'kernel_w' in params else params['kernel_size'])
                # Optional
                if 'pad' in params or ('pad_h' in params and 'pad_w' in params):
                    layer_dict[layer_name]['params']['pad_h']       = int(params['pad_h'] if 'pad_h' in params else params['pad'])
                    layer_dict[layer_name]['params']['pad_w']       = int(params['pad_w'] if 'pad_w' in params else params['pad'])
                else:
                    layer_dict[layer_name]['params']['pad_h']       = 0 
                    layer_dict[layer_name]['params']['pad_w']       = 0
                if 'stride' in params or ('stride_h' in params and 'stride_w' in params):
                    layer_dict[layer_name]['params']['stride_h']    = int(params['stride_h'] if 'stride_h' in params else params['stride'])
                    layer_dict[layer_name]['params']['stride_w']    = int(params['stride_w'] if 'stride_w' in params else params['stride'])
                else:
                    layer_dict[layer_name]['params']['stride_h']    = 1
                    layer_dict[layer_name]['params']['stride_w']    = 1

            elif layer_dict[layer_name]['type'] == 'Pooling' and 'pooling_param' in ele:
                params  = list2dict(ele['pooling_param'])
                # Required
                layer_dict[layer_name]['params']['kernel_h']        = int(params['kernel_h'] if 'kernel_h' in params else params['kernel_size'])
                layer_dict[layer_name]['params']['kernel_w']        = int(params['kernel_w'] if 'kernel_w' in params else params['kernel_size'])
                # Optional
                if 'pool' in params:
                    layer_dict[layer_name]['params']['pool']        = params['pool']
                else:
                    layer_dict[layer_name]['params']['pool']        = 'MAX'
                if 'pad' in params or ('pad_h' in params and 'pad_w' in params):
                    layer_dict[layer_name]['params']['pad_h']       = int(params['pad_h'] if 'pad_h' in params else params['pad'])
                    layer_dict[layer_name]['params']['pad_w']       = int(params['pad_w'] if 'pad_w' in params else params['pad'])
                else:
                    layer_dict[layer_name]['params']['pad_h']       = 0 
                    layer_dict[layer_name]['params']['pad_w']       = 0
                if 'stride' in params or ('stride_h' in params and 'stride_w' in params):
                    layer_dict[layer_name]['params']['stride_h']    = int(params['stride_h'] if 'stride_h' in params else params['stride'])
                    layer_dict[layer_name]['params']['stride_w']    = int(params['stride_w'] if 'stride_w' in params else params['stride'])
                else:
                    layer_dict[layer_name]['params']['stride_h']    = 1
                    layer_dict[layer_name]['params']['stride_w']    = 1

            elif layer_dict[layer_name]['type'] == 'InnerProduct' and 'inner_product_param' in ele:
                params  = list2dict(ele['inner_product_param'])
                # Required
                layer_dict[layer_name]['params']['channel_out']     = int(params['num_output'])


        layers_dict = dict(layers_dict, ** layer_dict)
    return layers_dict
            
        
# Calculate Layer Dictionary
#
def calc_layer_dict(layer_dict):
    uncalced_lst= list(layer_dict.keys())
    calced_lst  = []

    while len(uncalced_lst) != 0:
        for layer in uncalced_lst:
            print(layer)
            if set(layer_dict[layer]['bottom']).issubset(calced_lst):
                calced_lst.append(layer)
                uncalced_lst.remove(layer)
                if layer_dict[layer]['type'] == 'Input':
                    pass
                elif layer_dict[layer]['type'] == 'ReLU':
                    layer_dict[layer_dict[layer]['bottom'][0]]['params']['post'].append('ReLU')
                elif layer_dict[layer]['type'] == 'Dropout':
                    layer_dict[layer_dict[layer]['bottom'][0]]['params']['post'].append('Dropout')
                elif layer_dict[layer]['type'] == 'LRN':
                    layer_dict[layer]['params']['channel_in']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['channel_out']  = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['height_in']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_in']     = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['height_out']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_out']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['post']         = []
                elif layer_dict[layer]['type'] == 'Softmax':
                    layer_dict[layer]['params']['channel_in']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['channel_out']  = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['height_in']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_in']     = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['height_out']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_out']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['post']         = []
                elif layer_dict[layer]['type'] == 'Convolution':
                    layer_dict[layer]['params']['channel_in']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['height_in']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_in']     = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['height_out']   = math.floor((layer_dict[layer]['params']['height_in'] + layer_dict[layer]['params']['pad_h'] * 2 \
                                                                    - layer_dict[layer]['params']['kernel_h']) \
                                                                    / layer_dict[layer]['params']['stride_h']) + 1
                    layer_dict[layer]['params']['width_out']    = math.floor((layer_dict[layer]['params']['width_in'] + layer_dict[layer]['params']['pad_w'] * 2 \
                                                                    - layer_dict[layer]['params']['kernel_w']) \
                                                                    / layer_dict[layer]['params']['stride_w']) + 1
                    layer_dict[layer]['params']['post']         = []
                elif layer_dict[layer]['type'] == 'Pooling':
                    layer_dict[layer]['params']['channel_in']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['channel_out']  = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['height_in']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_in']     = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['height_out']   = math.ceil((layer_dict[layer]['params']['height_in'] + layer_dict[layer]['params']['pad_h'] * 2 \
                                                                    - layer_dict[layer]['params']['kernel_h']) \
                                                                    / layer_dict[layer]['params']['stride_h']) + 1
                    layer_dict[layer]['params']['width_out']    = math.ceil((layer_dict[layer]['params']['width_in'] + layer_dict[layer]['params']['pad_w'] * 2 \
                                                                    - layer_dict[layer]['params']['kernel_w']) \
                                                                    / layer_dict[layer]['params']['stride_w']) + 1
                    layer_dict[layer]['params']['post']         = []
                elif layer_dict[layer]['type'] == 'Eltwise':
                    layer_dict[layer]['params']['channel_in']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['channel_out']  = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['height_in']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_in']     = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['height_out']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_out']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['post']         = []
                elif layer_dict[layer]['type'] == 'Concat':
                    layer_dict[layer]['params']['channel_in']  = 0
                    for bottom in layer_dict[layer]['bottom']:
                        layer_dict[layer]['params']['channel_in']   += layer_dict[bottom]['params']['channel_out']
                    layer_dict[layer]['params']['channel_out']  = layer_dict[layer]['params']['channel_in']
                    layer_dict[layer]['params']['height_in']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_in']     = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['height_out']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_out']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['post']         = []
                elif layer_dict[layer]['type'] == 'InnerProduct':
                    layer_dict[layer]['params']['channel_in']   = layer_dict[layer_dict[layer]['bottom'][0]]['params']['channel_out']
                    layer_dict[layer]['params']['height_in']    = layer_dict[layer_dict[layer]['bottom'][0]]['params']['height_out']
                    layer_dict[layer]['params']['width_in']     = layer_dict[layer_dict[layer]['bottom'][0]]['params']['width_out']
                    layer_dict[layer]['params']['height_out']   = 1
                    layer_dict[layer]['params']['width_out']    = 1
                    layer_dict[layer]['params']['post']         = []
                break
    return layer_dict

# Print Table
#
def print_table(layer_dict):
    print('%-20s%-20s%-30s%-30s%-20s%-20s%-20s' % ('Layer', 'Type', 'Input_Size', 'Output_Size', 'Operations', 'Post', ''))
    print(100*'-')
    for key, val in layer_dict.items():
        if val['type'] not in ['Input', 'ReLU', 'Dropout']:
            Layer       = key
            Type        = val['type']
            Input_Size  = str(val['params']['channel_in']) + ' x ' + str(val['params']['height_in']) + ' x ' + str(val['params']['width_in']) + ' = ' \
                        + str(val['params']['channel_in'] * val['params']['height_in'] * val['params']['width_in']) 
            Output_Size = str(val['params']['channel_out']) + ' x ' + str(val['params']['height_out']) + ' x ' + str(val['params']['width_out']) + ' = ' \
                        + str(val['params']['channel_out'] * val['params']['height_out'] * val['params']['width_out'])
            Operations  = str( "")
            Post        = str(val['params']['post'])
            print('%-20s%-20s%-30s%-30s%-20s%-20s%-20s' % (Layer, Type, Input_Size, Output_Size, '', Post, ''))


#
# Main Function
#
opts, args  = getopt.getopt(sys.argv[1:], 'hf:')
for op, value in opts:
    if op == '-f':
        fname   = value
    elif op == '-h':
        usage()
        sys.exit()

context_lst = build_context_list(fname)
layer_lst   = build_layer_list(context_lst, [])[1]
layer_dict  = build_layer_dict(layer_lst)
layer_dict  = calc_layer_dict(layer_dict)
print_table(layer_dict)

#!/usr/local/bin/python3

import sys, time, getopt
import torch
import torch.utils.data as Data
import torch.nn as Nn
import torch.optim as Optim
import matplotlib.pyplot as Plot

# Print Usage
#
def usage():
    print('Please Contact Qian.(yuqian@xilinx.com)')
    print("./training.py -f filename -t instruction_type")

# Parameters
#
BATCH_SIZE  = 4
LR          = 0.1
DATA_LABEL  = {
    'LOAD' : ['corenum', 'mode', 'width', 'length', 'jump', 'offset'],
    'SAVE' : ['corenum', 'mode', 'width', 'length', 'jump', 'offset'],
    'CONV' : [],
    'ELEW' : [],
    'POOL' : []
}
DATA_NORM   = {
    'LOAD' : torch.Tensor([16, 2, 2048, 2048, 2048, 256]),
    'SAVE' : torch.Tensor([16, 2, 2048, 2048, 2048, 256]),
    'CONV' : [],
    'ELEW' : [],
    'POOL' : []
}

# Func: Parse Data File
#
def read_data(fname, itype):
    data_list   = []
    targets_list= []
    for line in open(fname, 'r'):
        elements    = line.strip().split()
        if len(elements) > 1 :
            data_ele    = []
            for label in DATA_LABEL[itype]:
                data_ele.append(float(elements[elements.index(label)+1]))
            data_list.append(data_ele)
            targets_list.append([float(elements[elements.index('eff')+1])])
    data    = torch.Tensor(data_list) / DATA_NORM[itype]
    targets = torch.Tensor(targets_list)
    dataset = Data.TensorDataset(data, targets)
    print('[INFO] Read Data...Done.')
    return dataset 

# Func: Build Network
#
def build_net():
    net = Nn.Sequential(
        Nn.Linear(6, 8),
        Nn.ReLU(),
        Nn.Linear(8, 1)
    )
    func_optim  = Optim.Adam(net.parameters(), lr=LR, betas=(0.9, 0.99))
    func_loss   = Nn.MSELoss()
    print('[INFO] Build Net...Done.')
    print(net)
    return net, func_optim, func_loss

# Func: Train Network
#
def train_net(net, func_optim, func_loss, dataset):
    loader  = Data.DataLoader(
        dataset     = dataset,
        batch_size  = BATCH_SIZE,
        shuffle     = True,
    )
    for epoch in range(100):
        for step, (batch_data, batch_targets) in enumerate(loader):
            prediction  = net(batch_data)
            loss        = func_loss(prediction, batch_targets)
            func_optim.zero_grad()
            loss.backward()
            func_optim.step()
            time.sleep(0.01)
            sys.stdout.write('[INFO] Training Net...Epoch=%d\tStep=%d.\r' % (epoch, step))
            sys.stdout.flush()
    print('\n[INFO} Training Net...Done.')
 

# Main
opts, args  = getopt.getopt(sys.argv[1:], 'hf:t:')
for op, value in opts:
    if op == '-f':
        fname   = value
    elif op == '-t':
        itype= value
    elif op == '-h':
        usage()
        sys.exit()
if not set(['fname', 'itype']) <=  set(dir()):
    usage()
    sys.exit()

net, func_optim, func_loss  = build_net()
dataset = read_data(fname, itype)
train_net(net, func_optim, func_loss, dataset)
torch.save(net, itype+".net.pkl")

print(net(torch.Tensor([10, 2, 1024, 4, 1024, 0])/DATA_NORM['LOAD'])) #0.6

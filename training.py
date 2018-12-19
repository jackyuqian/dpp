#!/usr/local/bin/python3

import sys, time
import torch
import torch.utils.data as Data
import torch.nn as Nn
import torch.optim as Optim
from matplotlib import pyplot

# Hyber Param
#
LR          = 0.1
BATCH_SIZE  = 4
DATA_NORM   = torch.Tensor([2048, 2048, 256, 16, 2, 2048])

# Func: Parse Data File
#
def read_data(fname):
    data_list   = []
    targets_list= []
    for line in open(fname, 'r'):
        elements    = line.strip().split()
        if len(elements) < 2 :
            break
        data_list.append([
            float(elements[elements.index('width')+1]),
            float(elements[elements.index('length')+1]),
            float(elements[elements.index('offset')+1]),
            float(elements[elements.index('corenum')+1]),
            float(elements[elements.index('mode')+1]),
            float(elements[elements.index('jump')+1])
        ])
        targets_list.append([
            float(elements[elements.index('eff')+1])
        ])
    data    = torch.Tensor(data_list) / DATA_NORM
    targets = torch.Tensor(targets_list)
    dataset = Data.TensorDataset(data, targets)
    print('[INFO] Read Data...Done.')
#return data, targets
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
net, func_optim, func_loss  = build_net()
dataset = read_data('./simdata/load/1.txt')
train_net(net, func_optim, func_loss, dataset)
torch.save(net, "loadnet.pkl")

print(net(torch.Tensor([1024, 4, 0, 10, 2, 1024])/DATA_NORM)) #0.6

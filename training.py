#!/usr/local/bin/python3

import torch
import torch.nn as NN

net = NN.Sequential(
    NN.Linear(2, 10),
    NN.ReLU(),
    NN.Linear(10, 1)
)


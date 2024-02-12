#!/usr/bin/env python3.11

import gurobipy as gp
from gurobipy import GRB

import numpy as np

#########################################################
# Constants
#########################################################
C = np.array([
    13.32,13.32,20.7,20.93,26.11,10.52,10.52,6.02,5.47,0,10.52,10.89
])

P_MAX = np.array([
    152,152,350,591,60,155,155,400,400,300,310,350
])

D = 1775.835

#########################################################
# Model
#########################################################

# Create a new model
m = gp.Model("Copper-plate single hour")

# Create variables
p = m.addMVar(shape=(12, ), lb=0, ub=P_MAX, name="power_generation", vtype=GRB.CONTINUOUS)

# Set objective: maximize x
objective = m.setObjective(sum(C[i]*p[i] for i in range(12)), GRB.MINIMIZE)

# Constraint: D - sum(p) = 0
m.addConstr(sum(p[i] for i in range(12)) - D == 0, "Generation balance")

# Optimize model
m.optimize()

#########################################################
# Model
#########################################################

generation = p.X
print('Generation units :')
for j in range(12):
    print(f'    Generation unit {j+1}: {generation[j]}')
print(f'Objective function is: {m.getObjective().getValue()}')

price = m.getAttr('Pi', m.getConstrs())[0]
print(f'Market price: {price}')
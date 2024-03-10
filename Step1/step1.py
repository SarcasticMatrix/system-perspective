import gurobipy as gp
from gurobipy import GRB

import pandas as pd
import numpy as np

#########################################################
# Constants
#########################################################

C = np.array(
    [13.32,13.32,20.7,20.93,26.11,10.52,10.52,6.02,5.47,0,10.52,10.89]+[0]*6
)

wind = pd.read_csv("step1/windData.csv",index_col="hour")
wind = wind[['V1','V2','V3','V4','V5','V6']].iloc[0].to_numpy()*200
P_MAX = np.array(
    [152,152,350,591,60,155,155,400,400,300,310,350]+wind.tolist()
)

D = 1775.835

#########################################################
# Model
#########################################################

# Create a new model
m = gp.Model("Copper-plate single hour")

# Create variables
p = m.addMVar(shape=(12+6, ), lb=0, ub=P_MAX, name="Power generation", vtype=GRB.CONTINUOUS)

# Set objective: maximize
objective = m.setObjective(sum(C[i]*p[i] for i in range(12+6)), GRB.MINIMIZE)

# Constraint: D - sum(p) = 0
balance = m.addConstr(sum(p[i] for i in range(12+6)) - D == 0, "Generation balance")

# Optimize model
m.optimize()

#########################################################
# Some prints
#########################################################

price = m.getAttr('Pi', m.getConstrs())[0]
print(f'Market-clearing price: {price}')
print('Generation units :')
for j in range(12+6):
    print(f'    Generation unit {j+1} produces: {round(p.X[j],2)} - Profit: {round(p.X[j]*price,2)}')
print(f'Social welfare is: {D*price - m.getObjective().getValue()}')


import matplotlib.pyplot as plt

generation_units = [f"{j+1}" for j in range(12+6)]
production = [round(p.X[j],2) for j in range(12+6)]
revenue = [round(p.X[j]*price,2)/1000 for j in range(12+6)]

plt.figure()
plt.bar(generation_units, production)
plt.ylabel('Power generation (MW)')
plt.xlabel('Unit')
plt.title('Production by Generation Unit')
plt.grid(which='minor', linestyle='--', linewidth=0.1, color='gray')
plt.grid(axis='y', linestyle="--", linewidth=0.5, color="gray")
plt.show()

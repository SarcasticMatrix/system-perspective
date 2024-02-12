import numpy as np 
import pandas as pd
import matplotlib as plt
import gurobipy as gp
from gurobipy import GRB

#Modelisation parameter
SUCostOn = False

#parameter unit
gen_para = pd.read_csv('../inputs/gen_parameters.csv', sep=';')
NbUnit = gen_para.shape[0] 
cost = gen_para['Ci'].values.tolist() # Extract cost from the DataFrame
p_max = gen_para['Pmax'].values.tolist()
p_min = gen_para['Pmin'].values.tolist()
Csu = gen_para['Csu'].values.tolist()
U_ini = gen_para['Uini'].values.tolist()

if SUCostOn:
    SUCost = [Csu[i]*U_ini[i] for i in range(NbUnit)] #take into account the state at t=0
else:
    SUCost = [0]*NbUnit

#parameter load
load_profile = pd.read_csv('../inputs/load_profile.csv', sep=';')
total_demand = load_profile['total_demand'].values.tolist()
NbHour = load_profile.shape[0] 

# create a new model
m = gp.Model()

# Create variables 
p = m.addMVar(shape=(NbHour, NbUnit), name="power_generation", vtype=GRB.CONTINUOUS)
y = m.addMVar(shape=(NbHour, NbUnit), name="unit_on", vtype='B')

# Set objective function
m.setObjective(gp.quicksum((p[t][i]*cost[i])*NbHour - SUCost[i]*y[t][i] for t in range(NbHour) for i in range(NbUnit)), GRB.MINIMIZE)


max_prod_constraint = []
min_prod_constraint = []
balance_constraint = []

# # Add constraints
for t in range(NbHour):
    for i in range(NbUnit):
        max_prod_constraint.append(m.addConstr(p[t][i] <= p_max[i]*y[t][i]))
        min_prod_constraint.append(m.addConstr(p[t][i] >= p_min[i]*y[t][i]))
    balance_constraint.append(m.addConstr(total_demand[t] - gp.quicksum(p[t][i] for i in range(NbUnit)) == 0, name=f"GenerationBalance_{t+1}"))

# Solve it!
m.optimize()


p_values = [p[t][i].X for i in range(NbUnit)]
y_values = [y[t][i].X for i in range(NbUnit)]

# price = [balance_constraint[t].Pi for t in range(NbHour)]
# profit = [p_values[i]*(price - cost[i]) - SUCost[i] for i in range(NbUnit)]

#result
print(f"Optimal objective value: {m.objVal} $")
for t in range(NbHour):
    for i in range(NbUnit):
        print(f"p_{i+1} for hour {t+1}: production: {p[t][i].X} MW, profit: {profit[i]} $")
# print("clearing price:", price)


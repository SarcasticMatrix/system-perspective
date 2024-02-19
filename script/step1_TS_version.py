import numpy as np 
import pandas as pd
import matplotlib as plt
import gurobipy as gp

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
p = m.addMVar(shape=(NbUnit, NbHour), name="power_generation", vtype=gp.GRB.CONTINUOUS)
binary = m.addMVar(shape=(NbUnit, NbHour), name="unit_on", vtype='B')

# Set objective function
m.setObjective(gp.quicksum((p[i][t]*cost[i])*NbHour - SUCost[i]*binary[i][t] for t in range(NbHour) for i in range(NbUnit)), gp.GRB.MINIMIZE)

# Add constraints
m.addConstr((p[i][t] <= p_max[i]*binary[i][t] for t in range(NbHour) for i in range(NbUnit)))
m.addConstr((p[i][t] >= p_min[i]*binary[i][t] for t in range(NbHour) for i in range(NbUnit)))
# Constraint: D - sum(p) = 0
m.addConstr((total_demand[t] - gp.quicksum(p[i][t] for i in range(NbUnit)) for t in range(NbHour))== 0, "Generation balance")


# Optimize model
m.optimize()

#########################################################
# Model
#########################################################

generation = p.X
price = m.getAttr('Pi', m.getConstrs())[0]

print('Generation units :')
for t in range(NbHour):
    for j in range(NbUnit):
        print(f'    Generation unit {j+1} at {t+1} hour: {generation[j][t]}')
print(f'Objective function is: {m.getObjective().getValue()}')

print(f'Market price: {price}')




# p_values = [p[i][t].X for i in range(NbUnit)]
# binary_values = [binary[i][t].X for i in range(NbUnit)]

# Pclearing = max(binary_values[i]*cost[i] for i in range(NbUnit))
# profit = [p_values[i]*(Pclearing - cost[i]) - SUCost[i] for i in range(NbUnit)]

# #result
# print(f"Optimal objective value: {m.objVal} $")
# for t in range(NbHour):
#     for i in range(NbUnit):
#         print(f"p_{i+1} for hour {t+1}: production: {p[i][t].X} MW, profit: {profit[i]} $")
# print("clearing price:", Pclearing)
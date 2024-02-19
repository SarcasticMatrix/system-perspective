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
wind = pd.read_csv("step2/windData.csv")
wind = wind[['V1','V2','V3','V4','V5','V6']].to_numpy()*200

demand = pd.read_csv("step2/load.csv",index_col='hour')['total_demand'].values

for t in range(24):
    print("\n \n")
    print("-"*50)
    print(f"Time {t}")
    P_MAX = np.array(
        [152,152,350,591,60,155,155,400,400,300,310,350]+wind[t,:].tolist()
    )

    D = demand[t]

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
    print(f'Social welfare is: {round(D*price - m.getObjective().getValue(),2)}')

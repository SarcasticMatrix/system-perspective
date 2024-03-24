import gurobipy as gp
from gurobipy import GRB

import pandas as pd
import numpy as np

#########################################################
# Constants
#########################################################

C = np.array(
    [13.32, 13.32, 20.7, 20.93, 26.11, 10.52, 10.52, 6.02, 5.47, 0, 10.52, 10.89]
    + [0] * 6
)

wind = pd.read_csv("Step1/windData.csv", index_col="hour")
wind = wind[["V1", "V2", "V3", "V4", "V5", "V6"]].iloc[0].to_numpy() * 200
P_MAX = np.array(
    [152, 152, 350, 591, 60, 155, 155, 400, 400, 300, 310, 350] + wind.tolist()
)

D = 1500*4
bid_price = np.array([9,12,15])

#########################################################
# Model
#########################################################

# Create a new model
m = gp.Model("Copper-plate single hour")

# Create variables
p = m.addMVar(
    shape=(12 + 6,), lb=0, ub=P_MAX, name="Power generation", vtype=GRB.CONTINUOUS
)
d = m.addMVar(
    shape=(3,), lb=0, ub=[0.5*D,0.4*D,0.1*D], name = "Demand", vtype=GRB.CONTINUOUS
)

# Set objective: maximize
objective = m.setObjective(sum(bid_price[i]*d[i] for i in range(3)) - sum(C[i] * p[i] for i in range(12 + 6)), GRB.MAXIMIZE)

# Constraint: D - sum(p) = 0
balance = m.addConstr(-sum(p[i] for i in range(12 + 6)) + sum(d[i] for i in range(3)) == 0, "Generation balance")

# Optimize model
m.optimize()

#########################################################
# Some prints
#########################################################

price = m.getAttr("Pi", m.getConstrs())[0]
generation_units = [f"{j+1}" for j in range(12 + 6)]
load_units = [f"{j+1}" for j in range(3)]
production = np.array([round(p.X[j], 2) for j in range(12 + 6)])
demand = np.array([round(d.X[j], 2) for j in range(3)])
utlity = demand*(bid_price - price)
revenue = np.array([round(p.X[j] * price, 2) for j in range(12 + 6)])
profit = revenue - production * C

print(f"Market-clearing price: {price}")
print(f"Social welfare is: {D*price - m.getObjective().getValue()}")
print("Generation units :")
for j in range(12 + 6):
    print(
        f"    Generation unit {j+1} produces: {round(p.X[j],2)} - Profit: {round(p.X[j]*price,2)}"
    )
print('Demand Supplied: ', demand)
print('Utility:', utlity)


import matplotlib.pyplot as plt

plt.figure(figsize=(15,8))
plt.bar(generation_units, profit, width=0.5)
plt.ylabel("Profit (currency unit)")
plt.xlabel("Unit")
plt.title("Profit by Generation Unit")
plt.grid(axis="y", which='major', linestyle="--", linewidth=0.5, color="gray")

plt.show()

plt.figure(figsize=(15,8))
plt.bar(load_units, demand * (bid_price - price), width=0.5)
plt.ylabel("Utility (MWh * currency unit)")
plt.xlabel("Load unit")
plt.title("Utility by Load Unit")
plt.grid(axis="y", which='major', linestyle="--", linewidth=0.5, color="gray")

plt.show()


from meritOrderCurve import *

curve = MeritOrderCurve(
    productions=production,
    prod_marginal_costs=C,
    demands=demand,
    demands_marginal_costs=bid_price
)

curve.merit_order_curve()
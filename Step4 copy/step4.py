import pandas as pd
import gurobipy as gp
import numpy as np
from gurobipy import GRB

################################################################################
# Initialisaiton of nodes
################################################################################
from scripts.nodes import Nodes

nbNode = 24
nodes = Nodes(number_nodes=nbNode)

################################################################################
# Creation of Conventionnal Generation Units
################################################################################

from scripts.generationUnits import GenerationUnits,GenerationUnit

# parameter unit
generationUnits_parameters = pd.read_csv("inputs/gen_parameters.csv", sep=";")
nodes_ids = generationUnits_parameters["Node"].values - 1
costs = generationUnits_parameters["Ci"].values
pmax = generationUnits_parameters["Pmax"].values
pmin = generationUnits_parameters["Pmin"].values
Csu = generationUnits_parameters["Csu"].values  # Start-up cost
Uini = generationUnits_parameters["Uini"].values  # Initial state (1 if on, 0 else)
ramp_up = generationUnits_parameters["RU"].values  # Maximum augmentation of production (ramp-up)
ramp_down = generationUnits_parameters["RD"].values  # Maximum decrease of production (ramp-up)
prod_init = generationUnits_parameters["Pini"].values  # Initial production

generation_units = GenerationUnits()
nbUnitsConventionnal = generationUnits_parameters.shape[0]
for unit_id in range(nbUnitsConventionnal):

    node_id = nodes_ids[unit_id]
    generationUnit = GenerationUnit(
        unit_id=unit_id,
        node_id=node_id,
        unit_type="conventionnal",
        cost=costs[unit_id],
        pmax=pmax[unit_id],
        pmin=pmin[unit_id],
        availability=[1] * 24,  # 100% availability for each hour
        ramp_up=ramp_up[unit_id],
        ramp_down=ramp_down[unit_id],
        prod_init=prod_init[unit_id],
    )
    nodes.add_generationUnit(id_node=node_id,generationUnit=generationUnit)
    generation_units.add_unit(generationUnit)

################################################################################
# Adding of the Wind Generation Units
################################################################################

wind_parameters = pd.read_csv("inputs/wind_parameters.csv", index_col="Unit", sep=";")
nodes_ids = wind_parameters["Node"].values - 1
pmax = wind_parameters["Pmax"].values
pmin = wind_parameters["Pmin"].values
costs = wind_parameters["Ci"].values

scenario = "V1"  # scenario : from V1 to V100

nbUnitsWind = wind_parameters.shape[0]
nbUnits = nbUnitsConventionnal + nbUnitsWind
for id in range(nbUnitsWind):

    availability = pd.read_csv(f"inputs/data/scen_zoneW{id}.csv", sep=",")[
        scenario
    ].values.tolist()

    node_id = nodes_ids[id]
    generationUnit = GenerationUnit(
        unit_id=id + nbUnitsConventionnal,
        node_id=node_id,
        unit_type="wind_turbine",
        cost=costs[id],
        pmax=pmax[id],
        pmin=pmin[id],
        availability=availability[:24],
        ramp_up=10000,  # big M, for no constraint on rampu_up
        ramp_down=0,
        prod_init=0,
    )
    nodes.add_generationUnit(id_node=node_id,generationUnit=generationUnit)
    generation_units.add_unit(generationUnit)

################################################################################
# Creation of Loads Units
################################################################################

from scripts.loadUnits import LoadUnits, LoadUnit

# parameter load
total_needed_demand = pd.read_csv("inputs/load_profile.csv", sep=";")["total_demand"].values
nbHour = total_needed_demand.shape[0]

load_location = pd.read_csv("inputs/load_location.csv", index_col="load_number", sep=";")
nodes_ids = load_location["node"].values - 1
load_percentage = load_location["load_percentage"].values

load_units = LoadUnits()
nbLoadUnits = load_location.shape[0]
for unit_id in range(nbLoadUnits):

    node_id = nodes_ids[unit_id]
    loadUnit = LoadUnit(
        unit_id=unit_id,
        node_id=node_id,
        bid_price=50,
        load_percentage=load_percentage[unit_id],
        total_needed_demand=total_needed_demand,
    )
    nodes.add_loadUnit(id_node=node_id,loadUnit=loadUnit)
    load_units.add_unit(loadUnit)

################################################################################
# Adding of the battery
################################################################################
efficiency = np.sqrt(0.937)
min_SoC = 0  # minimum of state of charge
max_SoC = 600  # MWh maximum of state of charge = battery capacity
value_init = max_SoC / 2
P_max = 150  # MW
delta_t = 1  # hour

################################################################################
# Model
################################################################################

m = gp.Model()

# Variables
production = m.addMVar(
    shape=(nbHour, nbUnits), lb=0, name="power_generation", vtype=GRB.CONTINUOUS
)
demand_supplied = m.addMVar(
    shape=(nbHour, nbLoadUnits), lb=0, name=f"demand_supplied", vtype=GRB.CONTINUOUS
)
state_of_charge = m.addMVar(
    shape=(nbHour,),
    lb=min_SoC,
    ub=max_SoC,
    name=f"SoC",
    vtype=GRB.CONTINUOUS,
)
power_injected = m.addMVar(
    shape=(nbHour,),
    lb=0,
    ub=P_max,
    name=f"power_injected",
    vtype=GRB.CONTINUOUS,
)
power_drawn = m.addMVar(
    shape=(nbHour,),
    lb=0,
    ub=P_max,
    name=f"power_drawn",
    vtype=GRB.CONTINUOUS,
)
voltage_angle = m.addMVar(
    shape=(nbHour, nbNode), 
    name="voltage_angle", 
    vtype=GRB.CONTINUOUS
)

# Objective function
objective = gp.quicksum(
gp.quicksum(
    demand_supplied[t, l] * load_units.get_bid_price(l)
    for l in range(nbLoadUnits)
) - gp.quicksum(
    production[t, g] * generation_units.get_cost(g)
    for g in range(nbUnits)
)
for t in range(nbHour)
)
m.setObjective(objective, GRB.MAXIMIZE)

# generation units have a max
for g in range(nbUnits):
    for t in range(nbHour):
        m.addConstr(
            production[t, g]
            <= generation_units.get_pmax(g)
            * generation_units.get_availability(g)[t],
            name=f"PMAX_generation_unit_{g}_at_time_{t}"
        )

# Cannot supply more than necessary
for l in range(nbLoadUnits):
    for t in range(nbHour): 
        m.addConstr(
            demand_supplied[t, l] <= load_units.get_total_needed_demand(l)[t],
            name=f"PMAX_load_unit_{g}_at_time_{t}"
            )

for n in range(nbNode):
    for t in range(nbHour):
        constraint = m.addConstr(
            sum(
                demand_supplied[t, l] for l in nodes.get_ids_load(n)
                )
            - sum(
                production[t, g] for g in nodes.get_ids_generation(n)
                )
            + (power_drawn[t] - power_injected[t]) * (n == (7 - 1))
            + sum(
                nodes.get_susceptance(n, to_node)
                * (voltage_angle[t, n] - voltage_angle[t, to_node])
                for to_node in nodes.get_to_node(n)
            )
            == 0,
            name=f"balancing_{n}_at_time_{t}"
        )

# Ramp-up and ramp-down constraint
for g in range(nbUnits):

    for t in range(nbHour):
        
        # Apply the special condition for t=0
        if t == 0:  
            pass
        #     m.addConstr(
        #         production[t, g] <= generation_units.get_prod_init(g) + generation_units.get_ramp_up(g),
        #         name=f"ramp_up_{g}_time_{t}"
        #     )
        #     m.addConstr(
        #         production[t, g] >= generation_units.get_prod_init(g) - generation_units.get_ramp_down(g),
        #         name=f"ramp_down_{g}_time_{t}"
        #     )
        # Apply the regular ramp-down constraint for t>0
        else:  
            m.addConstr(
                production[t, g] <= production[t - 1, g] + generation_units.get_ramp_up(g),
                name=f"ramp_up_{g}_time_{t}"
            )
            m.addConstr(
                production[t, g] >= production[t - 1, g] - generation_units.get_ramp_down(g),
                name=f"ramp_down_{g}_time_{t}"
            )


# Battery constraints
m.addConstr(state_of_charge[0] == value_init - (power_injected[0]/efficiency  - power_drawn[0]*efficiency),name=f"SoC_0")
for t in range(1,nbHour-1):
    m.addConstr(
        state_of_charge[t] == state_of_charge[t-1] + (power_drawn[t]*efficiency - power_injected[t]/efficiency )* delta_t,
        name=f"SoC_{t}"
    )    
m.addConstr(value_init - state_of_charge[-1] <= 0, name=f"SoC_finale")
m.addConstr(value_init - state_of_charge[-1] >= 0, name=f"SoC_finale")

# Node constraints
#Reference angle at bus 0 is equal to 0
for t in range(nbHour):
    m.addConstr(voltage_angle[t, 0] == 0, name=f"angle_reference_at_time_{t}") 

for t in range(nbHour):
    for n in range(nbNode):
        for to_node in nodes.get_to_node(n):
            m.addConstrs(
                - nodes.get_capacity(n, to_node)
                <= nodes.get_susceptance(n, to_node)
                * (voltage_angle[t, n] - voltage_angle[t, to_node]),
                name=f"power_flow_upper_limit_from_{n}_to_{to_node},at_time"
            )
            m.addConstrs(
                nodes.get_susceptance(n, to_node)
                * (voltage_angle[t, n] - voltage_angle[t, to_node])
                <= nodes.get_capacity(n, to_node),
                name=f"power_flow_upper_limit_from_{n}_to_{to_node},at_time"
            )

m.optimize()

#print(m.display())
print(m.status)
print('--'*40)
y=[]
for node_id in range(nbNode):

    print(f'\nNode: {node_id}')

    node_price = []
    node_generation = []
    ids_load = nodes.get_ids_load(node_id)    
    ids_generation = nodes.get_ids_generation(node_id)
    for t in range(nbHour):

        price = m.getConstrByName(f"balancing_{node_id}_at_time_{t}").Pi
        price = round(price,2)
        
        #print(f"Node {node_id}: ${price} - MWh{generation}")
        print(f"Node {node_id}: ${price}")

        if node_id == 19:
            y.append(price)

import matplotlib.pyplot as plt 
plt.figure()
plt.plot([i for i in range(24)],y,label='Clearing price')
plt.legend()
plt.xlabel('Hours')
plt.ylabel('c.u.')
plt.title("Day-Ahead clearing price at node 20")
plt.show()


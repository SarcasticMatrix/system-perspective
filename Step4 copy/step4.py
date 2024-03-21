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
init_SoC = max_SoC / 2
P_max = 150  # MW
delta_t = 1  # hour

################################################################################
# Model
################################################################################

def run_model(
        t:int,
        state_of_charge_previous:float
    ):

    m = gp.Model()

    # Variables
    production = m.addMVar(shape=nbUnits, lb=0, name="power_generation", vtype=GRB.CONTINUOUS)
    demand_supplied = m.addMVar(shape=nbLoadUnits, lb=0, name=f"demand_supplied", vtype=GRB.CONTINUOUS)
    state_of_charge = m.addMVar(shape=1,lb=min_SoC,ub=max_SoC,name=f"state_of_charge",vtype=GRB.CONTINUOUS)
    power_injected = m.addMVar(shape=1,lb=0,ub=P_max,name=f"power_injected",vtype=GRB.CONTINUOUS)
    power_drawn = m.addMVar(shape=1,lb=0,ub=P_max,name=f"power_drawn",vtype=GRB.CONTINUOUS)
    voltage_angle = m.addMVar(shape=nbNode,name="voltage_angle",vtype=GRB.CONTINUOUS)

    # Objective function
    objective = gp.quicksum(
        demand_supplied[l] * load_units.get_bid_price(l)
        for l in range(nbLoadUnits)
    ) - gp.quicksum(
        production[g] * generation_units.get_cost(g)
        for g in range(nbUnits)
    )
    m.setObjective(objective, GRB.MAXIMIZE)

    # generation units have a max
    for g in range(nbUnits):
        m.addConstr(
            production[g]
            <= generation_units.get_pmax(g)
            * generation_units.get_availability(g)[t],
            name=f"PMAX_generation_unit_{g}"
        )

    # Cannot supply more than necessary
    for l in range(nbLoadUnits):
        m.addConstr(
            demand_supplied[l] <= load_units.get_total_needed_demand(l)[t],
            name=f"PMAX_load_unit_{g}"
            )

    # Supplied demand match generation
    for n in range(nbNode):
        m.addConstr(
            sum(demand_supplied[l] for l in nodes.get_ids_load(n))
            - sum(production[g] for g in nodes.get_ids_generation(n))
            + (power_drawn - power_injected) * (n == (7 - 1))
            + sum(nodes.get_susceptance(n, to_node) * (voltage_angle[n] - voltage_angle[to_node]) for to_node in nodes.get_to_node(n))
            == 0,
            name=f"balancing_{n}"
        )

    # # Ramp-up and ramp-down constraint
    # for g in range(nbUnits):
            
    #     # Special condition for t = 0
    #     if t == 0:  
    #         m.addConstr(
    #                 production[g] <= generation_units.get_prod_init(g) + generation_units.get_ramp_up(g),
    #                 f"ramp_up_{g}"
    #             )
    #         m.addConstr(
    #                 production[g] >= generation_units.get_prod_init(g) - generation_units.get_ramp_down(g),
    #                 f"ramp_down_{g}"
    #             )
            
    #     # Regular ramp constraints for t > 0
    #     else:  
    #         m.addConstr(
    #                 production[g] <= production[t - 1, g] + generation_units.get_ramp_up(g),
    #                 f"ramp_up_{g}"
    #             )
    #         m.addConstr(
    #                 production[g] >= production[t - 1, g] - generation_units.get_ramp_down(g),
    #                 f"ramp_down_{g}"
    #             )

    # Battery constraints
    m.addConstr(
        state_of_charge == state_of_charge_previous + (power_drawn*efficiency - power_injected/efficiency) * delta_t,
        name=f"battery_SoC"
    )
    
    # m.addConstr(
    #     value_init - state_of_charge_last <= 0,
    #     "battery_final_state_of_charge"
    # )

    # Node constraints
    # Reference angle at bus 0 is equal to 0
    m.addConstr(
        voltage_angle[0] == 0,
        name=f"reference_angle_bus_0"
    ) 

    for from_node in range(nbNode):
        for to_node in nodes.get_to_node(from_node):
            m.addConstrs(
                - nodes.get_capacity(from_node, to_node) <= nodes.get_susceptance(from_node, to_node) * (voltage_angle[from_node] - voltage_angle[to_node]),
                name=f"power_flow_upper_limit_from_{from_node}_to_{to_node}"
            )

            m.addConstrs(
                nodes.get_susceptance(from_node, to_node) * (voltage_angle[from_node] - voltage_angle[to_node]) <= nodes.get_capacity(from_node, to_node),
                name=f"power_flow_lower_limit_from_{from_node}_to_{to_node}"
            )

    m.optimize()

    return m

for t in range(nbHour):
    print(f"\nHour {t}")

    m = run_model(t, init_SoC) 
    #print(m.display())
    for node_id in range(nbNode):
        constraint = m.getConstrByName(f"balancing_{node_id}[0]")
        price = constraint.Pi
        print(f"Price node {node_id}: {price}")
    init_SoC = m.getVarByName("state_of_charge[0]").X

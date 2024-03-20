import pandas as pd
import gurobipy as gp
import numpy as np
from gurobipy import GRB

################################################################################
# Creation of Conventionnal Generation Units
################################################################################

from scripts.generationUnits import GenerationUnits

# parameter unit
generationUnits_parameters = pd.read_csv("inputs/gen_parameters.csv", sep=";")

nodes = generationUnits_parameters["Node"].values - 1
costs = generationUnits_parameters["Ci"].values
pmax = generationUnits_parameters["Pmax"].values
pmin = generationUnits_parameters["Pmin"].values
Csu = generationUnits_parameters["Csu"].values  # Start-up cost
Uini = generationUnits_parameters["Uini"].values  # Initial state (1 if on, 0 else)
ramp_up = generationUnits_parameters[
    "RU"
].values  # Maximum augmentation of production (ramp-up)
ramp_down = generationUnits_parameters[
    "RD"
].values  # Maximum decrease of production (ramp-up)
prod_init = generationUnits_parameters["Pini"].values  # Initial production

generation_units = GenerationUnits()
nbUnitsConventionnal = generationUnits_parameters.shape[0]
for unit_id in range(nbUnitsConventionnal):
    generation_units.add_unit(
        unit_id=unit_id,
        node_id=nodes[unit_id],
        unit_type="conventionnal",
        cost=costs[unit_id],
        pmax=pmax[unit_id],
        pmin=pmin[unit_id],
        availability=[1] * 24,  # 100% availability for each hour
        ramp_up=ramp_up[unit_id],
        ramp_down=ramp_down[unit_id],
        prod_init=prod_init[unit_id],
    )

################################################################################
# Adding of the Wind Generation Units
################################################################################

wind_parameters = pd.read_csv("inputs/wind_parameters.csv", index_col="Unit", sep=";")
nodes = wind_parameters["Node"].values - 1
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

    generation_units.add_unit(
        unit_id=id + nbUnitsConventionnal,
        node_id=nodes[id],
        unit_type="wind_turbine",
        cost=costs[id],
        pmax=pmax[id],
        pmin=pmin[id],
        availability=availability[:24],
        ramp_up=10000,  # big M, for no constraint on rampu_up
        ramp_down=0,
        prod_init=0,
    )

#generation_units.export_to_json()

################################################################################
# Creation of Loads Units
################################################################################

from scripts.loadUnits import LoadUnits

# parameter load
total_needed_demand = pd.read_csv("inputs/load_profile.csv", sep=";")[
    "total_demand"
].values
nbHour = total_needed_demand.shape[0]

load_location = pd.read_csv(
    "inputs/load_location.csv", index_col="load_number", sep=";"
)
nodes = load_location["node"].values - 1
load_percentage = load_location["load_percentage"].values

load_units = LoadUnits()
nbLoadUnits = load_location.shape[0]
for unit_id in range(nbLoadUnits):
    load_units.add_unit(
        load_id=unit_id,
        node_id=nodes[unit_id],
        bid_price=50,
        load_percentage=load_percentage[unit_id],
        total_needed_demand=total_needed_demand,
    )

#load_units.export_to_json()

################################################################################
# Create the Nodes
################################################################################

from scripts.nodes import Nodes
from scripts.transmissionLine import TransmissionLine

nodes = Nodes()
nbNode = 24

for id_node in range(nbNode):

    print("-" * 40)
    print(f"Work on node: {id_node}")

    # We add the generation unit which are located at the node
    node_generation_units = GenerationUnits()
    print(" Generation units:")
    for unit in generation_units.units:
        if unit["Id node"]== id_node:
            print(f'  - a generation unit is added {unit["Id"]}' + " wind farm"*(unit["Type"] == "wind_turbine"))
            node_generation_units.add_constructed_unit(unit)

    # We add the load unit which are at located at the node
    node_load_units = LoadUnits()
    print(" Load units:")
    for unit in load_units.units:
        if unit["Id node"] == id_node:
            print(f'  - a load unit is added: {unit["Id"]}')
            node_load_units.add_constructed_unit(unit)

    # We add the transmission line
    print(" Transmission lines:")
    transmission_lines = []
    transmission_data = pd.read_csv("inputs/transmission_parameters.csv", sep=";")
    transmission_data["from"] += - 1
    transmission_data["to"] += - 1
    mask = (transmission_data["from"] == id_node) | (transmission_data["to"] == id_node)
    node_transmission_data = transmission_data.loc[mask]

    for row in range(len(node_transmission_data)):

        to_node = node_transmission_data.iloc[row, 1]
        if to_node == id_node:
            to_node = node_transmission_data.iloc[row, 0]

        susceptance = 1 / node_transmission_data.iloc[row, 2]
        capacity = node_transmission_data.iloc[row, 3]
        to_node = to_node
        transmissionLine = TransmissionLine(
            from_node=id_node,
            to_node=to_node,
            susceptance=susceptance,
            capacity=capacity,
        )
        transmission_lines.append(transmissionLine)

        print(f"  - a transmission line with node {to_node} is added")

    nodes.add_node(
        id=id_node,
        generationUnits=node_generation_units,
        loadUnits=node_load_units,
        transmissionLines=transmission_lines,
    )

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
    name=f"state_of_charge",
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
    demand_supplied[t, l] * load_units.units[l]["Bid price"]
    for l in range(nbLoadUnits)
) - gp.quicksum(
    production[t, g] * generation_units.units[g]["Cost"]
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
            <= generation_units.units[g]["PMAX"]
            * generation_units.units[g]["Availability"][t],
            f"PMAX_generation_unit_{g}_at_time_{t}"
        )

# Cannot supply more than necessary
for l in range(nbLoadUnits):
    for t in range(nbHour): 
        m.addConstr(
            demand_supplied[t, l] <= load_units.units[l]["Needed demand"][t],
            f"PMAX_load_unit_{g}_at_time_{t}"
            )

# Supplied demand match generation
balance_constraint = []
for n in range(nbNode):
    liste = []
    for t in range(nbHour):
        constraint = m.addConstr(
            sum(demand_supplied[t, l] for l in nodes.get_ids_load(n))
            - sum(production[t, g] for g in nodes.get_ids_generation(n))
            + (power_drawn[t] - power_injected[t]) * (n == (7 - 1))
            + sum(
                nodes.get_susceptances(n, to_node)
                * (voltage_angle[t, n] - voltage_angle[t, to_node])
                for to_node in nodes.get_to_node(n)
            )
            == 0
        )
        liste.append(constraint)
    balance_constraint.append(liste)

# Ramp-up and ramp-down constraint
ramp_up_constraint = []
ramp_down_constraint = []
for g in range(nbUnits):
    for t in range(nbHour):
        if t == 0:  # Apply the special condition for t=0
            ramp_up_constraint.append(
                m.addConstr(
                    production[t, g]
                    <= generation_units.units[g]["Initial production"]
                    + generation_units.units[g]["Ramp up"],
                )
            )
            ramp_down_constraint.append(
                m.addConstr(
                    production[t, g]
                    >= generation_units.units[g]["Initial production"]
                    - generation_units.units[g]["Ramp down"],
                )
            )
        else:  # Apply the regular ramp-down constraint for t>0
            ramp_up_constraint.append(
                m.addConstr(
                    production[t, g]
                    <= production[t - 1, g] + generation_units.units[g]["Ramp up"],
                )
            )
            ramp_down_constraint.append(
                m.addConstr(
                    production[t, g]
                    >= production[t - 1, g] - generation_units.units[g]["Ramp down"],
                )
            )


# Battery constraints
actualise_SoC = [
    m.addConstr(
        state_of_charge[t]
        == state_of_charge[t-1] + (power_drawn[t]*efficiency - power_injected[t]/efficiency )* delta_t
    )
    for t in range(1,nbHour)
]
m.addConstr(state_of_charge[0] == value_init - (power_injected[0]/efficiency  - power_drawn[0]*efficiency))
m.addConstr(value_init - state_of_charge[-1] <= 0)

# Node constraints
#Reference angle at bus 0 is equal to 0
power_flow_constraint_init = [
    m.addConstr(voltage_angle[t, 0] == 0) for t in range(nbHour)
]

power_flow_constraint_lower_limit = [
    m.addConstrs(
        - nodes.get_capacity(n, to_node)
        <= nodes.get_susceptances(n, to_node)
        * (voltage_angle[t, n] - voltage_angle[t, to_node])
        for to_node in nodes.get_to_node(n)
    )
    for n in range(nbNode)
    for t in range(nbHour)
]
power_flow_constraint_upper_limit = [
    m.addConstrs(
        nodes.get_susceptances(n, to_node)
        * (voltage_angle[t, n] - voltage_angle[t, to_node])
        <= nodes.get_capacity(n, to_node)
        for to_node in nodes.get_to_node(n)
    )
    for n in range(nbNode)
    for t in range(nbHour)
]
for t in range(nbHour):
    m.addConstr(voltage_angle[t, 0] == 0)


m.optimize()

for node_id in range(nbNode):

    print(f"Node {node_id}")
    for t in range(nbHour):
        
        constraint = balance_constraint[node_id][t]
        print(f"     {t}:",constraint.Pi)
    print("\n")
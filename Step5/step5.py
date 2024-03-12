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

nodes = generationUnits_parameters["Node"].values
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
nodes = wind_parameters["Node"].values
pmax = wind_parameters["Pmax"].values
pmin = wind_parameters["Pmin"].values
costs = wind_parameters["Ci"].values

scenario = "V1"  # scenario : from V1 to V100

nbUnitsWind = wind_parameters.shape[0]
nbUnits = nbUnitsConventionnal + nbUnitsWind
for unit_id in range(nbUnitsWind):

    availability = pd.read_csv(f"inputs/data/scen_zoneW{unit_id}.csv", sep=",")[
        scenario
    ].values.tolist()

    generation_units.add_unit(
        unit_id=unit_id + nbUnitsConventionnal,
        node_id=nodes[unit_id],
        unit_type="wind_turbine",
        cost=costs[unit_id],
        pmax=pmax[unit_id],
        pmin=pmin[unit_id],
        availability=availability[:24],
        ramp_up=10000,  # big M, for no constraint on rampu_up
        ramp_down=0,
        prod_init=0,
    )

generation_units.export_to_json()

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
nodes = load_location["node"].values
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

load_units.export_to_json()

################################################################################
# Create the Nodes
################################################################################

from scripts.nodes import Nodes
from scripts.transmissionLine import TransmissionLine

nodes = Nodes()
nbNode = 24

for id_node in range(1, nbNode + 1):

    print("-" * 40)
    print(f"Work on node: {id_node}")

    # We add the generation unit which are located at the node
    node_generation_units = GenerationUnits()
    print(" Generation units:")
    for unit in generation_units.units:
        if unit["Id node"] == id_node:
            print(f'  - a generation unit is added {unit["Id"]}')
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
    mask = (transmission_data["from"] == id_node) | (transmission_data["to"] == id_node)
    node_transmission_data = transmission_data.loc[mask]

    for row in range(len(node_transmission_data)):

        to_node = node_transmission_data.iloc[row, 1]
        if to_node == id_node:
            to_node = node_transmission_data.iloc[row, 0]

        susceptance = 1 / node_transmission_data.iloc[row, 2]
        capacity = node_transmission_data.iloc[row, 3]

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
# Create the Zones
################################################################################

from scripts.zone import Zone

node_ids_zone1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Id of the nodes in zone 1
node_ids_zone2 = [11, 12, 13, 14, 23, 20, 19, 16, 15, 24]  # Id of the nodes in zone 2
node_ids_zone3 = [17, 18, 21, 22]  # Id of the nodes in zone 3

zone1 = Zone()
zone2 = Zone()
zone3 = Zone()

for node in nodes.nodes:

    if node["Id"] in node_ids_zone1:
        zone1.add_constructed_node(node)
        print(f"Add node {node['Id']} in zone 1")
    elif node["Id"] in node_ids_zone2:
        zone2.add_constructed_node(node)
        print(f"Add node {node['Id']} in zone 2")
    elif node["Id"] in node_ids_zone3:
        zone3.add_constructed_node(node)
        print(f"Add node {node['Id']} in zone 3")
    else:
        print("Is not in a zone ?")

zone1.add_transmission_lines()
zone1.add_generation_units()
zone1.add_load_units()

zone2.add_transmission_lines()
zone2.add_generation_units()
zone2.add_load_units()

zone3.add_transmission_lines()
zone3.add_generation_units()
zone3.add_load_units()


# Il faut modifier les listes node_ids_zone1, node_ids_zone2 et node_ids_zone3 pour matcher avec les zones de Nico
# Sinon, réutiliser la Step2 pour chaque zone, puis gérer les transmissions entre chaque zone (normalement il suffit de faire que pour deux zones)
# Si j'ai pas fait n'importe quoi, la structure des données est la même que dans la Step2. Au lieu d'appeler generation_units, load_units etc. il suffit d'appler zone1.generation_units etc.et pouf ça fait ces chocopics

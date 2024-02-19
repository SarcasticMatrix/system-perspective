import pandas as pd
import gurobipy as gp
from gurobipy import GRB

import json 

################################################################################
# Creation of Conventionnal Generation Units
################################################################################

from generationUnits import GenerationUnits

# parameter unit
generationUnits_parameters = pd.read_csv('inputs/gen_parameters.csv', sep=';')

nodes = generationUnits_parameters['Node'].values
costs = generationUnits_parameters['Ci'].values 
pmax = generationUnits_parameters['Pmax'].values
pmin = generationUnits_parameters['Pmin'].values
Csu = generationUnits_parameters['Csu'].values
Uini = generationUnits_parameters['Uini'].values

generation_units = GenerationUnits()
nbUnits = generationUnits_parameters.shape[0] 
for unit_id in range(nbUnits):
    generation_units.add_unit(
        unit_id=unit_id,
        node_id=nodes[unit_id],
        unit_type="conventionnal",
        cost=costs[unit_id],
        pmax=pmax[unit_id],
        pmin=pmin[unit_id],
        availability=[1]*24
    )

################################################################################
# Adding of the Wind Generation Units
################################################################################

wind_parameters = pd.read_csv('inputs/wind_parameters.csv', index_col='Unit', sep=";")
nodes = wind_parameters['Node'].values
pmax = wind_parameters['Pmax'].values
pmin = wind_parameters['Pmin'].values
costs = wind_parameters['Ci'].values

scenario = "V1"

nbUnits = wind_parameters.shape[0]
for unit_id in range(nbUnits):

    availability = pd.read_csv('inputs/data/scen_zone8.csv', sep=",")[scenario].values.tolist()

    generation_units.add_unit(
        unit_id=unit_id,
        node_id=nodes[unit_id],
        unit_type="wind turbine",
        cost=costs[unit_id],
        pmax=pmax[unit_id],
        pmin=pmin[unit_id],
        availability=availability[:24]
    )

generation_units.export_to_json()

################################################################################
# Creation of Loads Units
################################################################################

from loadUnits import LoadUnits

#parameter load
total_needed_demand = pd.read_csv('inputs/load_profile.csv', sep=';')['total_demand'].values

load_location = pd.read_csv('inputs/load_location.csv', index_col='load_number', sep=';')
nodes = load_location['node'].values
load_percentage = load_location['load_percentage'].values

load_units = LoadUnits()
nbLoadUnits = load_location.shape[0]
for unit_id in range(nbLoadUnits):
    load_units.add_unit(
        load_id=unit_id,
        node_id=nodes[unit_id],
        bid_price=50,
        load_percentage=load_percentage[unit_id],
        total_needed_demand=total_needed_demand
    )

load_units.export_to_json()
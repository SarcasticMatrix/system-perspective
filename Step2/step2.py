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
nbUnitsConventionnal = generationUnits_parameters.shape[0] 
for unit_id in range(nbUnitsConventionnal):
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

scenario = "V1" #scenario : from V1 to V100

nbUnitsWind = wind_parameters.shape[0]
nbUnits = nbUnitsConventionnal + nbUnitsWind
for unit_id in range(nbUnitsWind):

    availability = pd.read_csv(f'inputs/data/scen_zoneW{unit_id}.csv', sep=",")[scenario].values.tolist()

    generation_units.add_unit(
        unit_id=unit_id,
        node_id=nodes[unit_id],
        unit_type="wind_turbine",
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
nbHour = total_needed_demand.shape[0]

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


################################################################################
# Model
################################################################################
# create a new model
m = gp.Model()

# Create variables 
production = m.addMVar(shape=(nbHour, nbUnits), lb=0, name="power_generation", vtype=GRB.CONTINUOUS)
demand_supplied = m.addMVar(shape=(nbHour, nbLoadUnits), lb=0, name=f"demand_supplied", vtype=GRB.CONTINUOUS) 

# Set objective function

objective = (gp.quicksum(demand_supplied[t, l]*load_units.units[l]['Bid price'] for t in range(nbHour) for l in range(nbLoadUnits)) 
        - gp.quicksum(production[t, g]*generation_units.units[g]['Cost'] for t in range(nbHour) for g in range(nbUnits)))

m.setObjective(objective, GRB.MAXIMIZE)

# define constraints
max_prod_constraint = [m.addConstr(production[t, g] <= generation_units.units[g]['PMAX']*generation_units.units[g]['Availability'][t]) for g in range(nbUnits) for t in range(nbHour)]
demand_supplied_constraint = [m.addConstr(demand_supplied[t, l] <= load_units.units[l]['Needed demand']) for l in range(nbLoadUnits) for t in range(nbHour)]
balance_constraint = [m.addConstr(sum(demand_supplied[t, l] for l in range(nbLoadUnits)) - gp.quicksum(production[t, g] for g in range(nbUnits)) == 0, name=f"GenerationBalance_{t+1}") for t in range(nbHour)]

# Solve it!
m.optimize()


################################################################################
# Result
################################################################################

production_values = [production[t].X for t in range(nbHour)]
demand_supplied_values = [demand_supplied[l].X for l in range(nbLoadUnits)]

price = [balance_constraint[t].Pi for t in range(nbHour)]
profit = [[production[t][g].X*(price[t] - generation_units.units[g]['Cost']) for g in range(nbUnits)] for t in range(nbHour)]

#result
print(f"Optimal objective value: {m.objVal} $")
for t in range(nbHour):
    for g in range(nbUnits):
        print(f"p_{g+1} for hour {t+1}: production: {production[t][g].X} MW, profit: {profit[t][g]} $")
print("clearing price:", price)
#modify the price print to remove the "array()"
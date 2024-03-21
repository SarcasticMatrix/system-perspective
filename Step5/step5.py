import pandas as pd
import gurobipy as gp
import numpy as np
from gurobipy import GRB
import sys
import os

# Ajoute le chemin du dossier Step2 à sys.path
chemin_dossier_step2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Step2'))
sys.path.insert(0, chemin_dossier_step2)

# Importe maintenant la fonction de step2.py
from step2 import step2_multiple_hours  

# cd C:\Users\julia\OneDrive\DTU\course\S2\46755 - Renewables in Electricity Markets\Assignment1 - git

################################################################################
# Creation of Conventionnal Generation Units
################################################################################

from generationUnits import GenerationUnits

# Parameter units
generationUnits_parameters = pd.read_csv("inputs/gen_parameters.csv", sep=";")

nodes = generationUnits_parameters["Node"].values
costs = generationUnits_parameters["Ci"].values
pmax = generationUnits_parameters["Pmax"].values
pmin = generationUnits_parameters["Pmin"].values
Csu = generationUnits_parameters["Csu"].values  # Start-up cost
Uini = generationUnits_parameters["Uini"].values  # Initial state (1 if on, 0 else)
ramp_up = generationUnits_parameters["RU"].values  # Maximum augmentation of production (ramp-up)
ramp_down = generationUnits_parameters["RD"].values  # Maximum decrease of production (ramp-up)
prod_init = generationUnits_parameters["Pini"].values  # Initial production
up_reserve = generationUnits_parameters["R+"].values # Up reserve capacity 
down_reserve = generationUnits_parameters["R-"].values # Down reserve capacity

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
        availability=[1] * 24,
        ramp_up=ramp_up[unit_id],
        ramp_down=ramp_down[unit_id],
        prod_init=prod_init[unit_id],
        up_reserve=up_reserve[unit_id],
        down_reserve=down_reserve[unit_id],
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
        up_reserve=0,
        down_reserve=0,
    )

generation_units.export_to_json()

################################################################################
# Creation of Loads Units
################################################################################

from loadUnits import LoadUnits

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
        bid_price=30,
        load_percentage=load_percentage[unit_id],
        total_needed_demand=total_needed_demand,
    )

load_units.export_to_json()


################################################################################
# Balancing bids
################################################################################
load_curtailment_cost = 400 # Demand curtailment cost: 400$/MWh
coef_up_regulation = 0.1
coef_down_regulation = 0.13

################################################################################
# Model
################################################################################

def step5_balancing_market(hour:int=17, outaged_generators:list=[10], delta_wind_production:list= [-0.1,0.15,0.15,-0.1,-0.1,-0.1],show_plots:bool=False):
    ############################################################################
    # Day-ahead market clearing
    ############################################################################

    day_ahead_model = step2_multiple_hours(show_plots=False)
    print("model", day_ahead_model)
    production = {t: {g: day_ahead_model.getVarByName(f'production of generator {g} at time {t}') for g in range(nbUnits)} for t in range(nbHour)}
    demand_supplied = {t: {l: day_ahead_model.getVarByName(f'Supplied demand to load {l} at time {t}') for l in range(nbLoadUnits)} for t in range(nbHour)}

    ############################################################################
    # Balancing market clearing
    ############################################################################
    t = hour # hour chosen for the balancing market clearing 

    # Balancing need calculation
    optimal_production = {g: production[t][g].X for g in range(nbUnits)} # Production in the day-ahead market clearing
    optimal_demand = {l: demand_supplied[t][l].x for l in range(nbLoadUnits)} # Supplied demand in the day-ahead market clearing

    delta_total_power = gp.quicksum(optimal_production[nbUnitsConventionnal + w]*delta_wind_production[w] for w in range(nbUnitsWind)) - gp.quicksum(optimal_production[g] for g in outaged_generators) # Lack or Surplus of power compared to day-ahead prediction
    balancing_need = - delta_total_power # Balancing need is the opposite of the surplus or lack of power

    # Balancing biding
    balance_constraint = day_ahead_model.getConstrByName(f'GenerationBalance_{t}')
    clearing_price = balance_constraint.Pi

    price_up_regulation = {g: clearing_price + generation_units.units[g]["Cost"]*coef_up_regulation for g in range(nbUnits) if g not in outaged_generators} # Conventional generators up-regulation price
    price_down_regulation = {g: clearing_price - generation_units.units[g]["Cost"]*coef_down_regulation for g in range(nbUnits) if g not in outaged_generators} # Conventional generators down-regulation price

    # Optimisation
    m = gp.Model()

    #variables
    up_production =  {g: m.addVar(
        lb=0, 
        ub=min(generation_units.units[g]["PMAX"] - optimal_production[g], generation_units.units[g]["Up reserve"]), #  Upper bound is the minimum between the up reserve capacity and the remaining power before reaching the generator's capacity
        name=f'up production of generator {g}',
        vtype=GRB.CONTINUOUS,        
        )
        for g in range(nbUnits) if g not in outaged_generators
    }     
    down_production =  {g: m.addVar(
        lb=0, 
        ub=min(generation_units.units[g]["PMAX"] - optimal_production[g], generation_units.units[g]["Down reserve"]), # Upper bound is the minimum between the down reserve capacity and the production of the day-ahead clearing
        name=f'down production of generator {g}',
        vtype=GRB.CONTINUOUS,        
        )
        for g in range(nbUnits) if g not in outaged_generators
    }  
    down_demand = {l: m.addVar( # Down-regulation load. 
        lb=0, 
        ub=optimal_demand[l], # Upper bound is the demand supplied after day-ahead clearing
        name=f'down production of generator {l}',
        vtype=GRB.CONTINUOUS,        
        )
        for l in range(nbLoadUnits)
    }  
    
    # Objective function
    objective = gp.quicksum(
        up_production[g] * price_up_regulation[g] - down_production[g] * price_down_regulation[g] for g in range(nbUnits) if g not in outaged_generators
    ) + gp.quicksum(
        load_curtailment_cost * down_demand[l] for l in range(nbLoadUnits)
    )
    m.setObjective(objective, GRB.MINIMIZE)
    
    # Constraints
    balancing_need_constraint = m.addLConstr(
        gp.quicksum( up_production[g] - down_production[g] for g in range(nbUnits) if g not in outaged_generators) 
        + gp.quicksum(down_demand[l] for l in range(nbLoadUnits))
        == balancing_need,
        name='Balancing need constraint'
    ) 
    
    # Optimise
    m.optimize()

    ################################################################################
    # Results
    ################################################################################
    # Get optimal values
    balancing_price = balancing_need_constraint.Pi 

    # Print results
    print("Day-ahead price: ", clearing_price)
    print("Balancing price: ", balancing_price)
    print("Balancing need: ", balancing_need)

    if not show_plots:
        return m
    
    return m


step5_balancing_market(show_plots=False)

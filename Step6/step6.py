import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import sys
import os

################################################################################
# Creation of Conventionnal Generation Units
################################################################################

from scripts.generationUnits import GenerationUnits

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
up_reserve_offer = generationUnits_parameters["Cu"].values #Up reserve offer price of the generating unit
down_reserve_offer = generationUnits_parameters["Cd"].values #Down reserve offer price of the generating unit

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
        up_reserve_offer=up_reserve_offer[unit_id],
        down_reserve_offer=down_reserve_offer[unit_id],
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
        up_reserve_offer=0,
        down_reserve_offer=0,
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

#load_units.export_to_json()


################################################################################
# Adding of the battery
################################################################################
efficiency = np.sqrt(0.937)
min_SoC = 0  # minimum of the battery capacity (called here Sate Of Charge but not in %)
max_SoC = 600  # MWh maximum of state of charge = battery capacity
value_init = max_SoC / 2 #Start with 50%
P_max = 150  # MW
delta_t = 1  # hour


################################################################################
# Balancing bids
################################################################################
load_curtailment_cost = 400 # Demand curtailment cost: 400$/MWh
coef_up_regulation = 0.1
coef_down_regulation = 0.13
reserve_up_needed = {}
reserve_down_needed = {}

# For each hour, the upward reserve requirement in the reserve market is 15% and the downward reserve requirement is 10% of the total demand in the corresponding hour.
for t in range(nbHour):
    reserve_up_needed[t] = total_needed_demand[t]*0.15
    reserve_down_needed[t] = total_needed_demand[t]*0.1


################################################################################
# Model
################################################################################

from scripts.plot_results import plot_results

def step6_reserve_market(
        outaged_generators : list = [10],
        delta_wind_production : list = [-0.1,0.15,0.15,-0.1,-0.1,-0.1],
        show_plots : bool = False
    ):
    ############################################################################
    # Reserve market clearing
    ############################################################################  
    reserve_model = gp.Model()

    # Variables    
    up_reserve_generator = {t: {g: reserve_model.addVar(
        lb=0, 
        ub=generation_units.units[g]["Up reserve"],
        name=f'up reserve capacity of generator {g} at time {t}')
        for g in range(nbUnits)}
        for t in range(nbHour)
    } 

    down_reserve_generator = {t: {g: reserve_model.addVar(
        lb=0, 
        ub=generation_units.units[g]["Down reserve"],
        name=f'down reserve capacity of generator {g} at time {t}')
        for g in range(nbUnits)}
        for t in range(nbHour)
    } 

    # Objective function
    objective = gp.quicksum(
        gp.quicksum(
            generation_units.units[g]["Up reserve offer"]*up_reserve_generator[t][g] +
            generation_units.units[g]["Down reserve offer"]*down_reserve_generator[t][g]
            for g in range(nbUnits))
        for t in range(nbHour))  

    reserve_model.setObjective(objective, GRB.MINIMIZE)  # minimize reserve cost
    
    # Constraints
    total_up_reserve = {t: reserve_model.addLConstr(
        gp.quicksum(up_reserve_generator[t][g] for g in range(nbUnits))
        == reserve_up_needed[t],
        name=f'Total of up reserve at time {t}')
        for t in range(nbHour)
    }
    total_down_reserve = {t: reserve_model.addLConstr(
        sum(down_reserve_generator[t][g] for g in range(nbUnits))
        ==  reserve_down_needed[t],
        name=f'Total of down reserve at time {t}')
        for t in range(nbHour)
    }
    # up + down reserve can't exceed capacity 
    total_reserve = {t: {g: reserve_model.addLConstr(
        up_reserve_generator[t][g] + down_reserve_generator[t][g]
        <= generation_units.units[g]["PMAX"],
        name=f'Maximum reserve capacity for generator {g} at time {t}')
        for g in range(nbUnits)}
        for t in range(nbHour)
    }

    # Clearing reserve market
    reserve_model.optimize()

    ############################################################################
    # Day-ahead market clearing
    ############################################################################   
    
    m = gp.Model()

    # Variables
    production =  {t: {g: m.addVar(
        lb=down_reserve_generator[t][g].x, 
        ub=generation_units.units[g]["PMAX"] * generation_units.units[g]["Availability"][t] - up_reserve_generator[t][g].x,  
        name=f'production of generator {g} at time {t}',
        vtype=GRB.CONTINUOUS
        ) 
        for g in range(nbUnits)} for t in range(nbHour)}
  

    demand_supplied = {t: {l: m.addVar(
        lb=0, 
        ub=load_units.units[l]["Needed demand"][t],     # Cannot supply more than necessary
        name=f'Supplied demand to load {l} at time {t}',
        vtype=GRB.CONTINUOUS        
        )
        for l in range(nbLoadUnits)} for t in range(nbHour)
    }
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

    # Objective function
    objective = gp.quicksum(
        demand_supplied[t][l] * load_units.units[l]["Bid price"]
        for t in range(nbHour)
        for l in range(nbLoadUnits)
    )  - gp.quicksum(
        production[t][g] * generation_units.units[g]["Cost"]
        for t in range(nbHour)
        for g in range(nbUnits)
    ) 
    m.setObjective(objective, GRB.MAXIMIZE)

    # Constraints

    # Supplied demand match generation
    balance_constraint = [
        m.addConstr(
            sum(demand_supplied[t][l] for l in range(nbLoadUnits)) + power_drawn[t]
            - gp.quicksum(production[t][g] for g in range(nbUnits)) - power_injected[t] 
            == 0,
            name=f"GenerationBalance_{t}",
        )
        for t in range(nbHour)
    ]

    # Ramp-up and ramp-down constraint
    ramp_up_constraint = []
    ramp_down_constraint = []
    for g in range(nbUnits):
        for t in range(nbHour):
            if t == 0:  # Apply the special condition for t=0
                ramp_up_constraint.append(
                    m.addConstr(
                        production[t][g]
                        <= generation_units.units[g]["Initial production"]
                        + generation_units.units[g]["Ramp up"],
                    )
                )
                ramp_down_constraint.append(
                    m.addConstr(
                        production[t][g]
                        >= generation_units.units[g]["Initial production"]
                        - generation_units.units[g]["Ramp down"],
                    )
                )
            else:  # Apply the regular ramp-down constraint for t>0
                ramp_up_constraint.append(
                    m.addConstr(
                        production[t][g]
                        <= production[t-1][g] + generation_units.units[g]["Ramp up"],
                    )
                )
                ramp_down_constraint.append(
                    m.addConstr(
                        production[t][g]
                        >= production[t-1][g] - generation_units.units[g]["Ramp down"],
                    )
                )

    # Battery constraints
    actualise_SoC = [
        m.addConstr(
            state_of_charge[t]
            == state_of_charge[t-1] + (- power_injected[t]/efficiency  + power_drawn[t]*efficiency)* delta_t
        )
        for t in range(1,nbHour)
    ]
    m.addConstr(state_of_charge[0] == value_init )# - (power_injected[0]/efficiency  - power_drawn[0]*efficiency))
    m.addConstr(value_init - state_of_charge[-1] <= 0)


    m.optimize()

    ################################################################################
    # Results
    ################################################################################

    clearing_price = [balance_constraint[t].Pi for t in range(nbHour)]
    clearing_price_values = [
        price_item.flatten()[0] for price_item in clearing_price
    ]  # remove the array values

    # Print results

    print('Social welfare reserve:', round(reserve_model.ObjVal, 2))
    print('Social welfare day ahead:', round(m.ObjVal, 2))

    profit = [
        [
            production[t][g].X * (clearing_price[t] - generation_units.units[g]["Cost"])
            for g in range(nbUnits)
        ]
        for t in range(nbHour)
    ]

    

    demand_unsatisfied = [
        total_needed_demand[t] - np.sum(demand_supplied[t][l].X for l in range(nbLoadUnits))
        for t in range(nbHour)
    ]

    # print result
    # print(f"Optimal objective value: {m.objVal} $")
    # for t in range(nbHour):
    #     for g in range(nbUnits):
    #         print(
    #             f"p_{g+1} for hour {t+1}: production: {round(production[t][g].X,2)} MW, profit: {round(profit[t][g],2)}  $"
    #         )
    #     print(f"clearing price for hour {t+1}:", clearing_price_values[t])
    #     print("\n")
    # print("clearing price:", clearing_price_values)
    # print("demand unsatisfied:", demand_unsatisfied)
    # print("SoC:", state_of_charge.X)

    results = pd.DataFrame()
    results["Hour"] = np.arange(nbHour)
    for g in range(nbUnits):
        results[f"PU production {g+1} (GW)"] = [production[t][g].X for t in range(nbHour)]
        results[f"PU profit {g+1} ($)"] = [profit[t][g] for t in range(nbHour)]
    results["Clearing price"] = clearing_price_values
    results["Demand"] = total_needed_demand
    results["Demand satisfied"] = total_needed_demand - demand_unsatisfied
    results["Demand unsatisfied"] = demand_unsatisfied
    results["Battery production"] = - power_injected.X + power_drawn.X
    results["State of charge"] = state_of_charge.X / max_SoC
    results["Battery profit"] = -results["Clearing price"] * results["Battery production"]
    results["up reserve price"] = [total_up_reserve[t].Pi for t in range(nbHour)]
    results["down reserve price"] = [total_down_reserve[t].Pi for t in range(nbHour)]
    results["up reserve generator"] = {t: {g: up_reserve_generator[t][g].X for g in range(nbUnits)} for t in range(nbHour)}
    results["down reserve generator"] = {t: {g: down_reserve_generator[t][g].X for g in range(nbUnits)} for t in range(nbHour)}

    # if show_plots:
    #     plot_results(nbUnits=nbUnits, results=results)


    # Plotting the reserve markets results.
    fig, axs = plt.subplots(2,1, figsize=(3,2), dpi=250)
    df_up_reserve= pd.DataFrame.from_dict(results["up reserve generator"])
    df_up_reserve = df_up_reserve.loc[:, (df_up_reserve != 0).any(axis=0)]
    df_up_reserve.plot(kind='bar', stacked=True, ax=axs[0])
    axs1_twin = axs[0].twinx()
    axs1_twin.step(results["up reserve price"], 'k-', label='price')
    axs1_twin.set(ylabel='price [$/MW]')
    axs1_twin.legend()
    axs[0].set(xlabel='Time [h]',
            ylabel='Up reserve capacity [MW]',
            title='Up reserve market'
            )
    
    df_down_reserve= pd.DataFrame.from_dict(results["down reserve generator"])
    df_down_reserve = df_down_reserve.loc[:, (df_down_reserve != 0).any(axis=0)]
    df_down_reserve.plot(kind='bar', stacked=True, ax=axs[0])
    axs2_twin = axs[0].twinx()
    axs2_twin.step(results["down reserve price"], 'k-', label='price')
    axs2_twin.set(ylabel='price [$/MW]')
    axs2_twin.legend()
    axs[0].set(xlabel='Time [h]',
            ylabel='Down reserve capacity [MW]',
            title='Down reserve market'
            )

    

    return m

step6_reserve_market(show_plots=True)






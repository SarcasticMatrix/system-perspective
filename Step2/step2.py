import pandas as pd
import gurobipy as gp
import numpy as np
from gurobipy import GRB

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
        availability=[1] * 24,
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

def step2_multiple_hours(show_plots:bool=False):
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

    # Objective function
    objective = gp.quicksum(
        demand_supplied[t, l] * load_units.units[l]["Bid price"]
        for t in range(nbHour)
        for l in range(nbLoadUnits)
    )  - gp.quicksum(
        production[t, g] * generation_units.units[g]["Cost"]
        for t in range(nbHour)
        for g in range(nbUnits)
    ) 
    m.setObjective(objective, GRB.MAXIMIZE)

    # Constraints

    # generation unitsPhave a _max
    max_prod_constraint = [
        m.addConstr(
            production[t, g]
            <= generation_units.units[g]["PMAX"]
            * generation_units.units[g]["Availability"][t]
        )
        for g in range(nbUnits)
        for t in range(nbHour)
    ]

    # Cannot supply more than necessary
    demand_supplied_constraint = [
        m.addConstr(demand_supplied[t, l] <= load_units.units[l]["Needed demand"][t])
        for l in range(nbLoadUnits)
        for t in range(nbHour)
    ]

    # Supplied demand match generation
    balance_constraint = [
        m.addConstr(
            sum(demand_supplied[t, l] for l in range(nbLoadUnits)) + power_drawn[t]
            - gp.quicksum(production[t, g] for g in range(nbUnits)) - power_injected[t] 
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
            == state_of_charge[t-1] + (- power_injected[t]/efficiency  + power_drawn[t]*efficiency)* delta_t
        )
        for t in range(1,nbHour)
    ]
    m.addConstr(state_of_charge[0] == value_init )# - (power_injected[0]/efficiency  - power_drawn[0]*efficiency))
    m.addConstr(value_init - state_of_charge[-1] <= 0)


    m.optimize()

    if not show_plots:
        return m

    ################################################################################
    # Results
    ################################################################################

    clearing_price = [balance_constraint[t].Pi for t in range(nbHour)]
    clearing_price_values = [
        price_item.flatten()[0] for price_item in clearing_price
    ]  # remove the array values

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
    #             f"p_{g+1} for hour {t+1}: production: {production[t][g].X} MW, profit: {profit[t][g]} $"
    #         )
    #     print(f"clearing price for hour {t+1}:", clearing_price_values[t])
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

    from plot_results import plot_results

    plot_results(nbUnits=nbUnits, results=results)

    return m

step2_multiple_hours(show_plots=True)


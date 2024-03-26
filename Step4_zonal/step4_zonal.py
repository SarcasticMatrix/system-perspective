import pandas as pd
import gurobipy as gp
import numpy as np
from gurobipy import GRB

################################################################################
# Initialisaiton of nodes
################################################################################
from scripts.nodes import Nodes

nbNode = [i for i in range(24)]
nodes = Nodes(list_ids=nbNode)

################################################################################
# Creation of Conventionnal Generation Units
################################################################################

from scripts.generationUnits import GenerationUnits,GenerationUnit

# parameter unit
generationUnits_parameters = pd.read_csv("../inputs/gen_parameters.csv", sep=";")
nodes_ids = generationUnits_parameters["Node"].values - 1
costs = generationUnits_parameters["Ci"].values
pmax = generationUnits_parameters["Pmax"].values
pmin = generationUnits_parameters["Pmin"].values
Csu = generationUnits_parameters["Csu"].values  # Start-up cost
Uini = generationUnits_parameters["Uini"].values  # Initial state (1 if on, 0 else)
ramp_up = generationUnits_parameters["RU"].values  # Maximum augmentation of production (ramp-up)
ramp_down = generationUnits_parameters["RD"].values  # Maximum decrease of production (ramp-up)
prod_init = generationUnits_parameters["Pini"].values  # Initial production

generationUnits = GenerationUnits()
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
    generationUnits.add_unit(generationUnit)

################################################################################
# Adding of the Wind Generation Units
################################################################################

wind_parameters = pd.read_csv("../inputs/wind_parameters.csv", index_col="Unit", sep=";")
nodes_ids = wind_parameters["Node"].values - 1
pmax = wind_parameters["Pmax"].values
pmin = wind_parameters["Pmin"].values
costs = wind_parameters["Ci"].values

scenario = "V1"  # scenario : from V1 to V100

nbUnitsWind = wind_parameters.shape[0]
nbUnits = nbUnitsConventionnal + nbUnitsWind
for id in range(nbUnitsWind):

    availability = pd.read_csv(f"../inputs/data/scen_zoneW{id}.csv", sep=",")[
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
    generationUnits.add_unit(generationUnit)

################################################################################
# Creation of Loads Units
################################################################################

from scripts.loadUnits import LoadUnits, LoadUnit

# parameter load
total_needed_demand = pd.read_csv("../inputs/load_profile.csv", sep=";")["total_demand"].values
nbHour = total_needed_demand.shape[0]

load_location = pd.read_csv("../inputs/load_location.csv", index_col="load_number", sep=";")
nodes_ids = load_location["node"].values - 1
load_percentage = load_location["load_percentage"].values

loadUnits = LoadUnits()
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
    loadUnits.add_unit(loadUnit)

################################################################################
# Creation of Transmission Lines
################################################################################
from scripts.transmissionLines import TransmissionLine

transmission_data = pd.read_csv("../inputs/transmission_parameters.csv", sep=";")
transmission_data["from"] += - 1
transmission_data["to"] += - 1

for node in nodes.nodes:
    id_node = node.id_node
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
        node.add_transmissionLine(transmissionLine)

################################################################################
# Create the Zones
################################################################################

from scripts.zone import Zone

# Python convention
node_ids_zone1 = [2, 13, 14, 15, 16, 17, 20, 21, 23]  # Id of the nodes in zone 1
node_ids_zone2 = [5, 9, 11, 12, 18, 19, 22]  # Id of the nodes in zone 2
node_ids_zone3 = [0, 1, 3, 4, 6, 7, 8, 10]  # Id of the nodes in zone 3

zone1 = Zone([])
zone2 = Zone([])
zone3 = Zone([])

for node in nodes.nodes:

    if node.id_node in node_ids_zone1:
        zone1.add_node(node)
        print(f"Add node {node.id_node + 1 } in zone 1")
    elif node.id_node in node_ids_zone2:
        zone2.add_node(node)
        print(f"Add node {node.id_node + 1} in zone 2")
    elif node.id_node in node_ids_zone3:
        zone3.add_node(node)
        print(f"Add node {node.id_node + 1} in zone 3")
    else:
        print("Is not in a zone ?")

zone1.add_transmissionLines()
zone1.add_generationUnits()
zone1.add_loadUnits()

zone2.add_transmissionLines()
zone2.add_generationUnits()
zone2.add_loadUnits()

zone3.add_transmissionLines()
zone3.add_generationUnits()
zone3.add_loadUnits()

zones = [zone1, zone2, zone3]

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

def run_model():
    m = gp.Model()

    # Variables
    production = m.addMVar(shape=(nbHour, nbUnits), lb=0, name="power_generation", vtype=GRB.CONTINUOUS)
    demand_supplied = m.addMVar(shape=(nbHour, nbLoadUnits), lb=0, name=f"demand_supplied", vtype=GRB.CONTINUOUS)
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
    flow_interzonal = m.addMVar(
        shape=(nbHour, len(zones), len(zones)),
        name=f"flow_interzonal",
        vtype=GRB.CONTINUOUS,
    )

    # Objective function
    objective = gp.quicksum(
        gp.quicksum( gp.quicksum(
            demand_supplied[t, l] * zone.loadUnits.get_bid_price(l)
            for l in zone.get_id_loads()
        )
        for zone in zones
    ) 
    - gp.quicksum(
        sum(
            production[t, g] * zone.generationUnits.get_cost(g)
            for g in zone.get_id_generators()
        )
        for zone in zones
    )
    for t in range(nbHour)
    )
    m.setObjective(objective, GRB.MAXIMIZE)

    # Constraints

    # generation unitsP have a P_max
    max_prod_constraint = [
        m.addConstr(
            production[t, g]
            <= zone.generationUnits.get_pmax(g)
            * zone.generationUnits.get_availability(g)[t],
            name=f"max_prod_constraint_{t}_{g}"
        )
        for t in range(nbHour)
        for zone in zones
        for g in zone.get_id_generators()
    ]


    # Cannot supply more than necessary
    max_demand_supplied_constraint = [
        m.addConstr(
            demand_supplied[t, l] <= zone.loadUnits.get_total_needed_demand(l)[t],
            name=f"max_demand_supplied_constraint_{t}_{l}"
        )
        for t in range(nbHour)
        for zone in zones
        for l in zone.get_id_loads()
    ]

    # Supplied demand match generation
    balance_constraint = []
    for z, zone in zip(range(len(zones)), zones):
        liste = []
        for t in range(nbHour):
            constraint = m.addConstr(
                sum(demand_supplied[t, l] for l in zone.get_id_loads())
                - gp.quicksum(production[t, g] for g in zone.get_id_generators())
                - (power_injected[t] - power_drawn[t]) * (z == 2)
                + sum(flow_interzonal[t, z, notz] for notz in range(len(zones)))
                == 0,
                name=f"balance_constraint_{z}_{t}"
            )
            liste.append(constraint)
        balance_constraint.append(liste)

    # Ramp-up and ramp-down constraint
    ramp_up_constraint = []
    ramp_down_constraint = []
    for zi, zoneZ in zip(range(len(zones)), zones):  # for each zones:
        for g in zoneZ.get_id_generators():
            for t in range(nbHour):
                if t == 0:  # Apply the special condition for t=0
                    ramp_up_constraint.append(
                        m.addConstr(
                            production[t, g]
                            <= zoneZ.generationUnits.get_prod_init(g)
                            + zoneZ.generationUnits.get_ramp_up(g),
                            name=f"ramp_up_ini_{t}_{g}_{zi}",
                        )
                    )
                    ramp_down_constraint.append(
                        m.addConstr(
                            production[t, g]
                            >= zoneZ.generationUnits.get_prod_init(g)
                            - zoneZ.generationUnits.get_ramp_down(g),
                            name=f"ramp_down_ini_{t}_{g}_{zi}",
                        )
                    )
                else:  # Apply the regular ramp-down constraint for t>0
                    ramp_up_constraint.append(
                        m.addConstr(
                            production[t, g]
                            <= production[t - 1, g]
                            + zoneZ.generationUnits.get_ramp_up(g),
                            name=f"ramp_up_constraint_{zi}_{t}_{g}"
                        )
                    )
                    ramp_down_constraint.append(
                        m.addConstr(
                            production[t, g]
                            >= production[t - 1, g]
                            - zoneZ.generationUnits.get_ramp_down(g),
                            name=f"ramp_down_constraint_{zi}_{t}_{g}"
                        )
                    )

    # Battery constraints
    actualise_SoC = [
        m.addConstr(
            state_of_charge[t]
            == state_of_charge[t-1] + (- power_injected[t]/efficiency  + power_drawn[t]*efficiency)* delta_t, name=f"battery_{t}"
        )
        for t in range(1,nbHour)
    ]
    m.addConstr(state_of_charge[0] == value_init - (power_injected[0]/efficiency  - power_drawn[0]*efficiency))
    m.addConstr(value_init - state_of_charge[-1] <= 0)

    # Flow between zone constraints
    for z, zone_z in zip(range(len(zones)), zones):
        for notz, notzone_z in zip(range(len(zones)), zones):
            if z != notz:
                capacity = zone_z.compute_capacity_between_zones(notzone_z)
                print(f"Max capacity between zone {z+1} and zone {notz+1}", capacity)
                for t in range(nbHour):
                    m.addConstr(flow_interzonal[t, z, notz] <= capacity)
                    m.addConstr(flow_interzonal[t, z, notz] >= - capacity)
                    m.addConstr(flow_interzonal[t, z, notz] == - flow_interzonal[t, notz, z])
            else:
                for t in range(nbHour):
                    m.addConstr(flow_interzonal[t, z, notz] == 0)
                    m.addConstr(flow_interzonal[t, notz, z] == 0)

    m.optimize()

    ################################################################################
    # Results
    ################################################################################

    import numpy as np

    # Arrays pour stocker les données
    prices = np.zeros((nbHour, len(zones)))  # Prix dans les trois zones
    production_demand = np.zeros((nbHour, len(zones), 2))  # Production et demande dans chaque zone
    flows_between_zones = np.zeros((nbHour, len(zones), len(zones)))  # Flux entre les trois zones

    # Récupération des données après optimisation
    for zone_id in range(len(zones)):
        for t in range(nbHour):
            # Prix dans la zone actuelle
            prices[t, zone_id] = balance_constraint[zone_id][t].Pi
            
            # Production dans la zone actuelle
            production_demand[t, zone_id, 0] = sum(production[t, g].X for g in zones[zone_id].get_id_generators())
            
            # Demande dans la zone actuelle
            production_demand[t, zone_id, 1] = sum(demand_supplied[t, l].X for l in zones[zone_id].get_id_loads())
            
            # Flux entre les zones
            for notzone_id in range(len(zones)):
                if zone_id != notzone_id:
                    flows_between_zones[t, zone_id, notzone_id] = flow_interzonal[t, zone_id, notzone_id].X

    # Création des DataFrames à partir des arrays
    import pandas as pd

    # DataFrame pour les prix dans les zones
    prices_df = pd.DataFrame(prices, columns=[f"Zone_{zone_id+1}" for zone_id in range(len(zones))])

    # DataFrame pour la production et la demande dans chaque zone
    production_demand_df = pd.DataFrame(
        production_demand.reshape(-1, 6),
        columns=["Production_Zone_1", "Demand_Zone_1", "Production_Zone_2", "Demand_Zone_2", "Production_Zone_3", "Demand_Zone_3"]
    )

    # DataFrame pour les flux entre les zones
    flows_between_zones_df = pd.DataFrame(flows_between_zones.reshape(-1, 9))

    # Affichage des DataFrames
    print("Prix dans les zones:")
    print(prices_df)
    print("\nProduction et demande dans chaque zone:")
    print(production_demand_df)
    print("\nFlux entre les zones:")
    print(flows_between_zones_df)


    return m,prices_df, production_demand_df, flows_between_zones_df

# Access the results like this:
# - prices_df[zone_id]: DataFrame of prices in zone_id
# - production_demand_df[zone_id]: DataFrame of production and demand in zone_id
# - flow_df[zone_id][notzone_id]: DataFrame of flow from zone_id to notzone_id


# clearing_price = [balance_constraint[t].Pi for t in range(nbHour)]
# clearing_price_values = [
#     price_item.flatten()[0] for price_item in clearing_price
# ]  # remove the array values

# profit = [
#     [
#         production[t][g].X * (clearing_price[t] - generationUnits.units[g]["Cost"])
#         for g in range(nbUnits)
#     ]
#     for t in range(nbHour)
# ]

# demand_unsatisfied = [
#     total_needed_demand[t] - np.sum(demand_supplied[t][l].X for l in range(nbLoadUnits))
#     for t in range(nbHour)
# ]

# # print result
# # print(f"Optimal objective value: {m.objVal} $")
# # for t in range(nbHour):
# #     for g in range(nbUnits):
# #         print(
# #             f"p_{g+1} for hour {t+1}: production: {production[t][g].X} MW, profit: {profit[t][g]} $"
# #         )
# #     print(f"clearing price for hour {t+1}:", clearing_price_values[t])
# # print("clearing price:", clearing_price_values)
# # print("demand unsatisfied:", demand_unsatisfied)
# # print("SoC:", state_of_charge.X)

# results = pd.DataFrame()
# results["Hour"] = np.arange(nbHour)
# for g in range(nbUnits):
#     results[f"PU production {g+1} (GW)"] = [production[t][g].X for t in range(nbHour)]
#     results[f"PU profit {g+1} ($)"] = [profit[t][g] for t in range(nbHour)]
# results["Clearing price"] = clearing_price_values
# results["Demand"] = total_needed_demand
# results["Demand satisfied"] = total_needed_demand - demand_unsatisfied
# results["Demand unsatisfied"] = demand_unsatisfied
# results["Battery production"] = power_drawn.X - power_injected.X
# results["State of charge"] = state_of_charge.X / max_SoC
# results["Battery profit"] = - results["Clearing price"] * results["Battery production"]

# from scripts.plot_results import plot_results

# plot_results(nbUnits=nbUnits, results=results)

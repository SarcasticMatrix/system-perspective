import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import pandas as pd
import numpy as np


def plot_results(nbUnits: int, results: pd.DataFrame):

    print(results.columns)
    # Common variables
    hours = results["Hour"].values.tolist() + [24]
    fig, axs = plt.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": [1, 2]})

    # axs[0] variables
    state_of_charge = results["State of charge"].values.tolist()
    axs[0].step(
        hours,
        state_of_charge + [state_of_charge[-1]],
        where="post",
        linewidth=0.8,
        color="gray",
        label="SoC of the battery",
    )
    axs[0].axhline(y=0, linestyle="--", linewidth=0.5, color="gray")
    axs[0].axhline(y=1, linestyle="--", linewidth=0.5, color="gray")
    axs[0].set_ylabel("%")

    axs[0].legend(loc="upper left")
    axs[0].xaxis.grid(which="minor", linestyle="--", linewidth=0.1, color="gray")
    axs[0].grid(axis="x", linestyle="--", linewidth=0.5, color="gray")
    axs[0].xaxis.set_minor_locator(AutoMinorLocator())
    axs[0].yaxis.grid(which="major", linestyle="-", linewidth=0.1, color="gray")

    # axs[1] variables
    demand_needed = (results["Demand"] / 1000).values.tolist()
    axs[1].scatter(
        hours,
        demand_needed + [demand_needed[-1]],
        label="Actual Demand",
        c="red",
        marker="+",
    )

    demand_satisfied = (results["Demand satisfied"] / 1000).values.tolist()
    axs[1].step(
        hours,
        demand_satisfied + [demand_satisfied[-1]],
        where="post",
        linewidth=0.8,
        label="Demand Satisfied",
    )

    production = 0
    for g in range(nbUnits):
        production += results[f"PU production {g+1} (GW)"].values
    production = (production / 1000).tolist()
    axs[1].step(
        hours,
        production + [production[-1]],
        where="post",
        linewidth=0.8,
        label="Production",
        color="green",
    )

    battery_production = -results["Battery production"].values / 1000
    battery_production = battery_production.tolist()
    axs[1].step(
        hours,
        battery_production + [battery_production[-1]],
        where="post",
        linewidth=1,
        label="Battery Production",
        color="gray",
    )
    axs[1].axhline(y=0, linestyle="--", linewidth=0.5, color="gray")
    axs[1].set_ylabel("GW")
    axs[1].set_ylim(bottom=min(0, np.min(battery_production)) - 0.5)
    axs[1].set_xlabel("Hours")
    axs[1].legend()

    axs[1].xaxis.grid(which="minor", linestyle="--", linewidth=0.1, color="gray")
    axs[1].grid(axis="x", linestyle="--", linewidth=0.5, color="gray")
    axs[1].xaxis.set_minor_locator(AutoMinorLocator())
    axs[1].yaxis.grid(which="major", linestyle="-", linewidth=0.1, color="gray")

    plt.show()

    plt.figure()
    clearing_price = results["Clearing price"].values.tolist()
    plt.step(
        hours,
        clearing_price + [clearing_price[-1]],
        where="post",
        linewidth=0.8,
        color="blue",
        label="Clearing price",
    )
    plt.axhline(y=0, linestyle="--", linewidth=0.5, color="gray")
    plt.ylabel("€/GWh")
    plt.xlabel("Hours")
    plt.legend(loc="upper left")
    plt.grid(which="minor", linestyle="--", linewidth=0.1, color="gray")
    plt.grid(axis="x", linestyle="--", linewidth=0.5, color="gray")
    plt.grid(which="major", linestyle="-", linewidth=0.1, color="gray")
    plt.show()

    plt.figure()


import networkx as nx
from scripts.nodes import Nodes


def plot_nodes(nodes: Nodes):
    """ "
    - list_nodes:list,
    - list_edges:list, list of tuples
    - list_name_nodes:list,
    """
    G = nx.DiGraph()

    index = 1
    for node in nodes.nodes:
        G.add_nodes_from([node["Id"]])

        G.nodes[index]["nom"] = f"Node {index}"
        index += 1

        for to_node_id in nodes.get_to_node(node["Id"]):
            G.add_edges_from([(node["Id"], to_node_id)])
            G.edges[(node["Id"], to_node_id)]["Capacity"] = nodes.get_capacity(
                node["Id"], to_node_id
            )

    pos = nx.spring_layout(G)
    nx.draw(
        G,
        pos,
        with_labels=True,
        font_weight="bold",
        node_size=700,
        node_color="lightblue",
        font_color="black",
        font_size=8,
        arrowsize=10,
    )

    plt.show()

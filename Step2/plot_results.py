import matplotlib.pyplot as plt 
from matplotlib.ticker import AutoMinorLocator
import pandas as pd
import numpy as np

def plot_results(nbUnits: int, results: pd.DataFrame):

    print(results.head())
    # Common variables
    hours = results["Hour"].values.tolist() + [24]
    fig, axs = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [1, 2]})

    # axs[0] variables
    state_of_charge = results["State of charge"].values.tolist()
    axs[0].step(hours, state_of_charge + [state_of_charge[-1]], where='post', linewidth=0.8, color='gray', label="State of charge of the battery")
    axs[0].set_ylabel("%")
    axs[0].legend(loc='upper left')
    axs[0].xaxis.grid(which='minor', linestyle='--', linewidth=0.1, color='gray')
    axs[0].grid(axis='x', linestyle="--", linewidth=0.5, color="gray")
    axs[0].xaxis.set_minor_locator(AutoMinorLocator())
    axs[0].yaxis.grid(which='major', linestyle='-', linewidth=0.1, color='gray')
    
    # axs[1] variables
    demand_needed = (results["Demand"]/1000).values.tolist()
    axs[1].scatter(hours, demand_needed + [demand_needed[-1]], label="Actual Demand", c='red', marker='+')

    demand_satisfied = (results["Demand satisfied"]/1000).values.tolist()
    axs[1].step(hours, demand_satisfied + [demand_satisfied[-1]], where='post', linewidth=0.8, label="Demand Satisfied")

    production = 0
    for g in range(nbUnits):
        production += results[f"PU production {g+1} (MW)"].values
    production = (production/1000).tolist()
    axs[1].step(hours, production + [production[-1]], where='post', linewidth=0.8, label="Production", color='green')
    
    battery_production = -results["Battery production"].values/1000
    battery_production = battery_production.tolist()
    axs[1].step(hours, battery_production + [battery_production[-1]], where='post', linewidth=1, label="Battery Production", color='gray')
    axs[1].axhline(y=0, linestyle="--", linewidth=0.5, color="gray")
    axs[1].set_ylabel("MW")
    axs[1].set_ylim(bottom=min(0,np.min(battery_production))-0.5)
    axs[1].set_xlabel("Hours")
    axs[1].legend()
    
    axs[1].xaxis.grid(which='minor', linestyle='--', linewidth=0.1, color='gray')
    axs[1].grid(axis='x', linestyle="--", linewidth=0.5, color="gray")
    axs[1].xaxis.set_minor_locator(AutoMinorLocator())
    axs[1].yaxis.grid(which='major', linestyle='-', linewidth=0.1, color='gray')

    plt.show()




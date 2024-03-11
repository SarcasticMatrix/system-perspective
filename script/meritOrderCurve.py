import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from typing import Optional


class MeritOrderCurve:

    def __init__(
        self,
        productions: np.array,
        prod_marginal_costs: np.array,
        demands: np.array,
        demands_marginal_costs: Optional[np.array] = None,
        boolean_cst_demand: Optional[bool] = False,
    ):
        self.productions = productions
        self.prod_marginal_costs = prod_marginal_costs
        self.demands = demands
        self.demands_marginal_costs = demands_marginal_costs
        self.boolean_cst_demand = boolean_cst_demand

        self.minimum_bids = min(0, np.min(self.prod_marginal_costs))

        try:
            if self.demands_marginal_costs == None and self.boolean_cst_demand == False:
                self.boolean_cst_demand = True
                print(
                    "[Attention] Les coûts marginaux pour la demande n'ont pas été spécifiés, et il n'a pas été indiqué que la demande est constante."
                )
        except:
            None

    def prepare_curves_production(self):

        sorted_indices = np.argsort(self.prod_marginal_costs)
        sorted_productions = self.productions[sorted_indices]
        sorted_costs = self.prod_marginal_costs[sorted_indices]

        sorted_productions = np.cumsum(sorted_productions)
        print(
            f"Production ... \n Costs:      {sorted_costs} \n Production: {sorted_productions} \n "
        )

        sorted_productions = np.insert(sorted_productions, 0, 0)

        sorted_costs = np.insert(sorted_costs, 0, sorted_costs[0])
        return sorted_productions, sorted_costs

    def prepare_curves_demand(self):

        sorted_indices = np.argsort(self.demands_marginal_costs)[::-1].copy()
        sorted_productions = self.demands[sorted_indices].copy()
        sorted_costs = self.demands_marginal_costs[sorted_indices].copy()

        sorted_productions = np.cumsum(sorted_productions)

        print(
            f"Demand ... \n Costs:  {sorted_costs} \n Demand: {sorted_productions} \n "
        )

        sorted_productions = np.concatenate(
            (sorted_productions, np.array([sorted_productions[-1]]))
        )
        sorted_costs = np.concatenate((sorted_costs, np.array([self.minimum_bids])))

        return sorted_productions, sorted_costs

    def merit_order_curve(self):

        sorted_productions, sorted_productions_costs = self.prepare_curves_production()

        plt.figure()
        plt.step(
            sorted_productions,
            sorted_productions_costs,
            label="Supply Curve",
            where="pre",
        )

        if not self.boolean_cst_demand:
            sorted_demands, sorted_demands_costs = self.prepare_curves_demand()

            plt.step(
                sorted_demands, sorted_demands_costs, label="Demand Curve", where="pre"
            )
        else:
            plt.axvline(
                x=self.demands[0], color="r", linestyle="--", label="Demand Curve"
            )
        plt.xlabel("Aggregated Production")
        plt.ylabel("Marginal Cost")

        plt.xticks(np.arange(0, max(sorted_productions), 100))
        minor_locator = MultipleLocator(10)
        plt.gca().xaxis.set_minor_locator(minor_locator)
        plt.grid(True, which="major", linestyle="--", linewidth=0.7, color="gray")
        plt.grid(True, which="minor", linestyle="--", linewidth=0.3, color="lightgray")

        plt.title("Merit Order Curve")
        plt.legend()
        plt.show()


# ##############################################################################################
# ## EXAMPLE 1 #################################################################################
# ##############################################################################################

## Production
# prod = np.array(step1.p_max)
# prod_bids = np.array(step1.cost)

# # Demand
# demands = np.array(step1.demand)
# demands_bids = np.array([300])

# # Plot
# curve = MeritOrderCurve(prod,prod_bids,demands,demands_bids)
# curve.merit_order_curve()


# ##############################################################################################
# ## EXAMPLE 2 - with a constant demand ########################################################
# ##############################################################################################

# ## Production
# prod = np.array([100,100,200,50,100,50])
# prod_bids = np.array([-25,-30,10,80,40,70])

# # Demand
# demands = np.array([50])

# # Plot
# curve = MeritOrderCurve(prod,prod_bids,demands,boolean_cst_demand=True)
# curve.merit_order_curve()

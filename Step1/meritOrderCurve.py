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
            if len(self.productions) != len(self.prod_marginal_costs):
                raise ValueError(
                    "Productions and prod_marginal_costs must have the same length."
                )

        except ValueError as e:
            print(f"[Error] {e}")
            raise e
        except Exception as e:
            print(f"[Error] An unexpected error occurred: {e}")
            raise e

        if self.demands_marginal_costs is not None:
            try:
                if len(self.demands) != len(self.demands_marginal_costs):
                    print(
                        "[Warning] Demands and demands_marginal_costs must have the same length, unless there is a constant demand with a single bid."
                    )
                    self.boolean_cst_demand = True

                if (
                    self.boolean_cst_demand
                    and len(set(self.demands_marginal_costs)) > 1
                ):
                    print(
                        "[Warning] Multiple demand marginal costs found for constant demand. Ignoring marginal costs for demand."
                    )
                    self.demands_marginal_costs = None
                    self.boolean_cst_demand = True

                if self.boolean_cst_demand and len(set(self.demands)) > 1:
                    print(
                        "[Warning] Multiple demands found for constant demand marginal costs. Ignoring demand marginal costs."
                    )
                    self.demands_marginal_costs = None
                    self.boolean_cst_demand = True

            except Exception as e:
                None

    def prepare_curves_production(self):

        sorted_indices = np.argsort(self.prod_marginal_costs)
        sorted_productions = self.productions[sorted_indices]
        sorted_costs = self.prod_marginal_costs[sorted_indices]

        sorted_productions = np.cumsum(sorted_productions)

        sorted_productions = np.insert(sorted_productions, 0, 0)

        sorted_costs = np.insert(sorted_costs, 0, sorted_costs[0])
        return sorted_productions, sorted_costs

    def prepare_curves_demand(self):

        sorted_indices = np.argsort(self.demands_marginal_costs)[::-1].copy()
        sorted_productions = self.demands[sorted_indices].copy()
        sorted_costs = self.demands_marginal_costs[sorted_indices].copy()

        sorted_productions = np.cumsum(sorted_productions)

        sorted_productions = np.concatenate(
            (sorted_productions, np.array([sorted_productions[-1]]))
        )
        sorted_costs = np.concatenate((sorted_costs, np.array([self.minimum_bids])))

        return sorted_productions, sorted_costs

    def find_intersection_point(self):
        sorted_productions, sorted_productions_costs = self.prepare_curves_production()

        if not self.boolean_cst_demand:
            sorted_demands, sorted_demands_costs = self.prepare_curves_demand()

            min_len = min(len(sorted_productions_costs), len(sorted_demands_costs))
            sorted_productions_costs = sorted_productions_costs[:min_len]
            sorted_demands_costs = sorted_demands_costs[:min_len]

            idx_intersection = np.argmin(
                np.abs(sorted_productions_costs - sorted_demands_costs)
            )

            intersection_point = (
                sorted_demands[idx_intersection],
                sorted_productions_costs[idx_intersection],
            )

            return intersection_point
        else:
            constant_demand_value = self.demands[0]

            idx_intersection = np.argmax(sorted_productions >= constant_demand_value)

            intersection_point = (
                constant_demand_value,
                sorted_productions_costs[idx_intersection],
            )

            return intersection_point

    def merit_order_curve(self):

        sorted_productions, sorted_productions_costs = self.prepare_curves_production()
        print(
            f"Production ... \n Costs:      {sorted_productions_costs[1:]} \n Production: {sorted_productions[1:]} \n "
        )

        plt.figure(figsize=(15,15))
        plt.step(
            sorted_productions,
            sorted_productions_costs,
            label="Supply Curve",
            where="pre",
        )

        if not self.boolean_cst_demand:
            sorted_demands, sorted_demands_costs = self.prepare_curves_demand()

            print(
                f"Demand ... \n Costs:  {sorted_demands_costs[:-1]} \n Demand: {sorted_demands[:-1]} \n"
            )

            plt.step(
                sorted_demands,
                sorted_demands_costs,
                label="Demand Curve",
                where="pre",
                color="r",
            )
        else:
            plt.axvline(x=self.demands[0], color="r", label="Demand Curve")

        optimum_prod, optimum_price = self.find_intersection_point()

        plt.plot(optimum_prod, optimum_price, "rx")

        plt.xlabel("Generation capacity", fontweight="bold")
        plt.ylabel("Bids", fontweight="bold")

        plt.xticks(np.arange(0, max(sorted_productions), 100))
        minor_locator = MultipleLocator(10)
        plt.gca().xaxis.set_minor_locator(minor_locator)
        plt.grid(True, which="major", linestyle="--", linewidth=0.7, color="gray")
        plt.grid(True, which="minor", linestyle="--", linewidth=0.3, color="lightgray")

        plt.title(
            "Merit Order Curve \n" + rf"$p* = {optimum_price}$, $q* = {optimum_prod}$",
            pad=15,
            fontweight="bold",
        )
        plt.legend()
        plt.show()

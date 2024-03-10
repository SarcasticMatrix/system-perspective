import numpy as np
import json


class LoadUnits:
    def __init__(self):
        self.units = []

    def add_unit(
        self,
        load_id: int,
        node_id: int,
        bid_price: float,
        load_percentage: float,
        total_needed_demand: np.array,
    ):

        """
        - Id (int): id of the load unit.
        - Id node (int): id of the node where the load unit is located.
        - Bid price (float): to be fixed.
        - Load percentage (float): % of the load unit.
        - Needed demand (np.array): array of shape (24,) with the system demand of the unit load (in MW)
        """

        load = {
            "Id": load_id,
            "Id node": node_id,
            "Bid price": bid_price,
            "Load percentage": load_percentage,
            "Needed demand": total_needed_demand * load_percentage / 100,
            # "Supplied demand":
        }

        self.units.append(load)
    
    def add_constructed_unit(self, unit: dict):
        """
        Add a unit already defined in an other LoadUnits
        """
        self.units.append(unit)

    def export_to_json(self):
        print("Export load units data in a json file ...")

        # Create a json file for data visualisation

        nbr_units = len(self.units)

        dictionary = {f"Generation unit {j}": self.units[j] for j in range(nbr_units)}
        json_object = json.dumps(dictionary, default=lambda x: x.tolist(), indent=4)
        with open("Step2/data_loadUnits.json", "w") as outfile:
            outfile.write(json_object)

        print("Export is done ...")

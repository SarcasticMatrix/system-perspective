import numpy as np
import json

class LoadUnit:

    def __init__(
        self,
        unit_id: int,
        node_id: int,
        bid_price: float,
        load_percentage: float,
        total_needed_demand: np.array,
    ):
        """
        Adds a new load unit to the units list.

        Parameters:
            unit_id (int): The unique identifier for the load unit.
            node_id (int): The identifier of the node where the load unit is located.
            bid_price (float): The bid price for the load unit.
            load_percentage (float): The percentage of the load unit's capacity that is being utilized.
            total_needed_demand (np.array): A numpy array of shape (24,) representing the total system demand for the load unit in MW (megawatts) for each hour of the day.

        Each load unit is represented as a dictionary with keys corresponding to its attributes (Id, Id node, Bid price, Load percentage, and Needed demand) and their respective values.
        """
        
        self.unit_id = unit_id
        self.node_id = node_id
        self.bid_price = bid_price
        self.load_percentage = load_percentage
        self.total_needed_demand = total_needed_demand * load_percentage / 100


class LoadUnits:
    def __init__(self):
        self.units = []
    
    def add_unit(self, unit:LoadUnit):
        self.units.append(unit)

    def export_to_json(self):
        dictionary = {f"Load unit {unit.unit_id}": unit.transform_to_dict() for unit in self.units}
        json_object = json.dumps(dictionary, default=lambda x: x.tolist(), indent=4)
        with open("Step2/data_loadUnits.json", "w") as outfile:
            outfile.write(json_object)

    def get_ids(self):
        return [unit.unit_id for unit in self.units]

    def get_unit(self, unit_id:int):
        for unit in self.units:
            if unit.unit_id == unit_id:
                return unit
        print('No load found in LoadUnits.get_unit()')

    def get_bid_price(self, unit_id):
        unit = self.get_unit(unit_id=unit_id)
        return unit.bid_price

    def get_total_needed_demand(self, unit_id):
        unit = self.get_unit(unit_id=unit_id)
        return unit.total_needed_demand
    

    


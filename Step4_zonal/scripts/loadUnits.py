import numpy as np
import json


class LoadUnits:
    def __init__(self):
        """
        Initializes the LoadUnits class.

        Attributes:
            units (list): A list to store information about each load unit.
        """
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
        Adds a new load unit to the units list.

        Parameters:
            load_id (int): The unique identifier for the load unit.
            node_id (int): The identifier of the node where the load unit is located.
            bid_price (float): The bid price for the load unit.
            load_percentage (float): The percentage of the load unit's capacity that is being utilized.
            total_needed_demand (np.array): A numpy array of shape (24,) representing the total system demand for the load unit in MW (megawatts) for each hour of the day.

        Each load unit is represented as a dictionary with keys corresponding to its attributes (Id, Id node, Bid price, Load percentage, and Needed demand) and their respective values.
        """
        load = {
            "Id": load_id,
            "Id node": node_id,
            "Bid price": bid_price,
            "Load percentage": load_percentage,
            "Needed demand": total_needed_demand * load_percentage / 100,
        }

        self.units.append(load)

    def add_constructed_unit(self, unit: dict):
        """
        Adds a load unit that has already been defined elsewhere to the units list.

        Parameters:
            unit (dict): A dictionary representing a load unit with all necessary attributes (as defined in `add_unit` method).
        """
        self.units.append(unit)

    def export_to_json(self):
        """
        Exports the load units data to a JSON file for further analysis or visualization.

        The method serializes the list of load units into a JSON format and writes it to a file named "data_loadUnits.json" within the "Step2" directory.
        """
        print("Export load units data in a json file ...")

        nbr_units = len(self.units)

        # Creating a dictionary where each key is a unique identifier for a load unit and its value is the unit's data.
        dictionary = {f"Generation unit {j}": self.units[j] for j in range(nbr_units)}
        # Serializing the dictionary into JSON format, converting numpy arrays to lists where necessary.
        json_object = json.dumps(dictionary, default=lambda x: x.tolist(), indent=4)
        with open("Step2/data_loadUnits.json", "w") as outfile:
            outfile.write(json_object)

        print("Export is done ...")

    def get_ids(self):
        """
        Retrieves the unique identifiers (Ids) of all load units stored in the units list.

        Returns:
            A list of integers representing the Ids of all load units.
        """
        return [unit["Id"] for unit in self.units]

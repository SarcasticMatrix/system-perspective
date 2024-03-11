import json


class GenerationUnits:
    def __init__(self):
        """
        Initializes the GenerationUnits class.

        Attributes:
            units (list): A list to store information about each generation unit.
        """
        self.units = []

    def add_unit(
        self,
        unit_id: int,
        node_id: int,
        unit_type: str,
        cost: float,
        pmax: float,
        pmin: float,
        availability: list,
        ramp_up: float,
        ramp_down: float,
        prod_init: float,
    ):
        """
        Adds a new generation unit to the units list.

        Parameters:
            unit_id (int): The unique identifier for the generation unit.
            node_id (int): The identifier of the node where the generation unit is located.
            unit_type (str): The type of generation unit (e.g., 'thermal', 'solar', 'wind', etc.).
            cost (float): The cost of generation per unit output.
            pmax (float): The maximum power output capacity of the generation unit.
            pmin (float): The minimum power output capacity of the generation unit.
            availability (list): A list representing the availability of the unit over time (e.g., [1, 1, 0, 1] indicating availability for each hour).
            ramp_up (float): The rate at which the unit can increase its power output.
            ramp_down (float): The rate at which the unit can decrease its power output.
            prod_init (float): The initial production level of the unit.

        Each generation unit is represented as a dictionary with keys corresponding to its attributes (Id, Id node, Type, Cost, PMAX, PMIN, Availability, Ramp up, Ramp down, and Initial production) and their respective values.
        """
        unit = {
            "Id": unit_id,
            "Id node": node_id,
            "Type": unit_type,
            "Cost": cost,
            "PMAX": pmax,
            "PMIN": pmin,
            "Availability": availability,
            "Ramp up": ramp_up,
            "Ramp down": ramp_down,
            "Initial production": prod_init,
        }

        self.units.append(unit)

    def add_constructed_unit(self, unit: dict):
        """
        Adds a generation unit that has already been defined elsewhere to the units list.

        Parameters:
            unit (dict): A dictionary representing a generation unit with all necessary attributes (as defined in `add_unit` method).
        """
        self.units.append(unit)

    def export_to_json(self):
        """
        Exports the generation units data to a JSON file for further analysis or visualization.

        The method serializes the list of generation units into a JSON format and writes it to a file named "data_generationUnits.json" within the "Step2" directory.
        """
        print("Export generation units data in a json file ...")

        nbr_units = len(self.units)

        # Creating a dictionary where each key is a unique identifier for a generation unit and its value is the unit's data.
        dictionary = {f"Generation unit {j}": self.units[j] for j in range(nbr_units)}
        # Serializing the dictionary into JSON format, converting numpy arrays to lists where necessary.
        json_object = json.dumps(dictionary, default=lambda x: x.tolist(), indent=4)
        with open("Step2/data_generationUnits.json", "w") as outfile:
            outfile.write(json_object)

        print("Export is done ...")

    def get_ids(self):
        """
        Retrieves the unique identifiers (Ids) of all generation units stored in the units list.

        Returns:
            A list of integers representing the Ids of all generation units.
        """
        return [unit["Id"] for unit in self.units]

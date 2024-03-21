import json


class GenerationUnits:
    def __init__(self):
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
        up_reserve: float,
        down_reserve: float,
        up_reserve_offer: float,
        down_reserve_offer: float,
    ):

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
            "Up reserve": up_reserve,
            "Down reserve": down_reserve,
            "Up reserve offer": up_reserve_offer,
            "Down reserve offer": down_reserve_offer,
            # "Production":
        }

        self.units.append(unit)

    def export_to_json(self):
        print("Export generation units data in a json file ...")

        # Create a json file for data visualisation

        nbr_units = len(self.units)

        dictionary = {f"Generation unit {j}": self.units[j] for j in range(nbr_units)}
        json_object = json.dumps(dictionary, default=lambda x: x.tolist(), indent=4)
        with open("Step5/data_generationUnits.json", "w") as outfile:
            outfile.write(json_object)

        print("Export is done ...")


# # Exemple d'utilisation
# generation_units = GenerationUnits()

# generation_units.add_unit(1, "wind_turbine", 0, 200, 0, 0.8)
# generation_units.add_unit(2, "conventional", 500, 100, 50, 1.0)

# for unit in generation_units.units:
#     print(unit)

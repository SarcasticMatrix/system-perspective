import numpy as np

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
            availability: list
        ):

        unit = {
            "Id": unit_id,
            "Id node": node_id,
            "Type": unit_type,
            "Cost": cost,
            "PMAX": pmax,
            "PMIN": pmin,
            "Availability": availability,
            #"Production":
        }

        self.units.append(unit)


# # Exemple d'utilisation
# generation_units = GenerationUnits()

# generation_units.add_unit(1, "wind_turbine", 0, 200, 0, 0.8)
# generation_units.add_unit(2, "conventional", 500, 100, 50, 1.0)

# for unit in generation_units.units:
#     print(unit)


import json

class GenerationUnit:

    def __init__(
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
        
        self.unit_id = unit_id
        self.node_id = node_id
        self.unit_type = unit_type
        self.cost = cost
        self.pmax = pmax
        self.pmin = pmin
        self.availability = availability
        self.ramp_up = ramp_up
        self.ramp_down = ramp_down
        self.prod_init = prod_init

    def transform_to_dict(self) -> dict:
        dictionnary = {
            "Unit id" : self.unit_id,
            "Node id" : self.node_id,
            "Unit type" : self.unit_type,
            "Cost" : self.cost,
            "Pmax" : self.pmax,
            "Pmin" : self.pmin,
            "Availability" : self.availability,
            "Ramp up" : self.ramp_up,
            "Ramp down" : self.ramp_down,
            "Prod init" : self.prod_init,
        }   
        return dictionnary 


class GenerationUnits:
    def __init__(self):
        self.units = []
    
    def add_unit(self, unit : GenerationUnit):
        self.units.append(unit)

    def export_to_json(self):
        """
        Exports the generation units data to a JSON file for further analysis or visualization.
        """
        dictionary = {f"Generation unit {unit.unit_id}": unit.transform_to_dict() for unit in self.units}
        json_object = json.dumps(dictionary, default=lambda x: x.tolist(), indent=4)
        with open("Step2/data_generationUnits.json", "w") as outfile:
            outfile.write(json_object)

    def get_unit(self, unit_id:int):
        for unit in self.units:
            if unit.unit_id == unit_id:
                return unit
        print('No load found in LoadUnits.get_unit()')

    def get_cost(self, unit_id):
        unit = self.get_unit(unit_id=unit_id)
        return unit.cost

    def get_pmax(self, unit_id):
        unit = self.get_unit(unit_id=unit_id)
        return unit.pmax

    def get_availability(self, unit_id):
        unit = self.get_unit(unit_id=unit_id)
        return unit.availability
    
    def get_prod_init(self, unit_id):
        unit = self.get_unit(unit_id)
        return unit.prod_init
    
    def get_ramp_up(self, unit_id):
        unit = self.get_unit(unit_id)
        return unit.ramp_up
    
    def get_ramp_down(self, unit_id):
        unit = self.get_unit(unit_id)
        return unit.ramp_down
    
    def get_ids(self):
        return [unit.unit_id for unit in self.units]
    


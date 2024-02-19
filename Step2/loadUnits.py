import numpy as np

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
            'Bid price': bid_price,
            "Load percentage": load_percentage,
            "Needed demand": total_needed_demand*load_percentage/100,
            #"Supplied demand": 
        }

        self.units.append(load)
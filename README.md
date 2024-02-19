# Structure of the data


### GenerationUnits Class

The `GenerationUnits` class is designed to represent a collection of power generation units (conventional units **AND** wind turbines). This class provides a convenient way to add and store information about individual generation units.

Parameters:
- `unit_id`: Unique identifier for the unit (`int`).
- `node_id`: Identifier for the node to which the unit is connected (`int`).
- `unit_type`: Type of the unit (`str`) *wind turbine* or *conventionnal*. 
- `cost`: Cost of production for the unit (`float`).
- `pmax`: Maximum power output of the unit (`float`).
- `pmin`: Minimum power output of the unit (`float`).
- `availability`: List representing the availability schedule of the unit (`list`).

### LoadUnits Class

Parameters:
- `load_id`: Unique identifier for the load unit (`int`).
- `node_id`: Identifier for the node where the load unit is located (`int`).
- `bid_price`: Bid price for the load unit (`float`). To be fixed.
- `load_percentage`: Percentage of the total load (`float`).
- `total_needed_demand`: Array of shape `(24,)` representing the system demand of the load unit (in MW) for each hour of the day.
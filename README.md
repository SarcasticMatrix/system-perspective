# Structure of the data

### Nice coding habits 
Before committing and pushing codes, you should call the `black` package on your file: `python -m black {path_to_your_file}`.

### GenerationUnits Class

The `GenerationUnits` class is designed to represent a collection of power generation units (conventional units **AND** wind turbines). This class provides a convenient way to add and store information about individual generation units. 

This object is a `list` of `dict`. Each dictionnary has the following parameters:
- `unit_id`: Unique identifier for the unit (`int`).
- `node_id`: Identifier for the node to which the unit is connected (`int`).
- `unit_type`: Type of the unit (`str`) *wind turbine* or *conventionnal*. 
- `cost`: Cost of production for the unit (`float`).
- `pmax`: Maximum power output of the unit (`float`).
- `pmin`: Minimum power output of the unit (`float`).
- `availability`: List representing the availability schedule of the unit (`list`). 
- `Ramp up`: Ramp up of the unit (`float`).
- `Ramp down`: Ramp down of the unit (`float`).
- `Initial production`: Initital production of the unit (`float`).

You can export the generation units data with the methods `export_to_json`

### LoadUnits Class
The LoadUnits class represents a collection of load units in an electricity market. This class provides a convenient way to add and store information about individual load units. This object is a `list` of `dict`. 

Each dictionnary has the following parameters:
- `load_id`: Unique identifier for the load unit (`int`).
- `node_id`: Identifier for the node where the load unit is located (`int`).
- `bid_price`: Bid price for the load unit (`float`). To be fixed.
- `load_percentage`: Percentage of the total load (`float`), e.g. $3.8$.
- `needed_demand`: Array of shape `(24,)` representing the asked demand of the load unit (in MW) for each hour of the day. Is calculated as `total_needed_demand * load_percentage/100`.

You can export the load units data with the methods `export_to_json`

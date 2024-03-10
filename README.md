# Structure of the data

Before committing and pushing codes, you should call the `black` package on your file: `python -m black <path_to_your_file>`.


## Nodes class
**Overview:** The Nodes class represents nodes in a system (`list` of node), where each node is a dictionary with specific attributes such as id, generation units, load units, and transmission lines.

**Attributes**:
- `id` (`int`): The unique identifier for the node.
- `generationUnits` (`GenerationUnits`): All the generation units located at this node.
- `loadUnits` (`LoadUnits`): All the load units located at this node.
- `transmissionLines` (`list` of `TransmissionLine`): All the transmission lines located at this node.

**Methods**
- `add_node(id: int, generationUnits: GenerationUnits, loadUnits: LoadUnits, transmissionLines: list)`: Adds a new node to the system with the specified attributes.

## GenerationUnits Class
**Overview:** The GenerationUnits class represents generation units in the system (`list` of generation unit). Each generation unit is defined by attributes such as id, node id, unit type, cost, maximum and minimum power, availability, ramp up, ramp down, and initial production.

**Attributes**
- `unit_id` (`int`): The unique identifier for the generation unit.
- `node_id` (`int`): The id of the node where the generation unit is located.
- `unit_type` (`str`): The type of the generation unit.
- `cost` (`float`): The cost of the generation unit.
- `pmax` (`float`): The maximum power output of the generation unit.
- `pmin` (`float`): The minimum power output of the generation unit.
- `availability` (`list`): The availability of the generation unit.
- `ramp_up` (`float`): The ramp-up rate of the generation unit.
- `ramp_down` (`float`): The ramp-down rate of the generation unit.
- `prod_init` (`float`): The initial production of the generation unit.

**Methods**
- `add_unit(unit_id: int, node_id: int, unit_type: str, cost: float, pmax: float, pmin: float, availability: list, ramp_up: float, ramp_down: float, prod_init: float)`: Adds a new generation unit to the system with the specified attributes.
- `add_constructed_unit(unit: dict)`: Adds a generation unit already defined in another GenerationUnits instance.
- `export_to_json()`: Exports generation units data to a JSON file for data visualization.

## LoadUnits Class
**Overview:** The LoadUnits class represents load units in the system (`list` of load unit). Each load unit is defined by attributes such as id, node id, bid price, load percentage, and needed demand over 24 hours.

**Attributes**
- `load_id` (`int`): The unique identifier for the load unit.
- `node_id` (`int`): The id of the node where the load unit is located.
- `bid_price` (`float`): The bid price to be fixed for the load unit.
- `load_percentage` (`float`): The percentage of the load unit.
- `total_needed_demand` (`np.array`): An array of shape (24,) with the system demand of the unit load (in MW).

**Methods**
- `add_unit(load_id: int, node_id: int, bid_price: float, load_percentage: float, total_needed_demand: np.array)`: Adds a new load unit to the system with the specified attributes.
- `add_constructed_unit(unit: dict)`: Adds a load unit already defined in another LoadUnits instance.
- `export_to_json()`: Exports load units data to a JSON file for data visualization.

## Transmission Class
**Overview:** The TransmissionLine class represents a transmission line between two nodes. It includes attributes such as from_node, to_node, susceptance, and capacity.

**Attributes**
- `from_node` (`int`): The id of the first node (where the transmission line originates).
- `to_node` (`int`): The id of the second node (where the transmission line terminates).
- `susceptance` (`float`): The susceptance of the transmission line.
- `capacity` (`float`): The capacity of the transmission line.

**Methods**
- `__init__(from_node: int, to_node: int, susceptance: float, capacity: float): Initializes a new TransmissionLine instance.`
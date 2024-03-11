class TransmissionLine:
    """
    Represents a transmission line in an electrical power system network.
    
    This class models the electrical properties and connectivity of a transmission line, including its starting and ending nodes, its susceptance, and its power transmission capacity. It is essential for simulations involving power flow, grid stability, and capacity planning.
    
    Attributes:
        from_node (int): The ID of the starting node (source) of the transmission line.
        to_node (int): The ID of the ending node (destination) of the transmission line.
        susceptance (float): The susceptance of the transmission line, representing its ability to pass alternating current.
        capacity (float): The maximum power capacity of the transmission line, usually measured in megawatts (MW) or similar units.
        
    Methods:
        __init__: Initializes a new instance of the TransmissionLine class with specified parameters.
    """

    def __init__(self, from_node: int, to_node: int, susceptance: float, capacity: float):
        """
        Initializes a new instance of the TransmissionLine class with specific characteristics.
        
        Parameters:
            from_node (int): The ID of the node where the transmission line originates.
            to_node (int): The ID of the node where the transmission line terminates.
            susceptance (float): The susceptance value of the transmission line, influencing its AC current flow capacity.
            capacity (float): The maximum power (in MW or equivalent units) that can be safely transmitted over the line.
        """
        self.from_node = from_node
        self.to_node = to_node
        self.susceptance = susceptance
        self.capacity = capacity

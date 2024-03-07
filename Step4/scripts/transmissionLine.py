
class TransmissionLine:
        
    """
    Class which represents a transmission line between two nodes :
        - from_node: id of the first node (int), is equal to the node where we are 
        - to_node: id of the second node (int),
        - susceptance: susceptance of the transmission line (float),
        - capacity: capacity of the transmission line (float)
    """

    def __init__(
            self,
            from_node: int,
            to_node: int,
            susceptance: float,
            capacity: float
        ):
    
        self.from_node = from_node
        self.to_node = to_node
        self.susceptance = susceptance
        self.capacity = capacity
class TransmissionLine:

    def __init__(
        self, from_node: int, to_node: int, susceptance: float, capacity: float
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.susceptance = susceptance
        self.capacity = capacity

class TransmissionLines:
    def __init__(self):
        self.transmissionLines = []
    
    def add_constructed_transmissionLine(self,transmissionLine:TransmissionLine):
        self.transmissionLines.append(transmissionLine)
    
    def get_transmissionLine(self, from_node:int, to_node:int):

        for transmissionLine in self.transmissionLines:
            if transmissionLine.from_node == from_node:
                if transmissionLine.to_node == to_node:
                    return transmissionLine
        #print('No TransmissionLine found in TransmissionLines.get_transmissionLine()')
    

        
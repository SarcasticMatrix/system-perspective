from scripts.generationUnits import GenerationUnits
from scripts.loadUnits import LoadUnits

class Nodes:
    """
    Class which represents the nodes in the system. 
    Is a list of node, each node is a dictionnary and is defined with the following attributes,
        - id: id of the node (int),
        - generationUnits: all the generation units located at this node (GenerationUnits),
        - loadUnits: all the load units located at this node (loadUnits),
        - transmissionLines: all the transmission lines located at this node (list of transmissionLine)
    """

    def __init__(self):
        self.nodes = []

    def add_node(
            self,
            id: int,
            generationUnits: GenerationUnits,
            loadUnits: LoadUnits,
            transmissionLines:list,
    ):
        
        node = {
            "Id": id,
            "Generation units": generationUnits,
            "Load units": loadUnits,
            "Transmission line": transmissionLines
        }

        self.nodes.append(node)

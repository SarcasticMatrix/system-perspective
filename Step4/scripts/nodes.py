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
        transmissionLines: list,
    ):

        node = {
            "Id": id,
            "Generation units": generationUnits,
            "Load units": loadUnits,
            "Transmission line": transmissionLines,
        }

        self.nodes.append(node)

    def get_ids_load(self, id_node):
        """
        return the ids of the load units located at the considered node
        """

        # Select the considered node
        for node in self.nodes:
            if node["Id"] == id_node:
                break

        # find the load units
        return node["Load units"].get_ids()

    def get_ids_generation(self, id_node):
        """
        return the ids of the generation units located at the considered node
        """

        # Select the considered node
        for node in self.nodes:
            if node["Id"] == id_node:
                break
        
        # find the generation units
        return node["Generation units"].get_ids()

    def get_susceptances(self, id_node, to_node):
        """
        return the susceptance line between id_node and to_node
        """

        # Select the considered node
        for node in self.nodes:
            if node["Id"] == id_node:
                break

        for transmissionLine in node["Transmission line"]:
            if transmissionLine.to_node == to_node:
                return transmissionLine.susceptance 

    def get_capacity(self, id_node, to_node):
        """
        return the capacity of of the transmission line between id_node and to_node
        """

        # Select the considered node
        for node in self.nodes:
            if node["Id"] == id_node:
                break

        for transmissionLine in node["Transmission line"]:
            if transmissionLine.to_node == to_node:
                return transmissionLine.capacity 
    
    def get_to_node(self,id_node):
        """
        return list of the to_node ids of all the neighbourg at the considered node
        """

        # Select the considered node
        for node in self.nodes:
            if node["Id"] == id_node:
                break

        return [transmission_line.to_node for transmission_line in node["Transmission line"]]

from scripts.generationUnits import GenerationUnits, GenerationUnit
from scripts.loadUnits import LoadUnits, LoadUnit
from scripts.transmissionLines import TransmissionLines, TransmissionLine

class Node:
    def __init__(
            self,
            id_node:int,
            generationUnits:GenerationUnits,
            loadUnits:LoadUnits,
            transmissionLines:TransmissionLines
        ):
        self.id_node = id_node
        self.generationUnits = generationUnits
        self.loadUnits = loadUnits
        self.transmissionLines = transmissionLines
    
    def add_generationUnit(self, generationUnit:GenerationUnit):
        self.generationUnits.add_unit(generationUnit)

    def add_loadUnit(self, loadUnit:LoadUnit):
        self.loadUnits.add_unit(loadUnit)

    def add_transmissionLine(self, transmissionLine:TransmissionLine):
        self.transmissionLines.add_transmissionLine(transmissionLine)
    
    def get_to_node(self):
        return [transmissionLine.to_node for transmissionLine in self.transmissionLines.transmissionLines]
        
class Nodes:
    
    def __init__(self, number_nodes:int):
        self.nodes = []
        for id in range(number_nodes):
            node = Node(
                id,
                GenerationUnits(),
                LoadUnits(),
                TransmissionLines()
            )
            self.nodes.append(node)

    def add_node(self,node:Node):
        self.nodes.append(node)
    
    def get_node(self, id_node:int):
        for node in self.nodes:
            if node.id_node == id_node:
                return node
        print('No node found in Nodes.get_node()')
    
    def get_ids_load(self, id_node:int):
        node = self.get_node(id_node)
        return node.loadUnits.get_ids()
    
    def get_ids_generation(self, id_node:int):
        node = self.get_node(id_node)
        return node.generationUnits.get_ids()

    def add_generationUnit(self, id_node:int, generationUnit:GenerationUnit):
        node = self.get_node(id_node)
        node.add_generationUnit(generationUnit)
    
    def add_loadUnit(self, id_node:int, loadUnit:LoadUnit):
        node = self.get_node(id_node)
        node.add_loadUnit(loadUnit)
    
    def add_transmissionLine(self, id_node:int, transmissionLine:TransmissionLine):
        node = self.get_node(id_node)
        node.add_transmissionLine(transmissionLine)

    def get_transmissionLine(self, from_node:int, to_node:int):
        node = self.get_node(from_node)
        transmissionLine = node.transmissionLines.get_transmissionLine(from_node, to_node)
        return transmissionLine

    def get_susceptance(self, from_node:int, to_node:int):
        transmissionLine = self.get_transmissionLine(from_node, to_node)
        return transmissionLine.susceptance
    
    def get_capacity(self, from_node:int, to_node:int):
        transmissionLine = self.get_transmissionLine(from_node, to_node)
        return transmissionLine.capacity

    def get_to_node(self, id_node):
        node = self.get_node(id_node)
        return node.get_to_node()


    # def get_ids_load(self, id_node):
    #     """
    #     Returns the IDs of all load units located at the specified node.

    #     Parameters:
    #         id_node (int): The ID of the node whose load units are being queried.

    #     Returns:
    #         list of int: The IDs of all load units located at the specified node.
    #     """
    #     for node in self.nodes:
    #         if node["Id"] == id_node:
    #             return node["Load units"].get_ids()

    # def get_ids_generation(self, id_node):
    #     """
    #     Returns the IDs of all generation units located at the specified node.

    #     Parameters:
    #         id_node (int): The ID of the node whose generation units are being queried.

    #     Returns:
    #         list of int: The IDs of all generation units located at the specified node.
    #     """
    #     for node in self.nodes:
    #         if node["Id"] == id_node:
    #             return node["Generation units"].get_ids()

    # def get_susceptances(self, id_node, to_node):
    #     """
    #     Returns the susceptance of the transmission line between two specified nodes.

    #     Parameters:
    #         id_node (int): The ID of the originating node.
    #         to_node (int): The ID of the destination node.

    #     Returns:
    #         float: The susceptance of the transmission line between the two nodes.
    #     """
    #     for node in self.nodes:
    #         if node["Id"] == id_node:
    #             for transmissionLine in node["Transmission line"]:
    #                 if transmissionLine.to_node == to_node:
    #                     return transmissionLine.susceptance

    # def get_capacity(self, id_node, to_node):
    #     """
    #     Returns the capacity of the transmission line between two specified nodes.

    #     Parameters:
    #         id_node (int): The ID of the originating node.
    #         to_node (int): The ID of the destination node.

    #     Returns:
    #         float: The capacity of the transmission line between the two nodes.
    #     """
    #     for node in self.nodes:
    #         if node["Id"] == id_node:
    #             for transmissionLine in node["Transmission line"]:
    #                 if transmissionLine.to_node == to_node:
    #                     return transmissionLine.capacity

    # def get_to_node(self, id_node):
    #     """
    #     Returns a list of IDs for all nodes that are directly connected to the specified node by a transmission line.

    #     Parameters:
    #         id_node (int): The ID of the node whose neighboring nodes are being queried.

    #     Returns:
    #         list of int: The IDs of all nodes directly connected to the specified node.
    #     """
    #     for node in self.nodes:
    #         if node["Id"] == id_node:
    #             return [
    #                 transmission_line.to_node
    #                 for transmission_line in node["Transmission line"]
    #             ]

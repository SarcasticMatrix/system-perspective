from scripts.generationUnits import GenerationUnits
from scripts.loadUnits import LoadUnits
from scripts.generationUnits import GenerationUnits


class Nodes:
    """
    Represents the nodes within a power system network.

    Each node within the system is characterized by its unique identifier, the generation units located at the node, the load units associated with it, and the transmission lines connected to it. This class facilitates the organization, retrieval, and manipulation of node-related data, essential for power system analysis and operation.

    Attributes:
        nodes (list of dict): A collection of dictionaries, each representing a node with attributes such as node ID, generation units, load units, and transmission lines.

    Methods:
        add_node: Adds a new node to the system.
        get_ids_load: Retrieves the IDs of all load units at a specified node.
        get_ids_generation: Retrieves the IDs of all generation units at a specified node.
        get_susceptances: Retrieves the susceptance of the transmission line between two nodes.
        get_capacity: Retrieves the capacity of the transmission line between two nodes.
        get_to_node: Retrieves a list of neighboring node IDs connected via transmission lines to a specified node.
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
        """
        Adds a new node to the system with specified characteristics.

        Parameters:
            id (int): The unique identifier of the node.
            generationUnits (GenerationUnits): An instance of the GenerationUnits class representing all generation units located at this node.
            loadUnits (LoadUnits): An instance of the LoadUnits class representing all load units located at this node.
            transmissionLines (list): A list of instances (possibly of a TransmissionLine class) representing all transmission lines connected to this node.
        """
        node = {
            "Id": id,
            "Generation units": generationUnits,
            "Load units": loadUnits,
            "Transmission line": transmissionLines,
        }

        self.nodes.append(node)

    def get_ids_load(self, id_node):
        """
        Returns the IDs of all load units located at the specified node.

        Parameters:
            id_node (int): The ID of the node whose load units are being queried.

        Returns:
            list of int: The IDs of all load units located at the specified node.
        """
        for node in self.nodes:
            if node["Id"] == id_node:
                return node["Load units"].get_ids()

    def get_ids_generation(self, id_node):
        """
        Returns the IDs of all generation units located at the specified node.

        Parameters:
            id_node (int): The ID of the node whose generation units are being queried.

        Returns:
            list of int: The IDs of all generation units located at the specified node.
        """
        for node in self.nodes:
            if node["Id"] == id_node:
                return node["Generation units"].get_ids()

    def get_susceptances(self, id_node, to_node):
        """
        Returns the susceptance of the transmission line between two specified nodes.

        Parameters:
            id_node (int): The ID of the originating node.
            to_node (int): The ID of the destination node.

        Returns:
            float: The susceptance of the transmission line between the two nodes.
        """
        for node in self.nodes:
            if node["Id"] == id_node:
                for transmissionLine in node["Transmission line"]:
                    if transmissionLine.to_node == to_node:
                        return transmissionLine.susceptance

    def get_capacity(self, id_node, to_node):
        """
        Returns the capacity of the transmission line between two specified nodes.

        Parameters:
            id_node (int): The ID of the originating node.
            to_node (int): The ID of the destination node.

        Returns:
            float: The capacity of the transmission line between the two nodes.
        """
        for node in self.nodes:
            if node["Id"] == id_node:
                for transmissionLine in node["Transmission line"]:
                    if transmissionLine.to_node == to_node:
                        return transmissionLine.capacity

    def get_to_node(self, id_node):
        """
        Returns a list of IDs for all nodes that are directly connected to the specified node by a transmission line.

        Parameters:
            id_node (int): The ID of the node whose neighboring nodes are being queried.

        Returns:
            list of int: The IDs of all nodes directly connected to the specified node.
        """
        for node in self.nodes:
            if node["Id"] == id_node:
                return [
                    transmission_line.to_node
                    for transmission_line in node["Transmission line"]
                ]

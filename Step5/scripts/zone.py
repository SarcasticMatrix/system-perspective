from scripts.nodes import Nodes
from scripts.loadUnits import LoadUnits
from scripts.generationUnits import GenerationUnits


class Zone:

    """
    Represents all the nodes within a zone in a power system network.
    Attributes :
        - nodes (Nodes), nodes in the zone
        - transmission_lines (list of TransmissionLine), list of the transmission lines which are linked to the zone (i.e. to one of the node of the zone)
        - generation_units (GenerationUnits), GenerationUnits which are linked to the zone
        - load_units (LoadUnits), LoadUnits which are linked to the zone
    """

    def __init__(self):
        self.nodes = Nodes()
        self.transmission_lines = []
        self.generation_units = GenerationUnits()
        self.load_units = LoadUnits()

    def add_constructed_node(self, node: dict):
        """
        Add a node which already exists
        """
        self.nodes.add_node(
            id=node["Id"],
            generationUnits=node["Generation units"],
            loadUnits=node["Generation units"],
            transmissionLines=node["Transmission line"],
        )

    def get_id_nodes(self):
        """
        Retrieve the list of the Ids of the nodes of the zone
        """
        return [node["Id"] for node in self.nodes.nodes]

    def add_transmission_lines(self):
        """
        Complete the self.transmission_line from the nodes of the zone
        """

        zone_id_nodes = self.get_id_nodes()
        for node in self.nodes.nodes:
            to_ids = self.nodes.get_to_node(node["Id"])

            for to_id in to_ids:
                if to_id not in zone_id_nodes:
                    self.transmission_lines.append(node["Transmission line"])

    def add_generation_units(self):
        """
        Complete self.generation_units with the GenerationUnits located at the zone nodes
        """

        self.get_id_nodes()
        for node in self.nodes.nodes:
            for unit in node["Generation units"].units:
                self.generation_units.add_constructed_unit(unit)

    def add_load_units(self):
        """
        Complete self.load_units with the LoadUnits located at the zone nodes
        """

        self.get_id_nodes()
        for node in self.nodes.nodes:
            for unit in node["Load units"].units:
                self.load_units.add_constructed_unit(unit)

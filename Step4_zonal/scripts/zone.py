from scripts.nodes import Nodes
from scripts.loadUnits import LoadUnits
from scripts.generationUnits import GenerationUnits
from scripts.transmissionLines import TransmissionLines

class Zone:
    """
    Represents all the nodes within a zone in a power system network.
    Attributes :
        - nodes (Nodes), nodes in the zone
        - transmissionLines (list of TransmissionLine), list of the transmission lines which are linked to the zone (i.e. to one of the node of the zone)
        - generationUnits (GenerationUnits), GenerationUnits which are linked to the zone
        - loadUnits (LoadUnits), LoadUnits which are linked to the zone
    """

    def __init__(self, list_ids:list):
        self.nodes = Nodes(list_ids)
        self.transmissionLines = TransmissionLines()
        self.generationUnits = GenerationUnits()
        self.loadUnits = LoadUnits()

    def add_node(self, node: Nodes):
        """
        Add a node which already exists
        """
        self.nodes.add_node(node)

    def get_id_loads(self):
        """
        Retrieve the list of the Ids of the loads of the zone
        """
        return self.loadUnits.get_ids()

    def get_id_generators(self):
        """
        Retrieve the list of the Ids of the generators of the zone
        """
        return self.generationUnits.get_ids()

    def get_id_nodes(self):
        """
        Retrieve the list of the Ids of the nodes of the zone
        """
        return self.nodes.get_ids_node()

    def add_transmissionLines(self):
        """
        Complete the self.transmissionLine from the nodes of the zone
        """

        zone_id_nodes = self.get_id_nodes()
        for node in self.nodes.nodes:
            to_ids = self.nodes.get_to_node(node.id_node)

            for to_id in to_ids:
                if to_id not in zone_id_nodes:
                    for transmission_line in self.transmissionLines.transmissionLines:
                        self.transmissionLines.append(transmission_line)

    def add_generationUnits(self):
        """
        Complete self.generationUnits with the GenerationUnits located at the zone nodes
        """

        for node in self.nodes.nodes:
            for unit in node.generationUnits.units:
                self.generationUnits.add_unit(unit)

    def add_loadUnits(self):
        """
        Complete self.loadUnits with the LoadUnits located at the zone nodes
        """

        for node in self.nodes.nodes:
            for unit in node.loadUnits.units:
                self.loadUnits.add_unit(unit)

    def compute_capacity_between_zones(self, to_zone):
        """
        Return the maximum capactiy between two zones.

        Inputs: the other zone
        """
        
        max_capacity = 0 
        for from_id in self.get_id_nodes():
            for to_id in to_zone.get_id_nodes():
                try:
                    max_capacity += self.nodes.get_transmissionLine(from_id,to_id).capacity
                except:
                    pass
        return max_capacity


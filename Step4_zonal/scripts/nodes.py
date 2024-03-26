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
        self.transmissionLines.add_constructed_transmissionLine(transmissionLine)
    
    def get_to_node(self):
        return [transmissionLine.to_node for transmissionLine in self.transmissionLines.transmissionLines]
    
    def get_id(self):
        return self.id_node
        
class Nodes:
    
    def __init__(self, list_ids:list):
        self.nodes = []
        for id in list_ids:
            node = Node(
                id,
                GenerationUnits(),
                LoadUnits(),
                TransmissionLines()
            )
            self.nodes.append(node)

    def add_node(self,node:Node):
        self.nodes.append(node)
    
    def get_ids_node(self):
        return [node.id_node for node in self.nodes]
    
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


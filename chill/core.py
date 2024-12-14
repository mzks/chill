import numpy as np
from .chill import process

class Node:
    
    def __init__(self, name, T=300, C=10000):
        self.name = name
        self.T = T  # Temperature [K]
        self.C = C # [J/K]
        self.Ts = []
    
    def save_T(self):
        self.Ts.append(self.T)
        
class Edge:
    
    def __init__(self, node1, node2, name='', edge_type=0, parameter=100):
        self.name = name
        self.nodes = (node1, node2)
        self.parameter = parameter
        self.edge_type = edge_type
        #self.q = (self.nodes[0].T - self.nodes[1].T) / self.parameter
        
class Chill:
    
    TYPE_TRANSFER = 0
    TYPE_RADIATION = 1
    TYPE_HEAT_INPUT = 2
    
    def __init__(self):
        self.nodes = []
        self.edges = [] 
        self.dt = 0.1 # seconds
        self.time = 0.
        self.ready = False
        self.temperatures_history = []
        self.times_history = []
        
    def register_node(self, node):
        self.nodes.append(node)
        
    def register_edge(self, edge):
        self.edges.append(edge)
        
    def register_edge_by_names(self, node_name1, node_name2, name='', edge_type=0, parameter=100):
        n1 = [n for n in self.nodes if n.name == node_name1][0]
        n2 = [n for n in self.nodes if n.name == node_name2][0]
        edge = Edge(n1, n2, name, edge_type=edge_type, parameter=parameter)
        self.edges.append(edge)
    
    def setup(self):
        self.temperatures = np.array([n.T for n in self.nodes], dtype=np.float64)
        self.capacities = np.array([n.C for n in self.nodes], dtype=np.float64)
        self.parameters = np.array([e.parameter for e in self.edges], dtype=np.float64)
        node_index_map = {id(node): idx for idx, node in enumerate(self.nodes)}
        self.connections = np.array([[node_index_map[id(node)] for node in edge.nodes] for edge in self.edges], dtype=np.uint64)
        self.edge_types = np.array([e.edge_type for e in self.edges], dtype=np.int32)
        self.ready = True
        
    def run(self, steps=100):
        if self.ready:
            self.temperatures = process(self.temperatures, self.capacities, self.parameters, self.connections, self.edge_types, self.dt, steps)
            self.time += self.dt * steps
        else:
            print('setup() first!')

    def note_data(self):
        self.temperatures_history.append(self.temperatures)
        self.times_history.append(self.time)




import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict
from .chill import process

@dataclass
class Node:
    """
    Represents a node in the thermal simulation.

    Attributes:
        temperature (float): Initial temperature of the node.
        capacity (float): Thermal capacity of the node
        name (str): Name of the node.
    """
    temperature: float = 300.0   # [K]
    capacity: float = 100.0      # [K/J]
    name: str = ''

@dataclass
class Edge:
    """
    Represents an edge between two nodes in the thermal simulation.

    Attributes:
        nodes (Tuple[Node, Node]): The two nodes connected by the edge.
        parameter (float): Parameter associated with the edge (e.g., thermal conductivity).
        edge_type (int): Type of the edge (e.g., conduction, radiation, heat input).
        name (str): Name of the edge.
    """
    nodes: Tuple[Node, Node]
    parameter: float
    edge_type: int
    name: str = ''

class Chill:
    """
    Manages the thermal simulation by defining nodes and edges, setting up the simulation,
    and running the simulation steps.
    """
    # Constants representing edge types
    TYPE_TRANSFER = 0
    TYPE_RADIATION = 1
    TYPE_HEAT_INPUT = 2

    def __init__(self, dt: float = 0.1):
        """
        Initializes the Chill simulation.

        Args:
            dt (float): Time step for the simulation [seconds]. Default is 0.1 seconds.
        """
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.dt: float = dt  # seconds
        self.time: float = 0.0
        self.ready: bool = False
        self.temperatures_history: List[np.ndarray] = []
        self.times_history: List[float] = []
        self._node_dict: Dict[str, Node] = {}

    def define_node(self, temperature: float, capacity: float, name: str = '') -> Node:
        """
        Defines a new node and adds it to the simulation.

        Args:
            temperature (float): Initial temperature of the node [K].
            capacity (float): Thermal capacity of the node [K/J].
            name (str, optional): Name of the node. Defaults to an empty string.

        Returns:
            Node: The created node object.
        """
        node = Node(temperature=temperature, capacity=capacity, name=name)
        self.nodes.append(node)
        if name:
            self._node_dict[name] = node  # Add to dictionary if name is provided
        self.ready = False  # Invalidate setup as a new node is added
        return node

    def define_edge(self, node0: Node, node1: Node, parameter: float, edge_type: int, name: str = '') -> None:
        """
        Defines a new edge between two nodes and adds it to the simulation.

        Args:
            node0 (Node): One end of the edge.
            node1 (Node): The other end of the edge.
            parameter (float): Parameter associated with the edge (e.g., thermal conductivity).
            edge_type (int): Type of the edge.
            name (str, optional): Name of the edge. Defaults to an empty string.
        """
        edge = Edge(nodes=(node0, node1), parameter=parameter, edge_type=edge_type, name=name)
        self.edges.append(edge)
        self.ready = False  # Invalidate setup as a new edge is added

    def find_node(self, name: str) -> Node:
        """
        Finds a node by its name.

        Args:
            name (str): The name of the node to find.

        Returns:
            Node: The node object with the specified name.

        Raises:
            ValueError: If no node with the specified name is found.
        """
        node = self._node_dict.get(name)
        if node is None:
            raise ValueError(f"Node with name '{name}' not found.")
        return node

    def define_thermal_conduction(self, node0: Node, node1: Node, conductance: float, name: str = '') -> None:
        """
        Defines a thermal conduction edge between two nodes.

        Args:
            node0 (Node): One end of the conduction edge.
            node1 (Node): The other end of the conduction edge.
            conductance (float): Thermal conductance.
            name (str, optional): Name of the edge. Defaults to an empty string.
        """
        self.define_edge(node0, node1, conductance, self.TYPE_TRANSFER, name=name)

    def define_thermal_radiation(self, node0: Node, node1: Node, constant: float, name: str = '') -> None:
        """
        Defines a thermal radiation edge between two nodes.

        Args:
            node0 (Node): One end of the radiation edge.
            node1 (Node): The other end of the radiation edge.
            constant (float): Radiation constant.
            name (str, optional): Name of the edge. Defaults to an empty string.
        """
        self.define_edge(node0, node1, constant, self.TYPE_RADIATION, name=name)

    def define_thermal_input(self, node0: Node, node1: Node, heat_input: float, name: str = '') -> None:
        """
        Defines a thermal input edge between two nodes.

        Args:
            node0 (Node): One end of the heat input edge.
            node1 (Node): The other end of the heat input edge.
            heat_input (float): Amount of heat input.
            name (str, optional): Name of the edge. Defaults to an empty string.
        """
        self.define_edge(node0, node1, heat_input, self.TYPE_HEAT_INPUT, name=name)

    def define_thermal_conduction_by_name(self, node_name0: str, node_name1: str, conductance: float, name: str = '') -> None:
        """
        Defines a thermal conduction edge between two nodes identified by their names.

        Args:
            node_name0 (str): Name of the first node.
            node_name1 (str): Name of the second node.
            conductance (float): Thermal conductance.
            name (str, optional): Name of the edge. Defaults to an empty string.
        """
        node0 = self.find_node(node_name0)
        node1 = self.find_node(node_name1)
        self.define_thermal_conduction(node0, node1, conductance, name=name)

    def define_thermal_radiation_by_name(self, node_name0: str, node_name1: str, constant: float, name: str = '') -> None:
        """
        Defines a thermal radiation edge between two nodes identified by their names.

        Args:
            node_name0 (str): Name of the first node.
            node_name1 (str): Name of the second node.
            constant (float): Radiation constant.
            name (str, optional): Name of the edge. Defaults to an empty string.
        """
        node0 = self.find_node(node_name0)
        node1 = self.find_node(node_name1)
        self.define_thermal_radiation(node0, node1, constant, name=name)

    def define_thermal_input_by_name(self, node_name0: str, node_name1: str, heat_input: float, name: str = '') -> None:
        """
        Defines a thermal input edge between two nodes identified by their names.

        Args:
            node_name0 (str): Name of the first node.
            node_name1 (str): Name of the second node.
            heat_input (float): Amount of heat input.
            name (str, optional): Name of the edge. Defaults to an empty string.
        """
        node0 = self.find_node(node_name0)
        node1 = self.find_node(node_name1)
        self.define_thermal_input(node0, node1, heat_input, name=name)

    def setup(self) -> None:
        """
        Sets up the simulation by initializing necessary data structures based on defined nodes and edges.
        """
        # Convert node temperatures and capacities to NumPy arrays
        self.temperatures = np.array([node.temperature for node in self.nodes], dtype=np.float64)
        self.capacities = np.array([node.capacity for node in self.nodes], dtype=np.float64)

        # Convert edge parameters to a NumPy array
        self.parameters = np.array([edge.parameter for edge in self.edges], dtype=np.float64)

        # Create a mapping from node IDs to their indices
        node_index_map = {id(node): idx for idx, node in enumerate(self.nodes)}

        # Convert edge connections to index pairs in a NumPy array
        self.connections = np.array([
            [node_index_map[id(node)] for node in edge.nodes]
            for edge in self.edges
        ], dtype=np.uint64)

        # Convert edge types to a NumPy array
        self.edge_types = np.array([edge.edge_type for edge in self.edges], dtype=np.int32)

        self.ready = True  # Mark setup as complete

    def run(self, steps: int = 100) -> None:
        """
        Runs the simulation for a specified number of steps.

        Args:
            steps (int, optional): Number of simulation steps to run. Defaults to 100.

        Raises:
            RuntimeError: If the setup has not been completed.
        """
        if not self.ready:
            raise RuntimeError("Setup must be called before running the simulation.")

        # Execute the simulation process
        self.temperatures = process(
            self.temperatures,
            self.capacities,
            self.parameters,
            self.connections,
            self.edge_types,
            self.dt,
            steps
        )
        self.time += self.dt * steps  # Update simulation time

    def record_data(self) -> None:
        """
        Records the current temperatures and time into their respective histories.
        """
        self.temperatures_history.append(self.temperatures.copy())
        self.times_history.append(self.time)

    def execute(self, total_time: float, record_interval: float = 0) -> None:
        """
        execute the simulation for a specified time.
        :param total_time: simulation time
        :param record_interval: recording interval
        """
        if record_interval == 0 or record_interval > total_time:
            self.run(steps=int(total_time / self.dt))
            return

        steps_per_interval = int(record_interval / self.dt)
        total_steps = int(total_time / self.dt)
        num_intervals = total_steps // steps_per_interval
        for _ in range(num_intervals):
            self.run(steps=steps_per_interval)
            self.record_data()

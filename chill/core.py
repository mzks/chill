import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.cm as colormap
import matplotlib.colors as mcolors
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from thermo import Chemical
from tqdm import tqdm
import networkx as nx
from .chill import process
from .constants import *

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

    def find_node_indices_by_name(self, name) -> List[int]:
        """
        Find node index by the node name

        Args:
            name (str): Node name

        Returns:
            list: The node index list
        """
        return [ index for index, node in enumerate(self.nodes) if name in node.name ]

    def define_object(self, material_name, temperature, volume, pressure=atm, name=''):
        """
        Defines a thermal node representing a specific object with given material properties.
        
        Args:
            material_name (str): The name of the material (must be supported by the `thermo` library).
            temperature (float): Initial temperature of the object.
            volume (float): Volume of the object, used to calculate its specific heat capacity.
            pressure (float, optional): Pressure of the system. Defaults to standard atmospheric pressure.
            name (str): The name used for the node name

        Returns:
            None
        """
        material = Chemical(material_name, T=temperature, P=pressure)
        capacity = material.rho * volume * material.Cp
        if name=='':
            name = material_name
        return self.define_node(temperature, capacity, name=name)

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
        return:
            Node: The created node object.
        """
        node0 = self.find_node(node_name0)
        node1 = self.find_node(node_name1)
        self.define_thermal_input(node0, node1, heat_input, name=name)

    def define_heater(self, target_node, heat_input):
        """
        Defines a heater connected to the specified target node, simulating a constant heat input.
    
        Args:
            target_node (Node): The node to which the heater is connected.
            heat_input (float): The amount of heat input provided by the heater.
    
        Returns:
            Node : The created node object (heater).
        """
        node = self.define_node(temperature=300*K, capacity=np.inf)
        self.define_thermal_input(node, target_node, heat_input)
        return node

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
        for _ in tqdm(range(num_intervals)):
            self.run(steps=steps_per_interval)
            self.record_data()


    def plot_top_temperature_changes(self, top_n: int = 5, figure_size: Optional[Tuple[int, int]] = (10, 6)) -> Figure:
        """
        Plots the temperature changes of the top N nodes with the most significant temperature variations over time.

        Args:
            top_n (int): The number of top nodes to plot based on temperature change. Defaults to 5.
            figure_size (Tuple[int, int], optional): Size of the figure in inches. Defaults to (10, 6).

        Returns:
            matplotlib.figure.Figure: The matplotlib figure object containing the plot.
        """
        temperature_history = np.array(self.temperatures_history, dtype=np.float64)

        initial_temperatures = temperature_history[0, :]
        final_temperatures = temperature_history[-1, :]
        temperature_differences = np.abs(final_temperatures - initial_temperatures)

        # Get indices of the top N nodes with the highest temperature change
        sorted_node_indices = np.argsort(temperature_differences)[::-1]  # Descending order
        selected_node_indices = sorted_node_indices[:top_n] if top_n < len(sorted_node_indices) else sorted_node_indices

        time_points = self.times_history

        # Create the plot
        figure, axis = plt.subplots(figsize=figure_size)

        for node_index in selected_node_indices:
            node_name = self.nodes[node_index].name
            axis.plot(time_points, temperature_history[:, node_index], label=node_name)

        # Enhance plot aesthetics
        axis.set_title('Top Temperature Changes during simulation')
        axis.set_xlabel('Time [s]')
        axis.set_ylabel('Temperature [K]')
        axis.legend()
        plt.tight_layout()
        plt.close(figure)
        return figure

    def plot_node_temperature_by_name(self, name: str, figure_size: Optional[Tuple[int, int]] = (10, 6)) -> Figure:
        """
        Plots the temperature changes of the node by the name

        Args:
            name (str): Node name to plot
            figure_size (Tuple[int, int], optional): Size of the figure in inches. Defaults to (10, 6).

        Returns:
            matplotlib.figure.Figure: The matplotlib figure object containing the plot.
        """
        temperature_history = np.array(self.temperatures_history, dtype=np.float64)
        time_points = self.times_history

        # Create the plot
        figure, axis = plt.subplots(figsize=figure_size)

        for node_index in self.find_node_indices_by_name(name) :
            node_name = self.nodes[node_index].name
            axis.plot(time_points, temperature_history[:,node_index], label=node_name)

        axis.set_xlabel('Time [s]')
        axis.set_ylabel('Temperature [K]')
        axis.legend()
        plt.tight_layout()
        plt.close(figure)
        return figure

    def plot_node_temperature_by_names(self, names: List[str], figure_size: Optional[Tuple[int, int]] = (10, 6)) -> Figure:
        """
        Plots the temperature changes of the nodes by the names

        Args:
            names (List[str]): Node names to plot
            figure_size (Tuple[int, int], optional): Size of the figure in inches. Defaults to (10, 6).

        Returns:
            matplotlib.figure.Figure: The matplotlib figure object containing the plot.
        """
        temperature_history = np.array(self.temperatures_history, dtype=np.float64)
        time_points = self.times_history

        # Create the plot
        figure, axis = plt.subplots(figsize=figure_size)

        for name in names:
            for node_index in self.find_node_indices_by_name(name) :
                node_name = self.nodes[node_index].name
                axis.plot(time_points, temperature_history[:,node_index], label=node_name)

        axis.set_xlabel('Time [s]')
        axis.set_ylabel('Temperature [K]')
        axis.legend()
        plt.tight_layout()
        plt.close(figure)
        return figure

    def update_node_temperature(self):
        if len(self.temperatures_history) == 0:
            return
        for n, t in zip(self.nodes, self.temperatures_history[-1]):
            n.temperature = t

    def plot_network(self, figure_size: Optional[Tuple[int, int]] = (10, 6),
                     vmin=None, vmax=None) -> Figure:
        """
        Plot the node and edge network

        Args:
            figure_size (Tuple[int, int], optional): Size of the figure in inches. Defaults to (10, 6).
            vmin (float): Minimum temperature shown in the colorbar
            vmax (float): Maximum temperature shown in the colorbar
        Returns:
            matplotlib.figure.Figure: The matplotlib figure object containing the plot.
        """

        self.update_node_temperature()
        figure, axis = plt.subplots(figsize=figure_size)

        G = nx.Graph()
        for node in self.nodes:
            G.add_node(node.name)
        for edge in self.edges:
            G.add_edge(edge.nodes[0].name, edge.nodes[1].name, label=f'{edge.parameter:.1e}')
        cmap = colormap.plasma
        temperatures = [node.temperature for node in self.nodes]
        if vmin == None:
            vmin = min(temperatures)
        if vmax == None:
            vmax = max(temperatures)
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

        pos = nx.kamada_kawai_layout(G)
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color=temperatures,
            cmap=cmap,
            node_size=300,
            alpha=0.8,
            ax=axis
        )
        nx.draw_networkx_labels(G, pos, ax=axis)
        nx.draw_networkx_edges(G, pos, edge_color="gray", ax=axis)
        edge_label_dict = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_label_dict, ax=axis)

        sm = colormap.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        figure.colorbar(sm, label="Temperature [K]")
        plt.close(figure)
        return figure
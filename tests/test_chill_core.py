import pytest
from chill import Chill

def test_simple_heat_transfer():
    c = Chill()
    assert c.time == 0.

    rho = 2700
    c_p = 900
    A = 0.1  # m^2
    h = 0.01 # 1 cm
    C = rho * A * h * c_p  # J/K

    h_c = 100
    R = 1/(A*h_c)

    node0 = c.define_node(500, C)
    node1 = c.define_node(300, C)
    node2 = c.define_node(300, C)

    c.define_thermal_conduction(node0, node1, R)
    c.define_thermal_conduction(node1, node2, R)

    c.setup()
    c.execute(10000, 100)

    assert len(c.temperatures_history) == 100
    assert abs(c.temperatures[0] - c.temperatures[1]) < 1.e-3
    assert abs(c.temperatures[1] - c.temperatures[2]) < 1.e-3


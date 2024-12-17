import pytest
from chill import Chill
from chill.constants import *

def simple_3plate_sim():

    c = Chill()
    object0 = c.define_object("Al", 300*K, volume=10.*cm3, name='obj.0')
    object1 = c.define_object("Al", 300*K, volume=10.*cm3, name='obj.1')
    object2 = c.define_object("Al", 500*K, volume=10.*cm3, name='obj.2')

    h_c = 100
    area = 10.*cm2
    heat_resistance = 1 / (h_c * area)

    c.define_thermal_conduction(object0, object1, heat_resistance)
    c.define_thermal_conduction(object1, object2, heat_resistance)

    c.setup()
    c.execute(1*hour, 1*s)

    theory = (300+300+500)/ 3
    for last_temp in c.temperatures_history[-1]:
        assert abs(last_temp - theory) < 10*K


"""
This file includes units and constants definition.
This tool internally use SI units.
"""
# SI base unit definitions
m = 1.0       # meter
s = 1.0       # second
kg = 1.0      # kilogram
K = 1.0       # kelvin

mol = 1.0     # mole
rad = 1.0     # radian
sr = 1.0      # steradian

# Derived units for convenience
mm = 1.e-3 * m          # millimeter
cm = 1.e-2 * m          # centimeter
km = 1.e3 * m           # kilometer
um = 1.e-6 * m          # micrometer
nm = 1.e-9 * m          # nanometer
pm = 1.e-12 * m         # picometer

m2 = m * m
mm2 = mm * mm
cm2 = cm * cm
km2 = km * km
um2 = um * um
nm2 = nm * nm
pm2 = pm * pm

m3 = m * m * m
mm3 = mm * mm * mm
cm3 = cm * cm * cm
km3 = km * km * km
um3 = um * um * um
nm3 = nm * nm * nm
pm3 = pm * pm * pm

ms = 1.e-3 * s          # millisecond
μs = 1.e-6 * s          # microsecond
ns = 1.e-9 * s          # nanosecond
ps = 1.e-12 * s         # picosecond
second = s              # second
minute = 60 * s         # minute
hour = 3600 * s         # hour
day = 24 * hour         # day

g = 1.e-3 * kg          # gram
mg = 1.e-3 * g          # milligram
μg = 1.e-6 * g          # microgram
ng = 1.e-9 * g          # nanogram
pg = 1.e-12 * g         # picogram
ton = 1.e3 * kg         # metric ton

N = kg * m / (s * s)   # newton (force)
J = N * m              # joule (energy)
cal = 4.184 * J        # calory (energy)
kcal = 4.184e3 * J     # kilocalory (energy)
W = J / s              # watt (power)
Pa = N / (m * m)       # pascal (pressure)
bar = 1e5 * Pa         # bar (pressure)
hPa = 100 * Pa         # hecto pascal (pressure)
atm = 1013.25 * hPa    # standard atmosphere pressure (pressure)

# Common energy units
kJ = 1e3 * J           # kilojoule
MJ = 1e6 * J           # megajoule
GJ = 1e9 * J           # gigajoule
Wh = 3600 * J          # watt-hour
kWh = 1e3 * Wh         # kilowatt-hour
MWh = 1e6 * Wh         # megawatt-hour

# Thermal conductivity
W_per_mK = W / (m * K) # watt per meter-kelvin

# Specific heat capacity
J_per_kgK = J / (kg * K) # joule per kilogram-kelvin

def K_to_C(T):
    return T - 273.15

def C_to_K(T):
    return T + 273.15

def K_to_F(T):
    return (T - 273.15) * 9 / 5 + 32

def F_to_K(T):
    return (T - 32) * 5 / 9 + 273.15

# Constants
sigma = 5.670374419e-8 * W / (m**2 * K**4)   # Stefan-Boltzmann constant
k_B = 1.380649e-23 * J / K                   # Boltzmann constant
R = 8.314462618 * J / (mol * K)              # Universal gas constant
c_p_water = 4184 * J / (kg * K)              # Specific heat capacity of water at 25°C
c_p_air = 1005 * J / (kg * K)                # Specific heat capacity of air at 25°C
rho_water = 1000 * kg / (m**3)               # Density of water
rho_air = 1.225 * kg / (m**3)                # Density of air at 15°C
lambda_water = 0.606 * W_per_mK              # Thermal conductivity of water at 25°C
lambda_air = 0.025 * W_per_mK                # Thermal conductivity of air at 15°C

__all__ = [name for name in globals() if not name.startswith("_")]
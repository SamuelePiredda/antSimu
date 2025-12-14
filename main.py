import matplotlib.pyplot as plt
import necpp
import numpy as np

#TODO: WRITE A LOT OF COMMENTS TO EXPLAIN THE USAGE OF THE NEC++ API
#TODO: IMPROVE ERROR HANDLING
#TODO: ADD EFFICIENCY CALCULATION FUNCTION

def nec_create():
    try:
        return necpp.nec_create()
    except Exception as e:
        print(e)


def nec_addWire(nec, tag, segs, x1, y1, z1, x2, y2, z2, radius_mm):
    try:
        err = necpp.nec_wire(nec, int(tag), int(segs), float(x1), float(y1), float(z1), \
                                float(x2), float(y2), float(z2), float(radius_mm/1000), float(1), float(1))
        if err != 0:
            print(f"Error during adding wire {err}!")
            print(necpp.nec_error_message())
            exit()
    except Exception as e:
        print(e)

GROUND_PLANE = 1
NO_GROUND_PLANE = 0
def nec_closeGeometry(nec, ground_plane_flag):
    try:
        err = necpp.nec_geometry_complete(nec, int(ground_plane_flag))
        if err != 0:
            print(f"Error during closing geometry {err}!")
            print(necpp.nec_error_message())
            exit()
    except Exception as e:
        print(e)


def nec_addLoads(nec, type_, tag, start, stop, R, L_u, C_n):
    try:
        err = necpp.nec_ld_card(nec, int(type_), int(tag), int(start), int(stop), \
                                float(R), float(L_u), float(C_n))
        if err != 0:
            print(f"Error during adding loads {err}!")
            print(necpp.nec_error_message())
            exit()
    except Exception as e:
        print(e)

FEED_TYPE_VOLTAGE = 0
def nec_addFeed(nec, type_, tag, seg, mag = 1, phase = 0):
    try:
        err = necpp.nec_ex_card(nec, int(type_), int(tag), int(seg), int(0), float(mag), \
                                float(phase), int(0), int(0), int(0), int(0))
        if err != 0:
            print(f"Error during adding feed {err}!")
            print(necpp.nec_error_message())
            exit()
    except Exception as e:
            print(e)

RANGE_TYPE_LINEAR = 0
RANGE_TYPE_LOG = 1
def nec_frequencySet(nec, range_type, freq_start_mhz, freq_stop_mhz, num_points):
    try:
        step = (freq_stop_mhz - freq_start_mhz)/( num_points + 1 )
        err = necpp.nec_fr_card(nec, int(range_type), int(num_points), float(freq_start_mhz), float(step))
        if err != 0:
            print(f"Error during setting frequency {err}!")
            print(necpp.nec_error_message())
            exit()
    except Exception as e:
        print(e)


def nec_runSimulation(nec):
    try:
        err = necpp.nec_rp_card(nec, int(0), int(1), int(1), int(0), int(0), int(0), int(0),\
                                    float(0), float(0), float(0), float(0), float(0), float(0))
        if err != 0:
            print(f"Error during running simulation {err}!")
            print(necpp.nec_error_message())
            exit()
    except Exception as e:
        print(e)


def getImpedance(nec, len):
    try:
        R = np.zeros(len)
        X = np.zeros(len)
        for index in range(0,len):
            R[index] = necpp.nec_impedance_real(nec, index)
            X[index] = necpp.nec_impedance_imag(nec, index)
        return R, X
    except Exception as e:
        print(e)

def get_vswr(nec, len):
    try:
        vswr = np.zeros(len)
        for index in range(0,len):
            R = necpp.nec_impedance_real(nec, index)
            X = necpp.nec_impedance_imag(nec, index)
            Z0 = 50.0
            ZL = complex(R, X)
            Gamma = (ZL - Z0) / (ZL + Z0)
            if abs(Gamma) >= 0.9999:
                vswr[index] = 100.0
            else:
                vswr[index] = (1 + abs(Gamma)) / (1 - abs(Gamma))
                if vswr[index] > 100.0: 
                    vswr[index] = 100.0

        return vswr

    except Exception as e:
        print(e)

def nec_wire_conductivity(nec, conductivity_mhos = 5.8e7):
        """
        Imposta la conduttività del filo.
        Rame = 5.8e7
        Alluminio = 3.7e7
        """
        necpp.nec_ld_card(nec, 5, 0, 0, 0, conductivity_mhos, 0, 0)



nec = nec_create()

start_f = 300
end_f = 500
steps = 500
ground_plane = 0.5

nec_addWire(nec, 1, 5, 0, 0, ground_plane, 0, 0, 0.12+ground_plane, 2)

X_ind = 0.52e-6

nec_closeGeometry(nec, GROUND_PLANE)
nec_wire_conductivity(nec)


Q = 100
R_coil = (2 * np.pi * 433e6 * X_ind) / Q


print(f"[REALE] Resistenza parassita Bobina (Q={Q}): {R_coil:.2f} Ohm")

nec_addLoads(nec, 0, 1, 1, 1, R_coil, X_ind, 0)
nec_addFeed(nec, FEED_TYPE_VOLTAGE, 1, 1)
nec_frequencySet(nec, RANGE_TYPE_LINEAR, start_f, end_f, steps)
nec_runSimulation(nec)






vswr = get_vswr(nec, steps)
x = np.linspace(start_f, end_f, steps)
plt.plot(x, vswr)

print(f"VSWR min: {min(vswr)} at {x[np.argmin(vswr)]} MHz")




R, X = getImpedance(nec, steps)

R_tot = R[np.argmin(abs(x-433))] + R_coil

plt.figure()
plt.plot(x, R, label='R (Ohm)')
plt.plot(x, X, label='X (Ohm)')

necpp.nec_delete(nec)

print(f"Impedance at frequency 433MHz : {R[np.argmin(abs(x-433))]} + j{X[np.argmin(abs(x-433))]} Ohm")
print(f"Total Resistance at frequency 433MHz : {R_tot} Ohm")
print(f"Efficiency at frequency 433MHz : {100*R[np.argmin(abs(x-433))]/R_tot} %")

plt.show()


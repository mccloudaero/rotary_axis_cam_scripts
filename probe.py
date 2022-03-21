# Probe Module

import sys
import numpy as np

def read_cylinder_probe_file(filename):

    X, Y, Z, A = np.loadtxt('probe_results.txt', unpack=True)
    X_values = np.unique(X)
    num_X = X_values.size
    A_values = np.unique(A)
    num_A = A_values.size

    X = np.reshape(X, (num_X,num_A))
    A = np.reshape(A, (num_X,num_A))
    Z = np.reshape(Z, (num_X,num_A))
    delta_R = Z - Z[0][0]

    # Copy 0 degree data to 360 data
    X_c1 = np.reshape(X[:,0], (num_X,1))
    X_final = np.append(X, X_c1, axis=1)
    Z_c1 = np.reshape(Z[:,0], (num_X,1))
    Z_final = np.append(Z, Z_c1, axis=1)
    A_c1 = np.ones(shape=(num_X,1))*360.0
    A_final = np.append(A, A_c1, axis=1)
    
    return num_X, num_A, X_final, Z_final, A_final
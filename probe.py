# Probe Module

import sys
import numpy as np

def read_cylinder_probe_file(filename):

    X, Y, Z, A = np.loadtxt(filename, unpack=True)
    X_values = np.unique(X)
    num_X = X_values.size
    A_values = np.unique(A)
    num_A = A_values.size

    X = np.reshape(X, (num_X,num_A))
    A = np.reshape(A, (num_X,num_A))
    Z = np.reshape(Z, (num_X,num_A))

    # Copy 0 degree data to 360 data
    X_c1 = np.reshape(X[:,0], (num_X,1))
    X_final = np.append(X, X_c1, axis=1)
    Z_c1 = np.reshape(Z[:,0], (num_X,1))
    Z_final = np.append(Z, Z_c1, axis=1)
    A_c1 = np.ones(shape=(num_X,1))*360.0
    A_final = np.append(A, A_c1, axis=1)
    
    return num_X, num_A, X_final, Z_final, A_final
    

def interpolation_check(probe_f, X_values, A_values, Z_values):

    max_error = 0
    avg_error = 0
    num_values = Z_values.size
    num_X = X_values.size
    num_A = A_values.size
    for i in range(num_X):
        for j in range(num_A):
            Z = Z_values[i][j]
            X = X_values[i]
            A = A_values[j]
            Z_interp = probe_f(X, A)[0][0]
            Z_error = Z_interp - Z
            max_error = max(max_error, abs(Z_error))
            avg_error += abs(Z_error)
    
    return max_error, avg_error
    
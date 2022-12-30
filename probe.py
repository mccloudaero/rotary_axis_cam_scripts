# Probe Module

import sys
import numpy as np
from scipy import interpolate

def read_cylinder_probe_file(filename):

    X, Y, Z, A = np.loadtxt(filename, unpack=True)
    print(X,Z,A)
    X_values = np.unique(X)
    num_X = X_values.size
    Z_values = np.unique(Z)
    num_Z = Z_values.size
    A_values = np.unique(A)
    num_A = A_values.size
    print(num_X,num_Z,num_A)

    if num_X > 1 and num_Z == 1:
        # Probe is edge data
        X = np.reshape(X, (num_Z,num_A))
        A = np.reshape(A, (num_Z,num_A))
        Z = np.reshape(Z, (num_Z,num_A))

        # Copy 0 degree data to 360 data
        X_c1 = np.reshape(X[:,0], (num_Z,1))
        X_final = np.append(X, X_c1, axis=1)
        Z_c1 = np.reshape(Z[:,0], (num_Z,1))
        Z_final = np.append(Z, Z_c1, axis=1)
        A_c1 = np.ones(shape=(num_Z,1))*360.0
        A_final = np.append(A, A_c1, axis=1)
    else:
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


def setup_interpolation(X, A, Z, probe_dim):
    if probe_dim == 1:
        print('\nInterpolating Probe Data in A axis only')
        f = interpolate.interp1d(A, Z)
    elif probe_dim == 2:
        print('\nInterpolating Probe Data in X and A axes')
        f = interpolate.RectBivariateSpline(X, A, Z)
        max_error, avg_error = interpolation_check(f, X, A, Z)
        print('  Max Error: {:5.4e}'.format(max_error))
    
    return f
    

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
    

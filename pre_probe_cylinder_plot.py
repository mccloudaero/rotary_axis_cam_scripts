#!/usr/bin/env python
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

import probe

pre_probe_inputs = {
    'probe_filename': 'probe_results.txt',
    'outer_diameter': None,
    'R_ref': None
}
script_inputs_file = './pre_probe_cylinder_plot.inputs'
R_ref = None
probe_type = None

# Read pre_probe_cylinder_plot.inputs
if os.path.isfile(script_inputs_file):
    print('Input file exists, loading inputs file\n')
    exec(open(script_inputs_file).read())
    R_ref = pre_probe_inputs['outer_diameter']/2.0
else:
    print('No pre_probe_cylinder.inputs file found. Using defaults')

# Read in cylinder probe data
probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file(pre_probe_inputs['probe_filename'])
probe_X_values = np.unique(probe_X)
probe_Z_values = np.unique(probe_Z)
probe_A_values = np.unique(probe_A)

# Check Probe Data Type
probe_dim = None
if probe_X_values.size == 1 and probe_Z_values.size > 1:
    print('Probe Data is 2D Z data (A and Z)')
    probe_dim = 2
    probe_type = 'Z' 
elif probe_X_values.size > 1 and probe_Z_values.size == 1:
    print('Probe Data is 2D X data (A and X)')
    probe_dim = 2
    probe_type = 'X' 
elif probe_X_values.size > 1 and probe_Z_values.size > 1:
    print('Probe Data is 3D Z data (X, A and Z)')
    probe_dim = 3
    probe_type = 'Z' 
else:
    print('Probe Data does not match known dimensions.\nExiting!')
    sys.exit(1)

if probe_type == 'Z':

    # Check for R_ref
    if R_ref is None:
        print('Z Data requires a reference diameter or radius.\nExiting')
        sys.exit(1)

    delta_R = probe_Z - R_ref
    R_avg = np.average(probe_Z)
    R_std = np.std(probe_Z)

    if R_ref is not None:
        print('Nominal Radius: {:5.4f}'.format(R_ref))
    print('Average Radius: {:5.4f}'.format(R_avg))
    print('Standard Deviation Radius: {:5.4f}'.format(R_std))

    # Cross Sections
    fig, ax = plt.subplots()
    for i in range(probe_num_X):
        #theta = np.pi/180.0*A
        #fig_polar, ax_polar = plt.subplots(subplot_kw={'projection': 'polar'})
        #ax_polar.plot(theta[0,:], Z[0,:], 'bo')
        #ax_polar.set_rmax(3.5)
        #plt.show()
        ax.plot(probe_A[i,:],probe_Z[i,:])
        ax.set_xlabel('A (deg)')
        ax.set_ylabel('Z/Radius (in)')
        if R_ref is not None:
            plt.axhline(y=R_ref, color='black', label='R_ref')
        plt.axhline(y=R_avg, color='gray', label='R_avg')

    fig.legend()

    plt.savefig('probe_cross_sections.png', dpi=150)

    if probe_dim == 3:
        # Contour Plot
        fig, ax = plt.subplots()
        contour = ax.contourf(probe_X, probe_A, delta_R, cmap = 'RdBu')
        #ax.plot(X, A, 'k.')
        cbar = fig.colorbar(contour)
        cbar.ax.set_ylabel('Delta_R (in)')
        ax.set_xlabel('X (in)')
        ax.set_ylabel('A (deg)')
        ax.yaxis.set_ticks(probe_A_values)
        plt.savefig('probe_contour.png')


elif probe_type == 'X':

    # Print stats and check range
    X_avg = np.average(probe_X)
    X_std = np.std(probe_X)
    print('Average Edge X: {:5.4f}'.format(X_avg))
    print('Standard Deviation Edge X: {:5.4f}'.format(X_std))
    X_min = np.min(probe_X)
    X_max = np.max(probe_X)
    if X_min > 0:
        print('Warning! X_min,', X_min, 'is greater than zero')
    elif X_max < 0:
        print('Warning! X_max,', X_min, 'is less than zero')

    # Cross Sections
    fig, ax = plt.subplots()
    ax.set_xlabel('A (deg)')
    ax.set_ylabel('X (in)')
    ax.plot(probe_A[0,:],probe_X[0,:], label='probe')
    plt.axhline(y=X_avg, color='gray', label='X_avg')

    fig.legend()

    plt.savefig('probe_edge.png', dpi=150)

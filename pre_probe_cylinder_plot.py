#!/usr/bin/env python
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

import probe

script_inputs_file = './pre_probe_cylinder.inputs'
R_ref = None
# Read pre_probe_cylinder.inputs
if os.path.isfile(script_inputs_file):
    print('Input file exists, loading inputs file\n')
    exec(open(script_inputs_file).read())
    R_ref = pre_probe_inputs['outer_diameter']/2.0
else:
    print('No pre_probe_cylinder.inputs file found.\nExiting!')
    sys.exit()


# Read in cylinder probe data
probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file('probe_results.txt')
probe_X_values = np.unique(probe_X)
probe_A_values = np.unique(probe_A)

delta_R = probe_Z - R_ref
R_avg = np.average(probe_Z)


# Check Probe Data dimensions
probe_dim = None
if probe_X_values.size == 1:
    print('Probe Data is 2D (A and Z)')
    probe_dim = 2
else:
    print('Probe Data is 3D (X, A and Z)')
    probe_dim = 3

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

if R_ref is not None:
    print('Nominal Radius: {:5.4f}'.format(R_ref))
print('Average Radius: {:5.4f}'.format(R_avg))

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
        plt.axhline(y=R_ref, color='black')
    plt.axhline(y=R_avg, color='gray')

plt.savefig('probe_cross_sections.png')

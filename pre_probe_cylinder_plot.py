#!/usr/bin/env python
import sys
import numpy as np
import matplotlib.pyplot as plt

import probe

# Read in cylinder probe data
num_X, num_A, X, Z, A = probe.read_cylinder_probe_file('probe_results.txt')
X_values = np.unique(X)
A_values = np.unique(A)

delta_R = Z - Z[0][0]


# Contour Plot
fig, ax = plt.subplots()
contour = ax.contourf(X, A, delta_R, cmap = 'RdBu')
ax.plot(X, A, 'k.')
cbar = fig.colorbar(contour)
cbar.ax.set_ylabel('Delta_R (in)')
ax.set_xlabel('X (in)')
ax.set_ylabel('A (deg)')
ax.yaxis.set_ticks(A_values)
plt.savefig('probe_contour.png')

# Cross Sections
fig, ax = plt.subplots()
for i in range(num_X):
    #theta = np.pi/180.0*A
    #fig_polar, ax_polar = plt.subplots(subplot_kw={'projection': 'polar'})
    #ax_polar.plot(theta[0,:], Z[0,:], 'bo')
    #ax_polar.set_rmax(3.5)
    #plt.show()
    ax.plot(A[i,:],delta_R[i,:])

plt.savefig('probe_cross_sections.png')
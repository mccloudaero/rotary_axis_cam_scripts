#!/usr/bin/env python
import sys
import numpy as np
import matplotlib.pyplot as plt

X, Y, Z, A = np.loadtxt('probe_results.txt', unpack=True)
X_values = np.unique(X)
num_X = X_values.size
A_values = np.unique(A)
num_A = A_values.size

print(num_X, num_A)

X = np.reshape(X, (num_X,num_A))
A = np.reshape(A, (num_X,num_A))
Z = np.reshape(Z, (num_X,num_A))
delta_R = Z - Z[0][0]

# Copy 0 degree data to 360 data
X_c1 = np.reshape(X[:,0], (num_X,1))
X_final = np.append(X, c1, axis=1)
print(X_final)

# Contour Plot
fig, ax = plt.subplots()
contour = ax.contourf(X, A, delta_R)
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

plt.show()
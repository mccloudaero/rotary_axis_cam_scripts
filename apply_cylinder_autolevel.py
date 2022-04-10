#!/usr/bin/env python
import sys
import math
import re
import numpy as np
from scipy import interpolate

import probe

# Code assumes we are in G90   (absolute travel mode)
# Code assumes we are in G90.1 (absolute arc center mode)


input_file = open('input.nc','r')
output_file = open('output.nc','w')

G_commands = ['G0','G00','G1','G01']

z_ref = 3.0
z_safe = None

x_current = 0
a_current = 0

# Store if last line is 'plunge' or 'first' or None
last_line = None
last_Z = None

print('\nReading Probe Data')
probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file('probe_file.txt')
probe_X_values = np.unique(probe_X)
probe_A_values = np.unique(probe_A)

# Convert Z to delta Z map
dZ = probe_Z - z_ref

dZ_min = np.min(dZ)
dZ_max = np.max(dZ)
print('  dZ Min: {:5.4f}'.format(dZ_min))
print('  dZ Max: {:5.4f}'.format(dZ_max))

    
print('\nInterpolating Probe Data')
probe_f = interpolate.RectBivariateSpline(probe_X_values, probe_A_values, dZ)
max_error, avg_error = probe.interpolation_check(probe_f, probe_X_values, probe_A_values, dZ)
print('  Max Error: {:5.4e}'.format(max_error))

for line in input_file:
    if line[0] == '%':
        # Don't modify
        output_file.write(line)
        last_line = None
    elif line[0] == '(':
        # Don't modify
        output_file.write(line)
        last_line = None
    elif line[0] == 'M': # Misc
        # Don't modify
        output_file.write(line)
        last_line = None
    elif line[0] == 'G':
        # Here we want to split the line to break out the coordinates
        # X, Y, Z, A, B, C, and the feedrate F. However, we want to
        # keep the delimiters, which requires the parenthesis.
        line_split = re.split('(X|Y|Z|A|B|C|F)',line)
        command = [item.strip() for item in line_split]
        trailing = line[2:]
        if command[0] in G_commands:
            # Check if X is present
            if 'X' in command:
                x_index = command.index('X')
                x_current = float(command[x_index + 1].strip())
            # Check if A is present
            if 'A' in command:
                a_index = command.index('A')
                a_current = float(command[a_index + 1].strip())
            # Check if F is present
            # Need this if added Z to command
            if 'F' in command:
                f_index = command.index('F')
            # Check if Z is present
            if 'Z' in command:
                z_index = command.index('Z') + 1
                z_current = float(command[z_index].strip())
                if z_safe is None:
                    # Assume first Z found is safe height
                    z_safe = z_current
                    print('\nZ Safe Height is: {:4.3f}'.format(z_safe))                
                if z_current != z_safe:
                    # Interpolate dZ based on X and A
                    dz_current = probe_f(x_current, a_current)[0,0]
                    command[z_index] = '{:5.4f}'.format(z_current + dz_current)
                    #print(x_current, a_current, z_current, dz_current)
            else:
                if z_current != z_safe:
                    # Add interpolated Z
                    dz_current = probe_f(x_current, a_current)[0,0]
                    command.insert(f_index, '{:5.4f}'.format(z_current + dz_current))
                    command.insert(f_index, 'Z')
            # Rebuild command with whitespace
            new_line = ''
            num_items = len(command)
            for i in range(0,num_items-1):
                new_line += command[i] + ' '
            new_line += command[-1] + '\n'
            output_file.write(new_line)
        else:
            # Don't modify all other GXX commands
            output_file.write(line)
            last_line = None
    elif line[0] == 'X' or line[0] == 'Y':
        # Don't modify
        output_file.write(line)
        if last_line == 'plunge':
            output_file.write('G1 F{:.4f}\n'.format(current_F*second_cut_factor))
            last_line = 'first'
        elif last_line == 'first':
            output_file.write('G1 F{:.4f}\n'.format(current_F))
            last_line = None
        else:
            last_line = None

input_file.close()
output_file.close()

#!/usr/bin/env python
import sys
import math
import re

input_file = open('drill_holes.nc','r')
output_file = open('drill_wider_holes.nc','w')

# Hole parameters
old_hole_diam = 0.1250
new_hole_diam = 0.1360
delta_R = (new_hole_diam-old_hole_diam)/2.0
print('Delta Radius: {:.4f}'.format(delta_R))
feed_rate = 4.0 # in/min

# Code assumes we are in G90   (absolute travel mode)
# Code assumes we are in G90.1 (absolute arc center mode)
last_X = 0.0
last_Y = 0.0

hole_count = 0
for line in input_file:
    if line[0] == '(':
        # Don't modify
        output_file.write(line)
    if line[0] == 'M':
        # Don't modify, but add G90.1 code if needed
        command = line[:2]
        trailing = line[2:]
        if command == 'M6':
            # Add absolute arc center mode
            output_file.write('(Set Absolute Arc Center Mode)\n')
            output_file.write('G90.1\n')
        output_file.write(line)
    if line[0] == 'G':
        command = line[:2]
        trailing = line[2:]
        if command == 'G0':
            # Don't modify, but get X, Y values
            output_file.write(line)
            # Get last x, and y locations
            if 'X' in trailing:
                last_X = float(re.split('X|Y|Z|F',trailing)[1])
            if 'Y' in trailing:
                last_Y = float(re.split('Y|Z|F',trailing)[1]) # Omit X, so Y value is always at the 1 index
        if command == 'G1':
            # Don't modify
            output_file.write(line)
            # Check if X, Y and A are not present 
            if 'X' not in line and 'Y' not in line and 'A' not in line:
                # Plunge Cut, Add Circular Arc Cut to Widen Hole
                hole_count += 1
                print('Hole Center:',last_X, last_Y)
                # First move to new starting point in X axis at Feed Rate
                new_X = last_X + delta_R
                new_line = 'G1 X{:.4f} F{:.2f}\n'.format(new_X,feed_rate)
                output_file.write(new_line)
                # Add circular arc
                new_line = 'G2 X{:.4f} Y{:.4f} I{:.4f} J{:.4f} F{:.2f}\n'.format(new_X,last_Y,last_X,last_Y,feed_rate)
                output_file.write(new_line)
            else:
                print('Not plunge, Fix This!')
                sys.exit(1)
    last_line = line 

print('Holes widened:', hole_count)
input_file.close()
output_file.close()

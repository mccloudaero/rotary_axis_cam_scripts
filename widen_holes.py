#!/usr/bin/env python
import sys
import math
import re

# Code assumes we are in G90   (absolute travel mode)
# Code assumes we are in G90.1 (absolute arc center mode)

input_file = open('drill_holes.nc','r')
output_file = open('drill_wider_holes.nc','w')

# Hole parameters
old_hole_diam = 0.1250
new_hole_diam = 0.1360
delta_R = (new_hole_diam-old_hole_diam)/2.0
print('Delta Radius: {:.4f}'.format(delta_R))
feed_rate = 4.0 # in/min

last_X = 0.0
last_Y = 0.0
arc_mode = ''

hole_count = 0
plunge_feed = 0.0
for line in input_file:
    if line[0] == '(':
        # Don't modify
        output_file.write(line)
    elif line[0] == 'M': # Misc
        # Don't modify, but add G90.1 code if needed
        command = line[:2]
        trailing = line[2:]
        if command == 'M6' and arc_mode is not 'G90.1':
            # Add absolute arc center mode
            output_file.write('(Set Absolute Arc Center Mode)\n')
            output_file.write('G90.1\n')
        output_file.write(line)
    elif line[0] == 'G':
        command = re.split('X|Y|Z|A|F',line)
        command_0 = command[0].strip()
        trailing = line[2:]
        # Check for arc mode
        if 'G90.1' in line:
            arc_mode = 'G90.1'
        if command_0 == 'G0' or command_0 == 'G00':
            # Don't modify, but get X, Y values
            output_file.write(line)
            # Get last x, and y locations
            if 'X' in trailing:
                last_X = float(re.split('X|Y|Z|A|F',trailing)[1])
            if 'Y' in trailing:
                last_Y = float(re.split('Y|Z|A|F',trailing)[1]) # Omit X, so Y value is always at the 1 index
        elif command_0 == 'G1' or command_0 == 'G01':
            # Check if X, Y and A are not present 
            if 'X' not in line and 'Y' not in line and 'A' not in line:
                # Plunge Cut, Add Circular Arc Cut to Widen Hole
                hole_count += 1
                print('Hole Center:',last_X, last_Y)
                # Check for plunge feed rate, save for later
                if 'F' in line:
                    plunge_feed_rate = float(re.split('F',line)[-1])
                    print('Found Plunge Feed Rate:', plunge_feed_rate)
                    # Don't modify current line and add additional lines
                    output_file.write(line)
                else:
                    # Add plunge feed rate
                    output_file.write(line.strip() + ' F {:.2f}\n'.format(plunge_feed_rate))
                
                # Move to arc starting point in X axis at Feed Rate
                new_X = last_X + delta_R
                new_line = 'G1 X {:.4f} Y {:.4f} F {:.2f}\n'.format(new_X, last_Y, feed_rate)
                output_file.write(new_line)
                # Add circular arc
                new_line = 'G2 X {:.4f} Y {:.4f} I {:.4f} J {:.4f} F {:.2f}\n'.format(new_X, last_Y, last_X, last_Y, feed_rate)
                output_file.write(new_line)
            else:
                print('Not plunge, Fix This!')
                print(line)
                sys.exit(1)
        else:
            # Don't modify all other GXX commands
            output_file.write(line)

print('Holes widened:', hole_count)
input_file.close()
output_file.close()

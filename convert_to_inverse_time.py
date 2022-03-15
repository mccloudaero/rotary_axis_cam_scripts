#!/usr/bin/env python
import sys
import math

verbose = False
input_file = open('test_input.nc','r')
output_file = open('test_output.nc','w')

# Code assumes we are in G90 (absolute travel mode)

# Assume that we are starting in G94 mode and not G93
current_mode = 'G94'

feed_rate = 0.0
last_x = 0.0
last_a = 0.0
last_z = 0.0

line_count = 0
for line in input_file:
    line_count +=1
    if line[0] == '(' or line[0] == 'M':
        # Don't modify
        output_file.write(line)
    if line[0] == 'G':
        command = line.split()
        if command[0] == 'G0':
            # Check current_mode and switch if needed
            if current_mode == 'G93':
                current_mode = 'G94'
                output_file.write(current_mode+'\n')
            # Get last x, a and z locations
            if 'X' in line:
                if 'X' in command:
                    # X is positive
                    x_index = command.index('X') + 1
                    last_x = float(command[x_index])
                else:
                    # X is negative
                    for item in command:
                        if 'X' in item:
                            last_x = float(item.split('X')[-1])
            if 'A' in command:
                # rotation is positive
                a_index = command.index('A') + 1
                last_a = float(command[a_index])
            else:
                for item in command:
                    if 'A' in item:
                        last_a = float(item.split('A')[-1])
            # Check for current Z
            # Note: we use this to get the radius of the part
            # We assume that Z will always be positive
            if 'Z' in line:
                z_index = command.index('Z') + 1
                last_z = command[z_index]
        if command[0] == 'G1':
            line_has_feedrate = False
            # Check for feedrate
            if 'F' in line:
                feed_rate_index = command.index('F') + 1
                feed_rate = float(command[feed_rate_index])
                line_has_feedrate = True
            # Check X
            if 'X' in line:
                if 'X' in command:
                    # X is positive
                    x_index = command.index('X') + 1
                    current_x = float(command[x_index])
                else:
                    # X is negative
                    for item in command:
                        if 'X' in item:
                            current_x = float(item.split('X')[-1])
                dx = current_x - last_x
                last_x = current_x
            else:
                dx = 0.0
            # Check for current Z
            # Note: we use this to get the radius of the part
            # We assume that Z will always be positive
            if 'Z' in line:
                try:
                    z_index = command.index('Z') + 1
                except ValueError:
                    print(line)
                    sys.exit()
                last_z = command[z_index]
            # Check for rotation
            if 'A' in line:
                # Check if line contains A and feedrate. If so, the input
                # likely isn't correct. Warn and exit the program.
                if line_has_feedrate is True:
                    print('A Gcode command is defining both A and F at the same\
                           time. It is likely the input is incorrect. If the\
                           input was wrapped using G-Code-Ripper, set Feed\
                           Adjust to None and regenerate the input.\nExiting')
                    sys.exit()


                # Need to modify code
                # Check current_mode and switch if needed
                if current_mode == 'G94':
                    current_mode = 'G93'
                    output_file.write(current_mode+'\n')
                # Get A-axis travel distance (d1)
                # Note if travel is negative, split command didn't work
                if 'A' in command:
                    # rotation is positive
                    a_index = command.index('A') + 1
                    current_a = float(command[a_index])
                else:
                    for item in command:
                        if 'A' in item:
                            current_a = float(item.split('A')[-1])
                rot = current_a - last_a
                last_a = current_a
                
                # Compute radial distance traveled (angle in radians * radius)
                # assume last Z is the current radius
                d_rot = (math.pi*rot/180)*float(last_z)
            else:
                d_rot = 0.0

            if current_mode == 'G93':
                # Compute total distance traveled
                # assumes that Z travel is neglgible
                distance = (dx**2 + d_rot**2)**0.5

                # Compute inverse time
                F = feed_rate/distance
                
                # Used to have this in here
                # If purely rotational motion, modify the feed rates
                #if dx == 0:
                #    F = F / 3.5 

                # Assemble updated line
                mod_line = ""
                for item in command:
                    if item != 'F':
                        mod_line += item + " " # add space back in
                    else:
                        # Add in new feedrate
                        mod_line += 'F {:5.2f}'.format(F)
                        break
                # Need to always include feedrate in G93 mode
                if line_has_feedrate == False:
                    if verbose:
                        mod_line += 'F {:5.2f} (lf: {:3.2f} ips)'.format(F,feed_rate)
                    else:
                        mod_line += 'F {:5.2f}'.format(F)

                output_file.write(mod_line.strip() + '\n')
                #print('lc {:4d} {:3.1f} {:5.3f} {:5.3f} {:5.3f} {:3.3f}'.format(line_count,feed_rate,distance,dx,d_rot,F))
                
                # Debug
                #print('angle: {:4.3f}'.format(rot))
                #print('total: {:4.3f} dx: {:4.3f} drot: {:4.3f}'.format(distance, dx, d_rot))
                #print('feed_rate: {:4.3f} F: {:4.3f}'.format(feed_rate,F))
                #if dx != 0.0:
                #    sys.exit()

            else:
                # Don't modify
                output_file.write(line)
            
        else:
            # Don't modify
            output_file.write(line)
    #if line_count > 40:
    #    sys.exit()


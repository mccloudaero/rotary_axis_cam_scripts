#!/usr/bin/env python
import sys
import math

# Script assumes:
#   1) The center of the cylinder is along the Y=0, Z=0 axis
#   2) X = 0 is the start of the cylinder

pre_probe_inputs = {
    'outer_diameter' : 12.75,
    'num_x_points' : 4,
    'num_a_points' : 24,
    'start_x' : -3.0,
    'end_x' : 0,
    'safe_clearance': 0.1,
    'min_probe_depth': -0.1,
    'probe_feedrate': 1.0,
    'output_file': None,
}

print('Creating pre-probe G-code file')
total_points = pre_probe_inputs['num_a_points']*pre_probe_inputs['num_x_points']
outer_radius = pre_probe_inputs['outer_diameter']/2.0
safe_z_height = outer_radius + pre_probe_inputs['safe_clearance']
probe_min_z = outer_radius + pre_probe_inputs['min_probe_depth']

if pre_probe_inputs['num_x_points'] < 1:
    print('\nInvalid number of X points\nExiting!')
    sys.exit(1)
if pre_probe_inputs['num_x_points'] == 1:
    delta_x = 0
else:
    delta_x = (pre_probe_inputs['end_x'] - pre_probe_inputs['start_x'])/(pre_probe_inputs['num_x_points']-1)
delta_a = 360.0/pre_probe_inputs['num_a_points']

print('Number of X Points: {:3d}'.format(pre_probe_inputs['num_x_points']))
print('Number of A Points: {:3d}'.format(pre_probe_inputs['num_a_points']))
print('Total Number of Points {:3d}'.format(total_points))


# Open Output File
if pre_probe_inputs['output_file'] is None:
    # Autocreate filename
    output_filename = 'pre_probe_'
    output_filename += str(pre_probe_inputs['outer_diameter']) + '_od'
    output_filename += '.nc'
else:
    output_filename = pre_probe_inputs['output_file']
print('\nWriting Gcode to:', output_filename)
output_file = open(output_filename,'w')


# Write Header
output_file.write('(G-code automatically written using pre_probe_cylinder.py)\n')
output_file.write('(Outer Diameter: {:4.2f})\n'.format(pre_probe_inputs['outer_diameter']))
output_file.write('(Total Number of points to Probe: {:4d})\n'.format(total_points))
output_file.write('G90   (set absolute distance mode)\n')
output_file.write('G90.1 (set absolute distance mode for arc centers)\n')
output_file.write('G17   (set active plane to XY)\n')
output_file.write('G20   (set units to inches)\n')
output_file.write('\n')

output_file.write('M0 (Attach probe wires and clips that need attaching)\n')
output_file.write('M40 (Open probe file)\n')
output_file.write('\n')

# Position at Start
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
output_file.write('G0 Y 0.0000\n')

for i in range(pre_probe_inputs['num_x_points']):
    x = pre_probe_inputs['start_x'] + i*delta_x
    output_file.write('(X={:5.4f})\n'.format(x))
    for j in range(pre_probe_inputs['num_a_points']):
        a = j*delta_a
        x = pre_probe_inputs['start_x'] + i*delta_x
        output_file.write('G0 X {:5.4f} A {:5.3f}\n'.format(x,a))
        output_file.write('G31 Z {:5.4f} F {:2.1f}\n'.format(probe_min_z,pre_probe_inputs['probe_feedrate']))
        output_file.write('G0 Z {:5.4f}\n'.format(safe_z_height))


# Complete File
output_file.write('\nM41 (Closes the opened log file)\n')
output_file.write('M30\n')
# Close File
output_file.close()

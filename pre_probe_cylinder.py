#!/usr/bin/env python
import sys
import math

# Script assumes:
#   1) The center of the cylinder is along the Y=0, Z=0 axis
#   2) X = 0 is the start of the cylinder

inputs = {
    'outer_diameter' : 6.0,
    'num_x_points' : 5,
    'num_a_points' : 12,
    'start_x' : 0.3125,
    'end_x' : 5.704,
    'safe_clearance': 0.1,
    'min_probe_depth': -0.1,
    'probe_feedrate': 1.0,
}

total_points = inputs['num_a_points']*inputs['num_x_points']
outer_radius = inputs['outer_diameter']/2.0
safe_z_height = outer_radius + inputs['safe_clearance']
probe_min_z = outer_radius + inputs['min_probe_depth']

delta_x = (inputs['end_x'] - inputs['start_x'])/(inputs['num_x_points']-1)
delta_a = 360.0/inputs['num_a_points']

# Open File
output_file = open('pre_probe.nc','w')

# Write Header
output_file.write('(G-code automatically written using pre_probe_cylinder.py)\n')
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

for i in range(inputs['num_x_points']):
    x = inputs['start_x'] + i*delta_x
    output_file.write('(X={:5.4f})\n'.format(x))
    for j in range(inputs['num_a_points']):
        a = j*delta_a
        x = inputs['start_x'] + i*delta_x
        output_file.write('G0 X {:5.4f} A {:5.3f}\n'.format(x,a))
        output_file.write('G31 Z {:5.4f} F {:2.1f}\n'.format(probe_min_z,inputs['probe_feedrate']))
        output_file.write('G0 Z {:5.4f}\n'.format(safe_z_height))


# Complete File
output_file.write('\nM41 (Closes the opened log file)\n')
output_file.write('M30\n')
# Close File
output_file.close()

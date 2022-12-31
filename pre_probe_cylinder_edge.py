#!/usr/bin/env python
import sys
import os
import math

import rotary_axis_cam

# Script assumes:
#   1) The center of the cylinder is along the Y=0, Z=0 axis
#   2) X = 0 is the start of the cylinder

script_inputs_file = './pre_probe_cylinder_edge.inputs'
pre_probe_inputs = {
    'outer_diameter' : None,
    'num_a_points' : None,
    'edge_x' : None,
    'probe_z' : None,
    'safe_clearance': 0.1,
    'min_probe_x': -0.1,
    'probe_feedrate': 1.0,
    'output_file': None,
}

if os.path.isfile(script_inputs_file):
    print('Input file exists, loading inputs file\n')
    exec(open(script_inputs_file).read())
else:
    # Write inputs file
    try:
        outputfile = open(script_inputs_file, 'w')
    except IOError:
        print('Cannot open', script_inputs_file, '\nExiting!')
    print('Writing input values to:', script_inputs_file)
    outputfile.write('pre_probe_inputs = {\n')
    rotary_axis_cam.write_dict(outputfile, pre_probe_inputs)
    outputfile.close()
    print('Update ' + script_inputs_file + ' and re-run')
    sys.exit()


print('Creating pre-probe G-code file')
outer_radius = pre_probe_inputs['outer_diameter']/2.0
safe_z_height = outer_radius + pre_probe_inputs['safe_clearance']
safe_x = pre_probe_inputs['edge_x'] + pre_probe_inputs['safe_clearance']
min_probe_x = pre_probe_inputs['min_probe_x']

delta_a = 360.0/pre_probe_inputs['num_a_points']

print('Number of A Points: {:3d}'.format(pre_probe_inputs['num_a_points']))


# Open Output File
if pre_probe_inputs['output_file'] is None:
    # Autocreate filename
    output_filename = 'pre_probe_edge_'
    output_filename += str(pre_probe_inputs['outer_diameter']) + '_od'
    output_filename += '.nc'
else:
    output_filename = pre_probe_inputs['output_file']
print('\nWriting Gcode to:', output_filename)
output_file = open(output_filename,'w')


# Write Header
output_file.write('(G-code automatically written using pre_probe_cylinder_edge.py)\n')
output_file.write('(Outer Diameter: {:4.2f})\n'.format(pre_probe_inputs['outer_diameter']))
output_file.write('(Total Number of points to Probe: {:4d})\n'.format(pre_probe_inputs['num_a_points']))
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
output_file.write('G0 A 0.000\n')
output_file.write('G0 X {:5.4f} (Safe X)\n'.format(safe_x))

# Lower in Z axis to Probe Edge
output_file.write('G1 Z {:5.4f} F {:2.1F} (Probe Z height)\n'.format(pre_probe_inputs['probe_z'], pre_probe_inputs['probe_feedrate']))

# 
for j in range(pre_probe_inputs['num_a_points']):
    a = j*delta_a
    output_file.write('G0 X {:5.4f} A {:5.3f}\n'.format(safe_x,a))
    output_file.write('G31 X {:5.4f} F {:2.1f} (Probe in -X dir)\n'.format(min_probe_x,pre_probe_inputs['probe_feedrate']))
    output_file.write('G0 X {:5.4f} (Return to safe X)\n'.format(safe_x))

# Return to Safe Z Height
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))

# Complete File
output_file.write('\nM41 (Closes the opened log file)\n')
output_file.write('M30\n')
# Close File
output_file.close()

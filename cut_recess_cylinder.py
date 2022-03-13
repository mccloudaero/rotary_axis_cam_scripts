#!/usr/bin/env python
import sys
import math

# Create gcode to cut recess in cylinder in a manner that accepts pre-probe
# results. Instead of cutting in a spiral pattern, cut are made in circles.


# Script assumes
#   1) The center of the cylinder is along the Y=0, Z=0 axis
#   2) X = 0 is the start of the cylinder

inputs = {
    'outer_diameter' : 6.0,
    'recess_depth' : 0.05,
    'flange_width' : 0.3125,
    'pattern_size' : 1.571,
    'num_rows': 4,
    'rib_width': 0.05,
}
cutter_inputs = {
    'mill_diameter' : 0.25,
    'overlap' : 0.4,
    'material_to_leave' : 0.01,
    'safe_clearance' : 0.1,
    'feedrate_plunge' : 0.75,
    'feedrate_linear': 5.0, # IPM
}

outer_radius = inputs['outer_diameter']/2.0

# Angular Data
angular_increment = 30 # degrees
A_values = range(30, 390, angular_increment)
angular_increment_distance = math.pi/180.0*angular_increment*outer_radius

# X-axis Data
triangle_height = (3.0**0.5)/2.0 * inputs['pattern_size'] # isogrid triangle height
x_start = inputs['flange_width'] + cutter_inputs['material_to_leave'] + cutter_inputs['mill_diameter']/2.0
recess_length = triangle_height*inputs['num_rows'] - inputs['rib_width'] - 2*cutter_inputs['material_to_leave']
dx_recess = recess_length - cutter_inputs['mill_diameter']
dx_stepover = cutter_inputs['mill_diameter']*cutter_inputs['overlap']
x_end = x_start + dx_recess

# Z-axis Data
safe_z_height = outer_radius + cutter_inputs['safe_clearance']
z_recess = outer_radius - inputs['recess_depth'] + cutter_inputs['material_to_leave']


print('Triangle Height: {:4.3f}'.format(triangle_height))
print('X start: {:5.4f}'.format(x_start))
print('X end: {:5.4f}'.format(x_end))
print('Z recess: {:5.4f}'.format(z_recess))

# Open File
output_file = open('test.nc','w')

# Write Header
output_file.write('(G-code automatically written using cut_recess_cylinder.py)\n')
output_file.write('G90   (set absolute distance mode)\n')
output_file.write('G90.1 (set absolute distance mode for arc centers)\n')
output_file.write('G17   (set active plane to XY)\n')
output_file.write('G20   (set units to inches)\n')
output_file.write('\n')

# Position at Start
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
output_file.write('G0 X {:5.4f} Y 0.0000 A 0.0000\n'.format(x_start))

# Plunge into material
local_z = z_recess
output_file.write('G1 Z {:5.4f} (plunge cut)\n'.format(local_z))

# First Cut
output_file.write('(first cut)\n')
x_current = x_start
A_absolute = 0
for A in A_values:
    # Interpolate Z based on X and A (0-360)
    z_local = z_recess
    A_absolute += angular_increment
    output_file.write('G1 Z {:5.4f} A {:6.2f} F {:3.2f} ({:6.2f})\n'.format(z_local, A_absolute, 1.0, A))
x_current += dx_stepover

# Keep Cutting
while x_current < x_end:
    # Interpolate Z based on X and A (0-360)
    z_local = z_recess
    
    # Move in X direction
    output_file.write('G1 X {:5.4f} Z {:5.4f}\n'.format(x_current, z_local))
    for A in A_values:
        # Interpolate Z based on X and A (0-360)
        z_local = z_recess
        A_absolute += angular_increment
        output_file.write('G1 Z {:5.4f} A {:6.2f} F {:3.2f} ({:6.2f})\n'.format(z_local, A_absolute, 1.0, A))
    
    # Increment X
    x_current += dx_stepover

# Final Pass
output_file.write('(final cut)\n')
x_current = x_end
# Interpolate Z based on X and A (0-360)
z_local = z_recess
    
# Move in X direction
output_file.write('G1 X {:5.4f} Z {:5.4f}\n'.format(x_current, z_local))
for A in A_values:
    z_local = z_recess
    output_file.write('G1 Z {:5.4f} A {:6.2f} F {:3.2f} ({:6.2f})\n'.format(z_local, A_absolute, 1.0, A))

output_file.write('M30\n')
# Close File
output_file.close()
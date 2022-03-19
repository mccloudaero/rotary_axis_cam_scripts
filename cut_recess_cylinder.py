#!/usr/bin/env python
import sys
import math
import numpy as np
import probe

# Create G-code to cut recess in cylinder in a manner that accepts pre-probe
# results. Instead of cutting in a spiral pattern, cut are made in circles.
# Inverse Time mode (G93) is used to specify feed rates


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
    'angular_increment': 30,
    'use_probe_file': True
}
cutter_inputs = {
    'mill_diameter' : 0.25,
    'overlap' : 0.4,
    'material_to_leave' : 0.01,
    'safe_clearance' : 0.1,
    'feedrate_plunge' : 0.75,
    'feedrate_linear': 5.0, # IPM
}

if inputs['use_probe_file']:
    # Load module for interpolation
    from scipy import interpolate

outer_radius = inputs['outer_diameter']/2.0

# Angular Data
angular_increment = inputs['angular_increment']
A_values = range(angular_increment, angular_increment + 360, angular_increment)
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
dz_recess = inputs['recess_depth'] + cutter_inputs['material_to_leave']
z_recess_nominal = outer_radius - dz_recess

print('\nRecess Dimensions')
print('Triangle Height: {:4.3f}'.format(triangle_height))
print('X start: {:5.4f}'.format(x_start))
print('X end: {:5.4f}'.format(x_end))
print('Z recess: {:5.4f}'.format(z_recess_nominal))

# Read Probe Data if needed
print('\nReading Probe Data')
probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file('probe_results.txt')
probe_X_values = np.unique(probe_X)
probe_A_values = np.unique(probe_A)
print('Interpolating Probe Data')
probe_f = interpolate.RectBivariateSpline(probe_X_values, probe_A_values, probe_Z)

# Open File
print('\nWriting Gcode')
output_file = open('test.nc','w')

# Write Header
output_file.write('(G-code automatically written using cut_recess_cylinder.py)\n')
output_file.write('G90   (set absolute distance mode)\n')
output_file.write('G90.1 (set absolute distance mode for arc centers)\n')
output_file.write('G17   (set active plane to XY)\n')
output_file.write('G20   (set units to inches)\n')
output_file.write('G94   (standard feed rates)\n')
output_file.write('\n')

# Position at Start
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
output_file.write('G0 X {:5.4f} Y 0.0000 A 0.0000\n'.format(x_start))

# Plunge into material
if inputs['use_probe_file']:
    # Interpolate Z based on X and A (0-360)
    z_local = probe_f(x_start, 0.0)[0,0] - dz_recess
else:
    z_local = z_recess_nominal
output_file.write('G1 Z {:5.4f} F {:3.2f} (plunge cut)\n'.format(z_local,cutter_inputs['feedrate_plunge']))

# First Cut
# Cut at fraction of full speed since it's cutting the full width of the bit
current_feedrate_linear = cutter_inputs['feedrate_linear']*0.75
current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
output_file.write('(first cut)\n')
output_file.write('G93 (switch to inverse time)\n')
x_current = x_start
A_absolute = 0
for A in A_values:
    if inputs['use_probe_file']:
        # Interpolate Z based on X and A (0-360)
        z_local = probe_f(x_current, A)[0,0] - dz_recess
    else:
        z_local = z_recess_nominal
    A_absolute += angular_increment
    output_file.write('G1 Z {:5.4f} A {:6.2f} F {:5.4f} ({:6.2f})\n'.format(z_local, A_absolute, current_feedrate_inverse_t, A))
x_current += dx_stepover

# Keep Cutting
current_feedrate_linear = cutter_inputs['feedrate_linear']
current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
while x_current < x_end:
    if inputs['use_probe_file']:
        # Interpolate Z based on X and A (0-360)
        z_local = probe_f(x_current, 0)[0,0] - dz_recess
    else:
        z_local = z_recess_nominal
    
    # Move in X direction
    current_feedrate_linear = cutter_inputs['feedrate_linear']*0.75
    current_feedrate_inverse_t = current_feedrate_linear/dx_stepover
    
    output_file.write('G1 X {:5.4f} Z {:5.4f} F {:5.4f}\n'.format(x_current, z_local, current_feedrate_inverse_t))
    
    current_feedrate_linear = cutter_inputs['feedrate_linear']
    current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
    for A in A_values:
        if inputs['use_probe_file']:
            # Interpolate Z based on X and A (0-360)
            z_local = probe_f(x_current, A)[0,0] - dz_recess
        else:
            z_local = z_recess_nominal
        A_absolute += angular_increment
        output_file.write('G1 Z {:5.4f} A {:6.2f} F {:5.4f} ({:6.2f})\n'.format(z_local, A_absolute, current_feedrate_inverse_t, A))
    
    # Increment X
    x_current += dx_stepover

# Final Pass
output_file.write('(final cut)\n')
x_current = x_end
# Interpolate Z based on X and A (0-360)
z_local = z_recess_nominal
    
# Move in X direction
current_feedrate_linear = cutter_inputs['feedrate_linear']*0.75
current_feedrate_inverse_t = current_feedrate_linear/dx_stepover
output_file.write('G1 X {:5.4f} Z {:5.4f} F {:5.4f}\n'.format(x_current, z_local, current_feedrate_inverse_t))

current_feedrate_linear = cutter_inputs['feedrate_linear']
current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
for A in A_values:
    if inputs['use_probe_file']:
        # Interpolate Z based on X and A (0-360)
        z_local = probe_f(x_current, A)[0,0] - dz_recess
    else:
        z_local = z_recess_nominal
    output_file.write('G1 Z {:5.4f} A {:6.2f} F {:5.4f} ({:6.2f})\n'.format(z_local, A_absolute, current_feedrate_inverse_t, A))

# Raise to safe Z height
output_file.write('G94 (switch back to normal feed rate)\n')
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))

output_file.write('M5 M2\n')
# Close File
output_file.close()

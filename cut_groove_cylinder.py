#!/usr/bin/env python
import sys
import math
import numpy as np
import probe

# Create G-code to cut a groove in cylinder in a manner that accepts pre-probe
# results. 
# Inverse Time mode (G93) is used to specify feed rates


# Script assumes
#   1) The center of the cylinder is along the Y=0, Z=0 axis
#   2) Ignores X-axis, unless it's specified.

inputs = {
    'outer_diameter' : 6.0,
    'groove_depth' : 0.1,
    'x_loc': None,
    'angular_increment': 30,
    'direction': -1,
    'use_probe_file': True,
    'output_file': None
}
cutter_inputs = {
    'safe_clearance' : 0.1,
    'depth_per_pass' : 0.02,
    'feedrate_plunge' : 0.75,
    'feedrate_linear': 7.0, # IPM
}

if inputs['use_probe_file']:
    # Load module for interpolation
    from scipy import interpolate

outer_radius = inputs['outer_diameter']/2.0
z_ref = outer_radius

# Angular Data
angular_increment = inputs['angular_increment']
direction = inputs['direction']
A_values = range(angular_increment*direction, angular_increment*direction + 360*direction, angular_increment*direction)

if direction == 1:
    A_values = range(angular_increment, angular_increment + 360, angular_increment)
elif direction == -1:
    A_values = range(360-angular_increment, -angular_increment, -angular_increment)
else:
    print('Invalid value for direction\nExiting')
    sys.exit(1)

angular_increment_distance = math.pi/180.0*angular_increment*outer_radius
a_current = 0

# X-axis Data
if inputs['x_loc'] is not None:
    x_groove = inputs['x_loc']

# Z-axis Data
safe_z_height = outer_radius + cutter_inputs['safe_clearance']
groove_depth = inputs['groove_depth']
num_passes = int(math.ceil(groove_depth/cutter_inputs['depth_per_pass']))

z_final = outer_radius - groove_depth

z_current = z_ref - cutter_inputs['depth_per_pass']

# Time (min)
total_time = 0.0

print('\nGroove Data')
if inputs['x_loc'] is not None:
    print('Groove X: {:5.4f}'.format(inputs['x_loc']))
print('Final Groove Depth: {:5.4f}'.format(inputs['groove_depth']))
print('Depth per Pass: {:5.4f}'.format(cutter_inputs['depth_per_pass']))
print('Number of Passes: {:5.4f}'.format(num_passes))

# Read Probe Data if needed
if inputs['use_probe_file']:
    print('\nReading Probe Data')
    probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file('probe_file.txt')
    probe_X_values = np.unique(probe_X)
    probe_A_values = np.unique(probe_A)
    
    # Check Probe Data dimensions
    probe_dim = None
    if probe_X_values.size == 1:
        print('Probe Data is 2D (A and Z)')
        probe_dim = 1
    else:
        print('Probe Data is 3D (X, A and Z)')
        probe_dim = 2
        
    # Convert Z to delta Z map
    dZ = probe_Z - z_ref

    dZ_min = np.min(dZ)
    dZ_max = np.max(dZ)
    print('  dZ Min: {:5.4f}'.format(dZ_min))
    print('  dZ Max: {:5.4f}'.format(dZ_max))
    
    probe_f = probe.setup_interpolation(probe_X_values, probe_A_values, dZ, probe_dim)


# Open Output File
if inputs['output_file'] is None:
    # Autocreate filename
    output_filename = 'cut_groove_'
    output_filename += str(inputs['outer_diameter']) + '_od_'
    output_filename += str(inputs['groove_depth']) + '_depth'
    if inputs['use_probe_file']: output_filename += '_autolevel'
    output_filename += '.nc'
    
 
else:
    output_filename = inputs['output_file']
print('\nWriting Gcode to:', output_filename)
output_file = open(output_filename,'w')

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
if inputs['x_loc'] is not None:
    output_file.write('G0 X {:5.4f} Y 0.0000 A {:5.4f}\n'.format(x_groove, a_current))
else:
    print('Warning, omitting X value in start location')
    output_file.write('G0 Y 0.0000 A {:5.4f}\n'.format(a_current))

A_absolute = 0
while z_current >= z_final:
    output_file.write('({:2.2f} cut)\n'.format(z_current))
    # Plunge into material
    if inputs['use_probe_file']:
        if probe_dim == 1:
            # Interpolate dZ based on A only
            dz_current = probe_f(0)[0]
        elif probe_dim == 2:
            # Interpolate dZ based on X and A
            dz_current = probe_f(x_groove, a_current)[0,0]
        z_local = z_current + dz_current
    else:
        z_local = z_current
    output_file.write('G1 Z {:5.4f} F {:3.2f} (plunge cut)\n'.format(z_local,cutter_inputs['feedrate_plunge']))
    total_time += (safe_z_height - z_local)/cutter_inputs['feedrate_plunge']

    current_feedrate_linear = cutter_inputs['feedrate_linear']
    current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
    output_file.write('G93 (switch to inverse time)\n')
    for A in A_values:
        if inputs['use_probe_file']:
            if probe_dim == 1:
                # Interpolate dZ based on A only
                dz_current = probe_f(A)[0]
                print(dz_current)
            elif probe_dim == 2:
                # Interpolate dZ based on X and A
                dz_current = probe_f(x_groove, a_current)[0,0]
            z_local = z_current + dz_current
        A_absolute += angular_increment*direction
        output_file.write('G1 Z {:5.4f} A {:6.2f} F {:5.4f} ({:6.2f})\n'.format(z_local, A_absolute, current_feedrate_inverse_t, A))
        total_time += 1.0/current_feedrate_inverse_t
    output_file.write('G94 (switch back to normal feed rate)\n')
    z_current -= cutter_inputs['depth_per_pass']

# Raise to safe Z height
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))

print('Machining Time Required: {:4.0f} mins'.format(total_time))
print('                         {:3.2f} hrs'.format(total_time/60.0))

output_file.write('M5 M2\n')

# Close File
output_file.close()

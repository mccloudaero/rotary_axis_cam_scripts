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
    'outer_diameter' : 12.75,
    'drill_depth' : 0.4,
    'x_loc': -0.259,
    'angular_increment': 15,
    'direction': 1,
    'use_probe_file': True,
    'output_file': None
}
cutter_inputs = {
    'safe_clearance' : 0.1,
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

if direction == 1:
    A_values = range(angular_increment, 360, angular_increment)
elif direction == -1:
    A_values = range(360, -angular_increment, -angular_increment)
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
drill_depth = inputs['drill_depth']
num_passes = int(math.ceil(drill_depth/cutter_inputs['depth_per_pass']))

z_final = outer_radius - drill_depth

# Time (min)
total_time = 0.0

print('\nDrill Holes')
if inputs['x_loc'] is not None:
    print('X location: {:5.4f}'.format(inputs['x_loc']))
print('Drill Depth: {:5.4f}'.format(inputs['drill_depth']))
print('Angular Increment: {:3d} deg'.format(inputs['angular_increment']))

# Read Probe Data if needed
if inputs['use_probe_file']:
    print('\nReading Probe Data')
    probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file('probe_results.txt')
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
    output_filename = 'drill_holes_'
    output_filename += str(inputs['outer_diameter']) + '_od_'
    output_filename += str(inputs['drill_depth']) + '_depth'
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
done = False
hole_num = 1
while done is False:
    # First Hole at A = 0
    # Plunge into material
    if inputs['use_probe_file']:
        if probe_dim == 1:
            # Interpolate dZ based on A only
            dz_current = probe_f(0)[0]
        elif probe_dim == 2:
            # Interpolate dZ based on X and A
            dz_current = probe_f(x_groove, a_current)[0,0]
        z_local = z_final + dz_current
    else:
        z_local = z_final
    output_file.write('G1 Z {:5.4f} F {:3.2f} (plunge, hole {:3d})\n'.format(z_local, cutter_inputs['feedrate_plunge'], hole_num))
    hole_num += 1
    total_time += (safe_z_height - z_local)/cutter_inputs['feedrate_plunge']
    # Raise to safe Z height
    output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))

    for A in A_values:
        if inputs['use_probe_file']:
            if probe_dim == 1:
                # Interpolate dZ based on A only
                dz_current = probe_f(A)[0]
            elif probe_dim == 2:
                # Interpolate dZ based on X and A
                dz_current = probe_f(x_groove, a_current)[0,0]
            z_local = z_final + dz_current
        A_absolute += angular_increment*direction
        output_file.write('G0 A {:6.2f} ({:6.2f})\n'.format(A_absolute, A))
        output_file.write('G1 Z {:5.4f} F {:3.2f} (plunge, hole {:3d})\n'.format(z_local, cutter_inputs['feedrate_plunge'], hole_num))
        hole_num += 1
        total_time += (safe_z_height - z_local)/cutter_inputs['feedrate_plunge']
        # Raise to safe Z height
        output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
    done = True

print('Machining Time Required: {:4.0f} mins'.format(total_time))
print('                         {:3.2f} hrs'.format(total_time/60.0))

output_file.write('M5 M2\n')
output_file.write('(Machine Time Required: {:4.0f} mins)'.format(total_time))

# Close File
output_file.close()

#!/usr/bin/env python
import sys
import os
import math
import numpy as np
import probe

import rotary_axis_cam

# Create G-code to cut a groove in cylinder in a manner that accepts pre-probe
# results. 
# Inverse Time mode (G93) is used to specify feed rates


# Script assumes
#   1) The center of the cylinder is along the Y=0, Z=0 axis
#   2) Ignores X-axis, unless it's specified.

script_inputs_file = './drill_holes_cylinder.inputs'
inputs = { 
    'outer_diameter' : 12.0,
    'hole_diameter' : 0.406,
    'drill_depth' : 0.75,
    'x_loc': -2.938,
    'angular_increment': 30,
    'direction': 1,
    'use_probe_file': False,
    'output_file': None
}
cutter_inputs = {
    'mill_diameter' : 0.25,
    'safe_clearance' : 0.1,
    'feedrate_plunge' : 0.5,
    'feedrate_linear': 1.0, # IPM
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
    outputfile.write('inputs = {\n')
    rotary_axis_cam.write_dict(outputfile, inputs)
    outputfile.write('cutter_inputs = {\n')
    rotary_axis_cam.write_dict(outputfile, cutter_inputs)
    outputfile.close()
    print('Update drill_holes_cylinder.inputs and re-run')
    sys.exit()

# Check mill diameter
if cutter_inputs['mill_diameter'] > inputs['hole_diameter']:
    print('Error! Mill diameter is larger than hole diameter')
    sys.exit(1)

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
    x_holes = inputs['x_loc']

# Z-axis Data
safe_z_height = outer_radius + cutter_inputs['safe_clearance']
drill_depth = inputs['drill_depth']

z_final = outer_radius - drill_depth

# Time (min)
total_time = 0.0

print('\nDrill Holes')
if inputs['x_loc'] is not None:
    print('X location: {:5.4f}'.format(inputs['x_loc']))
print('Drill Depth: {:5.4f}'.format(inputs['drill_depth']))
print('Angular Increment: {:3d} deg'.format(inputs['angular_increment']))
widen_holes = False
if cutter_inputs['mill_diameter'] < inputs['hole_diameter']:
    widen_holes = True
    print('Holes larger than Mill Diameter')
    hole_delta_R = (inputs['hole_diameter'] - cutter_inputs['mill_diameter'])/2.0
    print(hole_delta_R)

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
    if inputs['x_loc'] is not None:
        output_filename += str(inputs['x_loc']) + '_x_'
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
output_file.write('(Script Inputs)\n')
output_file.write('(X: {:6.4f})\n'.format(inputs['x_loc']))
output_file.write('(Hole Size: {:6.4f})\n'.format(inputs['hole_diameter']))
output_file.write('(Angular Increment: {:6.4f})\n'.format(inputs['angular_increment']))
output_file.write('(Mill Diameter: {:5.4f})\n'.format(cutter_inputs['mill_diameter']))
output_file.write('(Feedrate Plunge: {:3.2f})\n'.format(cutter_inputs['feedrate_plunge']))
output_file.write('(Feedrate Linear: {:3.2f})\n'.format(cutter_inputs['feedrate_linear']))
output_file.write('\n')

# Position at Start
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
if inputs['x_loc'] is not None:
    output_file.write('G0 X {:5.4f} Y 0.0000 A {:5.4f}\n'.format(x_holes, a_current))
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
            dz_current = probe_f(x_holes, a_current)[0,0]
        z_local = z_final + dz_current
    else:
        z_local = z_final
    output_file.write('G1 Z {:5.4f} F {:3.2f} (plunge, hole {:3d})\n'.format(z_local, cutter_inputs['feedrate_plunge'], hole_num))
    hole_num += 1
    total_time += (safe_z_height - z_local)/cutter_inputs['feedrate_plunge']
    if widen_holes is True:
        # Rough
        # Move to arc starting point in Y axis at Half the Linear Feed Rate
        output_file.write('G1 Y {:.4f} F {:.2f}\n'.format(hole_delta_R-0.01, 0.5*cutter_inputs['feedrate_linear']))
        # Circular arc
        output_file.write('G2 X {:.4f} Y {:.4f} I {:.4f} J {:.4f} F {:.2f}\n'.format(x_holes, hole_delta_R-0.01, x_holes, 0.0, cutter_inputs['feedrate_linear']))
        # Final
        # Move to arc starting point in Y axis at Half the Linear Feed Rate
        output_file.write('G1 Y {:.4f} F {:.2f}\n'.format(hole_delta_R, 0.5*cutter_inputs['feedrate_linear']))
        # Circular arc
        output_file.write('G2 X {:.4f} Y {:.4f} I {:.4f} J {:.4f} F {:.2f}\n'.format(x_holes, hole_delta_R, x_holes, 0.0, cutter_inputs['feedrate_linear']))
        # Return to center
        output_file.write('G0 Y 0.0000\n')
    # Raise to safe Z height
    output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))

    for A in A_values:
        if inputs['use_probe_file']:
            if probe_dim == 1:
                # Interpolate dZ based on A only
                dz_current = probe_f(A)[0]
            elif probe_dim == 2:
                # Interpolate dZ based on X and A
                dz_current = probe_f(x_holes, a_current)[0,0]
            z_local = z_final + dz_current
        A_absolute += angular_increment*direction
        output_file.write('G0 A {:6.2f} ({:6.2f})\n'.format(A_absolute, A))
        output_file.write('G1 Z {:5.4f} F {:3.2f} (plunge, hole {:3d})\n'.format(z_local, cutter_inputs['feedrate_plunge'], hole_num))
        hole_num += 1
        total_time += (safe_z_height - z_local)/cutter_inputs['feedrate_plunge']
        if widen_holes is True:
            # Rough
            # Move to arc starting point in Y axis at Half the Linear Feed Rate
            output_file.write('G1 Y {:.4f} F {:.2f}\n'.format(hole_delta_R-0.01, 0.5*cutter_inputs['feedrate_linear']))
            # Circular arc
            output_file.write('G2 X {:.4f} Y {:.4f} I {:.4f} J {:.4f} F {:.2f}\n'.format(x_holes, hole_delta_R-0.01, x_holes, 0.0, cutter_inputs['feedrate_linear']))
            # Final
            # Move to arc starting point in Y axis at Half the Linear Feed Rate
            output_file.write('G1 Y {:.4f} F {:.2f}\n'.format(hole_delta_R, 0.5*cutter_inputs['feedrate_linear']))
            # Circular arc
            output_file.write('G2 X {:.4f} Y {:.4f} I {:.4f} J {:.4f} F {:.2f}\n'.format(x_holes, hole_delta_R, x_holes, 0.0, cutter_inputs['feedrate_linear']))
            # Return to center
            output_file.write('G0 Y 0.0000\n')
        # Raise to safe Z height
        output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
    done = True

print('Machining Time Required: {:4.0f} mins'.format(total_time))
print('                         {:3.2f} hrs'.format(total_time/60.0))

output_file.write('M5 M2\n')
output_file.write('(Machine Time Required: {:4.0f} mins)'.format(total_time))

# Close File
output_file.close()

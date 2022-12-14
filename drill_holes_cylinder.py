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
    'angular_offset': 0,
    'direction': 1,
    'peck_drill': False,
    'use_Z_probe_file': False,
    'use_X_probe_file': False,
    'output_file': None
}
cutter_inputs = {
    'mill_diameter' : 0.25,
    'safe_clearance' : 0.1,
    'feedrate_plunge' : 0.5, # IPM
    'feedrate_linear': 1.0, # IPM
    'peck_amount': 0.0,
}

if os.path.isfile(script_inputs_file):
    print('Input file exists, loading inputs file')
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

if inputs['use_Z_probe_file']:
    # Load module for interpolation
    from scipy import interpolate

outer_radius = inputs['outer_diameter']/2.0
z_ref = outer_radius

# Angular Data
angular_increment = inputs['angular_increment']
direction = inputs['direction']

if direction == 1:
    # Go from Start from Zero and go towards 360
    A_values = np.arange(0, 360, angular_increment)
elif direction == -1:
    # Go from Start from 360 and go towards 0
    A_values = np.arange(360, -angular_increment, -angular_increment)
else:
    print('Invalid value for direction\nExiting')
    sys.exit(1)

# Apply offset
A_values += inputs['angular_offset']

angular_increment_distance = math.pi/180.0*angular_increment*outer_radius
a_current = 0

# X-axis Data
if inputs['x_loc'] is not None:
    x_holes = inputs['x_loc']

# Z-axis Data
safe_z_height = outer_radius + cutter_inputs['safe_clearance']
drill_depth = inputs['drill_depth']
depth_diams = inputs['drill_depth']/cutter_inputs['mill_diameter']

z_final = outer_radius - drill_depth

# Time (min)
total_time = 0.0

print('\nDrill Holes')
if inputs['x_loc'] is not None:
    print('X location: {:5.4f}'.format(inputs['x_loc']))
print('Drill Depth: {:5.4f}, Diameters: {:3.2f}'.format(inputs['drill_depth'],depth_diams)) 
print('Angular Increment: {:3d} deg'.format(inputs['angular_increment']))
print('Angular Offset: {:3d} deg'.format(inputs['angular_offset']))
print('Angles:', A_values)
widen_holes = False
if cutter_inputs['mill_diameter'] < inputs['hole_diameter']:
    widen_holes = True
    print('Holes larger than Mill Diameter')
    hole_delta_R = (inputs['hole_diameter'] - cutter_inputs['mill_diameter'])/2.0
    print(hole_delta_R)

# Read Probe Data if needed
if inputs['use_Z_probe_file']:
    print('\nReading Z Probe Data')
    probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file('probe_results.txt')
    probe_X_values = np.unique(probe_X)
    probe_A_values = np.unique(probe_A)
    
    # Check Probe Data dimensions
    Z_probe_dim = None
    if probe_X_values.size == 1:
        print('Probe Data is 2D (A and Z)')
        Z_probe_dim = 1
    else:
        print('Probe Data is 3D (X, A and Z)')
        Z_probe_dim = 2
        
    # Convert Z to delta Z map
    dZ = probe_Z - z_ref

    dZ_min = np.min(dZ)
    dZ_max = np.max(dZ)
    print('  dZ Min: {:5.4f}'.format(dZ_min))
    print('  dZ Max: {:5.4f}'.format(dZ_max))
    
    Z_probe_f = probe.setup_interpolation(probe_X_values, probe_A_values, dZ, Z_probe_dim)

if inputs['use_X_probe_file']:
    print('\nReading X Probe Data')
    probe_num_X, probe_num_A, probe_X, probe_Z, probe_A = probe.read_cylinder_probe_file('probe_results_edge.txt')
    probe_X_values = np.unique(probe_X)
    probe_Z_values = np.unique(probe_Z)
    probe_A_values = np.unique(probe_A)
    
    # Check Probe Data dimensions
    X_probe_dim = None
    if probe_Z_values.size == 1:
        print('Probe Data is 2D (A and X)')
        X_probe_dim = 1
    else:
        print('Bad Probe Dimensions.\nExiting!')
        sys.exit(1)

    dX_min = np.min(probe_X_values)
    dX_max = np.max(probe_X_values)
    print('  dX Min: {:5.4f}'.format(dX_min))
    print('  dX Max: {:5.4f}'.format(dX_max))
    
    X_probe_f = probe.setup_interpolation(probe_Z_values, probe_A_values, probe_X, X_probe_dim)

# Open Output File
if inputs['output_file'] is None:
    # Autocreate filename
    output_filename = 'drill_holes_'
    output_filename += str(inputs['outer_diameter']) + '_od_'
    if inputs['x_loc'] is not None:
        output_filename += str(inputs['x_loc']) + '_x_'
    output_filename += str(inputs['drill_depth']) + '_depth'
    if inputs['use_Z_probe_file']: output_filename += '_autolevel'
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
output_file.write('(Angular Offset: {:6.4f})\n'.format(inputs['angular_offset']))
output_file.write('(Angles: ' + str(A_values) + ' )\n')
output_file.write('(Mill Diameter: {:5.4f})\n'.format(cutter_inputs['mill_diameter']))
output_file.write('(Feedrate Plunge: {:3.2f})\n'.format(cutter_inputs['feedrate_plunge']))
output_file.write('(Feedrate Linear: {:3.2f})\n'.format(cutter_inputs['feedrate_linear']))
output_file.write('\n')

# Position at Start
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
if inputs['x_loc'] is not None:
    output_file.write('G0 X {:5.4f} Y 0.0000\n'.format(x_holes))
else:
    print('Warning, omitting X value in start location')
    output_file.write('G0 Y 0.0000 \n')

hole_num = 1
for A in A_values:
    # Go to next A
    output_file.write('G0 A {:6.2f}\n'.format(A))
    # Determine probe offsets
    if inputs['use_Z_probe_file']:
        if Z_probe_dim == 1:
            # Interpolate dZ based on A only
            dz_current = Z_probe_f(A)[0]
        elif Z_probe_dim == 2:
            # Interpolate dZ based on X and A
            dz_current = Z_probe_f(x_holes, A)[0,0]
        z_local = z_final + dz_current
        z_local_ref = z_ref + dz_current
    else:
        z_local = z_final
        z_local_ref = z_ref
    if inputs['use_X_probe_file']:
        # Interpolate dX based on A only
        dx_current = X_probe_f(A)[0]
        x_local = x_holes + dx_current 
        output_file.write('G0 X {:5.4f} (dx: {:5.4f})\n'.format(x_local, dx_current))
    # Plunge into material
    if inputs['peck_drill'] is True:
        # Peck drill
        z_retract = z_local_ref + 0.05
        output_file.write('G83 Z {:5.4f} Q {:5.4f} R {:5.4f} F {:3.2f} (peck drill, hole {:3d})\n'.format(z_local, cutter_inputs['peck_amount'], z_retract, cutter_inputs['feedrate_plunge'], hole_num))
    else:
        # Normal plunge
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

print('Machining Time Required: {:4.0f} mins'.format(total_time))
print('                         {:3.2f} hrs'.format(total_time/60.0))

output_file.write('M5 M2\n')
output_file.write('(Machine Time Required: {:4.0f} mins)'.format(total_time))

# Close File
output_file.close()

if depth_diams > 5 and inputs['peck_drill'] is False:
    print('\n***WARNING***')
    print('Holes are {:3.2f} diameters deep. Considering using peck drilling instead'.format(depth_diams))

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
    'outer_diameter' : 12.0,
    'recess_depth' : 0.06,
    'isogrid' : False,
    'x_start' : -3.75,
    'x_end' : 0.04,
    'angular_increment': 15,
    'direction': -1,
    'use_probe_file': False,
    'output_file': None
}
cutter_inputs = {
    'mill_diameter' : 0.5,
    'overlap' : 0.4,
    'material_to_leave' : 0.0,
    'safe_clearance' : 0.1,
    'depth_per_pass' : 0.10,
    'feedrate_plunge' : 0.5,  # IPM
    'feedrate_linear': 12.0,   # IPM
}
isogrid_inputs = {
    'flange_width' : 0.3125,
    'pattern_size' : 1.571,
    'num_rows': 4,
    'rib_width': 0.05,
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
    A_values = range(angular_increment, angular_increment + 360, angular_increment)
elif direction == -1:
    A_values = range(360-angular_increment, -angular_increment, -angular_increment)
else:
    print('Invalid value for direction\nExiting')
    sys.exit(1)
A_values_fc = range(360-angular_increment, -angular_increment, -angular_increment)
angular_increment_distance = math.pi/180.0*angular_increment*outer_radius
A_start = 360

# X-axis Data
dx_stepover = cutter_inputs['mill_diameter']*cutter_inputs['overlap']
if inputs['isogrid'] is True:
    print('Using isogrid parameters to size recess')
    triangle_height = (3.0**0.5)/2.0 * isogrid_inputs['pattern_size'] # isogrid triangle height
    x_start = isogrid_inputs['flange_width'] + cutter_inputs['material_to_leave'] + cutter_inputs['mill_diameter']/2.0
    recess_length = triangle_height*isogrid_inputs['num_rows'] - isogrid_inputs['rib_width'] - 2*cutter_inputs['material_to_leave']
    dx_recess = recess_length - cutter_inputs['mill_diameter']
    x_end = x_start + dx_recess
    print('Triangle Height: {:4.3f}'.format(triangle_height))
    print('Number of Rows: {:2d}'.format(isogrid_inputs['num_rows']))
else:
    print('Using specified x_start and x_end values for recess')
    x_start = inputs['x_start'] + cutter_inputs['material_to_leave'] + cutter_inputs['mill_diameter']/2.0
    x_end = inputs['x_end'] - cutter_inputs['material_to_leave'] - cutter_inputs['mill_diameter']/2.0

# Z-axis Data
safe_z_height = outer_radius + cutter_inputs['safe_clearance']
dz_recess = inputs['recess_depth'] - cutter_inputs['material_to_leave']
# NOTE: Dont want depth per pass to exceed dz_recess
if cutter_inputs['depth_per_pass'] > dz_recess:
    cutter_inputs['depth_per_pass'] = dz_recess
z_final = z_ref - dz_recess
# Check depth per pass
num_passes = int(math.ceil(dz_recess/cutter_inputs['depth_per_pass']))
z_current = z_ref - cutter_inputs['depth_per_pass']
print(z_current)
# Time (min)
total_time = 0.0

print('\nDimensions')
print('Outer Radius: {:5.4f}'.format(outer_radius))
print('Recess X start: {:5.4f}'.format(x_start))
print('Recess X end: {:5.4f}'.format(x_end))
print('dZ recess nominal: {:5.4f}'.format(dz_recess))
print('Z recess nominal: {:5.4f}'.format(z_final))
print('Number of Passes: {:3d}'.format(num_passes))

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
    output_filename = 'cut_recess_'
    output_filename += str(inputs['outer_diameter']) + '_od_'
    output_filename += str(cutter_inputs['mill_diameter']) + '_bit_'
    output_filename += 'leave_' + str(cutter_inputs['material_to_leave'])
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
output_file.write('(Recess Start: {:6.4f})\n'.format(inputs['x_start']))
output_file.write('(Recess End: {:6.4f})\n'.format(inputs['x_end']))
output_file.write('(Recess Depth: {:6.4f})\n'.format(inputs['recess_depth']))
output_file.write('(Feedrate Plunge: {:3.2f})\n'.format(cutter_inputs['feedrate_plunge']))
output_file.write('(Feedrate Linear: {:3.2f})\n'.format(cutter_inputs['feedrate_linear']))
output_file.write('(Depth per Pass: {:5.4f})\n'.format(cutter_inputs['depth_per_pass']))
output_file.write('(Material to Leave: {:5.4f})\n'.format(cutter_inputs['material_to_leave']))
output_file.write('\n')

# Position at Start
# Start at A=360 for first cut
output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
output_file.write('G0 Y 0.0000 A {:5.4f}\n'.format(A_start))

A_absolute = A_start
done = False
while done is False:
    print('    Writing G-code for {:5.4f} depth'.format(z_current))
    output_file.write('({:5.4f} cut)\n'.format(z_current))
    output_file.write('G0 X {:5.4f}\n'.format(x_start))
    # Plunge into material
    if inputs['use_probe_file']:
        if probe_dim == 1:
            # Interpolate dZ based on A only
            dz_current = probe_f(0)[0]
        elif probe_dim == 2:
            # Interpolate dZ based on X and A
            dz_current = probe_f(x_start, 0)[0,0]
        z_local = z_current + dz_current
    else:
        z_local = z_current
    output_file.write('G1 Z {:5.4f} F {:3.2f} (plunge cut)\n'.format(z_local, cutter_inputs['feedrate_plunge']))
    total_time += (safe_z_height - z_local)/cutter_inputs['feedrate_plunge']
    
    # First Cut
    # Need to make first cut moving in the Negative A axis to leave a good edge
    # on the flange. Start at A=360 to keep interpolation values positive
    # Cut at fraction of full speed since it's cutting the full width of the bit
    current_feedrate_linear = cutter_inputs['feedrate_linear']*0.75
    current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
    output_file.write('(first cut)\n')
    output_file.write('G93 (switch to inverse time)\n')
    x_current = x_start
    for A in A_values_fc:
        if inputs['use_probe_file']:
            if probe_dim == 1:
                # Interpolate dZ based on A only
                dz_current = probe_f(A)[0]
            elif probe_dim == 2:
                # Interpolate dZ based on X and A
                dz_current = probe_f(x_current, A)[0,0]
            z_local = z_current + dz_current
        else:
            z_local = z_current
        A_absolute -= angular_increment
        output_file.write('G1 Z {:5.4f} A {:6.2f} F {:5.4f} ({:6.2f})\n'.format(z_local, A_absolute, current_feedrate_inverse_t, A))
        total_time += 1.0/current_feedrate_inverse_t
    x_current += dx_stepover

    # Keep Cutting
    current_feedrate_linear = cutter_inputs['feedrate_linear']
    current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
    while x_current < x_end:
        if inputs['use_probe_file']:
            if probe_dim == 1:
                # Interpolate dZ based on A only
                dz_current = probe_f(0)[0]
            elif probe_dim == 2:
                # Interpolate dZ based on X and A
                dz_current = probe_f(x_current, 0)[0,0]
            z_local = z_current + dz_current
        else:
            z_local = z_current
        
        # Move in X direction
        current_feedrate_linear = cutter_inputs['feedrate_linear']*0.75
        current_feedrate_inverse_t = current_feedrate_linear/dx_stepover
        
        output_file.write('G1 X {:5.4f} Z {:5.4f} F {:5.4f}\n'.format(x_current, z_local, current_feedrate_inverse_t))
        total_time += 1.0/current_feedrate_inverse_t
        
        current_feedrate_linear = cutter_inputs['feedrate_linear']
        current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
        for A in A_values:
            if inputs['use_probe_file']:
                if probe_dim == 1:
                    # Interpolate dZ based on A only
                    dz_current = probe_f(A)[0]
                elif probe_dim == 2:
                    # Interpolate dZ based on X and A
                    dz_current = probe_f(x_current, A)[0,0]
                z_local = z_current + dz_current
            else:
                z_local = z_current
            A_absolute += angular_increment*direction
            output_file.write('G1 Z {:5.4f} A {:6.2f} F {:5.4f} ({:6.2f})\n'.format(z_local, A_absolute, current_feedrate_inverse_t, A))
            total_time += 1.0/current_feedrate_inverse_t
        
        # Increment X
        x_current += dx_stepover

    # Final Pass
    output_file.write('(final cut)\n')
    x_current = x_end
    # Interpolate Z based on X and A (0-360)
    if inputs['use_probe_file']:
        if probe_dim == 1:
            # Interpolate dZ based on A only
            dz_current = probe_f(A)[0]
        elif probe_dim == 2:
            # Interpolate dZ based on X and A
            dz_current = probe_f(x_current, A)[0,0]
        z_local = z_current + dz_current
    else:
        z_local = z_current
        
    # Move in X direction
    current_feedrate_linear = cutter_inputs['feedrate_linear']*0.75
    current_feedrate_inverse_t = current_feedrate_linear/dx_stepover
    output_file.write('G1 X {:5.4f} Z {:5.4f} F {:5.4f}\n'.format(x_current, z_local, current_feedrate_inverse_t))
    total_time += 1.0/current_feedrate_inverse_t

    current_feedrate_linear = cutter_inputs['feedrate_linear']
    current_feedrate_inverse_t = current_feedrate_linear/angular_increment_distance
    for A in A_values:
        if inputs['use_probe_file']:
            if probe_dim == 1:
                # Interpolate dZ based on A only
                dz_current = probe_f(A)[0]
            elif probe_dim == 2:
                # Interpolate dZ based on X and A
                dz_current = probe_f(x_current, A)[0,0]
            z_local = z_current + dz_current
        else:
            z_local = z_current
        A_absolute += angular_increment*direction
        output_file.write('G1 Z {:5.4f} A {:6.2f} F {:5.4f} ({:6.2f})\n'.format(z_local, A_absolute, current_feedrate_inverse_t, A))
        total_time += 1.0/current_feedrate_inverse_t
        
    output_file.write('G94 (switch back to normal feed rate)\n')
    # Raise to safe Z height
    output_file.write('G0 Z {:5.4f} (Safe Z height)\n'.format(safe_z_height))
    if z_current == z_final:
        done = True
    else:
        z_current -= cutter_inputs['depth_per_pass']
        z_current = max(z_current,z_final)


print('Machining Time Required: {:4.0f} mins'.format(total_time))
print('                         {:3.2f} hrs'.format(total_time/60.0))

output_file.write('M5 M2\n')
output_file.write('(Machine Time Required: {:4.0f} mins)'.format(total_time))

# Close File
output_file.close()

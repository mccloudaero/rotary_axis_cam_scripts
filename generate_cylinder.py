#!/usr/bin/env python
import sys
import math

# Generates G-code for machinging a cylindrical isogrid on a 4-axis machine
# Cylinder rotates around the X-axis
# Machining happens near the Y=0 plane
# Cells are roughed from the inside out

# All units in inches
cylinder_dimensions = {
    'outer_diameter' : 6.0,
    'wall_t' : 0.25,
    'overall_length' : 40,
}
isogrid_values = {
    'num_radial_cells' : 12, 
    'end_flange' : 5/16,
    'start_flange' : 1.25,
    'skin_t' : 0.05,
    'rib_t' : 0.05,
}
# inches per minute
rough_pass_values = {
    'feed' : 10,
    'plunge' : 2,
    'material_to_leave' : 0.02,
    'max_depth_per_pass' : 0.125,
    'max_stepover' : 0.125*0.4,
}
tool_values = {
    'diameter' : 0.125,
}

# Compute isogrid properties
print('\nIsogrid Dimensions')

# Find triangle dimensions
# Pattern size is the length side of the triangle cell
pattern_size = cylinder_dimensions['outer_diameter']*math.pi/isogrid_values['num_radial_cells']
# Pattern size is the height side of the triangle cell
pattern_height = pattern_size*(3**0.5)/2
# Apothem is the distance from the side to the center
apothem = pattern_height/3
print('Num Radial Cells: {:3d}'.format(isogrid_values['num_radial_cells']))
print('Pattern Size: {:5.3f}'.format(pattern_size))
print('Pattern Height: {:5.3f}'.format(pattern_height))

# Available length is the cylinder length availble for machining between the flanges
available_length = cylinder_dimensions['overall_length']-isogrid_values['start_flange']-isogrid_values['end_flange']
num_rows = math.floor(available_length/pattern_height)
# Excess length is the material length that remains by requiring an integer number of divisions
excess_length = available_length - num_rows*pattern_height
print('Num Rows: {:3d}'.format(num_rows))
print('Excess_Length: {:5.3f}'.format(excess_length))

# Open the gcode file and write header
output = open('test.nc','w')
output.write('G0 G90 G54 G17 G40 G49 G80\n') # Safe start line

# Find the starting point for the first row
first_row_center_x1 = isogrid_values['start_flange'] + excess_length + apothem 
first_row_center_x2 = isogrid_values['start_flange'] + excess_length + pattern_height - apothem 

# Process Rows
for i in range(1):
    cell_x1 = first_row_center_x1
    cell_x2 = first_row_center_x2
    # Process Cells in Row
    for j in range(2):
        cell_y = j*pattern_height
        # Cut First Cell
        output.write('G0 X{:5.3f} Y{:5.3f}\n'.format(cell_x1,cell_y))    # Rapid to XY position
        output.write('G52 X{:5.3f} Y{:5.3f}\n'.format(cell_x1,cell_y))   # Switch to local coordinate system 
        output.write('M98 P1001\n')                                      # Call subprogram number 1000
        cell_y = j*pattern_height + 0.5*pattern_height
        # Cut Next Cell, Swithcing the direction
        output.write('G0 X{:5.3f} Y{:5.3f}\n'.format(cell_x2,cell_y))    # Rapid to XY position
        output.write('G52 X{:5.3f} Y{:5.3f}\n'.format(cell_x2,cell_y))   # Switch to local coordinate system 
        output.write('M98 P1002\n')                                      # Call subprogram number 1000

# End Main Program
output.write('M30\n') # Program end and rewind

# ROUGH SUBPROGRAM MACROS

# Compute the number of roughing passes from the center to the sides
print('\nRoughing')
# Depth calcs
depth_to_rough = cylinder_dimensions['wall_t']-isogrid_values['skin_t']-rough_pass_values['material_to_leave']
depth_passes = math.ceil(depth_to_rough/rough_pass_values['max_depth_per_pass'])
depth_per_pass = depth_to_rough/depth_passes
print('Depth Values')
print('Depth to rough: {:5.3f}'.format(depth_to_rough))
print('Depth Passes: {:3d}'.format(depth_passes))
print('Depth per pass: {:5.3f}'.format(depth_per_pass))

rough_apothem = apothem-isogrid_values['rib_t']/2-rough_pass_values['material_to_leave']
rough_passes = math.ceil(rough_apothem/rough_pass_values['max_stepover']) 
rough_stepover = rough_apothem/rough_passes
print('\nHorizontal Values')
print('Distance to rough: {:5.3f}'.format(rough_apothem))
print('Passes: {:5.3f}'.format(rough_passes))
print('Stepover: {:5.3f}'.format(rough_stepover))

# Start strings for subprograms
subprogram_1_string = '\n'
subprogram_2_string = '\n'

subprogram_1_string += 'O1001 (ROUGH PASS CELL 1 BEGIN)\n' # Subprogram number
subprogram_2_string += 'O1002 (ROUGH PASS CELL 2 BEGIN)\n' # Subprogram number
for i in range(1,depth_passes+1):
    print(i)
    subprogram_1_string += 'G1 Z{:5.3f} F{:5.3f}\n'.format(-i*depth_per_pass,2)    # Plunge into material 
    subprogram_2_string += 'G1 Z{:5.3f} F{:5.3f}\n'.format(-i*depth_per_pass,2)    # Plunge into material 

    for j in range(1,rough_passes):
        subprogram_1_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(-j*rough_stepover,0.0)  # First triangle point
        subprogram_1_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(-j*rough_stepover,j*rough_stepover*(3**0.5))  # First triangle point
        subprogram_1_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(j*rough_stepover*2,0.0)  # First triangle point
        subprogram_1_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(-j*rough_stepover,-j*rough_stepover*(3**0.5))  # First triangle point
        subprogram_1_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(-j*rough_stepover,0.0)  # First triangle point

        subprogram_2_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(j*rough_stepover,0.0)  # First triangle point
        subprogram_2_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(j*rough_stepover,j*rough_stepover*(3**0.5))  # First triangle point
        subprogram_2_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(-j*rough_stepover*2,0.0)  # First triangle point
        subprogram_2_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(j*rough_stepover,-j*rough_stepover*(3**0.5))  # First triangle point
        subprogram_2_string += 'G1 X{:5.3f} Y{:5.3f} F2.0\n'.format(j*rough_stepover,0.0)  # First triangle point
    
subprogram_1_string += 'M99\n' # Return to main program
subprogram_2_string += 'M99\n' # Return to main program
output.write(subprogram_1_string)
output.write(subprogram_2_string)

# Close file
output.close()

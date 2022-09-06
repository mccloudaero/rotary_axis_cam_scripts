# Rotary Axis CAM scripts
An open source collection of Python scripts for creating and modifing rotary
axis G-code, cylindrical probing and performing cylindrical auto-leveling.

## Package Contents  

### Scripts
* **convert_to_inverse_time.py** - Take code using G94 feedrate and convert it to inverse time mode (G93)
* **pre_probe_cylinder.py**      - Script to create a G-code file for probing a cylinder before machining
* **pre_probe_cylinder_plot.py** - Script for plotting pre-probe results
* **cut_recess_cylinder.py**     - Script to cut a recess into a cylindrical part. Can either use a constant depth or interpolates from a pre-probe file

### Modules
* **probe.py** - Module containing common probe functions

## Detailed Descriptions
### General Notes
* Scripts assume the rotary axis (A) rotates around the X-axis
* All of the scripts take inputs via a python dictionary at the beginning of the
script

### Convert to Inverse Time (convert_to_inverse_time.py)
An easy way to generate rotary-axis G-code is to take a "flat" G-code file and
wrap it in a cylindrical manner. G-code-Ripper by Scorchworks is a great tool
for doing this. One issue with wrapping code is that the default feedrate mode
(G94) is used and it doesn't differentiate between linear (length/min) and
rotational (deg/min)units and the resulting tool path can be very slow(see
video for a great explanation).

A better option is to use Inverse Time Mode (G93). In this mode, the total time
of a move is computed and the inverse of the time is then specified as the
feedrate.

The script **convert_to_inverse_time.py** takes an existing G-code file (likely
built using a wrap tool), assumes that the input was built assuming G94 and
modifies it to use the inverse time mode (G93).

### Pre Probe Cylinder (pre_probe_cylinder.py)
This script creates a G-code file for probing a cylinder, which is the first
step for cylindrical auto-leveling. The user specifies the number of linear
and radial divisions and the script generates the G-code for performing the
probe operation.

The code outputs the results to a text file, with the default name
**probe_results.txt**. The resulting data file containing can be plotted
using the **pre_probe_cylinder_plot.py** script.

### Pre Probe Cylinder Plot (pre_probe_cylinder_plot.py)
Plots the probe results using matplotlib. The script detects if the data is 
2D or 3D and plots the data accordingly.

### Cut Recess Cylinder (cut_recess_cylinder.py)
Used to create a recess of a constant depth. Assumes



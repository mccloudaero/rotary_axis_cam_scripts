# Rotary Axis CAM Scripts
An open source collection of Python scripts for creating and modifing rotary
axis G-code, cylindrical probing and performing cylindrical auto-leveling.

## Package Contents  

### Scripts
 * **Probing
* **pre_probe_cylinder.py**      - Script to create a G-code file for probing a cylinder before machining
* **pre_probe_cylinder_plot.py** - Script for plotting pre-probe results
* **probe.py** - Python module containing common probe functions

 * **Create G-Code
* **cut_groove_cylinder.py**      - Script to cut a groove (one tool width) into a cylindrical part. Can either be a constant depth or interpolates from a pre-probe file
* **cut_recess_cylinder.py**      - Script to cut a recess (greater than one tool width) into a cylindrical part. Can either use a constant depth or interpolates from a pre-probe file
* **drill_holes_cylinder.py**     - Script to drill holes circumfrentially around a cylinder at a specific X location

 * **Modify G-Code
* **apply_cylinder_autolevel.py** - Reads in a G-code file, and writes out a new G-code file with cylinderical autoleveling applied
* **convert_to_inverse_time.py**  - Take G-code using G94 feedrate and convert it to inverse time mode (G93)


## Detailed Descriptions
### General Notes
* Scripts assume the rotary axis (A) rotates around the X-axis ( Y=0, Z=0 )
* All of the scripts take inputs via a python dictionary at the beginning of the
script
* Script outputs have feed rates specified in Inverse Time mode (G93)
* Groove is assumed to be one tool width wide
* Recess is assumed to be greater than one tool width wide

### Probing
 * **Pre Probe Cylinder (pre_probe_cylinder.py)**
This script creates a G-code file for probing a cylinder, which is the first
step for cylindrical auto-leveling. The user specifies the number of linear
and radial divisions and the script generates the G-code for performing the
probe operation.

The code outputs the results to a text file, with the default name
**probe_results.txt**. The resulting data file containing can be plotted
using the **pre_probe_cylinder_plot.py** script.

This script relies on the M40 and M41 macros for the probe operations. Macros
for Mach4 are included in the /mach4 folder.

 * **Pre Probe Cylinder Plot (pre_probe_cylinder_plot.py)**
Plots the probe results using matplotlib. The script detects if the data is 
2D or 3D and plots the data accordingly.


specified in the script, or omitted and the script will used the current
X location when the script is run. Can interpolate from a pre-probe
file for cylindrical autoleveling

### Create
 * **Cut Groove Cylinder (cut_groove_cylinder.py)**
Used to create a groove of a constant depth. A groove is considered the
width of one tool (no travel in the X direction). The X location can be
specified or not.

Can interpolate from a pre-probe file for cylindrical autoleveling

 * **Cut Recess Cylinder (cut_recess_cylinder.py)**
Used to create a recess of a constant depth. User species the start and
end X location.

Can interpolate from a pre-probe file for cyl:qindrical autoleveling

 * **Drill Holes Cylinder (drill_holes_cylinder.py)**
Used to drill holes circumfrentially around a cylinder. The X location
can be specified or not. Script assumes the holes are spaced evenly around
the cylinder. User specifies the angular increment. If holes are bigger
than the tool, then multiple passes will be made to widen the hole.

Can interpolate from a pre-probe file for cylindrical autoleveling

### Modify
 * **Apply Cylinder Autolevel (apply_cylinder_autolevel.py)**
Script to apply cylinder autolevel process. Modifies a G-code file to adjust
the Z-axis height using the **probe_results.txt** file obtained from the
pre-probe process. Requires the user to specify the nominal OD of the part
to be cut.

 * **Convert to Inverse Time (convert_to_inverse_time.py)**
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



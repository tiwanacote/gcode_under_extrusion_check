# gcode_under_extrusion_check
This program detects under extrusion in perimeter gcode lines.

USAGE: >>>> python gcode_repair_V1.py   -  Just complete imput file name into code
 
 Output: 
- Archive for visualization in CURA -----> Under extrusion is showes in yellow over perimeter line in red
- Archive with repaired perimeter lines with underextrusion (Only modify lines biggers than "min_lenght". This is why CURA makes
  underextrusions in tiny lines in sharp corners)
- Calculate ratio between "gcode line mm" / "extrusion in mm". For 0.4mm nozzle, 1,75 diameter filament and 100% flux.
  Expected ratio is 30.0 XY mm/ E mm. 


#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  gcode_repair_V1.py
#  
# This program detects under extrusion in gcode lines.
# 
# USAGE: Just complete imput file name
# 
# Output: 
# - Archive for visualization in CURA
# - Archive with repaired perimeter lines with underextrusion (Only modify lines biggers than "min_lenght". This is why CURA makes
#   underextrusions in tiny lines in sharp corners)
# - Calculate ratio between "gcode line mm" / "extrusion in mm". For 0.4mm nozzle, 1,75 diameter filament and 100% flux.
#   Expected ratio is 30.0 XY mm/ E mm. 
#
#



def main(args):
	
	import re
	import math
	import TableIt
	
	
	# --------------------------------------------------------------------------------------------------------
	# Input file
	# --------------------------------------------------------------------------------------------------------
	
	#NOMBRE_ARCHIVO_ENTRADA = 'CURA_test_short_3'
	NOMBRE_ARCHIVO_ENTRADA = 'CURA_test'
	#NOMBRE_ARCHIVO_ENTRADA = 'CURA_test_repaired'
	#NOMBRE_ARCHIVO_ENTRADA = 's3d'
	
	# --------------------------------------------------------------------------------------------------------
	  
	# Ingresar la media de extrusión para el contorno.
	# Para una boquilla de 0.4mm con filamento de 1.75mm y flujo de 100%, la media esperada de la relacción 
	# mm de avance/mm de extrusión = 30.0
	expected_ratio = 30.0 #30.0
	error_bound = 0.3
	min_lenght = 0.7				# Min lenght to operate over extrusion
	
	
	# --------------------------------------------------------------------------------------------------------
	
	# Repaired file output
	NOMBRE_ARCHIVO_SALIDA  = NOMBRE_ARCHIVO_ENTRADA + "_repaired.gcode"
	output_file = open(NOMBRE_ARCHIVO_SALIDA, "w")
	
	# Visualization output gcode file - This file change the line type in order to visualizate underextrued 
	# perimeter lines in CURA
	NOMBRE_ARCHIVO_SALIDA_VISUAL  = NOMBRE_ARCHIVO_ENTRADA + "_for_visual_check.gcode"
	output_file_visual = open(NOMBRE_ARCHIVO_SALIDA_VISUAL, "w")
	
	S3D_OUTER_PERIM = '; feature outer perimeter'
	CURA_OUTER_PERIM = ';TYPE:WALL-OUTER'
	
	is_gcode_perimeter = False
	
	line_counter = 0
	
	X_init_pos = 0.0
	Y_init_pos = 0.0
	E_init_pos = 0.0
	
	X_end_pos = 0.0
	Y_end_pos = 0.0
	E_end_pos = 0.0
	
	XY_distance = 0.0
	
	ratio_XYE = 0.0
	
	ratio_list = []

	# --------------------------------------------------------------------------------------------------------
	
	with open(NOMBRE_ARCHIVO_ENTRADA + ".gcode") as gcode:
		
		print "Processing ... "
		
		

		for gcode_line in gcode:
			
			
			# GCODE line starts with ";" - It is a comment
			if (gcode_line[0]==';'):
			
				# CURA and S3D comment behind a ";" when we are printing a part perimeter
				if ( (CURA_OUTER_PERIM in gcode_line) or  (S3D_OUTER_PERIM in gcode_line) ): 
				
					is_gcode_perimeter = True 				# Levanta flag que se está en contorno: Hay que procesar ese gcode
					line_counter = line_counter + 1			# Cuenta la línea de gcode en donde se está
					
					output_file.write(gcode_line)			# Copia la linea de GCODE al archivo de GCODE reparado. En este caso es una linea con ";" sin importancia.
					output_file_visual.write(gcode_line)
					
				# We are out perimeter (Maybe infill support, etc)
				else:
					
					is_gcode_perimeter = False				# Baja el flag que se está en contorno: Hay que procesar ese gcode. Se espera que nunca haya un ";" en medio de un contorno.
					line_counter = line_counter + 1			# Cuenta la línea de gcode en donde se está
					
					output_file.write(gcode_line)
					output_file_visual.write(gcode_line)
					
					
			
			# G92 - Es uno de los pocos GCODES que interesa ver que no se G0 y G1. Establece la posición actual. 
			elif ( ('G92' in gcode_line) ):
				
				temp_E_position = extract_number(gcode_line,'E')
				line_counter = line_counter + 1
				
				output_file.write(gcode_line)
				output_file_visual.write(gcode_line)
				
				
			# G1 - Must be processed
			elif (('G1' in gcode_line) ):			
				
				line_counter = line_counter + 1
				
				if (is_gcode_perimeter==True):
				
					if ("X" in gcode_line):
						X_end_pos = extract_number(gcode_line,'X')			# Extract the number of gcode string of selected axis and convert to float
					else:
						X_end_pos = X_init_pos
					if ("Y" in gcode_line):
						Y_end_pos = extract_number(gcode_line,'Y')
					else:
						Y_end_pos = Y_init_pos
					if ("E" in gcode_line):									# Never should be only an E parameter without X or Y ones
						E_end_pos = extract_number(gcode_line,'E')
					else:
						E_end_pos = E_init_pos
					
					print "--------------------------------------------"
					print '\x1b[6;30;42m' + ">>>>>>" +  '\x1b[0m'+ gcode_line
					
					 
					# Calculate the distance of x-y gcode line
					XY_distance = math.sqrt((X_end_pos - X_init_pos)**2 + (Y_end_pos - Y_init_pos)**2)
					E_distance = abs(E_end_pos - E_init_pos)
					print "XY_distance: " + str(XY_distance)
					
					# Ratio is defines as "mm in XY"/"mm in E". Big numbers over means there is underextrusion
					# Ratio = 0 means that there is no movement in XY axis but there is extrusion
					# Ratio = inf. means it is movement in XY but there is no extrusion. this must be imposible if we are talking about perimeter filling. 
					if (E_distance!= 0.0):
						ratio_XYE = XY_distance / E_distance	
						
						if (E_distance > min_lenght):
							# Recalculating Extrusion for XY gcode line - Gcode reparing
							new_E_distance = XY_distance/expected_ratio
							new_E_end_pos = new_E_distance + E_init_pos
							new_gcode_line = insert_number(gcode_line, 'E', new_E_end_pos)
						
							
							print "X_end_pos: " + str(X_end_pos)
							print "Y_end_pos: " + str(Y_end_pos)
							print "E_end_pos: " + str(E_end_pos)
							print "X_init_pos: " + str(X_init_pos)
							print "Y_init_pos: " + str(Y_init_pos)
							print "E_init_pos: " + str(E_init_pos)
							print "new_E_distance: " + str(new_E_distance)
							print "new_E_end_pos: " + str(new_E_end_pos)
							print "new_gcode_line: " + str(new_gcode_line)
						
							output_file.write(new_gcode_line)
							
							if ((ratio_XYE<expected_ratio-error_bound) or (ratio_XYE>expected_ratio+error_bound)):
								output_file_visual.write(';TYPE:SKIN\n')	#This line will change color next line to yellow 
								output_file_visual.write(gcode_line)
								output_file_visual.write(CURA_OUTER_PERIM+'\n')	#This line will change color again to perimeter
							else:
								output_file_visual.write(gcode_line)
								
						else:
							output_file.write(gcode_line)
							output_file_visual.write(gcode_line)
						
					else:
						ratio_XYE = 0.0
						output_file.write(gcode_line)
						
						output_file_visual.write(';TYPE:SKIN\n')	#This line will change color next line to yellow 
						output_file_visual.write(gcode_line)
						output_file_visual.write(CURA_OUTER_PERIM+'\n')	#This line will change color again to perimeter
						
					ratio_list.append([ratio_XYE,line_counter,XY_distance,gcode_line])
					print "ratio_XYE: " + str(ratio_XYE)
					print "E_distance: " + str(E_distance)
					
					 
					
					
					# For next gcode line, current end positions will be the init positions
					X_init_pos = X_end_pos
					Y_init_pos = Y_end_pos
					E_init_pos = E_end_pos
					
						
					
					
					
				
				# Out of perimeter (Maybe infill, support, etc)
				if (is_gcode_perimeter==False):
				
					if ("X" in gcode_line):
						X_init_pos = extract_number(gcode_line,'X')			# Extract the number of gcode string of selected axis and convert to float
					
					if ("Y" in gcode_line):
						Y_init_pos = extract_number(gcode_line,'Y')
				
					if ("E" in gcode_line):									# Never should be only an E parameter without X or Y ones
						E_init_pos = extract_number(gcode_line,'E')
					
					
					output_file.write(gcode_line)
					output_file_visual.write(gcode_line)
		
		
			
			# G0 - We just copy XY values to "X_init_pos" and "Y_init_pos". In a G0 should not be extrusion.
			elif (('G0' in gcode_line) ):		
				
				line_counter = line_counter + 1
				
				if ("X" in gcode_line):
					X_init_pos = extract_number(gcode_line,'X')			# Extract the number of gcode string of selected axis and convert to float
					
				if ("Y" in gcode_line):
					Y_init_pos = extract_number(gcode_line,'Y')
				
				if ("E" in gcode_line):									# Never should be only an E parameter without X or Y ones
					E_init_pos = extract_number(gcode_line,'E')
			
				
				output_file.write(gcode_line)
				output_file_visual.write(gcode_line)
				
				
			# Somthing else we are not taking in consideration 
			else:
		
				line_counter = line_counter + 1
				output_file.write(gcode_line)
				output_file_visual.write(gcode_line)
	
				
			print "Line_counter: " + str(line_counter)
				
	
	print "====================================================================================="
	lenght_ratio_list = len(ratio_list)	
	print "Largo de la lista: " + str(lenght_ratio_list)	
	print ratio_list
	
	#media = sum(ratio_list[0])/lenght_ratio_list
	#maximo = max(ratio_list[0])
	#minimo = min(ratio_list[0])
	#print ""
	#print "MEDIA: " + str(media)
	#print "MAXIMO: " + str(maximo)
	#print "MINIMO: " + str(minimo)
	#print ""
	
	fault_ratios = mean_list_filter(ratio_list, expected_ratio, error_bound, min_lenght)
	#print fault_ratios
	
	# RATIO , LINE NUMBER in gcode , LINE xy LENGHT , Line GCODE STRING 
	print " RATIO , LINE NUMBER in gcode , LINE xy LENGHT , Line GCODE STRING"
	TableIt.printTable(fault_ratios)
	print ""
	print "Line_counter: " + str(line_counter)
				
	return 0

def extract_number(line_string, axis):
	# Extract the number of the axis (X,Y,Z or E) and returns a float number
	
	#print "Se entra a la funcion"
	
	line_striped = line_string.strip()
	words = str.split(line_striped)

	for word in words:
						
		if word[:1]==axis:								# Si la palabra tiene una E
			number_string = word[1:]				# Le saco el "E"
			value = float(number_string)					# Convierto el numero en string a numero float
			#print "Value= " + str(value)
			return value
	return 0


def insert_number(line_string, axis, new_number):
	
	# insert the number of the axis (X,Y,Z or E) and returns the new string
	
	line_striped = line_string.strip()
	words = str.split(line_striped)

	for word in words:
						
		if word[:1]==axis:							# Si la palabra tiene una E
			new_word = word.replace(word[1:], str(new_number))
			line_string = line_string.replace(word,new_word)
			return line_string
	
	return line_string
	
def mean_list_filter(input_list, exp_mean, err_bound , min_line_lenght):
	
	output_list = []
	
	for element in input_list:
		if ((element[0]>exp_mean+err_bound) or (element[0]<exp_mean-err_bound)):
			if (element[2]>min_line_lenght):
				output_list.append([element[0],element[1], element[2], element[3]])
	
	return output_list


	

# 
	


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

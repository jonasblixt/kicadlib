#!/usr/bin/python
# -*- coding: utf-8 -*-

#Part Number,Status,Capacitance(Nominal),Rated Voltage(V),Temperature       Characteristics,Size Code (mm)/(inch),T size(mm Max.),Cap. Tolerance,Type
#GRM32ER60E337ME05,In Production,330uF,2.5,X5R,3225M/1210,2.8,+/-20%,General Purpose
#       0         ,     1       , 2   , 3 , 4 ,     5    , 6 , 7    , 8
import sys
import re
import math

template = """
#
# {C_NAME}
#
DEF {C_NAME} C 0 10 N Y 1 F N
F0 "C" 0 150 39 H V L CNN
F1 "{C_NAME}" 6 -85 40 H I L CNN
F2 "{C_FOOTPRINT}" 38 -150 30 H I C CNN
F3 "~" 0 0 60 H V C CNN
F4 "{C_DESCRIPTION}" 100 200 60 H I C CNN "Description"
F5 "{C_PNR}" 100 200 60 H I C CNN "Part Number"
F6 "{C_MANUF}" 100 200 60 H I C CNN "Manufacturer"
F7 "{C_CAPACITANCE}" 100 100 39 H V C CNN "Capacitance"
$FPLIST
{C_FOOTPRINT}
$ENDFPLIST
DRAW
P 2 0 1 20  -80 -30  80 -30 N
P 2 0 1 20  -80 30  80 30 N
X ~ 1 0 200 170 D 40 40 1 1 P
X ~ 2 0 -200 170 U 40 40 1 1 P
ENDDRAW
ENDDEF"""

dcm_template ="""
$CMP {C_NAME}
D {DCM_DESC}
$ENDCMP
#"""

f = open(sys.argv[1])
lines = f.readlines()
f.close()
r = re.compile(u"([0-9\.]+)([unp]{1})([F]{1})")
l_count = 0
files = {}
comp_count = 0

comp_names = {}

f  = open("capacitors_murata_GRM.lib","w")
f_dcm =open("capacitors_murata_GRM.dcm","w")
f.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8")
f_dcm.write("EESchema-DOCLIB  Version 2.0\n#encoding utf-8")
for l in lines[1:]:
	l_count = l_count + 1
	data = l.split(",")

	if len(data) < 7:
		print ("Bogus data on line %i, skipping..."%(l_count))
	else:
		footprint = data[5].split('/')[1]
		dielectric = data[4]
		pnr = data[0]
		voltage = data[3]+"Vdc"
		capacitance = data[2]
		tolerance = data[7]

		#print (footprint, dielectric,pnr)
		#print (data[3], data[7], data[9], data[10], data[11], data[12])

		fp_name = "C"+footprint

		# Component name example: C0402_1p2_50V
		result = r.match(capacitance)
		if result == None:
			print("ERROR:")
			print (capacitance)
			print (type(capacitance))
			raise Exception("Parse error")
		#print (capacitance)
		c = float(result.group(1))
		c_r = result.group(2)

		if (c_r == "u" and c < 1.0):
			c_r = "n"
			c = c * 1000.0

		if (c_r == "p" and c >= 1000.0):
			c_r = "n"
			c = c / 1000.0

		c_2 = (c % 1.0)*10.0
		c_name = ""
		if c_2 == 0:
			c_name = "%s_%1.f%s_%s_%s"%(fp_name,math.floor(c),c_r,voltage,dielectric)
		else:	
			c_name = "%s_%1.f%s%1.f_%s_%s"%(fp_name,math.floor(c),c_r,c_2,voltage,dielectric)


		if c_name in comp_names:
			comp_names[c_name] = comp_names[c_name] + 1
			c_name = c_name + "_%i"%(comp_names[c_name])
		else:
			comp_names[c_name] = 1
			
		print (c_name)

		c_data = template
		c_data = c_data.replace("{C_NAME}",c_name)
		c_data = c_data.replace("{C_CAPACITANCE}",capacitance)
		#c_data = c_data.replace("{C_TOLERANCE}",tolerance)
		#c_data = c_data.replace("{C_DIELEC}",dielectric)
		c_data = c_data.replace("{C_DESCRIPTION}","%s, %s, %s, %s"%(capacitance,voltage, tolerance,dielectric))
		c_data = c_data.replace("{C_PNR}",pnr)
		c_data = c_data.replace("{C_MANUF}","Murata")
		c_data = c_data.replace("{C_FOOTPRINT}",fp_name)


		f.write(c_data)


		dcm_data = dcm_template
		dcm_data = dcm_data.replace("{C_NAME}",c_name)
		dcm_data = dcm_data.replace("{DCM_DESC}","Ceramic Capacitor %s, %s, %s, %s"%(capacitance,voltage,tolerance,dielectric))
		f_dcm.write(dcm_data)

		comp_count = comp_count + 1



f.close()
f_dcm.close()

print ("Generated %i components!"%(comp_count))

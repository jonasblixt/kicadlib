#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     0           1              2                     3                      4                 5           6                   7              8                 9          10             11         12        13    14              
#"Datasheets","Image","Digi-Key Part Number","Manufacturer Part Number","Manufacturer","Description","Quantity Available","Factory Stock","Unit Price (USD)","@ qty","Minimum Quantity","Packaging","Series","Type","Material - Core",
#     15        16            17                    18                 19             20                21                22                          23                    24              25                   26             27                   28                       29                                                
# "Inductance","Tolerance","Current Rating","Current - Saturation","Shielding","DC Resistance (DCR)","Q @ Freq","Frequency - Self Resonant","Operating Temperature","Frequency - Test","Mounting Type","Package / Case","Size / Dimension","Height - Seated (Max)","Supplier Device Package"


import sys
import re
import math

template = """
#
# {NAME}
#
DEF {NAME} L 0 10 N Y 1 F N
F0 "L" 0 150 39 H V L CNN
F1 "{NAME}" 6 -85 40 H I L CNN
F2 "{FOOTPRINT}" 38 -150 30 H I C CNN
F3 "~" 0 0 60 H V C CNN
F4 "{DESCRIPTION}" 100 200 60 H I C CNN "Description"
F5 "{PNR}" 100 200 60 H I C CNN "Part Number"
F6 "{MANUF}" 100 200 60 H I C CNN "Manufacturer"
F7 "{INDUCTANCE}" 100 100 39 H V C CNN "Inductance"
$FPLIST
{FOOTPRINT}
$ENDFPLIST
DRAW
A -150 0 50 1 1799 0 1 0 N -100 0 -200 0
A -50 0 50 1 1799 0 1 0 N 0 0 -100 0
A 50 0 50 1 1799 0 1 0 N 100 0 0 0
A 150 0 50 1 1799 0 1 0 N 200 0 100 0
X 1 1 -250 0 50 R 30 30 1 1 I
X 2 2 250 0 50 L 30 30 1 1 I
ENDDRAW
ENDDEF"""

dcm_template ="""
$CMP {NAME}
D {DCM_DESC}
$ENDCMP
#"""

f = open(sys.argv[1])
lines = f.readlines()
f.close()
r = re.compile(u"([0-9\.]+)([UNµn]{1})([H]{1})")
l_count = 0
files = {}
comp_count = 0


f = open("vishay_IHLP_inductors.lib","w")
f_dcm = open("vishay_IHLP_inductors.dcm","w")
f.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8")
f_dcm.write("EESchema-DOCLIB  Version 2.0\n#encoding utf-8")


for l in lines[1:]:
	l_count = l_count + 1
	l = l.replace("\"","")
	data = l.split(",")

	if len(data) < 29:
		print ("Bogus data on line %i, skipping..."%(l_count))
	else:

		pnr = data[3]
		footprint = pnr[0:8]
		description = data[5]
		inductance = data[15]
		tolerance = data[16]
		current_rating = data[17]
		current_sat = data[18]
		dcr = data[20]
		q = data[21]
		self_res = data[22]
		temperature = data[23]
		dimensions = data[27]

		#print (footprint, dielectric,pnr)
		#print (data[3], data[7], data[9], data[10], data[11], data[12])

		#print (pnr, footprint,description,inductance,tolerance,current_rating,current_sat,dcr,q,self_res,temperature,dimensions)

		# Component name example: C0402_1p2_50V
		result = r.match(inductance)

		if result == None:
			print("ERROR:")
			print (inductance)
			print (type(inductance))
			raise Exception("Parse error")
		#print (capacitance)
		c = float(result.group(1))
		c_r = result.group(2)

		if c_r == "µ":
			c_r = "u"


		c_2 = (c % 1.0)*10.0
		c_name = ""
		if c_2 == 0:
			c_name = "%s_%1.f%s_%x"%(footprint,math.floor(c),c_r,comp_count)
		else:	
			c_name = "%s_%1.f%s%1.f_%x"%(footprint,math.floor(c),c_r,c_2,comp_count)

		print (c_name," - ",inductance)

		#continue
		c_data = template
		c_data = c_data.replace("{NAME}",c_name)
		c_data = c_data.replace("{INDUCTANCE}",inductance)
		#c_data = c_data.replace("{C_TOLERANCE}",tolerance)
		#c_data = c_data.replace("{C_DIELEC}",dielectric)
		c_data = c_data.replace("{DESCRIPTION}","%s, %s, %s, %s, %s, %s, %s, %s"%(inductance,tolerance,current_rating, current_sat,dcr,self_res,temperature,dimensions))
		c_data = c_data.replace("{PNR}",pnr)
		c_data = c_data.replace("{MANUF}","Vishay")
		c_data = c_data.replace("{FOOTPRINT}",footprint)


		f.write(c_data)


		dcm_data = dcm_template
		dcm_data = dcm_data.replace("{NAME}",c_name)
		dcm_data = dcm_data.replace("{DCM_DESC}","%s, %s, I=%s, I_sat=%s, DCR=%s, Self resonance: %s, %s, %s"%(inductance,tolerance,current_rating, current_sat,dcr,self_res,temperature,dimensions))
		f_dcm.write(dcm_data)

		comp_count = comp_count + 1



f.close()
f_dcm.close()

print ("Generated %i components!"%(comp_count))

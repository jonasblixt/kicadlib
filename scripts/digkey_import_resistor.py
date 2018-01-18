#!/usr/bin/python
# -*- coding: utf-8 -*-
#      0          1             2                      3                      4             5                 6                 7                 8              9           10              11         12          13               14           15               16          17            18
# "Datasheets","Image","Digi-Key Part Number","Manufacturer Part Number","Manufacturer","Description","Quantity Available","Factory Stock","Unit Price (USD)","@ qty","Minimum Quantity","Packaging","Series","Resistance (Ohms)","Tolerance","Power (Watts)","Composition","Features","Temperature Coefficient",
#        19                        20               21                      22             23            24
# "Operating Temperature","Package / Case","Supplier Device Package","Size / Dimension","Height","Number of Terminations"


import sys
import re
import math

template = """
#
# {NAME}
#
DEF {NAME} R 0 10 N Y 1 F N
F0 "R" 0 150 39 H V L CNN
F1 "{NAME}" 6 -85 40 H I L CNN
F2 "{FOOTPRINT}" 38 -150 30 H I C CNN
F3 "~" 0 0 60 H V C CNN
F4 "{DESCRIPTION}" 100 200 60 H I C CNN "Description"
F5 "{PNR}" 100 200 60 H I C CNN "Part Number"
F6 "{MANUF}" 100 200 60 H I C CNN "Manufacturer"
F7 "{RESISTANCE}" 100 100 39 H V C CNN "Resistance"
$FPLIST
{FOOTPRINT}
$ENDFPLIST
DRAW
S -40 150 40 -150 0 1 12 N
X ~ 1 0 250 100 D 60 60 1 1 P
X ~ 2 0 -250 100 U 60 60 1 1 P
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
r = re.compile(u"([0-9\.]+)([kKmM]*)")
l_count = 0
files = {}
comp_count = 0


f = open("vishay_resistors.lib","w")
f_dcm = open("vishay_resistors.dcm","w")
f.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8")
f_dcm.write("EESchema-DOCLIB  Version 2.0\n#encoding utf-8")

c_names = {}
for l in lines[1:]:
	l_count = l_count + 1
	l = l.replace("\"","")
	data = l.split(",")

	if len(data) < 24:
		print ("Bogus data on line %i, skipping..."%(l_count))
	else:

		pnr = data[3]
		manuf = data[4]
		description = data[5]
		resistance = data[13]
		tolerance = data[14]
		power = data[15]
		package = data[21]
		footprint = "R"+package[0:4]


		#print(pnr,manuf,description,resistance,tolerance,power,footprint)
		#continue

		#print (footprint, dielectric,pnr)
		#print (data[3], data[7], data[9], data[10], data[11], data[12])

		#print (pnr, footprint,description,inductance,tolerance,current_rating,current_sat,dcr,q,self_res,temperature,dimensions)

		# Component name example: C0402_1p2_50V
		result = r.match(resistance)

		if result == None:
			print("ERROR:")
			print (resistance)
			print (type(resistance))
			raise Exception("Parse error")
		#print (capacitance)
		c = float(result.group(1))
		c_r = result.group(2)

		if c_r == "":
			c_r = "R"

		c_2 = (c % 1.0)*100.0+0.0000001
		c_name = ""
		if c_2 < 0.0001:
			c_name = "%s_%1.f%s"%(footprint,math.floor(c),c_r)
		else:	
			c_name = "%s_%1.f%s%.2i"%(footprint,math.floor(c),c_r,c_2)

		print (c_name," - ",resistance,c)


		if c_name in c_names:
			c_names[c_name] = c_names[c_name] + 1
		else:
			c_names[c_name] = 1


		if c_names[c_name] > 1:
			v = c_names[c_name]
			c_name = c_name + "_%i"%(v)

		#continue
		c_data = template
		c_data = c_data.replace("{NAME}",c_name)
		c_data = c_data.replace("{RESISTANCE}",resistance)
		#c_data = c_data.replace("{C_TOLERANCE}",tolerance)
		#c_data = c_data.replace("{C_DIELEC}",dielectric)
		c_data = c_data.replace("{DESCRIPTION}","%s, %s, %s"%(resistance,tolerance,power))
		c_data = c_data.replace("{PNR}",pnr)
		c_data = c_data.replace("{MANUF}","Vishay")
		c_data = c_data.replace("{FOOTPRINT}",footprint)


		f.write(c_data)


		dcm_data = dcm_template
		dcm_data = dcm_data.replace("{NAME}",c_name)
		dcm_data = dcm_data.replace("{DCM_DESC}","%s, %s, %s"%(resistance,tolerance,power))
		f_dcm.write(dcm_data)

		comp_count = comp_count + 1



f.close()
f_dcm.close()

print ("Generated %i components!"%(comp_count))

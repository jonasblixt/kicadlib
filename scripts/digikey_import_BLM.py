#!/usr/bin/python
# -*- coding: utf-8 -*-

#                    0                                                                                     1                                             2                    3                      4                                    5                       6 7     8       9 10      11               12
#['"http://search.murata.co.jp/Ceramy/image/img/PDF/ENG/L0110S0100BLM18B.pdf"', 'http://media.digikey.com/Renders/Murata%20Renders/0603(LQG18).jpg"', '490-5977-1-ND"', 'BLM18BB141SN1D"', 'Murata Electronics North America"', 'FERRITE CHIP 140 OHM 450MA 0603",0,0', '0.10000",0,1', 'Cut Tape (CT)"', 'EMIFIL®, BLM18B"', 
#    13                  14         15                      16                      17                  
#'140 Ohm @ 100MHz"', '450mA"', '350 mOhm Max"', 'Differential Mode - Single"', '0603 (1608 Metric)"', 'Surface Mount"', '0.037"" (0.95mm)"', '0.063"" L x 0.031"" W (1.60mm x 0.80mm)"\n']

import sys
import re
import math

template = """
#
# {NAME}
#
DEF {NAME} FB 0 10 N Y 1 F N
F0 "FB" 0 150 39 H V L CNN
F1 "{NAME}" 6 -85 40 H I L CNN
F2 "{FOOTPRINT}" 38 -150 30 H I C CNN
F3 "~" 0 0 60 H V C CNN
F4 "{DESCRIPTION}" 100 200 60 H I C CNN "Description"
F5 "{PNR}" 100 200 60 H I C CNN "Part Number"
F6 "{MANUF}" 100 200 60 H I C CNN "Manufacturer"
F7 "{VALUE}" 100 100 39 H V C CNN "Impedance"
$FPLIST
{FOOTPRINT}
$ENDFPLIST
DRAW
A -150 0 50 1 1799 0 1 0 N -100 0 -200 0
A -50 0 50 1 1799 0 1 0 N 0 0 -100 0
A 0 0 0 0 0 0 1 0 N 0 0 0 0
A 50 0 50 1 1799 0 1 0 N 100 0 0 0
A 150 0 50 1 1799 0 1 0 N 200 0 100 0
S -225 75 225 -50 0 1 0 N
X 1 1 -350 0 150 R 40 40 1 1 P
X 2 2 350 0 150 L 40 40 1 1 P
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
r = re.compile(u"([0-9\.]+)([µ]*)")
l_count = 0
files = {}
comp_count = 0


f = open("beads_BLM.lib","w")
f_dcm = open("beads_BLM.dcm","w")
f.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8")
f_dcm.write("EESchema-DOCLIB  Version 2.0\n#encoding utf-8")

c_names = {}
for l in lines[1:]:
	l_count = l_count + 1
	#l = l.replace("\"","")
	data = l.split(",\"")
	#print (data,len(data))


	for i in range(len(data)):
		data[i] = data[i].replace("\"","")

	if len(data) < 15:
		print ("Bogus data on line %i, skipping..."%(l_count))
	else:

		pnr = data[3]
		manuf = data[4]
		description = data[5]
		footprint = data[13][0:4]
		c_name = "BL"+footprint+"_"+pnr
		value = data[9]
		dcr = data[11]
		footprint = "L"+footprint

		#print (pnr,description,footprint)
		#continue

		desc = description+ "DCR: "+dcr
		#continue
		c_data = template
		c_data = c_data.replace("{NAME}",c_name)
		c_data = c_data.replace("{VALUE}",value)
		c_data = c_data.replace("{DESCRIPTION}",desc)
		c_data = c_data.replace("{PNR}",pnr)
		c_data = c_data.replace("{MANUF}","Murata")
		c_data = c_data.replace("{FOOTPRINT}",footprint)


		f.write(c_data)


		dcm_data = dcm_template
		dcm_data = dcm_data.replace("{NAME}",c_name)
		dcm_data = dcm_data.replace("{DCM_DESC}",desc)
		f_dcm.write(dcm_data)

		comp_count = comp_count + 1



f.close()
f_dcm.close()

print ("Generated %i components!"%(comp_count))

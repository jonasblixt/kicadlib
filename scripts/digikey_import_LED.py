#!/usr/bin/python
# -*- coding: utf-8 -*-

#                                      0                                                                            1                                             2                 3                   4                           5                             6               7                8          9         10     
#['"http://rohmfs.rohm.com/en/products/databook/datasheet/opto/led/chip_mono/sml-p1.pdf"', 'http://media.digikey.com/Photos/Rohm%20Photos/MFG_SML-P10.jpg"', '846-1197-1-ND"', 'SML-P13PTT86R"', 'Rohm Semiconductor"', 'LED 560NM GRN TRANSP 1006",240,0', '0.57000",0,1', 'Cut Tape (CT)"', 'PicoLED™"', 'Green"', '560nm"', '-"', 
#  11         12      13       
#'10mcd"', '2.1V"', '20mA"', '-"', 'Clear"', 'Colorless"', 'Square with Flat Top, 0.60mm"', '0402 (1006 Metric)"', '1006 (0402)"', '1.00mm L x 0.60mm W"', '0.25mm"', 'Surface Mount"\n']

import sys
import re
import math

template = """
#
# {NAME}
#
DEF {NAME} D 0 10 N Y 1 F N
F0 "D" 0 150 39 H V L CNN
F1 "{NAME}" 6 -85 40 H I L CNN
F2 "{FOOTPRINT}" 38 -150 30 H I C CNN
F3 "~" 0 0 60 H V C CNN
F4 "{DESCRIPTION}" 100 200 60 H I C CNN "Description"
F5 "{PNR}" 100 200 60 H I C CNN "Part Number"
F6 "{MANUF}" 100 200 60 H I C CNN "Manufacturer"
F7 "{VALUE}" 100 100 39 H V C CNN "Color"
$FPLIST
{FOOTPRINT}
$ENDFPLIST
DRAW
P 2 0 1 0  50 50  50 -50 N
P 3 0 1 0  -50 50  50 0  -50 -50 F
P 3 0 1 0  65 -40  110 -80  105 -55 N
P 3 0 1 0  80 -25  125 -65  120 -40 N
X ~ 1 -200 0 150 R 40 40 1 1 P
X ~ 2 200 0 150 L 40 40 1 1 P
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


f = open("LEDs.lib","w")
f_dcm = open("LEDs.dcm","w")
f.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8")
f_dcm.write("EESchema-DOCLIB  Version 2.0\n#encoding utf-8")

c_names = {}
for l in lines[1:]:
	l_count = l_count + 1
	#l = l.replace("\"","")
	data = l.split(",\"")
	#print (data,len(data))
	#continue

	for i in range(len(data)):
		data[i] = data[i].replace("\"","")

	if len(data) < 15:
		print ("Bogus data on line %i, skipping..."%(l_count))
	else:

		pnr = data[3]
		manuf = data[4]
		description = data[5]
		color = data[9]
		wavelength = data[10]
		intencity = data[12]
		voltage = data[13]
		current = data[14]

		c_name = "LED0402_"+pnr
		footprint = "LED0402"

		print (voltage,current)
		#continue

		desc = "LED 0402, %s (%s), %s, %s, %s"%(color,wavelength,intencity,voltage,current)
		#continue
		c_data = template
		c_data = c_data.replace("{NAME}",c_name)
		c_data = c_data.replace("{VALUE}",color)
		c_data = c_data.replace("{DESCRIPTION}",desc)
		c_data = c_data.replace("{PNR}",pnr)
		c_data = c_data.replace("{MANUF}","Rohm")
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

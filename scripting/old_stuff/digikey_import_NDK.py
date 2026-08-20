#!/usr/bin/python
# -*- coding: utf-8 -*-
#     0          1              2                        3                   4              5               6                  7               8                9        10               11           12      13     14             15                   16
#"Datasheets","Image","Digi-Key Part Number","Manufacturer Part Number","Manufacturer","Description","Quantity Available","Factory Stock","Unit Price (USD)","@ qty","Minimum Quantity","Packaging","Series","Type","Frequency","Frequency Stability","Frequency Tolerance",
#     17                       18                             19                  20                21            22             23               24               25
#"Load Capacitance","ESR (Equivalent Series Resistance)","Operating Mode","Operating Temperature","Ratings","Mounting Type","Package / Case","Size / Dimension","Height"
#
#                                   0                                                                                 1                                           2                    3                4             5                           6            7               8            9
#['http://media.digikey.com/PDF/Data%20Sheets/NDK%20PDFs/NX2016AB-40MHZ%20SW2W.pdf', 'http://media.digikey.com/Renders/NDK%20Renders/4-SMD,%20No%20Lead.jpg', '644-1127-1-ND', 'NX2016AB-40MHZ SW2W', 'NDK', 'CRYSTAL 40.0000MHZ 7PF SMD,0,0', 'Call,0,1', 'Cut Tape (CT)', 'NX2016AB', 'MHz Crystal', 
#  10         11       12        13     14          15           16                   
#'40MHz', '±20ppm', '±20ppm', '7pF', '60 Ohm', 'Fundamental', '-30°C ~ 75°C', '-', 'Surface Mount', '4-SMD, No Lead (DFN, LCC)', '0.079 L x 0.063 W (2.00mm x 1.60mm)', '0.020 (0.50mm)\n']
#
import sys
import re
import math

template = """
#
# {NAME}
#
DEF {NAME} X 0 10 N Y 1 F N
F0 "X" 0 150 39 H V L CNN
F1 "{NAME}" 6 -85 40 H I L CNN
F2 "{FOOTPRINT}" 38 -150 30 H I C CNN
F3 "~" 0 0 60 H V C CNN
F4 "{DESCRIPTION}" 100 200 60 H I C CNN "Description"
F5 "{PNR}" 100 200 60 H I C CNN "Part Number"
F6 "{MANUF}" 100 200 60 H I C CNN "Manufacturer"
F7 "{VALUE}" 100 100 39 H V C CNN "Frequency"
$FPLIST
{FOOTPRINT}
$ENDFPLIST
DRAW
P 2 0 1 0  -100 100  -100 -100 N
P 2 0 1 0  100 100  100 -100 N
P 5 0 1 0  -50 50  50 50  50 -50  -50 -50  -50 50 N
X 1 1 -300 0 200 R 40 40 1 1 P
X 3 3 300 0 200 L 40 40 1 1 P
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


f = open("xtal_NDK.lib","w")
f_dcm = open("xtal_NDK.dcm","w")
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

	if len(data) < 20:
		print ("Bogus data on line %i, skipping..."%(l_count))
	else:

		pnr = data[3].replace(" ","")
		manuf = data[4]
		#description = data[5]
		frequency = data[10]
		freq_stab = data[11]
		freq_tol = data[12]
		load_cap = data[13]
		esr = data[14]
		footprint = data[8]
		op_temp = data[16]

		c_name = pnr



		desc = "f=%s, Stability:%s, Tol:%s,Load capacitance:%s,esr:%s,Temp:%s"%(frequency,freq_stab,freq_tol,load_cap,esr,op_temp)
		#continue
		c_data = template
		c_data = c_data.replace("{NAME}",c_name)
		c_data = c_data.replace("{VALUE}",frequency)
		c_data = c_data.replace("{DESCRIPTION}",desc)
		c_data = c_data.replace("{PNR}",pnr)
		c_data = c_data.replace("{MANUF}","NDK")
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

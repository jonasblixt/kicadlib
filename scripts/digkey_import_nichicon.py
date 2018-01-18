#!/usr/bin/python
# -*- coding: utf-8 -*-

#     0          1              2                       3                      4           5                 6                7                 8               9           10              11         12        13             14            15                16
#"Datasheets","Image","Digi-Key Part Number","Manufacturer Part Number","Manufacturer","Description","Quantity Available","Factory Stock","Unit Price (USD)","@ qty","Minimum Quantity","Packaging","Series","Capacitance","Tolerance","Voltage Rating","ESR (Equivalent Series Resistance)",
#    17                     18                 19       20            21              22            23             24                 25                      26                      27               28
#"Lifetime @ Temp.","Operating Temperature","Type","Applications","Ripple Current","Impedance","Lead Spacing","Size / Dimension","Height - Seated (Max)","Surface Mount Land Size","Mounting Type","Package / Case"

#
# ['"http://www.nichicon-us.com/english/products/pdfs/e-cr.pdf', 'http://media.digikey.com/Photos/Nichicon%20Photos/CR%20SERIES%2010.10mm.JPG', '493-13737-1-ND', 'PCR1C681MCL1GS', 'Nichicon', 
# 'CAP POLYMER 680UF 20% 16V SMD",7,0,"3.89000",0,1,"Cut Tape (CT)', 'CR', '680µF', '±20%', '16V', '19 mOhm', '4000 Hrs @ 125°C', '-55°C ~ 125°C', 'Polymer', 'General Purpose', '3.2A', '-', '-', '0.394"" Dia (10.00mm)', '0.398"" (10.10mm)', '0.406"" L x 0.406"" W (10.30mm x 10.30mm)', 'Surface Mount', 'Radial, Can - SMD"\n']
import sys
import re
import math

template = """
#
# {NAME}
#
DEF {NAME} C 0 10 N Y 1 F N
F0 "C" 0 150 39 H V L CNN
F1 "{NAME}" 6 -85 40 H I L CNN
F2 "{FOOTPRINT}" 38 -150 30 H I C CNN
F3 "~" 0 0 60 H V C CNN
F4 "{DESCRIPTION}" 100 200 60 H I C CNN "Description"
F5 "{PNR}" 100 200 60 H I C CNN "Part Number"
F6 "{MANUF}" 100 200 60 H I C CNN "Manufacturer"
F7 "{CAPACITANCE}" 100 100 39 H V C CNN "Capacitance"
$FPLIST
{FOOTPRINT}
$ENDFPLIST
DRAW
T 0 -50 100 80 0 0 0 +  Normal 0 C C
A 0 -200 180 563 1236 0 1 15 N 100 -50 -100 -50
P 4 0 1 15  -100 50  100 50  50 50  50 50 N
X ~ 1 0 200 150 D 40 40 1 1 P
X ~ 2 0 -200 180 U 40 40 1 1 P
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


f = open("nichicon_polymer_cap.lib","w")
f_dcm = open("nichicon_polymer_cap.dcm","w")
f.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8")
f_dcm.write("EESchema-DOCLIB  Version 2.0\n#encoding utf-8")

c_names = {}
for l in lines[1:]:
	l_count = l_count + 1
	l = l.replace("\"","")
	data = l.split(",")
	#print (data,len(data))

	if len(data) < 23:
		print ("Bogus data on line %i, skipping..."%(l_count))
	else:

		pnr = data[3]
		manuf = data[4]
		description = data[5]
		capacitance = data[13]
		tolerance = data[14]
		voltage = data[15]
		esr = data[16]
		lifetime = data[17]
		temperature = data[18]
		ripplecurrent = data[21]
		cap_size = data[22]


		if "FPCAP" in l:
			continue
		#print (cap_size,l)

		diam = re.compile(".+\(([0-9.]+)[m]{2}")
		footprint = "PCAP_"+diam.match(l).group(1)

		print(pnr,manuf,description,capacitance,tolerance,voltage,esr,lifetime,temperature,ripplecurrent,footprint)

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

		if c_r == "µ":
			c_r = "u"

		c_2 = (c % 1.0)*100.0+0.0000001
		c_name = ""
		if c_2 < 0.0001:
			c_name = "PCAP_%1.f%s"%(math.floor(c),c_r)
		else:	
			c_name = "PCAP_%1.f%s%.2i"%(math.floor(c),c_r,c_2)

		#print (c_name," - ",resistance,c)


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
		c_data = c_data.replace("{CAPACITANCE}",capacitance)
		#c_data = c_data.replace("{C_TOLERANCE}",tolerance)
		#c_data = c_data.replace("{C_DIELEC}",dielectric)
		c_data = c_data.replace("{DESCRIPTION}","%s, %s, %s, %s, %s, %s, %s"%(capacitance,tolerance,voltage,esr,lifetime,temperature,ripplecurrent))
		c_data = c_data.replace("{PNR}",pnr)
		c_data = c_data.replace("{MANUF}","Nichicon")
		c_data = c_data.replace("{FOOTPRINT}",footprint)


		f.write(c_data)


		dcm_data = dcm_template
		dcm_data = dcm_data.replace("{NAME}",c_name)
		dcm_data = dcm_data.replace("{DCM_DESC}","%s, %s, %s, %s, %s, %s, %s"%(capacitance,tolerance,voltage,esr,lifetime,temperature,ripplecurrent))
		f_dcm.write(dcm_data)

		comp_count = comp_count + 1



f.close()
f_dcm.close()

print ("Generated %i components!"%(comp_count))

#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import math

data = """LQG15HN1N0S02p 1.0nH±0.3nH 100MHz 300mA 0.10ohm 8 100MHz 6000MHz
LQG15HN1N1S02p 1.1nH±0.3nH 100MHz 300mA 0.10ohm 8 100MHz 6000MHz
LQG15HN1N2S02p 1.2nH±0.3nH 100MHz 300mA 0.10ohm 8 100MHz 6000MHz
LQG15HN1N3S02p 1.3nH±0.3nH 100MHz 300mA 0.10ohm 8 100MHz 6000MHz
LQG15HN1N5S02p 1.5nH±0.3nH 100MHz 300mA 0.10ohm 8 100MHz 6000MHz
LQG15HN1N6S02p 1.6nH±0.3nH 100MHz 300mA 0.10ohm 8 100MHz 6000MHz
LQG15HN1N8S02p 1.8nH±0.3nH 100MHz 300mA 0.10ohm 8 100MHz 6000MHz
LQG15HN2N0S02p 2.0nH±0.3nH 100MHz 300mA 0.12ohm 8 100MHz 6000MHz
LQG15HN2N2S02p 2.2nH±0.3nH 100MHz 300mA 0.15ohm 8 100MHz 6000MHz
LQG15HN2N4S02p 2.4nH±0.3nH 100MHz 300mA 0.16ohm 8 100MHz 6000MHz
LQG15HN2N7S02p 2.7nH±0.3nH 100MHz 300mA 0.17ohm 8 100MHz 6000MHz
LQG15HN3N0S02p 3.0nH±0.3nH 100MHz 300mA 0.18ohm 8 100MHz 6000MHz
LQG15HN3N3S02p 3.3nH±0.3nH 100MHz 300mA 0.19ohm 8 100MHz 6000MHz
LQG15HN3N6S02p 3.6nH±0.3nH 100MHz 300mA 0.19ohm 8 100MHz 6000MHz
LQG15HN3N9S02p 3.9nH±0.3nH 100MHz 300mA 0.19ohm 8 100MHz 6000MHz
LQG15HN4N3S02p 4.3nH±0.3nH 100MHz 300mA 0.21ohm 8 100MHz 6000MHz
LQG15HN4N7S02p 4.7nH±0.3nH 100MHz 300mA 0.23ohm 8 100MHz 6000MHz
LQG15HN5N1S02p 5.1nH±0.3nH 100MHz 300mA 0.24ohm 8 100MHz 6000MHz
LQG15HN5N6S02p 5.6nH±0.3nH 100MHz 300mA 0.26ohm 8 100MHz 5300MHz
LQG15HN6N2S02p 6.2nH±0.3nH 100MHz 300mA 0.27ohm 8 100MHz 4300MHz
LQG15HN6N8J02p 6.8nH±5% 100MHz 300mA 0.29ohm 8 100MHz 4200MHz
LQG15HN7N5J02p 7.5nH±5% 100MHz 300mA 0.31ohm 8 100MHz 3900MHz
LQG15HN8N2J02p 8.2nH±5% 100MHz 300mA 0.33ohm 8 100MHz 3600MHz
LQG15HN9N1J02p 9.1nH±5% 100MHz 300mA 0.34ohm 8 100MHz 3400MHz
LQG15HN10NJ02p 10nH±5% 100MHz 300mA 0.35ohm 8 100MHz 3200MHz
LQG15HN12NJ02p 12nH±5% 100MHz 300mA 0.41ohm 8 100MHz 2800MHz
LQG15HN15NJ02p 15nH±5% 100MHz 300mA 0.46ohm 8 100MHz 2300MHz
LQG15HN18NJ02p 18nH±5% 100MHz 300mA 0.51ohm 8 100MHz 2100MHz
LQG15HN22NJ02p 22nH±5% 100MHz 300mA 0.58ohm 8 100MHz 1800MHz
LQG15HN27NJ02p 27nH±5% 100MHz 300mA 0.67ohm 8 100MHz 1600MHz
LQG15HN33NJ02p 33nH±5% 100MHz 200mA 0.67ohm 8 100MHz 1500MHz
LQG15HN39NJ02p 39nH±5% 100MHz 200mA 1.06ohm 8 100MHz 1200MHz
LQG15HN47NJ02p 47nH±5% 100MHz 200mA 1.15ohm 8 100MHz 1000MHz
LQG15HN56NJ02p 56nH±5% 100MHz 200mA 1.20ohm 8 100MHz 800MHz
LQG15HN68NJ02p 68nH±5% 100MHz 180mA 1.25ohm 8 100MHz 800MHz
LQG15HN82NJ02p 82nH±5% 100MHz 150mA 1.60ohm 8 100MHz 600MHz
LQG15HNR10J02p 100nH±5% 100MHz 150mA 1.60ohm 8 100MHz 600MHz
LQG15HNR12J02p 120nH±5% 100MHz 150mA 1.60ohm 8 100MHz 600MHz"""


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



f = open("Murata_LQG15HN_inductors.lib","w")
f_dcm = open("Murata_LQG15HN_inductors.dcm","w")
f.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8")
f_dcm.write("EESchema-DOCLIB  Version 2.0\n#encoding utf-8")


lines = data.splitlines()


for l in lines:
        field = l.split(" ")

        component_name = "XXX-invalid-XXX"
        if "LQG15HNR" in field[0]:
                component_name = field[0][8:10]+"0n"
        else:
                component_name = field[0][7:10].lower()
        value = field[1]
        current = field[3]
        dcr = field[4]
        q = field[5]
        sfr = field[7]

        description = "%s, %s, DCR:%s, Q:%s, SFR:%s"%(value,current,dcr,q,sfr)

        output = template
        output = output.replace("{NAME}","LQG15HN_%s"%(component_name))
        output = output.replace("{FOOTPRINT}","L0402")
        output = output.replace("{DESCRIPTION}",description)
        output = output.replace("{PNR}",field[0])
        output = output.replace("{MANUF}","Murata")
        output = output.replace("{INDUCTANCE}",value)
        f.write(output)

        dcm_output = dcm_template
        dcm_output = dcm_output.replace("{NAME}",component_name)
        dcm_output = dcm_output.replace("{DESCRIPTION}",description)
        f_dcm.write(dcm_output)
        
f.close()
f_dcm.close()
        

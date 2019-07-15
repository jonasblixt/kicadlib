#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Called by .git/hooks/pre-commit

import glob
import re
import time
import sys

# #
# # C01005_100p_6.3Vdc_CH
# #
# DEF C01005_100p_6.3Vdc_CH C 0 10 N Y 1 F N
# F0 "C" 0 150 39 H V L CNN
# F1 "C01005_100p_6.3Vdc_CH" 6 -85 40 H I L CNN
# F2 "C01005" 38 -150 30 H I C CNN
# F3 "~" 0 0 60 H V C CNN
# F4 "100pF, 6.3Vdc, ±2%, CH" 100 200 60 H I C CNN "Description"
# F5 "GRM0222C0J101GA02" 100 200 60 H I C CNN "Part Number"
# F6 "Murata" 100 200 60 H I C CNN "Manufacturer"
# F7 "100pF" 100 100 39 H V C CNN "Capacitance"
# $FPLIST
# C01005
# $ENDFPLIST
# DRAW
# P 2 0 1 20  -80 -30  80 -30 N
# P 2 0 1 20  -80 30  80 30 N
# X ~ 1 0 200 170 D 40 40 1 1 P
# X ~ 2 0 -200 170 U 40 40 1 1 P
# ENDDRAW
# ENDDEF


FIELD_DESIGNATOR = '0'
FIELD_NAME       = '1'
FIELD_FOOTPRINT  = '2'
FIELD_RES0       = '3'
FIELD_DESC       = '4'
FIELD_PN         = '5'
FIELD_MANUF      = '6'
FIELD_VALUE      = '7'


r_field = re.compile("^F([0-9]{1})\ \"(.+)\"\ ([\-0-9]+)\ ([\-0-9]+)\ ([\-0-9]+)\ " +
    "([HV]{1})\ ([IV]{1})\ ([CLRTB]{1})\ ([CLRTB]{1})([IN]{1})([BN]{1})" +
    "\ ?\"?([a-zA-Z0-9\ ]+)?\"?")

def process_component(comp_data):
    comp_name = comp_data[0].split(' ')[1]
    comp_footprint = ''
    result = True
    has_manufacturer = False
    manufacturer_string = ""
    has_parnumber = False
    partnumber_string = ""

    # Process field F0 - F7
    fields = {}
    fields['0'] = ''
    fields['1'] = ''
    fields['2'] = ''
    fields['3'] = ''
    fields['4'] = ''
    fields['5'] = ''
    fields['6'] = ''
    fields['7'] = ''


    for l in comp_data:
        result = r_field.match(l)
        if result:
            fields[result.group(1)] = result.group(2)
            if result.group(12) == "Manufacturer":
                has_manufacturer = True
                manufacturer_string = result.group(2)
            if result.group(12) == "Part Number":
                has_partnumber = True
                partnumber_string = result.group(2)


    if (len(manufacturer_string) == 0) or (not has_manufacturer):
        print (fields[FIELD_NAME] + ": No manufacturer defined")
        result = False

    if (len(partnumber_string) == 0) or (not has_partnumber):
        print (fields[FIELD_NAME] + ": No partnumber defined")
        result = False

    if fields[FIELD_DESIGNATOR] == '#PWR':
        return True

    if len(fields[FIELD_FOOTPRINT]) == 0:
        print(fields[FIELD_NAME] + ": No footprint")
        result = False

    return result

def process_library(fn_lib):
    f = open(fn_lib, 'r')
    data = f.readlines()
    f.close()

    error_count = 0
    component_count = 0

    comp_data = []
    for l in data:
        if l.startswith('DEF '):
            component_count = component_count + 1
            comp_data = []
        comp_data.append(l)

        if l.startswith('ENDDEF'):
            component_count = component_count + 1
            if process_component(comp_data) == False:
                error_count = error_count + 1

    return error_count, component_count

if __name__ == "__main__":
    print ("Library check")
    error_count = 0
    component_count = 0

    for fn in glob.glob('./library/*.lib'):
        print ("Checking "+fn)
        errors, components = process_library(fn)
        error_count = error_count + errors
        component_count = component_count + components

    print ("Finished, checked %i components, found %i errors"%(component_count,error_count))

    sys.exit(error_count)

#!/usr/bin/env python3

import glob
import re
import time

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
ERROR_LIMIT = 100

r_field = re.compile("^F([0-9]{1})\ \"(.+)\"\ ([0-9]+)\ ([0-9]+)\ ([0-9]+)\ " +
	"([HV]{1})\ ([IV]{1})\ ([CLRTB]{1})\ ([CLRTB]{1})([IN]{1})([BN]{1})" +
	"\ ?\"?([a-zA-Z0-9\ ]+)?\"?")

def process_component(comp_data):
	comp_name = comp_data[0].split(' ')[1]
	fields = {}
	for l in comp_data:
		result = r_field.match(l)
		if result:
			print (result.group(1))
	time.sleep(1)
	return True

def process_library(fn_lib):
	f = open(fn_lib, 'r')
	data = f.readlines()
	f.close()

	component_count = 0
	error_count = 0

	comp_data = []
	for l in data:
		print (l)
		if l.startswith('DEF '):
			component_count = component_count + 1
			comp_data = []
		comp_data.append(l)

		if l.startswith('ENDDEF'):
			if not process_component(comp_data):
				error_count = error_count + 1
		if error_count > ERROR_LIMIT:
			print ("Too many errors stopping...")
			break

if __name__ == "__main__":
	print ("Library check")

	for fn in glob.glob('./library/*.lib'):
		print ("Checking "+fn)
		process_library(fn)

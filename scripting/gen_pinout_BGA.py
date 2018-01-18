
# X GND C1 -200 1600 200 R 50 50 1 1 I
# X GND C2 -200 1500 200 R 50 50 1 1 I
# X GND C3 300 1600 200 R 50 50 1 1 I
# X GND C4 300 1500 200 R 50 50 1 1 I

# +500 i x-led
# +100 i y-led


x = 0
y = 0


data="""1 2 3 4 5 6 7 8 9
A VDDQ DQU5 DQU7 DQU4 VDDQ VSS
B VSSQ VDD VSS DQSU# DQU6 VSSQ
C VDDQ DQU3 DQU1 DQSU DQU2 VDDQ
D VSSQ VDDQ DMU DQU0 VSSQ VDD
E VSS VSSQ DQL0 DML VSSQ VDDQ
F VDDQ DQL2 DQSL DQL1 DQL3 VSSQ
G VSSQ DQL6 DQSL# VDD VSS VSSQ
H VREFDQ VDDQ DQL4 DQL7 DQL5 VDDQ
J ODT1 VSS RAS# CK VSS CKE1
K ODT0 VDD CAS# CK# VDD CKE0
L CS1# CS0# WE# A10/AP ZQ0 ZQ1
M VSS BA0 BA2 NC VREFCA VSS
N VDD A3 A0 A12/BC# BA1 VDD
P VSS A5 A2 A1 A4 VSS
R VDD A7 A9 A11 A6 VDD
T VSS RESET# A13 A14 A8 VSS"""

i = 0
for l in data.splitlines()[1:]:
	
	r = l.split(' ')

	bn = r[0]

	xc = [1,2,3,7,8,9]
	xn = 0
	for n in r[1:]:
		y = y + 100
		#print ("%s%i - %s"%(bn,x[xn],n))
		pin = "%s%i"%(bn,xc[xn])
		print ("X %s %s %i %i 200 R 50 50 1 1 B"%(n,pin,x,y))		
		xn = xn + 1
		if (y > 1000):
			x = x + 500
			y = 0

	#y = y + 100

	#print ("X %s %s %i %i 200 R 50 50 1 1 B"%(name,pin,x,y))

	#if (y > 1000):
	#	x = x + 500
	#	y = 0	

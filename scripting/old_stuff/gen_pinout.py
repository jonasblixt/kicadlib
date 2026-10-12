import re
import sys

f = open(sys.argv[1])
pinout_data = f.readlines()
f.close()

# X GND C1 -200 1600 200 R 50 50 1 1 I
# X GND C2 -200 1500 200 R 50 50 1 1 I
# X GND C3 300 1600 200 R 50 50 1 1 I
# X GND C4 300 1500 200 R 50 50 1 1 I

# +500 i x-led
# +100 i y-led

r = re.compile ("^([A-Z0-9]+)\ +([A-Z0-9_]+).+")
x = 0
y = 0


for l in pinout_data:
    m = r.match(l)

    if not m:
        # print("Ignoring line '%s'" %(l))
        continue

    y = y + 100

    pin = m.group(1)
    name = m.group(2)
    subpart = 1

#    if "POWER" in l:
#        subpart = 2
#    if "ddr" in l:
#        subpart = 3
#    if "GND" in l:
#        subpart = 2

    print ("X %s %s %i %i 200 R 50 50 %i 1 B"%(name,pin,x,y,subpart))

    if (y > 1000):
        x = x + 500
        y = 0

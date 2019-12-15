# -*- coding: utf-8 -*-

import kicad
import model
from stackups import JLCPCB6Layers
from dram import lp4

if __name__ == "__main__":

    pcb = kicad.KicadPCB("test.kicad_pcb", JLCPCB6Layers())



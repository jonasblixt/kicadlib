# -*- coding: utf-8 -*-
import math

class Net(object):
    def __init__(self, index, name):
        self.index = index
        self.name = name
        self.length = 0.0
        self.segments = []
        self.vias = []
    def add_segment(self, seg):
        self.segments.append(seg)
        self.length += math.sqrt(math.pow(seg.ex - seg.sx, 2) + \
                                 math.pow(seg.ey - seg.sy, 2))
    def add_via(self, via):
        self.vias.append(via)
    def via_count(self):
        return len(self.vias)
    def length(self):
        return self.length

class Segment(object):
    def __init__(self, sx, sy, ex, ey, w, layer_str):
        self.sx = sx
        self.sy = sy
        self.ex = ex
        self.ey = ey
        self.w = w
        self.layer_str = layer_str

class Via(object):
    def __init__(self, x, y, dia, drill, start_layer, stop_layer, net_id):
        self.x = x
        self.y = y
        self.dia = dia
        self.drill = drill
        self.start_layer = start_layer
        self.stop_layer = stop_layer
        self.net_id = net_id

class Layer(object):
    def __init__(self, layer_idx, thickness, er, kind):
        self.thickness = thickness
        self.layer_idx = layer_idx
        self.er = er
        self.kind = kind
    def get_thickness(self):
        return self.thickness
    def get_er(self):
        return self.er
    def get_index(self):
        return self.layer_idx

class Stackup(object):
    def __init__(self, name="Generic"):
        self.name = name
        self.layers_by_name = {}
        self.layers_by_index = {}
        self.layers = []
        self.er = 4.0
        self.cu_layer_count = 1
    def get_name(self):
        return self.name
    def add_cu_layer(self, thickness, layer_mapping_str):
        l = Layer(self.cu_layer_count, thickness, self.er, "Cu")
        self.layers_by_name[layer_mapping_str] = l
        self.layers_by_index[self.cu_layer_count] = l
        self.layers.append(l)
        self.cu_layer_count += 1
        return l
    def add_pp_layer(self, thickness):
        self.layers.append(Layer(-1, thickness, -1.0, "pp"))
    def add_core_layer(self, thickness):
        self.layers.append(Layer(-1, thickness, -1.0, "core"))
    def get_layers(self):
        return self.layers
    def get_layer_by_index(self, idx):
        return self.layers_by_index[idx]
    def get_layer_by_name(self, name):
        return self.layers_by_name[name]
    def distance_from_to_layer(self, l1, l2):
        dist = 0.0
        start_measure = False
        i = 0

        while True:
            l = self.layers[i]
            if l.layer_idx == l2:
                break
            if start_measure:
                dist += l.thickness
            if l.layer_idx == l1:
                start_measure = True
            i = i + 1
        return dist

class PCB(object):
    def __init__(self, stackup):
        self.pcb_thickness = -1.0
        self.stackup = stackup
        self.nets = {}
    def add_segment(self, net_idx, seg):
        net = self.nets[net_idx]
        net.add_segment(seg)
    def add_net(self, name, net):
        self.nets[name] = net
    def add_via(self, net_idx, via):
        net = self.nets[net_idx]
        net.add_via(via)
    def process(self):
        assert(self.pcb_thickness > 0.0)
        assert(len(self.nets.keys()) > 0)

        # Calculate distance added by via's
        for n in self.nets.keys():
            net = self.nets[n]
            for v in net.vias:
                segs = []
                for s in net.segments:
                    if (v.x == s.sx and v.y == s.sy) or \
                       (v.x == s.ex and v.y == s.ey):
                        segs.append(s)
                if len(segs) > 1:
                    l_start = self.stackup.get_layer_by_name(segs[0].layer_str)
                    l_end = self.stackup.get_layer_by_name(segs[1].layer_str)
                    net.length += \
                        self.stackup.distance_from_to_layer(l_start.layer_idx,
                                                            l_end.layer_idx)

        print("Found %u nets"%(len(self.nets.keys())))

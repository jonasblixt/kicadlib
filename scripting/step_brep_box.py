# Minimal STEP AP214 B-Rep box generator for KiCad footprint 3D models.
#
# WHY THIS EXISTS: footprints/Murata_GA3.3dshapes/C_Murata_GA3_5.7x2.8.step
# was hand-authored using CSG primitives (BLOCK + CSG_SOLID entities, from
# ISO 10303-42's constructive-solid-geometry schema) wrapped in a plain
# SHAPE_REPRESENTATION. That's valid STEP syntax, but KiCad's underlying
# STEP importer (OpenCASCADE's STEPControl reader) does not support that
# corner of the standard - it expects boundary-representation solids
# (MANIFOLD_SOLID_BREP / ADVANCED_BREP_SHAPE_REPRESENTATION), which is
# what every real CAD-exported STEP file uses and what the repo's
# Panasonic_ECHU 3D models already correctly use. That mismatch is why
# KiCad fails to load C_Murata_GA3_5.7x2.8.step.
#
# This generator emits proper B-Rep rectangular boxes (8 vertices, 12
# edges, 6 planar quad faces per box, wrapped in a CLOSED_SHELL +
# MANIFOLD_SOLID_BREP), following the exact same topology pattern already
# proven to load correctly in the Panasonic_ECHU models - so any part
# that can be approximated as a small stack of boxes (chip components,
# simple pad-land + body shapes) can reuse this instead of CSG_SOLID.
# Boxes are CORNER-anchored (position = one corner, size = extent along
# +X/+Y/+Z), matching the corner/size convention already used by the
# Murata GA3 footprint's original (broken) BLOCK definitions, so the
# actual part geometry (position/size numbers) doesn't need to change -
# only the STEP entity type they're expressed with.
import re


class StepWriter:
    def __init__(self):
        self.lines = []
        self.next_id = 1

    def add(self, expr):
        """Add one entity, return its #id."""
        eid = self.next_id
        self.next_id += 1
        self.lines.append(f"#{eid}={expr};")
        return eid

    def point(self, xyz):
        x, y, z = xyz
        return self.add(f"CARTESIAN_POINT('',({x:.6f},{y:.6f},{z:.6f}))")

    def direction(self, xyz):
        x, y, z = xyz
        return self.add(f"DIRECTION('',({x:.6f},{y:.6f},{z:.6f}))")

    def axis2(self, origin_id, axis_id, ref_id):
        return self.add(f"AXIS2_PLACEMENT_3D('',#{origin_id},#{axis_id},#{ref_id})")

    def vertex(self, xyz):
        p = self.point(xyz)
        return self.add(f"VERTEX_POINT('',#{p})")

    def line_edge(self, v1_id, v1_xyz, v2_id, v2_xyz):
        """Straight EDGE_CURVE from vertex v1 to v2 (both already created)."""
        dx = v2_xyz[0] - v1_xyz[0]
        dy = v2_xyz[1] - v1_xyz[1]
        dz = v2_xyz[2] - v1_xyz[2]
        length = (dx * dx + dy * dy + dz * dz) ** 0.5
        d = self.direction((dx / length, dy / length, dz / length))
        vec = self.add(f"VECTOR('',#{d},{length:.6f})")
        p1 = self.point(v1_xyz)
        line = self.add(f"LINE('',#{p1},#{vec})")
        return self.add(f"EDGE_CURVE('',#{v1_id},#{v2_id},#{line},.T.)")

    def oriented(self, edge_id, sense):
        s = ".T." if sense else ".F."
        return self.add(f"ORIENTED_EDGE('',*,*,#{edge_id},{s})")

    def planar_face(self, loop_edges, plane_origin_xyz, plane_normal_xyz, plane_ref_xyz):
        edge_loop = self.add(f"EDGE_LOOP('',({','.join('#' + str(e) for e in loop_edges)}))")
        bound = self.add(f"FACE_OUTER_BOUND('',#{edge_loop},.T.)")
        o = self.point(plane_origin_xyz)
        n = self.direction(plane_normal_xyz)
        r = self.direction(plane_ref_xyz)
        ax = self.axis2(o, n, r)
        plane = self.add(f"PLANE('',#{ax})")
        return self.add(f"ADVANCED_FACE('',(#{bound}),#{plane},.T.)")

    def box(self, corner, size, rgb):
        """Corner-anchored box: corner=(x,y,z) is the min corner, size=(dx,dy,dz)
        extends in +X/+Y/+Z. Returns the #id of its MANIFOLD_SOLID_BREP."""
        x0, y0, z0 = corner
        dx, dy, dz = size
        # 8 corners of the box
        pts = {
            "000": (x0, y0, z0), "100": (x0 + dx, y0, z0),
            "010": (x0, y0 + dy, z0), "110": (x0 + dx, y0 + dy, z0),
            "001": (x0, y0, z0 + dz), "101": (x0 + dx, y0, z0 + dz),
            "011": (x0, y0 + dy, z0 + dz), "111": (x0 + dx, y0 + dy, z0 + dz),
        }
        v = {k: self.vertex(xyz) for k, xyz in pts.items()}

        def edge(a, b):
            key = (a, b)
            if key not in edges:
                eid = self.line_edge(v[a], pts[a], v[b], pts[b])
                edges[key] = eid
                edges[(b, a)] = eid
            return edges[key]

        edges = {}

        # 6 faces, each a quad loop of 4 oriented edges walked
        # counter-clockwise when viewed from outside the box.
        faces = []
        # -Z (bottom, z=z0), viewed from below -> normal (0,0,-1)
        loop = [self.oriented(edge("000", "100"), True),
                self.oriented(edge("100", "110"), True),
                self.oriented(edge("110", "010"), True),
                self.oriented(edge("010", "000"), True)]
        faces.append(self.planar_face(loop, pts["000"], (0, 0, -1), (1, 0, 0)))
        # +Z (top, z=z0+dz)
        loop = [self.oriented(edge("001", "011"), True),
                self.oriented(edge("011", "111"), True),
                self.oriented(edge("111", "101"), True),
                self.oriented(edge("101", "001"), True)]
        faces.append(self.planar_face(loop, pts["001"], (0, 0, 1), (1, 0, 0)))
        # -Y (front, y=y0)
        loop = [self.oriented(edge("000", "001"), True),
                self.oriented(edge("001", "101"), True),
                self.oriented(edge("101", "100"), True),
                self.oriented(edge("100", "000"), True)]
        faces.append(self.planar_face(loop, pts["000"], (0, -1, 0), (1, 0, 0)))
        # +Y (back, y=y0+dy)
        loop = [self.oriented(edge("010", "110"), True),
                self.oriented(edge("110", "111"), True),
                self.oriented(edge("111", "011"), True),
                self.oriented(edge("011", "010"), True)]
        faces.append(self.planar_face(loop, pts["010"], (0, 1, 0), (1, 0, 0)))
        # -X (left, x=x0)
        loop = [self.oriented(edge("000", "010"), True),
                self.oriented(edge("010", "011"), True),
                self.oriented(edge("011", "001"), True),
                self.oriented(edge("001", "000"), True)]
        faces.append(self.planar_face(loop, pts["000"], (-1, 0, 0), (0, 1, 0)))
        # +X (right, x=x0+dx)
        loop = [self.oriented(edge("100", "101"), True),
                self.oriented(edge("101", "111"), True),
                self.oriented(edge("111", "110"), True),
                self.oriented(edge("110", "100"), True)]
        faces.append(self.planar_face(loop, pts["100"], (1, 0, 0), (0, 1, 0)))

        shell = self.add(f"CLOSED_SHELL('',({','.join('#' + str(f) for f in faces)}))")
        solid = self.add(f"MANIFOLD_SOLID_BREP('',#{shell})")
        return solid, rgb

    def style_item(self, solid_id, rgb):
        r, g, b = rgb
        colour = self.add(f"COLOUR_RGB('',{r:.3f},{g:.3f},{b:.3f})")
        fasc = self.add(f"FILL_AREA_STYLE_COLOUR('',#{colour})")
        fas = self.add(f"FILL_AREA_STYLE('',(#{fasc}))")
        ssfa = self.add(f"SURFACE_STYLE_FILL_AREA(#{fas})")
        sss = self.add(f"SURFACE_SIDE_STYLE('',(#{ssfa}))")
        ssu = self.add(f"SURFACE_STYLE_USAGE(.BOTH.,#{sss})")
        psa = self.add(f"PRESENTATION_STYLE_ASSIGNMENT((#{ssu}))")
        return self.add(f"STYLED_ITEM('colour',(#{psa}),#{solid_id})")


def write_step_boxes(path, product_name, boxes, description=""):
    """boxes: list of (corner_xyz, size_xyz, rgb) tuples. Writes a valid
    ADVANCED_BREP_SHAPE_REPRESENTATION STEP file with one manifold solid
    brep box per entry, matching the topology KiCad's OCCT-based STEP
    importer already loads correctly elsewhere in this repo."""
    w = StepWriter()
    solids = []
    for corner, size, rgb in boxes:
        solid_id, rgb = w.box(corner, size, rgb)
        solids.append((solid_id, rgb))

    origin_pt = w.point((0.0, 0.0, 0.0))
    z_dir = w.direction((0.0, 0.0, 1.0))
    x_dir = w.direction((1.0, 0.0, 0.0))
    origin_ax = w.axis2(origin_pt, z_dir, x_dir)

    length_unit = w.add("( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) )")
    angle_unit = w.add("( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) )")
    solid_angle_unit = w.add("( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() )")
    uncertainty = w.add(
        f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),#{length_unit},"
        "'distance_accuracy_value','confusion accuracy')")
    rep_ctx = w.add(
        f"( GEOMETRIC_REPRESENTATION_CONTEXT(3) "
        f"GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{uncertainty})) "
        f"GLOBAL_UNIT_ASSIGNED_CONTEXT((#{length_unit},#{angle_unit},#{solid_angle_unit})) "
        f"REPRESENTATION_CONTEXT('','3D') )")

    app_ctx = w.add("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
    app_proto = w.add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{app_ctx})")
    pd_ctx = w.add(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{app_ctx},'design')")
    prod_ctx = w.add(f"PRODUCT_CONTEXT('',#{app_ctx},'mechanical')")
    product = w.add(f"PRODUCT('{product_name}','{product_name}','{description}',(#{prod_ctx}))")
    pdf = w.add(f"PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE('','',#{product},.NOT_KNOWN.)")
    pd = w.add(f"PRODUCT_DEFINITION('design','',#{pdf},#{pd_ctx})")
    pds = w.add(f"PRODUCT_DEFINITION_SHAPE('','',#{pd})")

    solid_ref_list = ",".join("#" + str(s) for s, _ in solids)
    abr = w.add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('{product_name}',(#{origin_ax},{solid_ref_list}),#{rep_ctx})")
    sdr = w.add(f"SHAPE_DEFINITION_REPRESENTATION(#{pds},#{abr})")
    w.add(f"PRODUCT_RELATED_PRODUCT_CATEGORY('part','',(#{product}))")

    styled = [w.style_item(s, rgb) for s, rgb in solids]
    styled_list = ",".join("#" + str(s) for s in styled)
    w.add(f"MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({styled_list}),#{rep_ctx})")

    header = (
        "ISO-10303-21;\n"
        "HEADER;\n"
        f"FILE_DESCRIPTION(('{description}'),'2;1');\n"
        f"FILE_NAME('{product_name}.step','2026-08-27T00:00:00',('Claude'),"
        "('Vishay Murata GA3 KiCad library'),'','','');\n"
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 3 1 4 }'));\n"
        "ENDSEC;\nDATA;\n"
    )
    footer = "ENDSEC;\nEND-ISO-10303-21;\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(w.lines))
        f.write("\n")
        f.write(footer)

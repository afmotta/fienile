"""
FIENILE - Piano terra, open space cucina/pranzo/soggiorno (14 x 4.5 m)
Genera la scena in Blender (testato su 5.0) e renderizza le varianti di materiali.

Uso:
  blender -b -P fienile_pt_render.py -- --out ./render
  blender -b -P fienile_pt_render.py -- --out ./render --preset rovere_calce --scene giorno --camera C1_ovest
  blender -b -P fienile_pt_render.py -- --preview          (bassa risoluzione, pochi campioni)
  blender    -P fienile_pt_render.py -- --build-only       (apre la scena per navigarla, niente render)
  blender -b -P fienile_pt_render.py -- --no-roof --no-p1   (nasconde falda del portico e/o primo piano)

Coordinate in metri. Origine = angolo interno sud-ovest del soggiorno (X verso est, Y verso nord).
Misure ricavate dal DWG "FIENILE_260430_post_rilievo" (piano terra), arredi segnaposto.
"""
import bpy, math, sys, os, argparse
from mathutils import Vector

# ----------------------------------------------------------------------------
# PARAMETRI GEOMETRICI (dal rilievo, in metri)
# ----------------------------------------------------------------------------
ROOM_X = 13.90          # lunghezza interna soggiorno
ROOM_Y = 4.50           # profondità interna
H_CEIL = 2.70           # altezza interna piano terra (da sezione)
H_GLASS = 2.45          # altezza vetrate a sud (da sezione)
W_EXT = 0.70            # spessore muri perimetrali in pietra (ovest/est)
NORTH_WALL = (4.50, 4.85)            # muro nord del soggiorno (Y da-a)
NORTH_OPENING = (8.50, 10.20)        # varco verso ingresso/scala (X da-a)
SOUTH_PIERS = [(-0.10, 1.20), (2.90, 3.75), (6.65, 7.35), (10.25, 11.10), (12.80, 13.90)]
SOUTH_Y = (-0.45, 0.05)              # profondità pilastri facciata sud
GLASS_Y = -0.15
CENTRAL_PIER = (6.55, 1.60, 7.30, 2.35)   # pilastro isolato nel soggiorno
PORTICO_DEPTH = 3.60                 # filo esterno pilastri portico
PORTICO_PIERS = [(-0.70, 0.00), (6.70, 7.30), (14.10, 14.80)]
ROOF_Z_WALL, ROOF_Z_EAVE, ROOF_Y_EAVE = 6.30, 4.50, -4.80
NORTH_ZONE_Y = 10.20                 # filo interno muro nord dell'edificio

# ----------------------------------------------------------------------------
# PRESET MATERIALI  (aggiungine quanti vuoi)
# ----------------------------------------------------------------------------
PRESETS = {
    "rovere_calce": dict(floor="rovere_naturale", walls="calce_bianca", stone="pietra",
                         ceiling="travi_rovere", kitchen="laccato_bianco", sofa="lino_sabbia"),
    "resina_intonaco": dict(floor="resina_grigia", walls="intonaco_bianco", stone="intonaco_bianco",
                            ceiling="intonaco_bianco", kitchen="rovere_fronti", sofa="tessuto_antracite"),
    "cotto_salvia": dict(floor="cotto", walls="calce_calda", stone="pietra",
                         ceiling="travi_scure", kitchen="verde_salvia", sofa="velluto_ruggine"),
}
SCENES = ["giorno", "sera"]
CAMERAS = {  # nome: (posizione, punto guardato, focale mm)
    "C1_ovest":   ((0.50, 4.20, 1.60), (11.0, 2.2, 1.00), 18),
    "C2_est":     ((13.55, 0.55, 1.55), (1.0, 3.2, 1.05), 18),
    "C3_varco":   ((9.30, 4.35, 1.50), (4.5, -2.5, 1.00), 16),
    "C4_portico": ((3.30, -2.60, 1.55), (9.0, 3.5, 1.20), 20),
}

# ----------------------------------------------------------------------------
# UTILITÀ
# ----------------------------------------------------------------------------
COLL = None
ROLE_OBJS = {}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global COLL
    COLL = bpy.data.collections.new("Fienile_PT")
    bpy.context.scene.collection.children.link(COLL)

def box(name, x0, y0, z0, x1, y1, z1, role):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return mesh(name, v, f, role)

def mesh(name, v, f, role):
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    ob = bpy.data.objects.new(name, me); COLL.objects.link(ob)
    ob["role"] = role; ROLE_OBJS.setdefault(role, []).append(ob)
    return ob

def set_role_material(role, mat):
    for ob in ROLE_OBJS.get(role, []):
        ob.data.materials.clear(); ob.data.materials.append(mat)

# ----------------------------------------------------------------------------
# MATERIALI PROCEDURALI (nessuna texture esterna necessaria)
# ----------------------------------------------------------------------------
def new_mat(name):
    m = bpy.data.materials.get(name)
    if m: return m, None
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    return m, (nt, p)

def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items(): setattr(n, k, v)
    return n

def mix(nt, blend="MIX", fac=0.5):
    n = nt.nodes.new("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = blend
    en = [s for s in n.inputs if s.enabled]
    en[0].default_value = fac
    return n, en[0], en[1], en[2], [o for o in n.outputs if o.enabled][0]

def coords(nt, scale=(1,1,1), rot=(0,0,0)):
    tc = node(nt, "ShaderNodeTexCoord"); mp = node(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale; mp.inputs["Rotation"].default_value = rot
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); return mp.outputs["Vector"]

def bump(nt, height_socket, p, strength=0.1, dist=0.01):
    b = node(nt, "ShaderNodeBump"); b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = dist
    nt.links.new(height_socket, b.inputs["Height"]); nt.links.new(b.outputs["Normal"], p.inputs["Normal"])

def rgb(h):
    h = h.lstrip("#"); c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(((x+0.055)/1.055)**2.4 if x > 0.04045 else x/12.92 for x in c) + (1.0,)

def m_plaster(name, color, rough=0.92, grain=0.04):
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    p.inputs["Base Color"].default_value = rgb(color); p.inputs["Roughness"].default_value = rough
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 8
    nt.links.new(coords(nt), nz.inputs["Vector"]); bump(nt, nz.outputs["Fac"], p, grain, 0.02)
    # leggera variazione tono (effetto calce)
    nz2 = node(nt, "ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 1.5
    nt.links.new(coords(nt), nz2.inputs["Vector"])
    mx, f, a, b, o = mix(nt, "MULTIPLY", 0.12)
    a.default_value = rgb(color); nt.links.new(nz2.outputs["Color"], b); nt.links.new(o, p.inputs["Base Color"])
    return m

def m_simple(name, color, rough=0.5, metal=0.0, sheen=0.0, coat=0.0):
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    p.inputs["Base Color"].default_value = rgb(color); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal; p.inputs["Sheen Weight"].default_value = sheen
    p.inputs["Coat Weight"].default_value = coat
    return m

def m_wood(name, light, dark, plank_w=0.19, plank_l=1.8, rough=0.45, planks=True, grain_dir="X"):
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    sc = (1, 1, 1) if grain_dir == "X" else (1, 1, 1)
    rot = (0, 0, 0) if grain_dir == "X" else (0, 0, math.pi/2)
    vec = coords(nt, sc, rot)
    # venatura parallela alla lunghezza della doga (asse X locale)
    wave = node(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    wave.inputs["Scale"].default_value = 5.0; wave.inputs["Distortion"].default_value = 4.0
    wave.inputs["Detail"].default_value = 3; wave.inputs["Detail Scale"].default_value = 0.8
    mpv = node(nt, "ShaderNodeMapping"); mpv.inputs["Scale"].default_value = (0.08, 1.0, 1.0)
    nt.links.new(vec, mpv.inputs["Vector"]); nt.links.new(mpv.outputs["Vector"], wave.inputs["Vector"])
    ramp = node(nt, "ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = rgb(dark); ramp.color_ramp.elements[1].color = rgb(light)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    if planks:
        br = node(nt, "ShaderNodeTexBrick", offset=0.37, offset_frequency=1)
        br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = plank_l
        br.inputs["Row Height"].default_value = plank_w; br.inputs["Mortar Size"].default_value = 0.0015
        br.inputs["Bias"].default_value = 0.0
        br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0.78, 0.74, 0.70, 1)
        br.inputs["Mortar"].default_value = (0.25, 0.22, 0.2, 1)
        nt.links.new(vec, br.inputs["Vector"])
        mx, f, a, b, o = mix(nt, "MULTIPLY", 1.0)
        nt.links.new(col, a); nt.links.new(br.outputs["Color"], b); col = o
        bump(nt, br.outputs["Fac"], p, 0.25, 0.003)
    nt.links.new(col, p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    return m

def m_resin(name, color):
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.8; nz.inputs["Detail"].default_value = 4
    nt.links.new(coords(nt), nz.inputs["Vector"])
    mx, f, a, b, o = mix(nt, "OVERLAY", 0.18)
    a.default_value = rgb(color); nt.links.new(nz.outputs["Color"], b); nt.links.new(o, p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.32; p.inputs["Coat Weight"].default_value = 0.4
    return m

def m_tiles(name, c1, c2, joint="#b9b2a6", size=0.30, rough=0.7):
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    br = node(nt, "ShaderNodeTexBrick", offset=0.0, offset_frequency=1)
    br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = size
    br.inputs["Row Height"].default_value = size; br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = rgb(c1); br.inputs["Color2"].default_value = rgb(c2)
    br.inputs["Mortar"].default_value = rgb(joint)
    nt.links.new(coords(nt), br.inputs["Vector"])
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 25
    nt.links.new(coords(nt), nz.inputs["Vector"])
    mx, f, a, b, o = mix(nt, "OVERLAY", 0.25)
    nt.links.new(br.outputs["Color"], a); nt.links.new(nz.outputs["Color"], b)
    nt.links.new(o, p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    bump(nt, br.outputs["Fac"], p, 0.3, 0.004)
    return m

def m_stone(name, c1="#a89c89", c2="#6f665b", joint="#cfc6b6"):
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    v = coords(nt, (1, 1, 1.6))
    vo = node(nt, "ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE"); vo.inputs["Scale"].default_value = 4.5
    vo.inputs["Randomness"].default_value = 0.9
    vc = node(nt, "ShaderNodeTexVoronoi"); vc.inputs["Scale"].default_value = 4.5
    nt.links.new(v, vo.inputs["Vector"]); nt.links.new(v, vc.inputs["Vector"])
    ramp = node(nt, "ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = rgb(c2)
    ramp.color_ramp.elements[1].color = rgb(c1); nt.links.new(vc.outputs["Color"], ramp.inputs["Fac"])
    jr = node(nt, "ShaderNodeMapRange"); jr.inputs["From Min"].default_value = 0.0; jr.inputs["From Max"].default_value = 0.035
    nt.links.new(vo.outputs["Distance"], jr.inputs["Value"])
    mx, f, a, b, o = mix(nt, "MIX", 1.0)
    nt.links.new(jr.outputs["Result"], f); a.default_value = rgb(joint); nt.links.new(ramp.outputs["Color"], b)
    nt.links.new(o, p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.9
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30; nt.links.new(v, nz.inputs["Vector"])
    add = node(nt, "ShaderNodeMath", operation="MULTIPLY_ADD")
    nt.links.new(nz.outputs["Fac"], add.inputs[0]); add.inputs[1].default_value = 0.15
    nt.links.new(jr.outputs["Result"], add.inputs[2])
    bump(nt, add.outputs["Value"], p, 0.6, 0.03)
    return m

def m_glass():
    m, r = new_mat("vetro")
    if not r: return m
    nt, p = r
    p.inputs["Transmission Weight"].default_value = 1.0; p.inputs["Roughness"].default_value = 0.0
    p.inputs["IOR"].default_value = 1.45; p.inputs["Base Color"].default_value = (0.95, 0.98, 0.97, 1)
    # vetro "architettonico": per i raggi non di camera è trasparente, così la luce
    # naturale entra senza bisogno delle caustiche (render molto più veloce e pulito)
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    lp = node(nt, "ShaderNodeLightPath"); tr = node(nt, "ShaderNodeBsdfTransparent")
    ms = node(nt, "ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], ms.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], ms.inputs[1]); nt.links.new(p.outputs["BSDF"], ms.inputs[2])
    nt.links.new(ms.outputs["Shader"], out.inputs["Surface"])
    return m

def m_emit(name, kelvin=3000, strength=40):
    m = bpy.data.materials.get(name)
    if m:  # aggiorna solo l'intensità (giorno = spento, sera = acceso)
        [n for n in m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"].default_value = strength
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = node(nt, "ShaderNodeOutputMaterial"); em = node(nt, "ShaderNodeEmission")
    bb = node(nt, "ShaderNodeBlackbody"); bb.inputs["Temperature"].default_value = kelvin
    nt.links.new(bb.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"]); return m

LIB = {
    # pavimenti
    "rovere_naturale": lambda: m_wood("rovere_naturale", "#c9a57a", "#9c7650"),
    "rovere_fume":     lambda: m_wood("rovere_fume", "#8a6f57", "#5a4636"),
    "resina_grigia":   lambda: m_resin("resina_grigia", "#9c9a96"),
    "cotto":           lambda: m_tiles("cotto", "#b5663f", "#9a4f2e", size=0.30),
    "gres_cemento":    lambda: m_tiles("gres_cemento", "#a7a39c", "#9d9992", joint="#8f8b85", size=0.60, rough=0.6),
    # pareti / soffitti
    "intonaco_bianco": lambda: m_plaster("intonaco_bianco", "#eeebe5", grain=0.02),
    "calce_bianca":    lambda: m_plaster("calce_bianca", "#ece6db", grain=0.06),
    "calce_calda":     lambda: m_plaster("calce_calda", "#e3d3bc", grain=0.06),
    "pietra":          lambda: m_stone("pietra"),
    # soffitto con travi: il materiale è quello delle travi, il fondo resta intonaco
    "travi_rovere":    lambda: m_wood("travi_rovere", "#b58a5c", "#7d5a3a", planks=False, grain_dir="Y", rough=0.7),
    "travi_scure":     lambda: m_wood("travi_scure", "#6e513a", "#3f2c1f", planks=False, grain_dir="Y", rough=0.7),
    # cucina
    "laccato_bianco":  lambda: m_simple("laccato_bianco", "#f2f0ec", 0.35),
    "rovere_fronti":   lambda: m_wood("rovere_fronti", "#c19b70", "#936f4b", planks=False, grain_dir="Y", rough=0.5),
    "verde_salvia":    lambda: m_simple("verde_salvia", "#8f9e86", 0.45),
    # tessuti
    "lino_sabbia":     lambda: m_simple("lino_sabbia", "#cdbfa8", 0.9, sheen=0.5),
    "tessuto_antracite": lambda: m_simple("tessuto_antracite", "#4a4a4c", 0.9, sheen=0.5),
    "velluto_ruggine": lambda: m_simple("velluto_ruggine", "#9b4f2f", 0.8, sheen=1.0),
}
def mat(key): return LIB[key]()

# ----------------------------------------------------------------------------
# GEOMETRIA
# ----------------------------------------------------------------------------
def build():
    X, Y, H = ROOM_X, ROOM_Y, H_CEIL
    # solai
    box("pavimento", 0, 0, -0.02, X, Y, 0, "floor")
    box("pavimento_ingresso", NORTH_OPENING[0]-1.5, NORTH_WALL[1], -0.02, X, NORTH_ZONE_Y, 0, "floor")
    box("soffitto", -W_EXT, -0.45, H, X+W_EXT, NORTH_ZONE_Y, H+0.35, "ceiling_base")
    # muri perimetrali in pietra (ovest/est)
    box("muro_ovest", -W_EXT, -0.45, 0, 0, NORTH_ZONE_Y, H, "stone")
    box("muro_est", X, -0.45, 0, X+W_EXT, NORTH_ZONE_Y, H, "stone")
    box("muro_nord_edificio", -W_EXT, NORTH_ZONE_Y, 0, X+W_EXT, NORTH_ZONE_Y+0.6, H, "stone")
    # muro nord soggiorno con varco
    y0, y1 = NORTH_WALL
    box("muro_nord_a", 0, y0, 0, NORTH_OPENING[0], y1, H, "walls")
    box("muro_nord_b", NORTH_OPENING[1], y0, 0, X, y1, H, "walls")
    box("architrave_varco", NORTH_OPENING[0], y0, 2.20, NORTH_OPENING[1], y1, H, "walls")
    box("tramezzo_ingresso", NORTH_OPENING[0]-1.5, y1, 0, NORTH_OPENING[0]-1.35, NORTH_ZONE_Y, H, "walls")
    # facciata sud: pilastri, vetrate, trave
    for i, (a, b) in enumerate(SOUTH_PIERS):
        box(f"pilastro_sud_{i}", a, SOUTH_Y[0], 0, b, SOUTH_Y[1], H, "stone")
    box("trave_vetrate", -W_EXT, SOUTH_Y[0], H_GLASS, X+W_EXT, SOUTH_Y[1], H, "walls")
    for i in range(len(SOUTH_PIERS)-1):
        a, b = SOUTH_PIERS[i][1], SOUTH_PIERS[i+1][0]
        box(f"vetro_{i}", a, GLASS_Y-0.01, 0.02, b, GLASS_Y+0.01, H_GLASS-0.02, "glass")
        # telaio perimetrale + montante centrale
        for (xa, xb, za, zb) in [(a, b, 0, 0.05), (a, b, H_GLASS-0.05, H_GLASS), (a, a+0.05, 0, H_GLASS),
                                 (b-0.05, b, 0, H_GLASS), ((a+b)/2-0.025, (a+b)/2+0.025, 0, H_GLASS)]:
            box(f"telaio_{i}", xa, GLASS_Y-0.035, za, xb, GLASS_Y+0.035, zb, "frame")
    # pilastro centrale
    cx0, cy0, cx1, cy1 = CENTRAL_PIER
    box("pilastro_centrale", cx0, cy0, 0, cx1, cy1, H, "stone")
    # piano primo in facciata (massa) e portico
    box("facciata_p1", -W_EXT, SOUTH_Y[0], H, X+W_EXT, SOUTH_Y[1], ROOF_Z_WALL, "p1")
    box("pavimento_portico", -W_EXT, -PORTICO_DEPTH, -0.04, X+W_EXT, SOUTH_Y[0], -0.01, "portico_floor")
    for i, (a, b) in enumerate(PORTICO_PIERS):
        box(f"pilastro_portico_{i}", a, -PORTICO_DEPTH, 0, b, -PORTICO_DEPTH+0.7, ROOF_Z_EAVE+0.4, "exterior")
    # falda del portico (lastra inclinata)
    x0, x1 = -W_EXT-0.3, X+W_EXT+0.3
    v = [(x0, SOUTH_Y[0], ROOF_Z_WALL), (x1, SOUTH_Y[0], ROOF_Z_WALL), (x1, ROOF_Y_EAVE, ROOF_Z_EAVE), (x0, ROOF_Y_EAVE, ROOF_Z_EAVE)]
    v += [(a, b, c+0.25) for a, b, c in v]
    mesh("falda_portico", v, [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)], "roof")
    box("terreno", -40, -40, -0.06, 40, 40, -0.04, "ground")
    build_ceiling_beams()
    build_furniture()
    build_cove()

def build_ceiling_beams(step=0.60, w=0.12, h=0.18):
    x = 0.30
    while x < ROOM_X - 0.1:
        if not (CENTRAL_PIER[0]-0.05 < x < CENTRAL_PIER[2]+0.05):
            box("trave", x-w/2, 0, H_CEIL-h, x+w/2, ROOM_Y, H_CEIL, "beams")
        x += step
    box("trave_principale", CENTRAL_PIER[0], 0, H_CEIL-0.30, CENTRAL_PIER[2], ROOM_Y, H_CEIL-h, "beams")

def build_furniture():
    Hn = NORTH_WALL[0]
    # ---- cucina lineare lungo il muro nord (est del varco) + isola
    kx0, kx1 = NORTH_OPENING[1]+0.15, ROOM_X-0.05
    box("cucina_basi", kx0, Hn-0.62, 0.10, kx1, Hn, 0.88, "kitchen")
    box("cucina_zoccolo", kx0, Hn-0.57, 0, kx1, Hn, 0.10, "dark")
    box("cucina_top", kx0, Hn-0.64, 0.88, kx1, Hn, 0.92, "worktop")
    box("cucina_colonne", ROOM_X-1.25, Hn-0.62, 0, ROOM_X-0.05, Hn, 2.30, "kitchen")
    box("isola", 11.0, 1.70, 0.10, 13.2, 2.70, 0.88, "kitchen")
    box("isola_zoccolo", 11.05, 1.75, 0, 13.15, 2.65, 0.10, "dark")
    box("isola_top", 10.95, 1.65, 0.88, 13.25, 2.75, 0.92, "worktop")
    # ---- tavolo da pranzo + sedie (lato lungo perpendicolare alla facciata, come nel viewer 3D)
    tx0, ty0, tx1, ty1 = 8.55, 1.05, 9.55, 3.25
    box("tavolo_top", tx0, ty0, 0.72, tx1, ty1, 0.76, "table")
    for lx, ly in [(tx0+0.08, ty0+0.08), (tx1-0.13, ty0+0.08), (tx0+0.08, ty1-0.13), (tx1-0.13, ty1-0.13)]:
        box("gamba", lx, ly, 0, lx+0.05, ly+0.05, 0.72, "dark")
    for i in range(3):
        cy = ty0 + 0.35 + i*0.75
        for side, (xa, xb) in enumerate([(tx0-0.50, tx0-0.08), (tx1+0.08, tx1+0.50)]):
            box("sedia_seduta", xa, cy, 0.44, xb, cy+0.45, 0.48, "chair")
            bx = (xa, xa+0.04) if side == 0 else (xb-0.04, xb)
            box("sedia_schienale", bx[0], cy, 0.48, bx[1], cy+0.45, 0.85, "chair")
            for ly in (cy+0.02, cy+0.40):
                for lx in (xa+0.02, xb-0.05):
                    box("sedia_gamba", lx, ly, 0, lx+0.03, ly+0.03, 0.44, "dark")
    # ---- zona living (ovest): divano a L, tappeto, tavolino, mobile TV sulla parete ovest
    box("tappeto", 1.3, 0.9, 0, 4.2, 3.6, 0.012, "rug")
    sx0, sy0 = 3.25, 0.85
    box("divano_base", sx0, sy0, 0.10, sx0+0.95, sy0+2.60, 0.42, "sofa")
    box("divano_schienale", sx0+0.72, sy0, 0.42, sx0+0.95, sy0+2.60, 0.82, "sofa")
    box("divano_chaise", sx0-1.10, sy0+1.95, 0.10, sx0, sy0+2.60, 0.42, "sofa")
    box("divano_bracciolo", sx0, sy0, 0.42, sx0+0.72, sy0+0.20, 0.62, "sofa")
    box("tavolino", 1.85, 1.6, 0.0, 2.75, 2.4, 0.36, "table")
    box("mobile_tv", 0.02, 1.2, 0.0, 0.47, 3.4, 0.45, "table")
    box("tv", 0.05, 1.65, 1.0, 0.09, 2.95, 1.73, "dark")

def build_cove():
    # profilo LED a sguscio lungo il perimetro, 10 cm sotto il soffitto, luce verso l'alto
    z = H_CEIL - 0.22
    segs = [(0.05, 0.12, ROOM_X-0.05, 0.17), (0.05, ROOM_Y-0.17, NORTH_OPENING[0]-0.1, ROOM_Y-0.12),
            (0.05, 0.12, 0.10, ROOM_Y-0.12), (ROOM_X-0.10, 0.12, ROOM_X-0.05, ROOM_Y-0.12)]
    for (a, b, c, d) in segs:
        box("led_cove", a, b, z, c, d, z+0.012, "led")

# ----------------------------------------------------------------------------
# LUCI, CAMERE, RENDER
# ----------------------------------------------------------------------------
def world_and_sun(scene_kind):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("cielo") or bpy.data.worlds.new("cielo"); sc.world = w
    w.use_nodes = True; nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = node(nt, "ShaderNodeOutputWorld"); bg = node(nt, "ShaderNodeBackground")
    sky = node(nt, "ShaderNodeTexSky")
    for t in ("MULTIPLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try: sky.sky_type = t; break
        except Exception: pass
    el, az = (math.radians(28), math.radians(35)) if scene_kind == "giorno" else (math.radians(-4), math.radians(80))
    try:
        sky.sun_elevation = el; sky.sun_rotation = math.radians(180) + az; sky.sun_disc = False
    except Exception: pass
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35 if scene_kind == "giorno" else 0.02
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    # sole: da sud-ovest, pomeriggio
    for ob in [o for o in bpy.data.objects if o.type == "LIGHT"]: bpy.data.objects.remove(ob)
    if scene_kind == "giorno":
        ld = bpy.data.lights.new("sole", "SUN"); ld.energy = 4.5; ld.angle = math.radians(0.6)
        ld.color = (1.0, 0.93, 0.84)
        so = bpy.data.objects.new("sole", ld); COLL.objects.link(so)
        s = Vector((-math.sin(az)*math.cos(el), -math.cos(az)*math.cos(el), math.sin(el)))
        so.rotation_euler = (-s).to_track_quat("-Z", "Y").to_euler()
    on = scene_kind == "sera"
    set_role_material("led", m_emit("led_3000k", 3000, 18 if on else 0.0))
    # sera: luce calda anche dalle lampade a sospensione su tavolo e isola
    if on:
        for (x, y) in [(9.05, 1.7), (9.05, 2.6), (11.6, 2.2), (12.6, 2.2)]:
            ld = bpy.data.lights.new("sospensione", "POINT"); ld.energy = 25; ld.shadow_soft_size = 0.12
            ld.color = (1.0, 0.78, 0.55)
            o = bpy.data.objects.new("sospensione", ld); o.location = (x, y, 1.75); COLL.objects.link(o)

def cameras():
    out = {}
    for name, (pos, tgt, lens) in CAMERAS.items():
        cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = 0.05
        ob = bpy.data.objects.new(name, cd); COLL.objects.link(ob); ob.location = pos
        ob.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        out[name] = ob
    return out

def apply_preset(p):
    set_role_material("floor", mat(p["floor"]))
    set_role_material("walls", mat(p["walls"]))
    set_role_material("stone", mat(p["stone"]))
    ceil = p["ceiling"]
    set_role_material("ceiling_base", mat(p["walls"] if ceil.startswith("travi") else ceil))
    for ob in ROLE_OBJS.get("beams", []): ob.hide_render = not ceil.startswith("travi")
    if ceil.startswith("travi"): set_role_material("beams", mat(ceil))
    set_role_material("kitchen", mat(p["kitchen"]))
    set_role_material("sofa", mat(p["sofa"]))
    set_role_material("worktop", m_simple("top_pietra", "#d8d3ca", 0.35))
    set_role_material("table", m_wood("rovere_mobili", "#a88158", "#7a5a3b", planks=False, rough=0.5))
    set_role_material("chair", m_simple("sedia", "#2f2d2b", 0.6))
    set_role_material("dark", m_simple("metallo_scuro", "#1d1d1d", 0.45, metal=0.6))
    set_role_material("rug", m_simple("tappeto", "#bfb4a3", 1.0, sheen=0.6))
    set_role_material("glass", m_glass())
    set_role_material("frame", m_simple("telaio", "#2b2b2b", 0.4, metal=0.8))
    set_role_material("exterior", mat("pietra"))
    set_role_material("p1", mat("pietra"))
    set_role_material("roof", m_wood("tavolato_portico", "#8d6a4a", "#5e4430", planks=True, plank_w=0.14))
    set_role_material("portico_floor", m_tiles("pietra_portico", "#9d968b", "#8a8378", joint="#6d675f", size=0.5))
    set_role_material("ground", m_simple("prato", "#4d5e32", 1.0))

def set_visibility(show_p1=True, show_roof=True):
    # come i toggle "Primo piano" e "Tetto" del viewer 3D: nasconde in render e in viewport
    for role, show in (("p1", show_p1), ("roof", show_roof)):
        for ob in ROLE_OBJS.get(role, []):
            ob.hide_render = ob.hide_viewport = not show

def render_setup(preview, gpu):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"
    sc.cycles.samples = 24 if preview else 256
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.cycles.max_bounces = 8; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.light_sampling_threshold = 0.01
    if gpu:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try: prefs.compute_device_type = t; prefs.get_devices(); break
            except Exception: pass
        for d in prefs.devices: d.use = True
        sc.cycles.device = "GPU"
    sc.render.resolution_x, sc.render.resolution_y = (960, 540) if preview else (1920, 1080)
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try: sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception: pass
    sc.render.image_settings.file_format = "PNG"

def main():
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="render")
    ap.add_argument("--preset", action="append"); ap.add_argument("--scene", action="append")
    ap.add_argument("--camera", action="append")
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--exposure", type=float, default=None)
    ap.add_argument("--no-p1", action="store_true", help="nasconde il primo piano in facciata")
    ap.add_argument("--no-roof", action="store_true", help="nasconde la falda del portico")
    a = ap.parse_args(argv)
    reset(); build(); cams = cameras(); render_setup(a.preview, a.gpu)
    set_visibility(show_p1=not a.no_p1, show_roof=not a.no_roof)
    presets = a.preset or list(PRESETS); scenes = a.scene or SCENES; camnames = a.camera or list(CAMERAS)
    if a.build_only:
        apply_preset(PRESETS[presets[0]]); world_and_sun(scenes[0])
        bpy.context.scene.camera = cams[camnames[0]]; return
    out = bpy.path.abspath(a.out); os.makedirs(out, exist_ok=True)
    sc = bpy.context.scene
    for pn in presets:
        apply_preset(PRESETS[pn])
        for sk in scenes:
            world_and_sun(sk)
            sc.view_settings.exposure = a.exposure if a.exposure is not None else (1.3 if sk == "giorno" else -0.2)
            for cn in camnames:
                sc.camera = cams[cn]
                sc.render.filepath = os.path.join(out, f"{cn}__{pn}__{sk}.png")
                print("RENDER", sc.render.filepath, flush=True)
                bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    main()

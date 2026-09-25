"""
FIENILE - Piano terra, open space cucina/pranzo/soggiorno lungo la parete ovest
Genera la scena in Blender (testato su 4.5 e 5.0) e renderizza le varianti di pavimento in Cotto Milano.

Il riferimento è il viewer 3D (src/viewer_3d.js): stessi parametri, stessa geometria, stesse varianti
di finestre, stessi materiali, stessi punti di vista e stesso sole (posizione reale a Pioltello per data e ora).
Le funzioni di costruzione usano le coordinate del viewer (x = est, y = alto, z = sud, metri) e le
convertono in Blender (X = est, Y = nord, Z = alto) con V(): così il codice si confronta riga per riga.

Il pavimento usa le texture del produttore (src/texture/cottomilano, 5 facce per colore) posate a caso
con la stessa sequenza del viewer: stessa faccia e stessa rotazione su ogni lastra 120×120.
Portico e terrazzo usano lo stesso cotto del soggiorno, come nel viewer.

Uso:
  blender -b -P fienile_pt_render.py -- --out ./render
  blender -b -P fienile_pt_render.py -- --out ./render --preset terracotta --scene giorno --camera nord
  blender -b -P fienile_pt_render.py -- --var-pt A --var-p1 C --data 2026-06-21 --ora 18.5
  blender -b -P fienile_pt_render.py -- --preview          (bassa risoluzione, pochi campioni)
  blender    -P fienile_pt_render.py -- --build-only       (apre la scena per navigarla, niente render)
  blender -b -P fienile_pt_render.py -- --no-roof --no-p1   (come i toggle "Tetto" e "Primo piano" del viewer)
  blender -b -P fienile_pt_render.py -- --no-sofa           (arredo senza il divano)
"""
import bpy, bmesh, math, sys, os, argparse, colorsys, datetime
from mathutils import Vector, Euler

# ----------------------------------------------------------------------------
# PARAMETRI DI PROGETTO (copiati da P in viewer_3d.js)
# ----------------------------------------------------------------------------
P = dict(
    sito=(45.51, 9.33),       # Pioltello (MI)
    L=13.47,                  # lunghezza interna parete ovest
    tW=0.45,                  # spessore parete ovest
    hPiano=2.70,              # altezza parete per piano
    solaio=0.30,              # spessore solaio tra PT e P1
    profSoggiorno=4.64,       # profondità open space
    profEdificio=10.50,       # filo esterno ovest → filo esterno est
    tTestata=0.60,            # muri di testata nord/sud
    tEst=0.45,                # muro est
    arretramentoP1=1.10,      # il primo piano è arretrato di 110 cm rispetto al piano terra
    colonna=dict(z=(6.355, 7.115), x=(1.60, 2.36)),   # 76 cm, centrata; x dal filo interno
    varco=(8.50, 10.20),                              # passaggio verso ingresso/scala
    ribassamento=dict(h=0.28, prof=0.70),             # soffitto ribassato lungo il lato est dell'open space
    portico=dict(prof=3.60, pilastri=[(-0.60, 0.10), (6.435, 7.035), (13.37, 14.07)]),
    gelosia=dict(spessore=0.25, zoccolo=0.60, fasciaAlta=0.25, spallaFacciata=0.25),
    parapetto=dict(h=1.00, arretramento=0.06, passo=0.114, bacchetta=0.014, montante=0.04, interasseMontanti=1.50),
    tetto=dict(colmoX=6.30, colmoH=8.80, hOvest=6.10, grondaOvestX=-4.80, hEst=7.10, grondaEstX=11.90),
)

# Cucina Veneta Cucine "Sakura Presa" (CUCINA nel viewer): u = lungo la parete, s = distanza dalla parete.
# Parete nord: u dal filo interno ovest; pareti ovest ed est: u dalla testata nord.
CUCINA = dict(
    hZoccolo=0.12, hScocca=0.90, hTop=0.012, pBase=0.60, pTop=0.63, hColonna=2.42, pColonna=0.78,
    schienale=0.558, alzatina=0.06,
    nord=dict(u=(0, 3.76), moduli=[(0.63, 0.76, "fianco"), (0.76, 1.51, "cassetti"), (1.51, 2.71, "cassetti"),
                                   (2.71, 3.46, "cassetti"), (3.46, 3.76, "anta")]),
    ovest=dict(u=(0.63, 3.34), moduli=[(0.63, 1.30, "anta"), (1.30, 2.50, "cassetti"), (2.50, 3.10, "anta"),
                                       (3.10, 3.34, "giorno")]),
    colonne=[(0, 1.45, "walkin"), (1.45, 2.05, "forno"), (2.05, 2.08, "fianco"), (2.08, 2.38, "estraibile"),
             (2.38, 2.45, "fianco")],
    frigo=dict(u=(2.45, 3.283), h=1.793),                       # frigo americano del cliente
    isola=dict(x=(1.75, 2.83), z=(1.64, 3.29), ante=4),
    piano=dict(u=2.11, s=0.315, w=0.80, d=0.52),                # Bosch PVQ811H26E, cappa integrata
    lavello=dict(u=(1.53, 2.27), s=(0.12, 0.52), rubinetto=1.90),  # Franke MRG 110-72 Sahara
    presa=dict(x=2.04, z=2.18),                                  # presa a scomparsa sul top dell'isola
)

# finestra = (posizione da nord, larghezza, altezza, davanzale)  — VAR_PT / VAR_P1 del viewer
VAR_PT = {
    "E":        [(1.000, 1.74, 1.5, 1), (3.5375, 2.9, 2.5, 0), (7.0325, 2.9, 2.5, 0), (10.730, 1.74, 1.5, 1)],
    "A":        [(1.045, 1.9, 2.5, 0), (3.538, 2.9, 2.5, 0), (7.033, 2.9, 2.5, 0), (10.525, 1.9, 2.5, 0)],
    "B":        [(1.045, 1.9, 1.5, 1), (3.538, 2.9, 2.5, 0), (7.033, 2.9, 2.5, 0), (10.525, 1.9, 1.5, 1)],
    "C":        [(0.1475, 2.795, 1.5, 1), (3.5375, 2.9, 2.5, 0), (7.0325, 2.9, 2.5, 0), (10.5275, 2.795, 1.5, 1)],
    "D":        [(1.000, 1.6, 1.5, 1), (3.5375, 2.9, 2.5, 0), (7.0325, 2.9, 2.5, 0), (10.870, 1.6, 1.5, 1)],
    "attuale":  [(0.735, 2, 2.5, 0), (3.735, 2, 2.5, 0), (7.735, 2, 2.5, 0), (10.735, 2, 2.5, 0)],
    "regolare": [(0.735, 2, 2.5, 0), (3.9875, 2, 2.5, 0), (7.4825, 2, 2.5, 0), (10.735, 2, 2.5, 0)],
}
def _p1(w): return [(0.65, 0.6, 1.5, 1), (2.50, w, 2.5, 0), (P["L"] - 2.50 - w, w, 2.5, 0), (P["L"] - 0.65 - 0.6, 0.6, 1.5, 1)]
VAR_P1 = {"B": _p1(1.74), "A": _p1(1.60), "C": _p1(1.80), "D": _p1(2.00)}

# punti di vista (VIEWS del viewer, coordinate del viewer); upper=False nasconde primo piano e tetto
CAMERAS = {
    "ovest":   dict(pos=(-19, 4.5, P["L"] / 2 - 4), tgt=(0, 3.2, P["L"] / 2)),
    "portico": dict(pos=(-3.0, 1.6, 0.9), tgt=(0.3, 1.4, 9.5)),
    "nord":    dict(pos=(4.6, 1.65, 3.45), tgt=(0.9, 1.15, 13)),   # appena a sud del frigo
    "sud":     dict(pos=(4.4, 1.6, P["L"] - 0.6), tgt=(0.9, 1.1, 2)),
    # viste della cucina: di giorno è in fondo all'open space, lontana dalle vetrate, e va esposta di più
    "cucina":  dict(pos=(4.4, 1.75, 4.2), tgt=(1.4, 0.9, 1.4), exp=dict(giorno=1.6)),
    "colonne": dict(pos=(1.3, 1.65, 4.3), tgt=(4.6, 1.2, 1.2), exp=dict(giorno=1.6)),
    "isola":   dict(pos=(2.75, 1.75, 3.8), tgt=(2.3, 1.1, 0.3), exp=dict(giorno=1.6)),
    "pianta":  dict(pos=(P["profEdificio"] / 2 - 0.5, 21, P["L"] / 2 + 0.01),
                    tgt=(P["profEdificio"] / 2 - 0.5, 0, P["L"] / 2), upper=False),
}
FOV_Y = 55            # apertura verticale della camera del viewer (gradi)

# preset: cambia solo il colore del Cotto Milano (pavimento PT, portico, terrazzo)
PRESETS = ("creta", "terracotta")
# giorno: sole all'ora scelta, luci spente; sera: luci interne accese (toggle "Luci interne" del viewer)
SCENES = ("giorno", "sera")

# Cotto Milano 120×120 ultramatt: stessi parametri di COTTO_MILANO nel viewer.
TEX_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "texture")
TEX_DIR = os.path.join(TEX_ROOT, "cottomilano")
COTTO = dict(facce=5, nx=8, nz=12, lato=1.2, seme=57, px=512)

# ----------------------------------------------------------------------------
# GEOMETRIA DI BASE: box ed estrusi in coordinate del viewer
# ----------------------------------------------------------------------------
ROOT = None
GROUPS = {}          # gruppo del viewer (pt, upper, roof, kitchen, furniture, lights, ground) → collection
FLOOR_OBJS = {}      # "pavimento" / "portico" → oggetti il cui materiale cambia col preset

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global ROOT
    ROOT = bpy.data.collections.new("Fienile"); bpy.context.scene.collection.children.link(ROOT)
    GROUPS.clear(); FLOOR_OBJS.clear()
    for g in ("pt", "upper", "roof", "kitchen", "furniture", "lights", "ground"):
        GROUPS[g] = bpy.data.collections.new(g); ROOT.children.link(GROUPS[g])
    # il divano sta in una collection figlia dell'arredo, per poterlo escludere da solo
    GROUPS["sofa"] = bpy.data.collections.new("sofa"); GROUPS["furniture"].children.link(GROUPS["sofa"])

def V(x, y, z):
    """viewer (x est, y alto, z sud) → Blender (X est, Y nord, Z alto); Y = 0 sulla testata sud interna."""
    return (x, P["L"] - z, y)

def mesh_obj(name, verts, faces, uvs, mats, group):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for k, li in enumerate(poly.loop_indices): uvl.data[li].uv = uvs[poly.index][k]
    keys = list(dict.fromkeys(mats))
    for k in keys: me.materials.append(material(k))
    for poly in me.polygons: poly.material_index = keys.index(mats[poly.index])
    ob = bpy.data.objects.new(name, me); GROUPS[group].objects.link(ob)
    if len(keys) == 1 and keys[0] in ("pavimento", "portico"): FLOOR_OBJS.setdefault(keys[0], []).append(ob)
    return ob

def box(x0, y0, z0, x1, y1, z1, mat, group, name="box"):
    """Come box() del viewer: UV in metri su ogni faccia (sul piano superiore u = x - x0, v = z1 - z).
    mat: chiave materiale, o lista di 6 nell'ordine di BoxGeometry (+x, -x, +y, -y, +z, -z)."""
    X0, X1 = sorted((x0, x1)); Z0, Z1 = sorted((y0, y1)); Y0, Y1 = sorted((P["L"] - z0, P["L"] - z1))
    if min(X1 - X0, Y1 - Y0, Z1 - Z0) < 1e-4: return None
    lo, ext = (X0, Y0, Z0), ((X0, X1), (Y0, Y1), (Z0, Z1))
    quads = [  # angoli (i, j, k) su X/Y/Z e assi della UV
        ([(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (1, 2)),   # +x (lato interno delle pareti ovest)
        ([(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], (1, 2)),   # -x
        ([(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (0, 1)),   # alto
        ([(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], (0, 1)),   # basso
        ([(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], (0, 2)),   # +z viewer = sud
        ([(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], (0, 2)),   # -z viewer = nord
    ]
    verts, faces, uvs = [], [], []
    for corners, (a, b) in quads:
        f = []
        for ijk in corners:
            f.append(len(verts)); verts.append(tuple(ext[ax][ijk[ax]] for ax in range(3)))
        faces.append(f); uvs.append([(verts[i][a] - lo[a], verts[i][b] - lo[b]) for i in f])
    mats = list(mat) if isinstance(mat, (list, tuple)) else [mat] * 6
    return mesh_obj(name, verts, faces, uvs, mats, group)

def extrude(points, z0, z1, mat, group, name="estruso"):
    """Profilo nel piano x/y del viewer estruso lungo z (tetto, timpani, gelosie).
    UV come ExtrudeGeometry di three.js: (x, y) sulle facce del profilo, (x o y, z) sui fianchi."""
    n = len(points)
    verts = [V(x, y, z0) for x, y in points] + [V(x, y, z1) for x, y in points]
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    uvs = [[(x, y) for x, y in points], [(x, y) for x, y in reversed(points)]]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
        (xa, ya), (xb, yb) = points[i], points[j]
        u = (lambda q: q[0]) if abs(ya - yb) < abs(xa - xb) else (lambda q: q[1])
        uvs.append([(u(points[i]), z0), (u(points[j]), z0), (u(points[j]), z1), (u(points[i]), z1)])
    ob = mesh_obj(name, verts, faces, uvs, [mat] * len(faces), group)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    return ob

# ----------------------------------------------------------------------------
# MATERIALI (gli stessi del viewer; il Cotto Milano usa le texture del produttore)
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

def math_node(nt, op, a, b=0.0):
    n = node(nt, "ShaderNodeMath", operation=op)
    for sock, v in ((n.inputs[0], a), (n.inputs[1], b)):
        if isinstance(v, (int, float)): sock.default_value = v
        else: nt.links.new(v, sock)
    return n.outputs["Value"]

def coords(nt, scale=(1,1,1), rot=(0,0,0)):
    tc = node(nt, "ShaderNodeTexCoord"); mp = node(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale; mp.inputs["Rotation"].default_value = rot
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); return mp.outputs["Vector"]

def uv_coords(nt, scale=(1, 1, 1)):
    tc = node(nt, "ShaderNodeTexCoord"); mp = node(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); return mp.outputs["Vector"]

def bump(nt, height_socket, p, strength=0.1, dist=0.01):
    b = node(nt, "ShaderNodeBump"); b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = dist
    nt.links.new(height_socket, b.inputs["Height"]); nt.links.new(b.outputs["Normal"], p.inputs["Normal"])

def rgb(h):
    h = h.lstrip("#"); c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(((x+0.055)/1.055)**2.4 if x > 0.04045 else x/12.92 for x in c) + (1.0,)

def rgb255(r, g, b): return rgb("#%02x%02x%02x" % (int(r), int(g), int(b)))

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
    rot = {"X": (0, 0, 0), "Y": (0, 0, math.pi/2), "Z": (0, math.pi/2, 0)}[grain_dir]   # Z: fibra verticale
    vec = coords(nt, (1, 1, 1), rot)
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

def m_brick(name="mattone"):
    # come brickTex() del viewer: mattone ~25 × 5,5 cm, fuga 1 cm (passo 26 × 6,5 cm), UV in metri
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    vec = uv_coords(nt)
    br = node(nt, "ShaderNodeTexBrick", offset=0.5, offset_frequency=2)
    br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = 0.26
    br.inputs["Row Height"].default_value = 0.065; br.inputs["Mortar Size"].default_value = 0.01
    br.inputs["Mortar Smooth"].default_value = 0.1; br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = rgb255(165, 86, 59); br.inputs["Color2"].default_value = rgb255(117, 61, 42)
    br.inputs["Mortar"].default_value = rgb("#9d9383")
    nt.links.new(vec, br.inputs["Vector"])
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60
    nt.links.new(vec, nz.inputs["Vector"])
    mx, f, a, b, o = mix(nt, "OVERLAY", 0.15)
    nt.links.new(br.outputs["Color"], a); nt.links.new(nz.outputs["Color"], b)
    nt.links.new(o, p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.9
    bump(nt, br.outputs["Fac"], p, 0.4, 0.006)
    return m

def m_lattice(name="gelosia"):
    # come latticeTex() del viewer: corsi da 6,5 cm (letto di malta continuo da 1 cm), mattoni da 25 cm
    # alternati a vuoti da 12,5 cm, corsi alterni sfalsati di mezzo passo. Il vuoto è trasparente.
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    sep = node(nt, "ShaderNodeSeparateXYZ"); nt.links.new(uv_coords(nt), sep.inputs["Vector"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    passo, bw, ch, mt = 0.375, 0.25, 0.065, 0.01
    corso = math_node(nt, "FLOOR", math_node(nt, "DIVIDE", v, ch))
    malta = math_node(nt, "LESS_THAN", math_node(nt, "FLOORED_MODULO", v, ch), mt)
    us = math_node(nt, "SUBTRACT", u, math_node(nt, "MULTIPLY", math_node(nt, "FLOORED_MODULO", corso, 2), passo / 2))
    mattone = math_node(nt, "LESS_THAN", math_node(nt, "FLOORED_MODULO", us, passo), bw)
    pieno = math_node(nt, "MAXIMUM", malta, mattone)
    # tono diverso per ogni mattone
    idm = math_node(nt, "ADD", math_node(nt, "MULTIPLY", corso, 1000), math_node(nt, "FLOOR", math_node(nt, "DIVIDE", us, passo)))
    wn = node(nt, "ShaderNodeTexWhiteNoise", noise_dimensions="1D"); nt.links.new(idm, wn.inputs["W"])
    _, f1, a1, b1, o1 = mix(nt, "MIX"); nt.links.new(wn.outputs["Value"], f1)
    a1.default_value = rgb255(117, 61, 42); b1.default_value = rgb255(165, 86, 59)
    _, f2, a2, b2, o2 = mix(nt, "MIX"); nt.links.new(malta, f2)
    nt.links.new(o1, a2); b2.default_value = rgb("#9d9383")
    nt.links.new(o2, p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.9
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    tr = node(nt, "ShaderNodeBsdfTransparent"); ms = node(nt, "ShaderNodeMixShader")
    nt.links.new(pieno, ms.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], ms.inputs[1]); nt.links.new(p.outputs["BSDF"], ms.inputs[2])
    nt.links.new(ms.outputs["Shader"], out.inputs["Surface"])
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

def lcg(seed):
    # stesso generatore di rand() nel viewer 3D, per avere la stessa posa
    s = seed & 0xFFFFFFFF
    def r():
        nonlocal s
        s = (s * 1664525 + 1013904223) & 0xFFFFFFFF
        return s / 4294967296
    return r

def cotto_posa(colore):
    """Compone l'immagine del campo 8×12 lastre posando a caso le 5 facce del produttore:
    faccia diversa da quelle a sinistra e sopra, rotazione casuale di 90°, fughe sottili."""
    import numpy as np
    name = f"posa_cotto_{colore}"
    if name in bpy.data.images: return bpy.data.images[name]
    C, s = COTTO, COTTO["px"]
    facce = []
    for k in range(C["facce"]):
        im = bpy.data.images.load(os.path.join(TEX_DIR, f"{colore}_{k+1:02d}.jpg"), check_existing=True)
        a = np.empty(im.size[0] * im.size[1] * 4, np.float32); im.pixels.foreach_get(a)
        a = np.flipud(a.reshape(im.size[1], im.size[0], 4))          # righe dall'alto, come il canvas
        if a.shape[0] != s:                                           # campionamento semplice alla risoluzione della lastra
            idx = (np.arange(s) * a.shape[0] / s).astype(int); a = a[idx][:, idx]
        facce.append(a); bpy.data.images.remove(im)
    W, H = C["nx"] * s, C["nz"] * s
    out = np.empty((H, W, 4), np.float32)
    rnd, scelte = lcg(C["seme"]), []
    for j in range(C["nz"]):
        for i in range(C["nx"]):
            vicine = (scelte[j*C["nx"] + i - 1] if i else -1, scelte[(j-1)*C["nx"] + i] if j else -1)
            while True:
                k = int(rnd() * C["facce"])
                if k not in vicine: break
            scelte.append(k)
            rot = int(rnd() * 4)                                      # canvas.rotate: senso orario
            out[j*s:(j+1)*s, i*s:(i+1)*s] = np.rot90(facce[k], -rot)
    fuga, alpha = np.array([95, 80, 68, 255], np.float32) / 255, 0.45
    for i in range(C["nx"]): out[:, i*s] = out[:, i*s] * (1 - alpha) + fuga * alpha
    for j in range(C["nz"]): out[j*s, :] = out[j*s, :] * (1 - alpha) + fuga * alpha
    out[..., 3] = 1
    img = bpy.data.images.new(name, W, H, alpha=False)
    img.pixels.foreach_set(np.flipud(out).ravel())                   # in Blender la riga 0 è in basso (come three.js con flipY)
    img.pack()
    return img

def m_cotto(colore, rough=0.85, suffix=""):
    m, r = new_mat(f"cotto_{colore}{suffix}")
    if not r: return m
    nt, p = r
    C = COTTO
    # UV in metri (come nel viewer) → campo di 9,6 × 14,4 m
    tx = node(nt, "ShaderNodeTexImage"); tx.image = cotto_posa(colore); tx.extension = "REPEAT"
    nt.links.new(uv_coords(nt, (1 / (C["nx"] * C["lato"]), 1 / (C["nz"] * C["lato"]), 1)), tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    # leggera ondulazione della superficie, per non avere riflessi da specchio
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40
    nt.links.new(coords(nt), nz.inputs["Vector"]); bump(nt, nz.outputs["Fac"], p, 0.05, 0.002)
    return m

def m_photo(name, rel, meters, rough=0.5):
    """Foto di un materiale del produttore (src/texture/<rel>) sulle UV in metri, ripetuta a specchio."""
    m, r = new_mat(name)
    if not r: return m
    nt, p = r
    tx = node(nt, "ShaderNodeTexImage"); tx.extension = "MIRROR"
    tx.image = bpy.data.images.load(os.path.join(TEX_ROOT, rel), check_existing=True)
    nt.links.new(uv_coords(nt, (1 / meters[0], 1 / meters[1], 1)), tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    return m

def m_emit(name, kelvin=3000, strength=18):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = node(nt, "ShaderNodeOutputMaterial"); em = node(nt, "ShaderNodeEmission")
    bb = node(nt, "ShaderNodeBlackbody"); bb.inputs["Temperature"].default_value = kelvin
    nt.links.new(bb.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"]); return m

# stesse chiavi di M nel viewer
LIB = {
    "facade":      lambda: m_plaster("facade", "#efe2b4"),                 # intonaco giallo molto pallido
    "interno":     lambda: m_plaster("interno", "#f2efe9", grain=0.02),
    "soffitto":    lambda: m_plaster("soffitto", "#f4f2ee", grain=0.02),
    "pavimento":   lambda: m_simple("pavimento", "#cfa27c", 0.85),         # sostituito dal preset
    "portico":     lambda: m_simple("portico", "#cfa27c", 0.92),           # sostituito dal preset
    "mattone":     m_brick,
    "gelosia":     m_lattice,
    "telaio":      lambda: m_simple("telaio", "#f3f1ec", 0.5),              # infissi bianchi
    "vetro":       m_glass,
    "davanzale":   lambda: m_simple("davanzale", "#d8d2c6", 0.6),
    "pavimentoP1": lambda: m_wood("rovere", "#cea068", "#9c7650", grain_dir="Y", rough=0.55),
    "ferro":       lambda: m_simple("ferro", "#3a3936", 0.55, metal=0.7),  # ferro micaceo scuro
    "coppi":       lambda: m_simple("coppi", "#9f5638", 0.85),
    "tavolato":    lambda: m_wood("tavolato", "#80664f", "#5a4636", grain_dir="Y", rough=0.8),
    "prato":       lambda: m_simple("prato", "#66753f", 1.0),
    "ante":        lambda: m_photo("ante_rovere", "cucina/rovere_ikebana.jpg", (0.30, 0.283), 0.6),  # rovere Ikebana
    "laccato":     lambda: m_simple("laccato_verde_avocado", "#8c8a62", 0.7),
    "travertino":  lambda: m_plaster("travertino", "#dccab0", rough=0.55, grain=0.01),
    "bronzo":      lambda: m_simple("bronzo", "#5f4b37", 0.45, metal=0.6),
    "vetroNero":   lambda: m_simple("vetro_nero", "#111111", 0.15, metal=0.2),
    "lavello":     lambda: m_simple("lavello_sahara", "#c9b393", 0.6),
    "vasca":       lambda: m_simple("vasca", "#9c8769", 0.7),
    "cromo":       lambda: m_simple("cromo", "#d8d8d8", 0.15, metal=1.0),
    "frigo":       lambda: m_simple("frigo", "#2c2c2e", 0.35, metal=0.5),
    "legno":       lambda: m_wood("legno", "#c9a57a", "#9c7650", grain_dir="Y", rough=0.6),
    "tessuto":     lambda: m_simple("tessuto", "#c8baa3", 1.0, sheen=0.5),
    "scuro":       lambda: m_simple("scuro", "#222222", 0.5, metal=0.4),
    "led":         lambda: m_emit("led", 3000, 18),
}
def material(key): return LIB[key]()

# ----------------------------------------------------------------------------
# COSTRUZIONE (traduzione di build() del viewer)
# ----------------------------------------------------------------------------
T = P["tetto"]
def roofH(x):
    if x <= T["colmoX"]: return T["colmoH"] - (T["colmoH"] - T["hOvest"]) * (T["colmoX"] - x) / T["colmoX"]
    return T["colmoH"] - (T["colmoH"] - T["hEst"]) * (x - T["colmoX"]) / (P["profEdificio"] - T["colmoX"])

WALL = ["interno", "facade", "facade", "facade", "facade", "facade"]   # +x = lato interno

def west_wall(y0, windows, group, ox=0.0):
    """Parete ovest di un piano: tratti pieni, finestre con telaio, davanzali, architravi."""
    H, t, L = P["hPiano"], P["tW"], P["L"]
    z = 0.0
    for a, b in sorted((p, p + w) for p, w, _, _ in windows):
        if a > z: box(ox, y0, z, ox + t, y0 + H, a, WALL, group, "parete_ovest")
        z = max(z, b)
    if z < L: box(ox, y0, z, ox + t, y0 + H, L, WALL, group, "parete_ovest")
    for p, w, h, sill in windows:
        a, b, top = p, p + w, y0 + sill + h
        if sill > 0:
            box(ox, y0, a, ox + t, y0 + sill - 0.03, b, WALL, group, "parapetto_finestra")
            box(ox - 0.04, y0 + sill - 0.03, a - 0.03, ox + t - 0.1, y0 + sill, b + 0.03, "davanzale", group, "davanzale")
        box(ox, top, a, ox + t, y0 + H, b, WALL, group, "architrave")
        if sill == 0: box(ox - 0.02, y0 - 0.02, a, ox + t, y0, b, "davanzale", group, "soglia")
        # telaio a ~2/3 dello spessore, verso l'interno: traversi a tutta larghezza, montanti tra i traversi
        # e vetri solo nelle luci; i pezzi non si compenetrano (agli incroci Cycles dava pixel neri)
        fx0, fx1, fw, yb, mw = ox + t - 0.16, ox + t - 0.09, 0.055, y0 + sill, 0.03
        box(fx0, yb, a, fx1, yb + fw, b, "telaio", group, "telaio")
        box(fx0, top - fw, a, fx1, top, b, "telaio", group, "telaio")
        box(fx0, yb + fw, a, fx1, top - fw, a + fw, "telaio", group, "telaio")
        box(fx0, yb + fw, b - fw, fx1, top - fw, b, "telaio", group, "telaio")
        # come nei prospetti: le finestre grandi sono divise in due, le strette hanno un'anta sola
        zm = a + w / 2
        luci = [(a + fw, zm - mw), (zm + mw, b - fw)] if w > 1.1 else [(a + fw, b - fw)]
        if w > 1.1: box(fx0, yb + fw, zm - mw, fx1, top - fw, zm + mw, "telaio", group, "montante")
        for za, zb in luci: box(fx0 + 0.03, yb + fw, za, fx0 + 0.035, top - fw, zb, "vetro", group, "vetro")

def railing(yb, z0, z1, group):
    """Parapetto in ferro: corrimano e corrente inferiore piatti, montanti, bacchette verticali."""
    R = P["parapetto"]; x0 = R["arretramento"]; x1 = x0 + 0.05; ytop = yb + R["h"]
    box(x0 - 0.005, ytop - 0.01, z0, x1 + 0.005, ytop, z1, "ferro", group, "corrimano")
    box(x0, yb + 0.07, z0, x1 - 0.02, yb + 0.08, z1, "ferro", group, "corrente")
    n_post = max(2, round((z1 - z0) / R["interasseMontanti"]) + 1)
    for i in range(n_post):
        z = z0 + (z1 - z0) * i / (n_post - 1)
        za = min(max(z - R["montante"] / 2, z0), z1 - R["montante"])
        box(x0, yb, za, x0 + R["montante"], ytop - 0.01, za + R["montante"], "ferro", group, "montante")
    b = R["bacchetta"] / 2
    for i in range(int((z1 - z0) // R["passo"])):
        zc, xc = z0 + R["passo"] * (i + 0.5), x0 + 0.02
        box(xc - b, yb + 0.08, zc - b, xc + b, ytop - 0.01, zc + b, "ferro", group, "bacchetta")

def kitchen(xi, xs, var_pt):
    """Cucina reale (traduzione di kitchen() del viewer): basi a L su nord e ovest, colonne a est, isola."""
    C, g, gap, tf = CUCINA, "kitchen", 0.0015, 0.02
    yz, yb = C["hZoccolo"], C["hScocca"]; yt = yb + C["hTop"]
    # un "lato" traduce (u lungo la parete, s dalla parete, y) in coordinate del viewer
    lato = dict(
        nord=lambda u0, u1, s0, s1, y0, y1, m: box(xi + u0, y0, s0, xi + u1, y1, s1, m, g, "cucina"),
        ovest=lambda u0, u1, s0, s1, y0, y1, m: box(xi + s0, y0, u0, xi + s1, y1, u1, m, g, "cucina"),
        est=lambda u0, u1, s0, s1, y0, y1, m: box(xs - s1, y0, u0, xs - s0, y1, u1, m, g, "cucina"),
    )
    def fronte(L, u0, u1, sp, tipo, y0, y1, mat):
        a, b = u0 + gap, u1 - gap
        f = lambda ya, yb2: L(a, b, sp - tf, sp, ya + gap, yb2 - gap, mat)
        if tipo == "cassetti":
            ym = (y0 + y1) / 2; f(y0, ym - 0.0125); f(ym + 0.0125, y1)
        elif tipo == "giorno":                                   # vano a giorno: fianchi, ripiano, schienale
            L(u0, u0 + tf, 0, sp, y0, y1, "ante"); L(u1 - tf, u1, 0, sp, y0, y1, "ante")
            L(u0, u1, 0, sp, y0, y0 + tf, "ante"); L(u0, u1, 0, sp, (y0 + y1) / 2 - tf / 2, (y0 + y1) / 2 + tf / 2, "ante")
            L(u0, u1, 0, tf, y0, y1, "ante")
        else: f(y0, y1)
    def basi(L, run, u1_top=None):
        u0, u1 = run["u"]
        L(u0, u1, 0, C["pBase"] - 0.06, 0, yz, "bronzo")                     # zoccolo arretrato
        for a, b, tipo in run["moduli"]:                                       # scocca: si vede solo nelle fughe
            if tipo != "giorno": L(u0 if a == run["moduli"][0][0] else a, b, 0, C["pBase"] - tf, yz, yb, "bronzo")
        for a, b, tipo in run["moduli"]: fronte(L, a, b, C["pBase"], tipo, yz, yb, "ante")
        L(u0, u1_top if u1_top is not None else u1, 0, C["pTop"], yb, yt, "travertino")   # top
    # le basi nord arrivano fino alla walk-in; l'eventuale differenza con la parete est è un tamponamento
    u_col = xs - xi - C["pColonna"]
    basi(lato["nord"], C["nord"], u_col)
    if u_col - C["nord"]["u"][1] > 0.005:
        lato["nord"](C["nord"]["u"][1], u_col, 0, C["pBase"] - 0.06, 0, yz, "bronzo")
        fronte(lato["nord"], C["nord"]["u"][1], u_col, C["pBase"], "anta", yz, yb, "ante")
    basi(lato["ovest"], C["ovest"])
    # schienale sulla parete nord e fino alla finestra F1 sulla ovest, alzatina sotto la finestra
    u_f1 = min(VAR_PT[var_pt][0][0] - 0.03, C["ovest"]["u"][1])
    lato["nord"](0, u_col, 0, 0.012, yt, yt + C["schienale"], "travertino")
    lato["ovest"](0.012, u_f1, 0, 0.012, yt, yt + C["schienale"], "travertino")
    lato["ovest"](u_f1, C["ovest"]["u"][1], 0, 0.012, yt, yt + C["alzatina"], "travertino")
    # piano cottura a filo top, lavello sottotop con rubinetto
    pc = C["piano"]
    lato["nord"](pc["u"] - pc["w"] / 2, pc["u"] + pc["w"] / 2, pc["s"] - pc["d"] / 2, pc["s"] + pc["d"] / 2, yt, yt + 0.003, "vetroNero")
    lv = C["lavello"]; (lu0, lu1), (ls0, ls1), r = lv["u"], lv["s"], lv["rubinetto"]
    lato["ovest"](lu0, lu1, ls0, ls1, yt, yt + 0.002, "lavello")
    lato["ovest"](lu0 + 0.03, lu1 - 0.03, ls0 + 0.03, ls1 - 0.03, yt + 0.002, yt + 0.003, "vasca")
    lato["ovest"](r - 0.015, r + 0.015, 0.05, 0.08, yt, yt + 0.42, "cromo")
    lato["ovest"](r - 0.012, r + 0.012, 0.05, 0.30, yt + 0.40, yt + 0.42, "cromo")

    # colonne laccate sulla parete est
    pc2, yc, est = C["pColonna"], C["hColonna"], lato["est"]
    for a, b, tipo in C["colonne"]:
        est(a, b, 0, pc2 - 0.06, 0, yz, "bronzo")
        est(a, b, 0, pc2 - tf, yz, yc, "laccato" if tipo == "fianco" else "bronzo")
        if tipo == "fianco":
            est(a, b, pc2 - tf, pc2, 0, yc, "laccato"); continue
        if tipo == "walkin":
            fronte(est, a, a + 0.46, pc2, "anta", yz, yc, "laccato"); fronte(est, a + 0.46, b, pc2, "anta", yz, yc, "laccato")
        elif tipo == "forno":                                     # anta, forno, micro, anta
            fronte(est, a, b, pc2, "anta", yz, 0.68, "laccato")
            fronte(est, a, b, pc2, "anta", 0.68, 1.28, "vetroNero")
            fronte(est, a, b, pc2, "anta", 1.28, 1.665, "vetroNero")
            fronte(est, a, b, pc2, "anta", 1.665, yc, "laccato")
        else: fronte(est, a, b, pc2, "anta", yz, yc, "laccato")
    # frigo americano a due ante + due cassetti
    fr = C["frigo"]; fu0, fu1 = fr["u"][0] + 0.005, fr["u"][1] - 0.005; fm = (fu0 + fu1) / 2
    est(fu0, fu1, 0.04, 0.74, 0.02, fr["h"], "frigo")
    for ya, yb2 in ((0.02, 0.5), (0.52, 0.93), (0.95, fr["h"])):
        if ya < 0.9: est(fu0, fu1, 0.74, 0.76, ya, yb2, "frigo")
        else: est(fu0, fm - 0.003, 0.74, 0.76, ya, yb2, "frigo"); est(fm + 0.003, fu1, 0.74, 0.76, ya, yb2, "frigo")

    # isola: ante sui due lati lunghi, fianchi in rovere sulle testate, presa a scomparsa sul top
    I = C["isola"]; ix0, ix1 = xi + I["x"][0], xi + I["x"][1]; iz0, iz1 = I["z"]
    box(ix0 + 0.06, 0, iz0 + 0.06, ix1 - 0.06, yz, iz1 - 0.06, "bronzo", g, "isola")
    box(ix0 + 0.02 + tf, yz, iz0 + tf, ix1 - 0.02 - tf, yb, iz1 - tf, "bronzo", g, "isola")
    box(ix0 + 0.02, yz, iz0, ix1 - 0.02, yb, iz0 + tf, "ante", g, "isola_fianco")
    box(ix0 + 0.02, yz, iz1 - tf, ix1 - 0.02, yb, iz1, "ante", g, "isola_fianco")
    dz = (iz1 - iz0 - 2 * tf) / I["ante"]
    for i in range(I["ante"]):
        za = iz0 + tf + i * dz + gap; zb = za + dz - 2 * gap
        box(ix0 + 0.02, yz + gap, za, ix0 + 0.02 + tf, yb - gap, zb, "ante", g, "isola_anta")
        box(ix1 - 0.02 - tf, yz + gap, za, ix1 - 0.02, yb - gap, zb, "ante", g, "isola_anta")
    box(ix0, yb, iz0, ix1, yt, iz1, "travertino", g, "isola_top")
    pr = C["presa"]
    box(xi + pr["x"] - 0.03, yt, pr["z"] - 0.03, xi + pr["x"] + 0.03, yt + 0.01, pr["z"] + 0.03, "vetroNero", g, "presa")

def build(var_pt, var_p1):
    L, D, t, H, S = P["L"], P["profEdificio"], P["tW"], P["hPiano"], P["solaio"]
    xi, xs = t, t + P["profSoggiorno"]          # filo interno ovest, fine open space
    y1 = H + S                                   # quota pavimento P1
    tt = P["tTestata"]

    # --- terreno e portico
    box(-60, -0.06, -60, 60, -0.04, 60, "prato", "ground", "prato")
    box(-P["portico"]["prof"], -0.04, -tt, 0, -0.01, L + tt, "portico", "ground", "pavimento_portico")
    for a, b in P["portico"]["pilastri"]:
        x0 = -P["portico"]["prof"]
        box(x0, 0, a, x0 + 0.6, roofH(x0 + 0.6) + 0.05, b, "mattone", "pt", "pilastro_portico")
    # muri a gelosia sui due lati corti: portico al piano terra e, sopra il solaio, i lati del terrazzo
    gz = P["gelosia"]; xa, xb, xt = -P["portico"]["prof"] + 0.6, 0.0, P["arretramentoP1"]
    xl0, xl1, yt = xa, xb - gz["spallaFacciata"], H + S
    hTop = lambda x: roofH(x) - gz["fasciaAlta"]
    for zOut in (-tt + 0.05, L + tt - 0.05 - gz["spessore"]):
        z0, z1 = zOut, zOut + gz["spessore"]
        box(xa, 0, z0, xb, gz["zoccolo"], z1, "mattone", "pt", "zoccolo_gelosia")
        box(xl1, gz["zoccolo"], z0, xb, yt, z1, "mattone", "pt", "spalla_gelosia")
        extrude([(xl0, gz["zoccolo"]), (xl1, gz["zoccolo"]), (xl1, hTop(xl1)), (xl0, hTop(xl0))],
                z0, z1, "gelosia", "pt", "gelosia_portico")
        extrude([(xl1, yt), (xt, yt), (xt, hTop(xt)), (xl1, hTop(xl1))], z0, z1, "gelosia", "upper", "gelosia_terrazzo")
        extrude([(xa, hTop(xa)), (xt, hTop(xt)), (xt, roofH(xt) + 0.05), (xa, roofH(xa) + 0.05)],
                z0, z1, "mattone", "upper", "fascia_gelosia")

    # --- piano terra
    box(xi, -0.02, 0, D - P["tEst"], 0, L, "pavimento", "pt", "pavimento")
    west_wall(0, VAR_PT[var_pt], "pt")
    # testate nord/sud e muro est fino al solaio
    box(0, 0, -tt, D, y1, 0, "facade", "pt", "testata_nord")
    box(0, 0, L, D, y1, L + tt, "facade", "pt", "testata_sud")
    box(D - P["tEst"], 0, 0, D, y1, L, "facade", "pt", "muro_est")
    # pelli interne bianche dell'open space
    box(xi, 0, 0, xs, H, 0.01, "interno", "pt", "pelle_nord")
    box(xi, 0, L - 0.01, xs, H, L, "interno", "pt", "pelle_sud")
    # muro interno est dell'open space, con varco
    va, vb = P["varco"]
    box(xs, 0, 0, xs + 0.3, H, va, "interno", "pt", "muro_interno")
    box(xs, 0, vb, xs + 0.3, H, L, "interno", "pt", "muro_interno")
    box(xs, 2.2, va, xs + 0.3, H, vb, "interno", "pt", "architrave_varco")
    # colonna in mattoni
    c = P["colonna"]
    box(xi + c["x"][0], 0, c["z"][0], xi + c["x"][1], H, c["z"][1], "mattone", "pt", "colonna")
    # solaio: intradosso bianco, fascia di facciata gialla.
    # Sotto il pavimento del P1 si ferma 2 cm più in basso, per non compenetrarlo
    xp = P["arretramentoP1"] + t    # filo interno della parete ovest del P1
    box(xi, H, 0, xp, y1, L, "soffitto", "upper", "solaio")
    box(xp, H, 0, D - P["tEst"], y1 - 0.02, L, "soffitto", "upper", "solaio_sotto_p1")
    box(0, H, 0, xi, y1, L, "facade", "upper", "fascia_solaio")
    # ribassamento sul lato est, opposto alle finestre: passa sopra il varco (h 2,20) senza interromperlo
    rb = P["ribassamento"]; xr = xs - rb["prof"]
    box(xr, H - rb["h"], 0.01, xs, H, L - 0.01, "soffitto", "upper", "ribassamento")

    # --- primo piano (involucro) + tetto
    ox = P["arretramentoP1"]
    west_wall(y1, VAR_P1[var_p1], "upper", ox)
    box(ox, y1 + H, 0, ox + t, roofH(ox) + 0.05, L, WALL, "upper", "parete_ovest_alta")
    box(ox + t, y1 - 0.02, 0, D - P["tEst"], y1, L, "pavimentoP1", "upper", "pavimento_p1")
    box(0, y1, 0, ox, y1 + 0.02, L, "portico", "upper", "terrazzo")
    railing(y1 + 0.02, -tt + 0.05 + gz["spessore"], L + tt - 0.05 - gz["spessore"], "upper")
    box(D - P["tEst"], y1, 0, D, roofH(D) + 0.05, L, "facade", "upper", "muro_est_p1")
    gable = [(ox, y1), (D, y1), (D, roofH(D)), (T["colmoX"], T["colmoH"]), (ox, roofH(ox))]
    extrude(gable, -tt, 0, "facade", "upper", "timpano_nord")
    extrude(gable, L, L + tt, "facade", "upper", "timpano_sud")
    # falde: tavolato sotto (visibile dal portico), coppi sopra
    xw, xe = T["grondaOvestX"], T["grondaEstX"]
    hwE = roofH(0) + (xw / T["colmoX"]) * (T["colmoH"] - T["hOvest"])            # prolungamento falda ovest
    heE = roofH(D) - ((xe - D) / (D - T["colmoX"])) * (T["colmoH"] - T["hEst"])  # prolungamento falda est
    under = [(xw, hwE), (T["colmoX"], T["colmoH"]), (xe, heE)]
    lay = lambda pts, d0, d1: [(x, y + d0) for x, y in pts] + [(x, y + d1) for x, y in reversed(pts)]
    extrude(lay(under, 0, 0.12), -tt - 0.5, L + tt + 0.5, "tavolato", "roof", "tavolato")
    extrude(lay(under, 0.12, 0.32), -tt - 0.6, L + tt + 0.6, "coppi", "roof", "coppi")

    kitchen(xi, xs, var_pt)

    # --- arredo indicativo: tavolo 200 × 80 centrato tra cucina e colonna (lungo z) e nella larghezza
    # dell'open space (lungo x), divano e tappeto nella metà sud
    tzc = (max(CUCINA["ovest"]["u"][1], CUCINA["isola"]["z"][1]) + P["colonna"]["z"][0]) / 2; txc = (xi + xs) / 2
    tz0, tz1, tx0, tx1 = tzc - 0.40, tzc + 0.40, txc - 1.00, txc + 1.00
    box(tx0, 0.72, tz0, tx1, 0.76, tz1, "legno", "furniture", "tavolo")
    for x, z in ((tx0 + 0.06, tz0 + 0.06), (tx1 - 0.11, tz0 + 0.06), (tx0 + 0.06, tz1 - 0.11), (tx1 - 0.11, tz1 - 0.11)):
        box(x, 0, z, x + 0.05, 0.72, z + 0.05, "scuro", "furniture", "gamba")
    for i in range(3):
        for side in (-1, 1):
            x = tx0 + 0.13 + i * 0.65; z = tz0 - 0.5 if side < 0 else tz1 + 0.08
            box(x, 0.44, z, x + 0.44, 0.48, z + 0.42, "scuro", "furniture", "sedia")
            bzz = z if side < 0 else z + 0.38
            box(x, 0.48, bzz, x + 0.44, 0.85, bzz + 0.04, "scuro", "furniture", "schienale")
    box(xi + 0.9, 0, 8.3, xi + 3.7, 0.012, 11.6, "tessuto", "furniture", "tappeto")
    sx = xi + 3.3
    box(sx, 0.1, 8.5, sx + 0.95, 0.42, 11.4, "tessuto", "sofa", "divano")
    box(sx + 0.72, 0.42, 8.5, sx + 0.95, 0.82, 11.4, "tessuto", "sofa", "divano_schienale")
    box(xi + 1.6, 0, 9.4, xi + 2.4, 0.36, 10.4, "legno", "furniture", "tavolino")

    # --- luci interne: profili LED a sguscio + punti luce caldi
    # sul lato est il profilo corre davanti al ribassamento, continuo anche sopra il varco
    zc = H - 0.2
    box(xi + 0.08, zc, 0.12, xr - 0.08, zc + 0.012, 0.17, "led", "lights", "led")
    box(xi + 0.08, zc, L - 0.17, xr - 0.08, zc + 0.012, L - 0.12, "led", "lights", "led")
    box(xr - 0.17, zc, 0.12, xr - 0.12, zc + 0.012, L - 0.12, "led", "lights", "led")
    for x, z in ((xi + 1.8, 1.9), (xi + 1.8, 4.6), (xi + 2.4, 10.0), (xi + 3.2, 7.3)):
        ld = bpy.data.lights.new("punto_luce", "POINT"); ld.energy = 40; ld.shadow_soft_size = 0.1
        ld.color = (1.0, 0.78, 0.55)
        o = bpy.data.objects.new("punto_luce", ld); o.location = V(x, 2.1, z); GROUPS["lights"].objects.link(o)

# ----------------------------------------------------------------------------
# SOLE (stesso algoritmo NOAA semplificato del viewer) E CIELO
# ----------------------------------------------------------------------------
def sun_position(date_str, hour):
    """Azimut (da nord, verso est) ed elevazione in radianti, ora locale italiana con ora legale."""
    lat, lon = P["sito"]
    y, mo, d = map(int, date_str.split("-"))
    hh = int(hour); mm = round((hour - hh) * 60)
    utc = datetime.timezone.utc
    last_sunday = lambda m: max(dd for dd in range(25, 32) if datetime.date(y, m, dd).weekday() == 6)
    dst0 = datetime.datetime(y, 3, last_sunday(3), 1, tzinfo=utc)
    dst1 = datetime.datetime(y, 10, last_sunday(10), 1, tzinfo=utc)
    t = datetime.datetime(y, mo, d, tzinfo=utc) + datetime.timedelta(hours=hh - 1, minutes=mm)
    if dst0 <= t < dst1: t -= datetime.timedelta(hours=1)
    rad = math.pi / 180
    n = t.timestamp() / 86400 + 2440587.5 - 2451545.0
    g = (357.529 + 0.98560028 * n) * rad
    q = 280.459 + 0.98564736 * n
    Lm = (q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) * rad
    e = (23.439 - 0.00000036 * n) * rad
    ra = math.atan2(math.cos(e) * math.sin(Lm), math.cos(Lm))
    dec = math.asin(math.sin(e) * math.sin(Lm))
    gmst = ((18.697374558 + 24.06570982441908 * n) % 24 + 24) % 24
    Ha = (gmst * 15 + lon) * rad - ra; phi = lat * rad
    el = math.asin(math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(Ha))
    az = math.atan2(-math.sin(Ha), math.tan(dec) * math.cos(phi) - math.sin(phi) * math.cos(Ha))
    return az % (2 * math.pi), el

def smoothstep(a, b, x):
    x = min(max((x - a) / (b - a), 0.0), 1.0); return x * x * (3 - 2 * x)

def sky_and_sun(date_str, hour):
    az, el = sun_position(date_str, hour)
    eld = math.degrees(el); day = smoothstep(-1, 8, eld)
    sc = bpy.context.scene
    w = bpy.data.worlds.get("cielo") or bpy.data.worlds.new("cielo"); sc.world = w
    w.use_nodes = True; nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = node(nt, "ShaderNodeOutputWorld"); bg = node(nt, "ShaderNodeBackground")
    sky = node(nt, "ShaderNodeTexSky")
    for t in ("MULTIPLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try: sky.sky_type = t; break
        except Exception: pass
    try:
        # Cycles mette il sole in (-sin r, cos r) con r = sun_rotation: con Y = nord basta r = -azimut
        sky.sun_elevation = el; sky.sun_rotation = (-az) % (2 * math.pi); sky.sun_disc = False
    except Exception: pass
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.03 + 0.32 * day
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    for ob in [o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN"]: bpy.data.objects.remove(ob)
    if day > 0:
        ld = bpy.data.lights.new("sole", "SUN"); ld.energy = 4.5 * day; ld.angle = math.radians(0.6)
        ld.color = colorsys.hls_to_rgb(0.09, 0.62 + 0.3 * smoothstep(2, 30, eld), 0.9)
        so = bpy.data.objects.new("sole", ld); ROOT.objects.link(so)
        s = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
        so.rotation_euler = (-s).to_track_quat("-Z", "Y").to_euler()
    print(f"SOLE {date_str} {hour:05.2f}: azimut {math.degrees(az):.0f}°, elevazione {eld:.0f}°", flush=True)

# ----------------------------------------------------------------------------
# CAMERE, VISIBILITÀ, RENDER
# ----------------------------------------------------------------------------
def cameras():
    out = {}
    for name, c in CAMERAS.items():
        cd = bpy.data.cameras.new(name); cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24
        cd.lens = 12 / math.tan(math.radians(FOV_Y / 2)); cd.clip_start = 0.05; cd.clip_end = 2000
        ob = bpy.data.objects.new(name, cd); ROOT.objects.link(ob)
        pos, tgt = Vector(V(*c["pos"])), Vector(V(*c["tgt"]))
        ob.location = pos; d = tgt - pos
        # vista dall'alto: nord in su, come nel viewer
        ob.rotation_euler = Euler((0, 0, 0)) if abs(d.normalized().z) > 0.999 else d.to_track_quat("-Z", "Y").to_euler()
        out[name] = ob
    return out

def set_visibility(cam, a, lights):
    upper = CAMERAS[cam].get("upper", True)
    show = dict(upper=upper and not a.no_p1, roof=upper and not a.no_roof,
                kitchen=not a.no_kitchen, furniture=not a.no_furniture, sofa=not a.no_sofa, lights=lights)
    for g, v in show.items():
        GROUPS[g].hide_render = GROUPS[g].hide_viewport = not v

def apply_preset(colore):
    for key, rough, suffix in (("pavimento", 0.85, ""), ("portico", 0.92, "_portico")):   # portico: versione R11
        m = m_cotto(colore, rough, suffix)
        for ob in FLOOR_OBJS.get(key, []): ob.data.materials[0] = m

def render_setup(preview, gpu):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"
    sc.cycles.samples = 24 if preview else 256
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.cycles.max_bounces = 8; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.transparent_max_bounces = 16                            # gelosie viste attraverso altre gelosie
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

def is_black(path):
    # un render interrotto dalla GPU viene salvato tutto nero: lo riconosciamo per riprovare
    import numpy as np
    im = bpy.data.images.load(path); px = np.empty(im.size[0] * im.size[1] * 4, np.float32)
    im.pixels.foreach_get(px); bpy.data.images.remove(im)
    return float(px.reshape(-1, 4)[:, :3].max()) < 0.02

def main():
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="render")
    ap.add_argument("--preset", action="append", choices=PRESETS)
    ap.add_argument("--scene", action="append", choices=SCENES)
    ap.add_argument("--camera", action="append", choices=list(CAMERAS))
    ap.add_argument("--var-pt", default="E", choices=list(VAR_PT), help="variante finestre piano terra (viewer)")
    ap.add_argument("--var-p1", default="B", choices=list(VAR_P1), help="variante finestre primo piano (viewer)")
    ap.add_argument("--data", default=datetime.date.today().isoformat(), help="AAAA-MM-GG (default: oggi, come il viewer)")
    ap.add_argument("--ora", type=float, default=16.0, help="ora locale della scena giorno (16 = 16:00)")
    ap.add_argument("--ora-sera", type=float, default=20.5, help="ora locale della scena sera")
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--exposure", type=float, default=None)
    ap.add_argument("--no-p1", action="store_true", help="nasconde il primo piano")
    ap.add_argument("--no-roof", action="store_true", help="nasconde il tetto")
    ap.add_argument("--no-kitchen", action="store_true", help="nasconde la cucina (Sakura)")
    ap.add_argument("--no-furniture", action="store_true", help="nasconde l'arredo indicativo")
    ap.add_argument("--no-sofa", action="store_true", help="nasconde solo il divano")
    a = ap.parse_args(argv)
    reset(); build(a.var_pt, a.var_p1); cams = cameras(); render_setup(a.preview, a.gpu)
    presets = a.preset or list(PRESETS); scenes = a.scene or list(SCENES); camnames = a.camera or list(CAMERAS)
    sc = bpy.context.scene
    if a.build_only:
        apply_preset(presets[0]); sky_and_sun(a.data, a.ora if scenes[0] == "giorno" else a.ora_sera)
        set_visibility(camnames[0], a, scenes[0] == "sera"); sc.camera = cams[camnames[0]]; return
    out = bpy.path.abspath(a.out); os.makedirs(out, exist_ok=True)
    for pn in presets:
        apply_preset(pn)
        for sk in scenes:
            sky_and_sun(a.data, a.ora if sk == "giorno" else a.ora_sera)
            base = a.exposure if a.exposure is not None else (1.0 if sk == "giorno" else -0.2)
            for cn in camnames:
                sc.view_settings.exposure = base + CAMERAS[cn].get("exp", {}).get(sk, 0.0)
                set_visibility(cn, a, sk == "sera")
                sc.camera = cams[cn]
                sc.render.filepath = os.path.join(out, f"{cn}__PT-{a.var_pt}__{pn}__{sk}.png")
                for tentativo in range(3):
                    print("RENDER", sc.render.filepath, flush=True)
                    bpy.ops.render.render(write_still=True)
                    if not is_black(sc.render.filepath): break
                    print("RENDER NERO, lo rifaccio", flush=True)   # a volte Cycles su GPU si interrompe senza errori

if __name__ == "__main__":
    main()

"""
FIENILE - Importa il divano IKEA NOCKEBY (3 posti + pouf) dal file 3ds Max e lo prepara per render e viewer.

Si lancia una volta sola, quando cambia il modello o il rivestimento. Produce:
  src/modelli/nockeby.blend          piena risoluzione, per fienile_pt_render.py
  src/modelli/nockeby.glb            alleggerito, per il viewer 3D
  src/texture/divano/*.jpg           tessuti (verde foresta, lino, grigio) e trama per il rilievo

Il .max (3ds Max 2015 + V-Ray, da 3dsmj.com) contiene un angolare con chaise, un 3 posti, un pouf, cuscini
e un plaid. Lo legge l'estensione "Import Autodesk MAX" (io_scene_max, extensions.blender.org), che però
importa solo la mesh di base: il TurboSmooth di 3ds Max è rifatto qui con una suddivisione, i materiali
V-Ray sono rifatti con le texture del pacchetto. Cuscini e plaid (simulazione Cloth) arrivano già deformati.
Le gambe a slitta del modello sono sostituite da quelle aftermarket di casa (GAMBE): cilindri in legno scuro
negli angoli del fondo, e la scocca sollevata della loro altezza.

Assi e origine come gli altri oggetti del viewer: metri, schienale verso est (+x), seduta rivolta a ovest,
origine al centro dell'ingombro a terra. Il glb (y in alto) ha quindi x = est e z = sud come il viewer.

Uso:
  blender -b -P importa_divano.py -- --src "~/Downloads/Sofas and ottoman IKEA NOCKEBY (max 2011)"
"""
import bpy, bmesh, sys, os, argparse, addon_utils
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MODELLI = os.path.normpath(os.path.join(HERE, "..", "modelli"))
OUT_TEX = os.path.normpath(os.path.join(HERE, "..", "texture", "divano"))

# parti del file .max (nome dopo il prefisso del sito) → ruolo
DIVANO = {
    "Box058": "verde", "Box062": "verde",            # braccioli
    "Box061": "verde",                               # scocca con schienale
    "Box059": "verde", "Box060": "verde",            # cuscini della seduta
    "526746": "verde",                               # cuscini dello schienale
    "5788789656": "bianco", "Object007": "bianco", "Object008": "grigio",   # cuscini decorativi
}
POUF = {
    "Box039": "verde", "Box040": "verde",            # cuscino e base
    "5859468": "lino",                               # plaid
}
# gambe aftermarket di divano e pouf: cilindri in legno scuro alti 20 cm, negli angoli del fondo della scocca,
# con il fianco a 5 cm dai due bordi vicini (diametro presunto: 5 cm)
GAMBE = dict(h=0.20, d=0.05, margine=0.05, lati=32, colore="#3a2a1f")
SMUSSA = {k for k in (*DIVANO, *POUF) if k.startswith("Box")}   # mesh grezze che in Max avevano TurboSmooth

# Tessuti: (sorgente, colore sRGB o None = colori della foto, contrasto della trama, lato del tassello in metri).
# Il verde foresta tinge la trama in bianco e nero del pacchetto (la "bump" del Beddinge).
TESSUTI = {
    "verde":  ("beddinge-three-seat-sofa bump.jpg", "#2f4a37", 0.35, 0.22),
    "bianco": ("Canvas-and-linen.jpg", "#ece6da", 0.25, 0.40),
    "grigio": ("beddinge-three-seat-sofa grey diffuse.jpg", None, 1.0, 0.22),
    "lino":   ("Canvas-and-linen.jpg", None, 1.0, 0.40),
}
TRAMA = "beddinge-three-seat-sofa bump.jpg"
RIDUZIONE_GLB = 0.25   # frazione di facce che resta nel glb del viewer

def load_px(path, size=1024):
    im = bpy.data.images.load(path); im.scale(size, size)
    px = np.empty(size * size * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im)
    return px.reshape(size, size, 4)

def save_px(px, path):
    n = px.shape[0]; im = bpy.data.images.new(os.path.basename(path), n, n)
    im.pixels.foreach_set(px.ravel()); im.filepath_raw = path; im.file_format = "JPEG"
    sc = bpy.context.scene; sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 88
    im.save_render(path, scene=sc); bpy.data.images.remove(im)

def make_textures(src):
    os.makedirs(OUT_TEX, exist_ok=True)
    bpy.context.scene.view_settings.view_transform = "Standard"   # save_render non deve applicare AgX/Filmic
    out = {}
    for key, (fn, col, contrast, _) in TESSUTI.items():
        px = load_px(os.path.join(src, fn))
        if col:
            lum = px[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            k = 1 + contrast * (lum / lum.mean() - 1)
            c = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)
            px[..., :3] = np.clip(c[None, None, :] * k[..., None], 0, 1)   # pixel di un'immagine 8 bit = sRGB
        out[key] = os.path.join(OUT_TEX, f"{key}.jpg"); save_px(px, out[key])
    px = load_px(os.path.join(src, TRAMA), 512); out["trama"] = os.path.join(OUT_TEX, "trama.jpg"); save_px(px, out["trama"])
    return out

def make_materials(tex):
    mats = {}
    for key, (_, _, _, tile) in TESSUTI.items():
        m = bpy.data.materials.new(f"divano_{key}"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes["Principled BSDF"]
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(tex[key]); nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = 0.9
        p.inputs["Sheen Weight"].default_value = 0.6; p.inputs["Sheen Roughness"].default_value = 0.4
        if key in ("verde", "grigio"):   # rilievo della trama (solo render: il glb lo ignora)
            tb = nt.nodes.new("ShaderNodeTexImage"); tb.image = bpy.data.images.load(tex["trama"])
            tb.image.colorspace_settings.name = "Non-Color"
            b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = 0.3
            b.inputs["Distance"].default_value = 0.001
            nt.links.new(tb.outputs["Color"], b.inputs["Height"]); nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
        m["tile"] = tile; mats[key] = m
    m = bpy.data.materials.new("divano_legno_scuro"); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]; h = GAMBE["colore"]
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    p.inputs["Base Color"].default_value = [((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c] + [1]
    p.inputs["Roughness"].default_value = 0.45; m["tile"] = 1.0; mats["legno"] = m
    return mats

def short(name): return name.split("  ")[-1].strip()

def box_uv(ob):
    """UV a proiezione cubica in metri / tassello del materiale: la trama ha la stessa scala su tutti i pezzi."""
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    tiles = [m.get("tile", 1.0) for m in me.materials]
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [i for i in range(3) if i != ax]; t = tiles[f.material_index]
        for l in f.loops: l[uv].uv = (l.vert.co[a] / t, l.vert.co[b] / t)
    bm.to_mesh(me); bm.free()

def gambe(x0, x1, y0, y1, mat):
    """Le 4 gambe negli angoli del rettangolo (x0..x1, y0..y1); salgono 3 cm dentro il fondo arrotondato."""
    r, h, m = GAMBE["d"] / 2, GAMBE["h"], GAMBE["margine"]
    bm = bmesh.new()
    for x in (x0 + m + r, x1 - m - r):
        for y in (y0 + m + r, y1 - m - r):
            g = bmesh.ops.create_cone(bm, cap_ends=True, segments=GAMBE["lati"], radius1=r, radius2=r, depth=h + 0.03)
            bmesh.ops.translate(bm, verts=g["verts"], vec=(x, y, (h + 0.03) / 2))
    me = bpy.data.meshes.new("gambe"); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    for f in me.polygons: f.use_smooth = abs(f.normal.z) < 0.5      # fianchi lisci, basi piatte
    ob = bpy.data.objects.new("gambe", me); bpy.context.scene.collection.objects.link(ob)
    vg = ob.vertex_groups.new(name="gambe"); vg.add(range(len(me.vertices)), 1.0, "REPLACE")
    return ob

def assemble(name, parts, objs, mats, footprint, base):
    """Unisce le parti in un solo oggetto: metri, schienale a est, origine al centro dell'ingombro a terra.
    `base` è la parte su cui poggiano le gambe: il suo fondo va a GAMBE["h"] da terra."""
    obs = []
    for key, role in parts.items():
        ob = objs[key]
        if key in SMUSSA:
            md = ob.modifiers.new("smussa", "SUBSURF"); md.levels = md.render_levels = 2
            bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier=md.name)
        ob.data.materials.clear(); ob.data.materials.append(mats[role])
        for poly in ob.data.polygons: poly.material_index = 0
        ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4)
        obs.append(ob)
    pts = [v.co for k in footprint for v in objs[k].data.vertices]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2; cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    z0 = min(p.z for p in pts)
    # in Max la seduta guarda verso -Y: ruotata di -90° su Z guarda verso -X (ovest)
    M = Matrix.Rotation(-np.pi / 2, 4, "Z") @ Matrix.Scale(0.001, 4) @ Matrix.Translation((-cx, -cy, -z0))
    for ob in obs: ob.data.transform(M)
    fondo = [v.co for v in objs[base].data.vertices if v.co.z < 0.02]
    x0, x1 = min(p.x for p in fondo), max(p.x for p in fondo); y0, y1 = min(p.y for p in fondo), max(p.y for p in fondo)
    for ob in obs: ob.data.transform(Matrix.Translation((0, 0, GAMBE["h"])))
    obs.append(gambe(x0, x1, y0, y1, mats["legno"]))
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs: ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = ob.data.name = name
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(ob.data); bm.free()
    for f in ob.data.polygons:   # tessuti lisci; le gambe hanno già le basi piatte
        if ob.data.materials[f.material_index] is not mats["legno"]: f.use_smooth = True
    box_uv(ob)
    d = ob.dimensions; print(f"MODELLO {name}: {d.x * 100:.0f} × {d.y * 100:.0f} × {d.z * 100:.0f} cm, {len(ob.data.polygons)} facce")
    return ob

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="~/Downloads/Sofas and ottoman IKEA NOCKEBY (max 2011)")
    a = ap.parse_args(argv); src = os.path.expanduser(a.src)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    if not addon_utils.enable("bl_ext.user_default.io_scene_max", default_set=True):
        sys.exit("Serve l'estensione 'Import Autodesk MAX' (io_scene_max) da extensions.blender.org")
    bpy.ops.import_scene.max(filepath=os.path.join(src, "2011.max"))

    objs = {}
    for ob in list(bpy.data.objects):
        k = short(ob.name)
        if ob.type == "MESH" and k in DIVANO.keys() | POUF.keys(): objs[k] = ob
        else: bpy.data.objects.remove(ob)
    missing = (DIVANO.keys() | POUF.keys()) - objs.keys()
    if missing: sys.exit(f"Parti mancanti nel .max: {sorted(missing)}")
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    for im in list(bpy.data.images): bpy.data.images.remove(im)

    mats = make_materials(make_textures(src))
    divano = assemble("divano", DIVANO, objs, mats, ["Box058", "Box061", "Box062"], "Box061")
    pouf = assemble("pouf", POUF, objs, mats, ["Box039", "Box040"], "Box040")
    pouf.location.y = -1.5   # solo per vederli affiancati aprendo il .blend; chi li usa imposta la posizione

    os.makedirs(OUT_MODELLI, exist_ok=True)
    for im in bpy.data.images: im.filepath = bpy.path.relpath(im.filepath, start=OUT_MODELLI)
    bpy.context.preferences.filepaths.save_version = 0   # niente nockeby.blend1
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_MODELLI, "nockeby.blend"), relative_remap=False, compress=True)

    # glb del viewer: facce ridotte, origine di ogni oggetto al suo posto
    pouf.location.y = 0
    for ob in (divano, pouf):
        md = ob.modifiers.new("riduci", "DECIMATE"); md.ratio = RIDUZIONE_GLB
        md.vertex_group = "gambe"; md.invert_vertex_group = True   # le gambe restano cilindri
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_MODELLI, "nockeby.glb"), export_format="GLB",
                              export_apply=True, export_image_format="JPEG", export_jpeg_quality=80,
                              export_yup=True)
    print("GLB", os.path.getsize(os.path.join(OUT_MODELLI, "nockeby.glb")) // 1024, "KB")

if __name__ == "__main__":
    main()

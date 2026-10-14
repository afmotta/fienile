"""Track clean-up after autorouting: micro-segments, collinear overlaps, off-grid coordinates."""
import math
import pcbnew

TOL = 1000          # 1 um, in KiCad internal units (nm)
MICRO = 10000       # segments shorter than 10 um are removed


def _segs(b):
    return [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]


def _same(p, q):
    return abs(p.x - q.x) <= TOL and abs(p.y - q.y) <= TOL


def remove_micro(b):
    n = 0
    for t in _segs(b):
        if t.GetLength() >= MICRO:
            continue
        a, c = t.GetStart(), t.GetEnd()
        for o in _segs(b):          # re-attach neighbours that ended on the far end
            if o is t or o.GetNetCode() != t.GetNetCode() or o.GetLayer() != t.GetLayer():
                continue
            if _same(o.GetStart(), c):
                o.SetStart(a)
            if _same(o.GetEnd(), c):
                o.SetEnd(a)
        b.Remove(t)
        n += 1
    return n


def merge_collinear(b):
    """Merge collinear overlapping segments of the same net/layer; drop narrower ones fully covered by wider."""
    merged = 0
    changed = True
    while changed:
        changed = False
        segs = _segs(b)
        for i, s in enumerate(segs):
            ax, ay, bx, by = s.GetStart().x, s.GetStart().y, s.GetEnd().x, s.GetEnd().y
            dx, dy = bx - ax, by - ay
            ln = math.hypot(dx, dy)
            if ln == 0:
                continue
            for o in segs[i + 1:]:
                if o.GetNetCode() != s.GetNetCode() or o.GetLayer() != s.GetLayer():
                    continue
                pts = [o.GetStart(), o.GetEnd()]
                if any(abs((p.x - ax) * dy - (p.y - ay) * dx) / ln > TOL for p in pts):
                    continue
                t0, t1 = sorted(((p.x - ax) * dx + (p.y - ay) * dy) / ln for p in pts)
                if min(t1, ln) - max(t0, 0) < -TOL:      # disjoint
                    continue
                ws, wo = s.GetWidth(), o.GetWidth()
                if ws == wo:
                    lo, hi = min(0, t0), max(ln, t1)
                    ux, uy = dx / ln, dy / ln
                    s.SetStart(pcbnew.VECTOR2I(int(round(ax + ux * lo)), int(round(ay + uy * lo))))
                    s.SetEnd(pcbnew.VECTOR2I(int(round(ax + ux * hi)), int(round(ay + uy * hi))))
                    b.Remove(o)
                elif ws > wo and t0 >= -TOL and t1 <= ln + TOL:
                    b.Remove(o)
                elif wo > ws and t0 <= TOL and t1 >= ln - TOL:
                    b.Remove(s)
                else:
                    continue
                merged += 1
                changed = True
                break
            if changed:
                break
    return merged


def snap_footprints(b):
    n = 0
    for f in b.GetFootprints():
        p = f.GetPosition()
        q = pcbnew.VECTOR2I(int(round(p.x / 1000.0)) * 1000, int(round(p.y / 1000.0)) * 1000)
        if q.x != p.x or q.y != p.y:
            f.SetPosition(q)
            n += 1
    return n


def run(b):
    m = remove_micro(b)
    c = merge_collinear(b)
    m += remove_micro(b)
    print(f"cleanup: {m} micro-segmenti rimossi, {c} sovrapposizioni collineari unite")

"""Athena Desk Orb - printable case: base, top plate, mid deck, BME280 pod (STL).

    python orb_case.py                 # writes the STLs to ../stl
    python orb_case.py dome_id=46.5    # after measuring your bulb dome's rim

The desk orb and the smart desk in one (11 Oct 2026): mains-adapter powered
(12 V), no battery. All sizes in mm - measure your parts and change the values
below or pass name=value. Print PLA/PETG, 0.2 mm, 3 walls, 20% infill, no
supports: base upright, plate/deck flat, pod open side up.

Front (+y): OLED window on a flat bezel, radar window (wall thinned to 1.2 mm),
mic hole. Right (+x): listen button. Back (-y): 12 V DC jack, LED-strip and
fan cable exits, BME280 pod cable hole. Left: vents. Top plate: LED ring
pocket, dome lip, light-sensor hole outside the dome, vents.
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import Manifold, set_circular_segments

P = dict(
    od=90.0, height=70.0, wall=2.4, floor=2.0, deck_z=30.0,
    oled_win_w=25.0, oled_win_h=14.0, oled_z=48.0, oled_hole_dx=23.0, oled_hole_dz=23.5,
    radar_w=26.0, radar_h=20.0, radar_z=20.0, radar_skin=1.2,
    mic_d=3.0, mic_z=62.0, mic_x=-22.0,
    btn_d=12.2, btn_z=50.0,                                   # PBS-33B 12 mm push button (Robu, 11 Oct)
    jack_d=8.2, jack_x=-18.0, jack_z=12.0,
    cable_d=5.5, cable_xs=(8.0,), cable_z=12.0,               # LED strip cable (no fan since 11 Oct)
    pod_hole_d=4.5, pod_x=30.0, pod_z=24.0,
    plate_t=3.0, ring_od=44.6, ring_seat=1.8, wire_hole=30.0, dome_id=47.0, lip_h=3.0,
    lux_d=6.0, lux_r=37.0,
)
for arg in sys.argv[1:]:
    k, v = arg.split("=")
    P[k] = float(v)
set_circular_segments(160)
OUT = Path(__file__).resolve().parent.parent / "stl"
R, RI = P["od"] / 2, P["od"] / 2 - P["wall"]
RECESS_R = RI + 0.9


def cyl(h, r, x=0, y=0, z=0):
    return Manifold.cylinder(h, r).translate([x, y, z])


def box(w, d, h, x=0, y=0, z=0):
    return Manifold.cube([w, d, h]).translate([x - w / 2, y - d / 2, z])


def through_y(dia, x, z, y0, length):
    return Manifold.cylinder(length, dia / 2).rotate([-90, 0, 0]).translate([x, y0, z])


def base():
    H, fz = P["height"], P["floor"]
    b = cyl(H, R) - cyl(H, RI, z=fz)
    b = b - cyl(P["plate_t"], RECESS_R, z=H - P["plate_t"])
    # front: a flat bezel behind the curved wall for the OLED, window through both
    half = 17.0
    flat_y = np.sqrt(RI ** 2 - half ** 2) - 0.6
    bez = box(2 * half, RI - flat_y + 1, 32, 0, (flat_y + RI + 1) / 2, P["oled_z"] - 16) ^ cyl(H, RI + 0.5)
    b = b + bez
    b = b - box(P["oled_win_w"], 20, P["oled_win_h"], 0, R, P["oled_z"] - P["oled_win_h"] / 2)
    for dx in (-1, 1):
        for dz in (-1, 1):
            x, z = dx * P["oled_hole_dx"] / 2, P["oled_z"] + dz * P["oled_hole_dz"] / 2
            b = b + (Manifold.cylinder(2.6, 2.4).rotate([90, 0, 0]).translate([x, flat_y, z])
                     - Manifold.cylinder(2.6, 0.85).rotate([90, 0, 0]).translate([x, flat_y, z]))
    # radar: wall skimmed from inside to an even 1.2 mm over the window
    skim = (cyl(P["radar_h"], R - P["radar_skin"], z=P["radar_z"] - P["radar_h"] / 2)
            ^ box(P["radar_w"], R, P["radar_h"], 0, R / 2 + 1, P["radar_z"] - P["radar_h"] / 2))
    b = b - skim
    b = b + (box(P["radar_w"] + 4, 5, 1.6, 0, RI - 4, P["radar_z"] - P["radar_h"] / 2 - 1.6) ^ cyl(H, RI + 0.5))
    b = b - Manifold.cylinder(10, P["mic_d"] / 2).rotate([-90, 0, 0]).translate([P["mic_x"], R - 6, P["mic_z"]])
    # right: listen button
    b = b - Manifold.cylinder(10, P["btn_d"] / 2).rotate([0, 90, 0]).translate([R - 5, 0, P["btn_z"]])
    # back: DC jack, cable exits with zip-tie bars, BME280 pod cable
    b = b - through_y(P["jack_d"], P["jack_x"], P["jack_z"], -R - 1, 8)
    for cx in P["cable_xs"]:
        b = b - through_y(P["cable_d"], cx, P["cable_z"], -R - 1, 8)
        b = b + (box(9, 3, 6, cx, -RI + 9, fz) - box(9, 1.6, 2.4, cx, -RI + 9, fz + 1.2))
    b = b - through_y(P["pod_hole_d"], P["pod_x"], P["pod_z"], -R - 1, 8)
    # left: vents low (cool air in) and high (warm air out)
    for z0 in (8.0, 40.0):
        for a in np.arange(150, 211, 12):
            t = np.radians(a)
            b = b - box(8, 2.2, 14, 0, 0, 0).rotate([0, 0, a + 90]).translate([np.cos(t) * R, np.sin(t) * R, z0])
    # three ledges for the mid deck
    for ang in (0, 120, 240):
        a = np.radians(ang)
        led = box(7, 4, 3, 0, 0, P["deck_z"] - 3).rotate([0, 0, ang - 90]).translate([np.cos(a) * (RI - 1.6), np.sin(a) * (RI - 1.6), 0])
        b = b + (led ^ cyl(H, RI + 0.5))
    return b


def plate():
    t = P["plate_t"]
    p = cyl(t, RECESS_R - 0.25)
    p = p - cyl(P["ring_seat"], P["ring_od"] / 2, z=t - P["ring_seat"])
    p = p - cyl(t, P["wire_hole"] / 2)
    lip_r = P["dome_id"] / 2 - 0.25
    p = p + (cyl(P["lip_h"], lip_r, z=t) - cyl(P["lip_h"], max(lip_r - 1.6, P["ring_od"] / 2 + 0.3), z=t))
    # light sensor outside the dome (back), so the ring's glow is not what it measures
    p = p - cyl(t, P["lux_d"] / 2, 0, -P["lux_r"])
    for a in (-60, -40, 40, 60):                                      # warm air out, either side of the sensor
        r = np.radians(a - 90)
        p = p - box(10, 2.4, t, 0, 0, 0).rotate([0, 0, a]).translate([np.cos(r) * 36.5, np.sin(r) * 36.5, 0])
    return p


def deck():
    r = RI - 0.4
    d = cyl(2.0, r)
    for x in (-(r - 4), r - 4):
        d = d - box(8, 16, 2, x, 0, 0)                               # wire passes
    d = d - box(36, 8, 2, 0, r - 4, 0)                               # clears the OLED bezel
    for x in np.arange(-24, 25, 8):
        d = d - cyl(2, 1.6, x, -20, 0)
    return d


def pod():
    """BME280 pod: hangs on the back, outside the case's heat; glue or screw it on."""
    w, d, h, t = 26.0, 22.0, 16.0, 1.6
    pd = box(w, d, h) - box(w - 2 * t, d - 2 * t, h - t, 0, 0, t)
    for x in (-7.5, -2.5, 2.5, 7.5):
        pd = pd - box(2.2, d + 2, h - 6, x, 0, 4)                   # air through both long sides
    pd = pd - cyl(t, P["pod_hole_d"] / 2, 0, 0)                     # cable, faces the case
    return pd


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as f:
        f.write(b"Athena desk orb".ljust(80, b" ") + np.uint32(len(t)).tobytes() + rec.tobytes())
    return len(t)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("orb_base", base), ("orb_top_plate", plate), ("orb_mid_deck", deck), ("orb_bme280_pod", pod)):
        m = fn()
        assert m.status().name == "NoError" and m.volume() > 0, name
        bb = m.bounding_box()
        n = write_stl(m, OUT / f"{name}.stl")
        print(f"{name}.stl  {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm  {m.volume()/1000:.1f} cm3  {n} tris")

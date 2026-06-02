#!/usr/bin/env pvpython
"""
visualize.py — scripted ParaView visualization of field.vtk.

Run with ParaView's bundled Python (NOT system python):
    pvpython visualize.py      # interactive-capable
    pvbatch  visualize.py      # headless / offscreen

Produces, in ./outputs/ :
    01_volume.png        volume rendering of the concentration scalar
    02_isosurfaces.png   Contour isosurfaces at several levels
    03_slice.png         an axis-aligned slice colored by concentration
    04_streamlines.png   Stream Tracer of the ABC-flow velocity, as tubes
    anim/frame_###.png   a 36-frame orbiting animation

Tested against ParaView 5.11+. If your version differs, the only likely
tweaks are the colormap preset name and the Stream Tracer seed type
(fallbacks are included).
"""
from paraview.simple import *
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
os.makedirs(os.path.join(OUT, "anim"), exist_ok=True)
PI = math.pi
RES = [1600, 1200]

paraview.simple._DisableFirstRenderCameraReset()

# ---- load ---------------------------------------------------------------
field = LegacyVTKReader(FileNames=[os.path.join(HERE, "field.vtk")])

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = RES
# force a flat white background (ParaView 6 defaults to a gray gradient palette)
for attr, val in [("UseColorPaletteForBackground", 0),
                  ("BackgroundColorMode", "Single Color")]:
    try:
        setattr(view, attr, val)
    except Exception:
        pass
view.Background = [1, 1, 1]          # white background for clean figures
view.OrientationAxesVisibility = 1


def solo(src):
    """Hide every source, then show `src`; return its display proxy."""
    for s in GetSources().values():
        try:
            Hide(s, view)
        except Exception:
            pass
    return Show(src, view)


def apply_preset(array_name, preset="Viridis (matplotlib)"):
    ctf = GetColorTransferFunction(array_name)
    try:
        ctf.ApplyPreset(preset, True)
    except Exception:
        pass
    return ctf


# ---- 1) volume rendering of concentration -------------------------------
d = solo(field)
ColorBy(d, ("POINTS", "concentration"))
d.SetRepresentationType("Volume")
apply_preset("concentration")
ResetCamera(view)
view.CameraPosition = [3 * PI, -2 * PI, 3 * PI]
view.CameraFocalPoint = [PI, PI, PI]
view.CameraViewUp = [0, 0, 1]
Render()
SaveScreenshot(os.path.join(OUT, "01_volume.png"), view, ImageResolution=RES)

# ---- 2) isosurfaces (Contour) -------------------------------------------
contour = Contour(Input=field)
contour.ContourBy = ["POINTS", "concentration"]
contour.Isosurfaces = [0.35, 0.70, 1.00]
d = solo(contour)
ColorBy(d, ("POINTS", "concentration"))
apply_preset("concentration")
d.Opacity = 0.65
Render()
SaveScreenshot(os.path.join(OUT, "02_isosurfaces.png"), view, ImageResolution=RES)

# ---- 3) slice -----------------------------------------------------------
sl = Slice(Input=field)
sl.SliceType = "Plane"
sl.SliceType.Origin = [PI, PI, PI]
sl.SliceType.Normal = [0, 0, 1]
d = solo(sl)
ColorBy(d, ("POINTS", "concentration"))
apply_preset("concentration")
Render()
SaveScreenshot(os.path.join(OUT, "03_slice.png"), view, ImageResolution=RES)

# ---- 4) streamlines of the velocity field -------------------------------
stream = StreamTracer(Input=field, Vectors=["POINTS", "velocity"])
stream.MaximumStreamlineLength = 6 * PI
try:                                   # ParaView 5.10+
    stream.SeedType = "Point Cloud"
    stream.SeedType.Center = [PI, PI, PI]
    stream.SeedType.Radius = 2.2
    stream.SeedType.NumberOfPoints = 300
except Exception:                      # older fallback
    stream.SeedType = "High Resolution Line Source"
    stream.SeedType.Point1 = [0.5, 0.5, 0.5]
    stream.SeedType.Point2 = [2 * PI - 0.5, 2 * PI - 0.5, 2 * PI - 0.5]
    stream.SeedType.Resolution = 200
tube = Tube(Input=stream)
tube.Radius = 0.03
d = solo(tube)
ColorBy(d, ("POINTS", "velocity"))     # color by speed (vector magnitude)
apply_preset("velocity", "Cool to Warm")
Render()
SaveScreenshot(os.path.join(OUT, "04_streamlines.png"), view, ImageResolution=RES)

# ---- 5) orbiting animation (PNG frames) ---------------------------------
cam = GetActiveCamera()
for i in range(36):
    cam.Azimuth(10)
    Render()
    SaveScreenshot(os.path.join(OUT, "anim", "frame_%03d.png" % i), view,
                   ImageResolution=[1000, 800])

print("Done. Figures + animation frames written to:", OUT)
print("Stitch the animation with ffmpeg:")
print("  ffmpeg -framerate 12 -i outputs/anim/frame_%03d.png "
      "-pix_fmt yuv420p outputs/orbit.mp4")

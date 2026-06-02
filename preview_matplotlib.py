#!/usr/bin/env python
"""
preview_matplotlib.py — render the synthetic field with matplotlib so the data
can be inspected (and portfolio figures produced) without ParaView installed.

This is the "sanity-check / preview" layer; visualize.py is the production
ParaView pipeline. Both operate on the same field defined in generate_field.py.

Outputs -> outputs/preview/
    slices.png        orthogonal mid-plane slices of the concentration field
    projections.png   max-intensity projections along X, Y, Z
    isosurface.png    marching-cubes isosurface of concentration (3D)
    streamplot.png    2D streamlines of velocity on a mid-Z slice
    quiver3d.png      subsampled 3D vector field (velocity)

Deps: numpy, matplotlib, scikit-image (marching cubes).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")               # headless / file output
import matplotlib.pyplot as plt
from skimage import measure

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "preview")
os.makedirs(OUT, exist_ok=True)

# ---- rebuild the same field as generate_field.py ------------------------
N = 64
L = 2.0 * np.pi
x = np.linspace(0.0, L, N)
X, Y, Z = np.meshgrid(x, x, x, indexing="ij")


def gaussian(cx, cy, cz, amp, sigma):
    r2 = (X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2
    return amp * np.exp(-r2 / (2.0 * sigma ** 2))


C = (gaussian(2.0, 2.0, 3.0, 1.00, 0.90)
     + gaussian(4.5, 3.5, 3.0, 0.80, 1.10)
     + gaussian(3.0, 5.0, 4.0, 0.60, 0.70))

A = B = Cc = 1.0
U = A * np.sin(Z) + Cc * np.cos(Y)
V = B * np.sin(X) + A * np.cos(Z)
W = Cc * np.sin(Y) + B * np.cos(X)
mid = N // 2
CMAP = "viridis"

# ---- 1) orthogonal slices ----------------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(15, 5))
for a, (data, title) in zip(ax, [
    (C[mid, :, :], "Slice  X = pi  (Y–Z plane)"),
    (C[:, mid, :], "Slice  Y = pi  (X–Z plane)"),
    (C[:, :, mid], "Slice  Z = pi  (X–Y plane)")]):
    im = a.imshow(data.T, origin="lower", cmap=CMAP, extent=[0, L, 0, L])
    a.set_title(title); a.set_xlabel("axis 1"); a.set_ylabel("axis 2")
    fig.colorbar(im, ax=a, fraction=0.046, pad=0.04, label="concentration")
fig.suptitle("Concentration field — orthogonal mid-plane slices", fontsize=14)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "slices.png"), dpi=130)
plt.close(fig)

# ---- 2) max-intensity projections --------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(15, 5))
for a, (axis, title) in zip(ax, [(0, "along X"), (1, "along Y"), (2, "along Z")]):
    im = a.imshow(C.max(axis=axis).T, origin="lower", cmap="inferno",
                  extent=[0, L, 0, L])
    a.set_title(f"Max-intensity projection {title}")
    fig.colorbar(im, ax=a, fraction=0.046, pad=0.04, label="max concentration")
fig.suptitle("Concentration field — max-intensity projections", fontsize=14)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "projections.png"), dpi=130)
plt.close(fig)

# ---- 3) isosurface (marching cubes) ------------------------------------
level = 0.45
verts, faces, normals, _ = measure.marching_cubes(C, level=level, spacing=(L / (N - 1),) * 3)
fig = plt.figure(figsize=(9, 8))
ax = fig.add_subplot(111, projection="3d")
ax.plot_trisurf(verts[:, 0], verts[:, 1], faces, verts[:, 2],
                cmap="viridis", lw=0.1, alpha=0.9)
ax.set_title(f"Concentration isosurface  (level = {level})")
ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
ax.view_init(elev=22, azim=-60)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "isosurface.png"), dpi=130)
plt.close(fig)

# ---- 4) 2D streamplot of velocity on a mid-Z slice ---------------------
fig, ax = plt.subplots(figsize=(8, 7))
xs = ys = np.linspace(0, L, N)
speed = np.sqrt(U[:, :, mid] ** 2 + V[:, :, mid] ** 2)
strm = ax.streamplot(xs, ys, U[:, :, mid].T, V[:, :, mid].T,
                     color=speed.T, cmap="cool", density=1.6, linewidth=1.0)
fig.colorbar(strm.lines, ax=ax, label="in-plane speed")
ax.set_title("Velocity field (ABC flow) — streamlines on Z = pi slice")
ax.set_xlabel("X"); ax.set_ylabel("Y")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "streamplot.png"), dpi=130)
plt.close(fig)

# ---- 5) 3D quiver (subsampled) -----------------------------------------
s = 6  # subsample stride
fig = plt.figure(figsize=(9, 8))
ax = fig.add_subplot(111, projection="3d")
ax.quiver(X[::s, ::s, ::s], Y[::s, ::s, ::s], Z[::s, ::s, ::s],
          U[::s, ::s, ::s], V[::s, ::s, ::s], W[::s, ::s, ::s],
          length=0.35, normalize=True, color="#2b6cb0", linewidth=0.6)
ax.set_title("Velocity field (ABC flow) — 3D quiver")
ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
ax.view_init(elev=20, azim=-55)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "quiver3d.png"), dpi=130)
plt.close(fig)

print("Wrote 5 preview figures to:", OUT)
for f in ["slices.png", "projections.png", "isosurface.png", "streamplot.png", "quiver3d.png"]:
    print("  -", f)

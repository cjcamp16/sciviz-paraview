#!/usr/bin/env python
"""
generate_field.py — build a synthetic 3D scientific dataset with NumPy and
export it to a ParaView-readable legacy VTK file (STRUCTURED_POINTS).

The dataset combines two physically-motivated fields on a regular grid:

  • concentration  (scalar) : superposition of 3D Gaussian "sources", as in a
                              diffusion / transport problem. Good for volume
                              rendering and isosurfaces.
  • velocity       (vector) : an Arnold–Beltrami–Childress (ABC) flow, a
                              classic analytic 3D velocity field. Good for
                              streamlines.

Only NumPy is required. Output: field.vtk
"""
import numpy as np

# ---- grid ----------------------------------------------------------------
N = 64                      # points per axis (64^3 = 262,144 points)
L = 2.0 * np.pi             # domain length per axis
x = np.linspace(0.0, L, N)
X, Y, Z = np.meshgrid(x, x, x, indexing="ij")   # X[i,j,k] = x[i], etc.

# ---- scalar field: sum of Gaussian concentration sources -----------------
def gaussian(cx, cy, cz, amp, sigma):
    r2 = (X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2
    return amp * np.exp(-r2 / (2.0 * sigma ** 2))

concentration = (
    gaussian(2.0, 2.0, 3.0, amp=1.00, sigma=0.90)
    + gaussian(4.5, 3.5, 3.0, amp=0.80, sigma=1.10)
    + gaussian(3.0, 5.0, 4.0, amp=0.60, sigma=0.70)
).astype(np.float32)

# ---- vector field: ABC flow (Arnold–Beltrami–Childress) ------------------
A = B = C = 1.0
U = (A * np.sin(Z) + C * np.cos(Y)).astype(np.float32)
V = (B * np.sin(X) + A * np.cos(Z)).astype(np.float32)
W = (C * np.sin(Y) + B * np.cos(X)).astype(np.float32)

# ---- write legacy VTK STRUCTURED_POINTS (ASCII) --------------------------
# VTK iterates x fastest, then y, then z -> ravel with Fortran order.
spacing = L / (N - 1)
n_pts = N ** 3
out = "field.vtk"

with open(out, "w") as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Synthetic concentration (scalar) + ABC-flow velocity (vector)\n")
    f.write("ASCII\n")
    f.write("DATASET STRUCTURED_POINTS\n")
    f.write(f"DIMENSIONS {N} {N} {N}\n")
    f.write("ORIGIN 0 0 0\n")
    f.write(f"SPACING {spacing:.6f} {spacing:.6f} {spacing:.6f}\n")
    f.write(f"POINT_DATA {n_pts}\n")

    # scalar
    f.write("SCALARS concentration float 1\n")
    f.write("LOOKUP_TABLE default\n")
    np.savetxt(f, concentration.ravel(order="F"), fmt="%.5f")

    # vector
    f.write("VECTORS velocity float\n")
    vec = np.column_stack([U.ravel("F"), V.ravel("F"), W.ravel("F")])
    np.savetxt(f, vec, fmt="%.5f")

print(f"Wrote {out}: {N}x{N}x{N} grid, {n_pts:,} points "
      f"(concentration scalar + velocity vector).")

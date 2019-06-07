import taichi_lang as ti
import numpy as np
import random
import cv2

real = ti.f32
dim = 2
n_particles = 8192 * 4
n_grid = 256
dx = 1.0 / n_grid
inv_dx = 1.0 / dx
dt = 1e-4
p_mass = 1.0
p_vol = 1.0
E = 100.0

scalar = lambda: ti.var(dt=real)
vec = lambda: ti.Vector(dim, dt=real)
mat = lambda: ti.Matrix(dim, dim, dt=real)

x, v = vec(), vec()
grid_v, grid_m = vec(), scalar()
C, J = mat(), scalar()


@ti.layout
def place():
  ti.root.dense(ti.k, n_particles).place(x, v, J, C)
  ti.root.dense(ti.ij, n_grid).place(grid_v, grid_m)


@ti.kernel
def clear_grid():
  for i, j in grid_m:
    grid_v[i, j] = ti.Vector([0.0, 0.0])
    grid_m[i, j] = 0.0


@ti.kernel
def p2g():
  for p in x:
    base = ti.cast(x[p] * inv_dx - 0.5, ti.i32)
    fx = x[p] * inv_dx - ti.cast(base, ti.f32)
    w = [0.5 * ti.sqr(1.5 - fx), 0.75 - ti.sqr(fx - 1.0),
         0.5 * ti.sqr(fx - 0.5)]
    stress = dt * p_vol * (J[p] - 1.0) * -4.0 * inv_dx * inv_dx * E
    affine = ti.Matrix([[stress, 0.0], [0.0, stress]]) + p_mass * C[p]
    for i in ti.static(range(3)):
      for j in ti.static(range(3)):
        dpos = (ti.cast(ti.Vector([i, j]), ti.f32) - fx) * dx
        weight = w[i](0) * w[j](1)
        grid_v[base(0) + i, base(1) + j] += weight * (p_mass * v[p] + affine @ dpos)
        grid_m[base(0) + i, base(1) + j] += weight * p_mass


bound = 3


@ti.kernel
def grid_op():
  for i, j in grid_m:
    if grid_m[i, j] > 0.0:
      inv_m = 1.0 / grid_m[i, j]
      grid_v[i, j] = inv_m * grid_v[i, j]
      grid_v(1)[i, j] = grid_v(1)[i, j] - dt * 9.8
      if i < bound:
        if grid_v(0)[i, j] < 0.0:
          grid_v(0)[i, j] = 0.0
      if i > n_grid - bound:
        if grid_v(0)[i, j] > 0.0:
          grid_v(0)[i, j] = 0.0
      if j < bound:
        if grid_v(1)[i, j] < 0.0:
          grid_v(1)[i, j] = 0.0
      if j > n_grid - bound:
        if grid_v(1)[i, j] > 0.0:
          grid_v(1)[i, j] = 0.0


@ti.kernel
def g2p():
  for p in x:
    base = ti.cast(x[p] * inv_dx - 0.5, ti.i32)
    fx = x[p] * inv_dx - ti.cast(base, ti.f32)
    w = [0.5 * ti.sqr(1.5 - fx), 0.75 - ti.sqr(fx - 1.0),
         0.5 * ti.sqr(fx - 0.5)]
    new_v = ti.Vector([0.0, 0.0])
    new_C = ti.Matrix([[0.0, 0.0], [0.0, 0.0]])

    for i in ti.static(range(3)):
      for j in ti.static(range(3)):
        dpos = ti.cast(ti.Vector([i, j]), ti.f32) - fx
        g_v = grid_v[base(0) + i, base(1) + j]
        weight = w[i](0) * w[j](1)
        new_v += weight * g_v
        new_C += 4.0 * weight * ti.outer_product(g_v, dpos) * inv_dx

    v[p] = new_v
    x[p] = x[p] + dt * v[p]
    J[p] = J[p] * (1.0 + dt * new_C.trace())
    C[p] = new_C


def main():
  for i in range(n_particles):
    x[i] = [random.random() * 0.4 + 0.2, random.random() * 0.4 + 0.2]
    v[i] = [0, -1]
    J[i] = 1.0

  for f in range(200):
    for s in range(150):
      clear_grid()
      p2g()
      grid_op()
      g2p()
    scale = 4
    img = np.zeros(shape=(scale * n_grid, scale * n_grid)) + 0.3
    for i in range(n_particles):
      p_x = int(scale * x(0)[i] / dx)
      p_y = int(scale * x(1)[i] / dx)
      img[p_x, p_y] = 1
    img = img.swapaxes(0, 1)[::-1]
    cv2.imshow('MPM', img)
    cv2.waitKey(1)
    cv2.imwrite('frame{:03d}.png'.format(f), img * 255)

if __name__ == '__main__':
  main()


import math
import os
import re
import cPickle as pickle

import numpy

class Map(object):
  def __init__(self, db, map_name):
    c = db.cursor()
    c.execute("""
      select id, division_id, srid,
             width, height,
             x_min, x_max,
             y_min, y_max
      from map
      where name = %s
    """, (map_name,))
    map_id, division_id, srid, width, height, x_min, x_max, y_min, y_max = c.fetchone()
    c.close()
    
    self.map_id, self.division_id, self.srid = map_id, division_id, srid
    self.width, self.height = width, height
    self.x_min, self.y_min, self.x_max, self.y_max = map(float, (x_min, y_min, x_max, y_max))


class Interpolator(object):
  """
  Linear interpolation for cartogram grids.
  """
  def __init__(self, grid_filename, the_map):
    self.m = the_map
    self.a = numpy.fromfile(grid_filename, sep=' ').reshape(3*self.m.height+1, 3*self.m.width+1, 2)

  def __call__(self, rx, ry, slide=1.0):
    x = (rx - self.m.x_min) * self.m.width  / (self.m.x_max - self.m.x_min) + self.m.width
    y = (ry - self.m.y_min) * self.m.height / (self.m.y_max - self.m.y_min) + self.m.height
    if x < 0 or x > 3 * self.m.width or y < 0 or y > 3 * self.m.height:
      return rx, ry
    
    ix, iy = int(x), int(y)
    dx, dy = x - ix, y - iy
    
    tx, ty = (1-dx)*(1-dy)*self.a[iy][ix] \
           + dx*(1-dy)*self.a[iy][ix+1]   \
           + (1-dx)*dy*self.a[iy+1][ix]   \
           + dx*dy*self.a[iy+1][ix+1]
    
    ix, iy = (
      (tx - self.m.width)  * (self.m.x_max - self.m.x_min) / self.m.width  + self.m.x_min,
      (ty - self.m.height) * (self.m.y_max - self.m.y_min) / self.m.height + self.m.y_min,
    )
    
    return (
      (1.0 - slide) * rx + slide * ix,
      (1.0 - slide) * ry + slide * iy,
    )
  
  def map(self, coords):
    return [ self(x, y) for x, y in coords ]

def is_newer(a, b):
  """Is the file a newer than (or, more precisely, not older than) b?
  """
  return os.stat(a).st_mtime >= os.stat(b).st_mtime

class FastInterpolator(object):
  """Faster linear interpolation, using scipy.interpolate.
  """
  def __init__(self, grid_filename, m):
    pickle_filename = grid_filename + ".pickled"
    if os.path.isfile(pickle_filename) and is_newer(pickle_filename, grid_filename):
      with open(pickle_filename, 'r') as f:
        self.x = pickle.load(f)
        self.y = pickle.load(f)
    else:
      self.load_cart(grid_filename, m)
      with open(pickle_filename, 'w') as f:
        pickle.dump(self.x, f, -1)
        pickle.dump(self.y, f, -1)
  
  def load_cart(self, grid_filename, m):
    import scipy.interpolate
    grid = numpy.fromfile(grid_filename, sep=' ').reshape(3*m.height+1, 3*m.width+1, 2)
    
    x_pts = (numpy.arange(3*m.width+1) - m.width) * (m.x_max - m.x_min) / m.width  + m.x_min
    y_pts = (numpy.arange(3*m.height+1) - m.height) * (m.y_max - m.y_min) / m.height  + m.y_min
    
    x_grid = (grid[:,:,0] - m.width) * (m.x_max - m.x_min) / m.width  + m.x_min
    y_grid = (grid[:,:,1] - m.height) * (m.y_max - m.y_min) / m.height  + m.y_min
    
    self.x = scipy.interpolate.RectBivariateSpline(y_pts, x_pts, x_grid, kx=1, ky=1)
    self.y = scipy.interpolate.RectBivariateSpline(y_pts, x_pts, y_grid, kx=1, ky=1)

  def __call__(self, rx, ry):
    return self.x(ry, rx), self.y(ry, rx)
  
  def map(self, coords):
    # map is much faster than calling __call__ repeatedly.
    c = numpy.array(coords)
    ys, xs = c[:,1], c[:,0]
    return zip(self.x.ev(ys, xs), self.y.ev(ys, xs))


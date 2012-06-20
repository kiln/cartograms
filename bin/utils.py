
import math
import numpy
import re

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

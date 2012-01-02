#!/usr/bin/python

import optparse
import sys

import shapely.wkb
import psycopg2

import utils

class AsSVG(object):
  def __init__(self, options):
    self.options = options
    self.db = psycopg2.connect("host=localhost")
    self.m = utils.Map(self.db, options.map)
    if options.cart:
      self.f = utils.Interpolator(options.cart, self.m)
    else:
      self.f = None
    
    if options.output:
      self.out = open(options.output, 'w')
    else:
      self.out = sys.stdout

  def print_robinson_path(self):
    c = self.db.cursor()
    try:
      c.execute("""
        select ST_AsEWKB(ST_Transform(ST_Segmentize(ST_GeomFromText(
          'POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))', 4326), 5), 954030))
      """)
      path_bin = c.fetchone()[0]
    finally:
      c.close()
  
    p = shapely.wkb.loads(str(path_bin))
    if self.f is None or self.options.static:
      print >>self.out, '<path id="robinson" d="{path}"/>'.format(path=self.polygon_as_svg(p))
    else:
      original_path = self.polygon_as_svg(p)
      morphed_path = self.polygon_as_svg(p)
      print """<path id="robinson" d="{original}">
        <animate dur="10s" repeatCount="indefinite" attributeName="d" 
           values="{original};{morphed};{morphed};{original};{original}"/>
      </path>""".format(original=original_path, morphed=morphed_path)

  def print_region_paths(self):
    c = self.db.cursor()
    try:
      if self.options.dataset:
        c.execute("""
          select region.name
               , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %s), %s)) g
               , exists(
                  select *
                  from data_value
                  join dataset on data_value.dataset_id = dataset.id
                  where dataset.name = %s
                  and data_value.region_id = region.id) has_data
          from region
          where region.division_id = %s
        """, (self.m.srid, self.options.simplification, self.options.dataset, self.m.division_id))
      else:
        c.execute("""
          select region.name
               , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %s), %s)) g
               , false
          from region
          where region.division_id = %s
        """, (self.m.srid, self.options.simplification, self.m.division_id))

      for iso2, g, has_data in c.fetchall():
        classes = "has-data" if has_data else "no-data"
        p = shapely.wkb.loads(str(g))
        if self.f is None or self.options.static:
          path = self.multipolygon_as_svg(p)
          if path:
            print >>self.out, '<path id="{iso2}" d="{path}" class="{classes}"/>'.format(iso2=iso2, path=path, classes=classes)
        else:
          original_path = self.multipolygon_as_svg(p)
          if original_path:
            morphed_path = self.multipolygon_as_svg(p)
            print """<path id="{iso2}" d="{original}" class="{classes}">
              <animate dur="10s" repeatCount="indefinite" attributeName="d" 
                  values="{original};{morphed};{morphed};{original};{original}"/>
            </path>""".format(iso2=iso2, original=original_path, morphed=morphed_path, classes=classes)
          
    finally:
      c.close()

  def polygon_ring_as_svg(self, ring):
      poly_arr = ["M"]
      first = True
      for x, y in ring.coords:
        if self.f:
          x, y = self.f(x, y)
        poly_arr.append("%.0f" % x)
        poly_arr.append("%.0f" % -y)
        if first:
          poly_arr.append("L")
          first = False
      poly_arr.pop(); poly_arr.pop() # Remove the last point
      poly_arr.append("Z")
      return poly_arr

  def polygon_as_svg(self, polygon):
    return " ".join(self.polygon_ring_as_svg(polygon.exterior))

  def multipolygon_as_svg(self, multipolygon):
    path_arr = []
    for g in multipolygon.geoms:
      path_arr.append(self.polygon_ring_as_svg(g.exterior))
      for interior in g.interiors:
        path_arr.append(self.polygon_ring_as_svg(interior))
  
    return " ".join(sum(path_arr, []))
  
  def print_circles(self):
    c = self.db.cursor()
    c.execute("""
    with t as (select ST_Transform(location, %s) p from {table_name})
    select ST_X(t.p), ST_Y(t.p) from t
    """.format(table_name=self.options.circles), (self.m.srid,) )
    if self.f is None:
      for x, y in c:
        print >>self.out, '<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>'.format(x=x, y=-y, r=self.options.circle_radius)
    elif self.options.static:
      for x, y in c:
        tx, ty = self.f(x, y)
        print >>self.out, '<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>'.format(x=tx, y=-ty, r=self.options.circle_radius)
    else:
      for x, y in c:
        tx, ty = self.f(x, y)
        print >>self.out, '<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}">'.format(x=x, y=-y, r=self.options.circle_radius)
        print >>self.out, '<animate dur="10s" repeatCount="indefinite" attributeName="cx" ' + \
                       'values="{x:.0f};{tx:.0f};{tx:.0f};{x:.0f};{x:.0f}"/>'.format(x=x, tx=tx)
        print >>self.out, '<animate dur="10s" repeatCount="indefinite" attributeName="cy" ' + \
                       'values="{y:.0f};{ty:.0f};{ty:.0f};{y:.0f};{y:.0f}"/>'.format(y=-y, ty=-ty)
        print >>self.out, '</circle>'
    c.close()

  def print_document(self):
    print >>self.out, """<?xml version="1.0" encoding="UTF-8"?>
  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%(width)d" height="%(height)d" viewBox="%(x_min).5f %(minus_y_max).5f %(x_extent).5f %(y_extent).5f">
    <style type="text/css">
      svg { background: #eee; }
      #robinson { fill: #9ec7f3; stroke: #999; stroke-width: 40000; }
      #bounds { fill: #9ec7f3; stroke: #9ec7f3; }
      path { fill: #f7d3aa; stroke: #a08070; stroke-width: %(stroke_width)d; }
      path.no-data { fill: white; }
      circle { fill: red; opacity: %(circle_opacity)f; }
    </style>
    <path id="bounds" d="M %(x_min).5f %(minus_y_max).5f h %(x_extent).5f v %(y_extent).5f h -%(x_extent).5f Z"/>
    """ % {
      "width": self.m.width, "height": self.m.height,
      "x_min": self.m.x_min, "minus_y_max": -self.m.y_max,
      "x_extent": self.m.x_max-self.m.x_min, "y_extent": self.m.y_max-self.m.y_min,
      "stroke_width": self.options.stroke_width,
      "circle_opacity": self.options.circle_opacity
    }
    
    if self.options.robinson:
      self.print_robinson_path()
    
    self.print_region_paths()
    if self.options.circles:
      self.print_circles()
    print >>self.out, "</svg>"

def main():
  global options
  parser = optparse.OptionParser()
  parser.add_option("", "--map",
                    action="store",
                    help="the name of the map to use")
  parser.add_option("", "--cart",
                    action="store",
                    help="the name of the file containing the cartogram grid")
  parser.add_option("", "--dataset",
                    action="store",
                    help="the name of the dataset (used to mark which regions have data)")
  
  parser.add_option("-o", "--output",
                    action="store",
                    help="the name of the output file (defaults to stdout)")
  
  parser.add_option("", "--simplification",
                    action="store", default=1000,
                    help="how much to simplify the paths (default %default)")
  parser.add_option("", "--stroke-width",
                    action="store", default=2000, type="int",
                    help="width of SVG strokes (default %default)")

  parser.add_option("", "--robinson",
                    action="store_true", default=False,
                    help="include the Robinson map outline")

  parser.add_option("", "--static",
                    action="store_true", default=False,
                    help="Do not animate")
  
  parser.add_option("", "--circles",
                    action="store",
                    help="the name of the table containing data points to plot")
  parser.add_option("", "--circle-radius",
                    action="store", default=500, type="int",
                    help="radius of circles (default %default)")
  parser.add_option("", "--circle-opacity",
                    action="store", default=0.1, type="float",
                    help="opacity of circles (default %default)")
  
  (options, args) = parser.parse_args()
  if args:
    parser.error("Unexpected non-option arguments")
  
  if not options.map:
    parser.error("Missing option --map")
  
  AsSVG(options=options).print_document()

main()

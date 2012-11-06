#!/usr/bin/python

import datetime
import json
import math
import optparse
import os
from pipes import quote as shell_quote
import cPickle as pickle
import re
import shlex
import sys

import shapely.wkb
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import psycopg2

import utils

class SimplifiedPolygonRing(object):
    def __init__(self, coords):
        self.coords = coords

class SimplifiedGeom(object):
    def __init__(self, exterior, interiors):
        self.exterior = exterior
        self.interiors = interiors

class SimplifiedMultipolygon(object):
  def __init__(self, region_name, geoms):
    self.region_name = region_name
    self.geoms = geoms

class MultipolygonSimplifier(object):
  def __init__(self, simplification_dict, simplification, interpolators, raw_key):
    self.simplification_dict = simplification_dict
    self.simplification = simplification
    self.interpolators = interpolators
    self.raw_key = raw_key
  
  def simplify(self, region_name, multipolygon, breakpoints):
    return [
      SimplifiedGeom(
        exterior=self._simplify(region_name, geom.exterior, breakpoints),
        interiors=[
          self._simplify(region_name, interior, breakpoints)
          for interior in geom.interiors
        ]
      )
      for geom in multipolygon.geoms
    ]
  
  def _simplify(self, region_name, ring, breakpoints):
    simplification = self.simplification_dict.get(region_name, self.simplification)
    
    prev = None
    ret = []
    for segment in self._segments(ring.coords, breakpoints):
      ls = LineString(segment)
      ls = ls.simplify(tolerance=simplification / self._max_stretch(segment), preserve_topology=False)
      
      for coord in ls.coords:
        if coord != prev:
          ret.append(coord)
        prev = coord
    
    return SimplifiedPolygonRing(ret)
  
  def _segments(self, coords, breakpoints):
    segments = [[]]
    for coord in coords:
      segments[-1].append(coord)
      if coord in breakpoints:
        segments.append([coord])
    
    if len(segments) > 1:
      # Join the first and last segments
      segments[0] = segments.pop() + segments[0]
    
    return segments
  
  def _segment_length(self, segment):
    return sum([
      math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))
      for (x1, y1), (x2, y2) in zip(segment, segment[1:])
    ])
  
  def _max_stretch(self, segment):
    l = self._segment_length(segment)
    if l == 0 or self.interpolators.keys() == [self.raw_key]:
      return 1
    
    max_stretch = max([
      self._segment_length(interpolator.map(segment))
      for interpolator in self.interpolators.values() if interpolator
    ])
    
    if max_stretch > l:
      return max_stretch / l
    else:
      return 1


class AsJSON(object):
  def __init__(self, options, carts):
    self.options = options
    self.carts = carts
    
    db_connection_data = []
    if options.db_host:
      db_connection_data.append("host=" + options.db_host)
    if options.db_name:
      db_connection_data.append(" dbname=" + options.db_name)
    if options.db_user:
      db_connection_data.append(" user=" + options.db_user)
    
    self.db = psycopg2.connect(" ".join(db_connection_data))
    self.m = utils.Map(self.db, options.map)
    
    if options.output:
      self.out = open(options.output, 'w')
    else:
      self.out = sys.stdout
    
    if self.options.simplification_json:
      self.simplification_dict = json.loads(self.options.simplification_json)
    else:
      self.simplification_dict = {}
  
  @staticmethod
  def _extract_cart_name(cart):
    n = re.sub(r".*/", "", cart)
    n = re.sub(r"\.cart$", "", n)
    return n
  
  def _init_carts(self):
    self.interpolators = {
      self.options.raw_key: None
    }
    for cart in self.carts:
      cart_name = self._extract_cart_name(cart)
      print >>sys.stderr, "Loading cartogram grid for {cart_name}...".format(cart_name=cart_name)
      self.interpolators[cart_name] = utils.FastInterpolator(cart, self.m)
  
  def region_paths(self):
    if self.options.load_regions:
      with open(self.options.load_regions, 'r') as f:
        while True:
          try:
            yield pickle.load(f)
          except EOFError:
            return
    
    if self.options.dump_regions:
      with open(self.options.dump_regions + ".new", 'w') as f:
        for region in self._region_paths(f):
          yield region
      os.rename(self.options.dump_regions + ".new", self.options.dump_regions)
    else:
      for region in self._region_paths():
        yield region
  
  def _region_paths(self, dump_file=None):
    simplifier = MultipolygonSimplifier(
        simplification_dict=self.simplification_dict,
        simplification=self.options.simplification,
        interpolators=self.interpolators,
        raw_key=self.options.raw_key,
    )
    
    c = self.db.cursor()
    try:
      c.execute("""
        select region.id
             , region.name
             , ST_AsEWKB(ST_Transform(region.the_geom, %(srid)s)) geom_wkb
             , ST_AsEWKB(ST_Transform(region.breakpoints, %(srid)s)) breakpoints_wkb
        from region
        where region.division_id = %(division_id)s
      """, {
          "srid": self.m.srid,
          "division_id": self.m.division_id
      })
      
      for region_id, region_name, geom_wkb, breakpoints_wkb in c:
        geom = shapely.wkb.loads(str(geom_wkb))
        breakpoints = set() if breakpoints_wkb is None else set((
          (point.x, point.y) for point in shapely.wkb.loads(str(breakpoints_wkb))
        ))
        
        smp = SimplifiedMultipolygon(region_name, simplifier.simplify(region_name, geom, breakpoints))
        if dump_file: pickle.dump(smp, dump_file, -1)
        yield smp
    
    finally:
      c.close()
  
  def print_region_paths(self):
    self._init_carts()
    
    print >>self.out, "// This file is auto-generated. Please do not edit."
    print >>self.out, "// Generated at {t} UTC.".format(t=str(datetime.datetime.utcnow()))
    print >>self.out, "// Generated by {c}".format(c=" ".join(map(shell_quote, sys.argv)))
    print >>self.out
    
    {
        "js": self.print_region_paths_js,
        "actionscript": self.print_region_paths_actionscript,
    }[self.options.format]()

  def print_region_paths_js(self):
    empty_object_json = json.dumps( dict(( (k, {}) for k in self.interpolators.keys() )) )
    print >>self.out, "var %s = %s;" % (self.options.data_var, empty_object_json,)
    
    for region in self.region_paths():
      print >>sys.stderr, "Extracting paths for {region_name}...".format(region_name=region.region_name)
      for k, path in self.multipolygon_as_svg(region).items():
        print >>self.out, "{data_var}[{k}][{region_name}] = {path};".format(
          data_var=self.options.data_var,
          k=json.dumps(k),
          region_name=json.dumps(region.region_name),
          path=json.dumps(path),
        )
  
  def print_region_paths_actionscript(self):
    paths_by_key = {}
    for region in self.region_paths():
      print >>sys.stderr, "Extracting paths for {region_name}...".format(region_name=region.region_name)
      for k, path in self.multipolygon_as_svg(region).items():
        paths_by_key.setdefault(k, []).append(path)
    
    print >>self.out, "package {"
    print >>self.out, "public class MapData {"
    print >>self.out, "  public var paths : Object = {};"
    print >>self.out, "  public function MapData() {"
    
    def try_int(x):
      try:
        return int(x)
      except ValueError:
        return x
    
    for k, paths in paths_by_key.iteritems():
      print >>self.out, "    paths[{k}] = {paths};".format(
        paths=json.dumps(map(try_int, re.split(r" +", " ".join(paths)) )),
        k=json.dumps(k),
      )
    
    print >>self.out, "  }"
    print >>self.out, "}}"
  
  def _transform(self, x, y):
    if not self.options.output_grid:
      return x, -y
    return (
      (x - self.m.x_min) * self.options.output_grid_width / (self.m.x_max - self.m.x_min),
      self.options.output_grid_height - (y - self.m.y_min) * self.options.output_grid_height / (self.m.y_max - self.m.y_min),
    )
  
  def polygon_ring_as_svg(self, ring, path_arrs):
    for k, path_arr in path_arrs.items():
      path_arr.append("M")
      first = True
      interpolator = self.interpolators.get(k)
      for x, y in interpolator.map(ring.coords) if interpolator else ring.coords:
        x, y = self._transform(x, y)
        path_arr.append("%.0f" % x)
        path_arr.append("%.0f" % y)
        if first:
          path_arr.append("L")
          first = False
      
      if path_arr[-1] == "L":
        # The path contains only one point, so skip it
        path_arr[-4:] = []
        return
      
      path_arr[-2:] = ["Z"] # The last point is presumably equal to the first
      
      if path_arr[-2] == "L":
        # The path contains only one point, so skip it
        path_arr[-5:] = []
        return

  def multipolygon_as_svg(self, region):
    path_arrs = dict((
      (k, []) for k in self.interpolators.keys()
    ))
    for g in region.geoms:
      self.polygon_ring_as_svg(g.exterior, path_arrs)
      for interior in g.interiors:
        self.polygon_ring_as_svg(interior, path_arrs)
  
    return dict((
      (k, " ".join(path_arr))
      for k, path_arr in path_arrs.items()
    ))
  
  def print_json(self):
    self.print_region_paths()

def main():
  global options
  parser = optparse.OptionParser()
  parser.add_option("", "--map",
                    action="store",
                    help="the name of the map to use")
  
  parser.add_option("", "--output-grid",
                    action="store",
                    help="the output grid, in the form <width>x<height>")
  
  parser.add_option("", "--simplification",
                    action="store", default=20000, type="int",
                    help="how much to simplify the paths (default %default)")
  parser.add_option("", "--simplification-json",
                    action="store",
                    help="A JSON-encoded dict of region name => simplification")
  
  parser.add_option("", "--format",
                    action="store",
                    default="js",
                    choices=["js", "actionscript"],
                    help="output format, js or actionscript (default %default).")
  parser.add_option("", "--data-var",
                    action="store",
                    default="data",
                    help="name of variable to use for the path data (default %default)")
  parser.add_option("", "--raw-key",
                    action="store",
                    default="_raw",
                    help="name of key to use for the raw map (default %default)")
  
  parser.add_option("", "--db-host",
                    action="store",
                    default="localhost",
                    help="database hostname (default %default)")
  parser.add_option("", "--db-name",
                    action="store",
                    help="database name")
  parser.add_option("", "--db-user",
                    action="store",
                    help="database username")
  
  # Dump and load regions
  #
  # This is useful in certain special circumstances:
  #
  # - if a new cartogram needs to be generated to add to an existing set,
  #   so that we do not want to generate a new and possibly different
  #   simplification.
  #
  # - if we need to generate a cartogram in a hurry for some reason, so
  #   do not want to wait for the raw paths to be loaded and the best
  #   simplification to be computed.
  parser.add_option("", "--dump-regions",
                    action="store",
                    help="name of a file into which to dump the region paths")
  parser.add_option("", "--load-regions",
                    action="store",
                    help="name of a file from which to load region paths")
  
  parser.add_option("-o", "--output",
                    action="store",
                    help="the name of the output file (defaults to stdout)")
  
  (options, carts) = parser.parse_args()
  
  if not options.map:
    parser.error("Missing option --map")
  
  if options.dump_regions and options.load_regions:
    parser.error("Cannot specify both --dump-regions and --load-regions")
  
  if options.output_grid:
    mo = re.match(r"^(\d+)x(\d+)$", options.output_grid)
    if mo is None:
      parser.error("Unrecognised value for --output-grid: " + options.output_grid)
    setattr(options, "output_grid_width", int(mo.group(1)))
    setattr(options, "output_grid_height", int(mo.group(2)))
  
  as_json = AsJSON(options=options, carts=carts)
  as_json.print_json()

main()

#!/usr/bin/python
# -*- encoding: utf-8 -*-

import optparse
import sys
import psycopg2

"""
Generate a density grid that can be fed to cart.
"""

parser = optparse.OptionParser()
parser.add_option("", "--dataset",
                action="store",
                help="the name of the dataset to use")
parser.add_option("", "--map",
                action="store",
                help="the name of the map to use")

parser.add_option("", "--zero",
                action="store", type="float", default=0.1,
                help="Value to use for regions with zero data values (default %default)")
parser.add_option("", "--missing",
                action="store", type="float", default=None,
                help="Value to use for regions with missing data (default %default)")
parser.add_option("", "--multiplier",
                action="store", default=1,
                help="the density multiplier (default %default)")

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

(options, args) = parser.parse_args()

if len(args) in (2,3) and not options.map and not options.dataset:
    # Legacy syntax
    dataset_name = args[0]
    map_name = args[1]
    multiplier = args[2] if len(args) == 3 else 1
else:
    if not options.map:
        parser.error("Missing option --map")
    if not options.dataset:
        parser.error("Missing option --dataset")
    if args:
        parser.error("Unexpected non-option arguments")
    
    dataset_name = options.dataset
    map_name = options.map
    multiplier = options.multiplier

db_connection_string = "host=" + options.db_host
if options.db_name:
    db_connection_string += " dbname=" + options.db_name
if options.db_user:
    db_connection_string += " user=" + options.db_user
db = psycopg2.connect(db_connection_string)

c = db.cursor()
c.execute("""
  select id, division_id, srid,
         width, height
  from map
  where name = %s
""", (map_name,))
map_id, division_id, srid, X, Y = c.fetchone()
c.close()

def get_global_density():
    c = db.cursor()
    try:
        c.execute("""
            select sum(data_value.value) / sum(region.area)
            from region
            join data_value on region.id = data_value.region_id
            join dataset on data_value.dataset_id = dataset.id
            where dataset.name = %s and region.division_id = %s
        """, (dataset_name, division_id))
        return c.fetchone()[0]
    finally:
        c.close()

def get_local_densities():
  c = db.cursor()
  try:
    c.execute("""
      select y, x, data_value.value / region.area density
         , grid.region_id
      from grid
      join region on grid.region_id = region.id
      left join (
         select region_id, value
         from data_value
         join dataset on data_value.dataset_id = dataset.id
         where dataset.name = %s
      ) data_value using (region_id)
      where grid.map_id = %s
      and grid.division_id = %s
      order by y, x
    """, (dataset_name, map_id, division_id))
    
    a = [ [None for i in range(X+1)] for j in range(Y+1) ]
    for r in c.fetchall():
      y, x, v, region_id = r
      if v == 0 and options.zero:
        v = options.zero / multiplier
      if v is None and options.missing:
        v = options.missing / multiplier
      try:
        a[y][x] = v
      except IndexError:
        raise Exception("Grid point (%d,%d) is out of range (%d,%d)" % (x,y,X,Y))
    
    return a
    
  finally:
    c.close()

global_density = get_global_density()
local_densities = get_local_densities()
def density_at_position(x, y):
  return multiplier * (local_densities[y][x] or global_density)

padding = " ".join(["%.5f" % (multiplier * global_density)] * X)
for y in range(Y):
  print padding, padding, padding
for y in range(Y):
  print padding, (" ".join(["%.5f"] * X)) % tuple((
    density_at_position(x, y) for x in range(X)
  )), padding
for y in range(Y):
  print padding, padding, padding


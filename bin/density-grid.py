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
                action="store", default="10%",
                help="Value to use for regions with zero data values (default %default)")
parser.add_option("", "--missing",
                action="store", default=None,
                help="Value to use for regions with missing data (default %default)")
parser.add_option("", "--min-area",
                action="store", default=None, type="float",
                help="Minimum area of resulting region (imposes a density floor)")
parser.add_option("", "--multiplier",
                action="store", default=1,
                help="the density multiplier (default %default)")
parser.add_option("", "--ignore-region",
                action="store",
                help="the name of a region to ignore")

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
        if options.missing:
            # Assume the value of the --missing option is small, so can
            # be approximated by a zero data value for the missing regions.
            query = """
                select sum(coalesce(data_value.value, %s)) / sum(region.area)
                from region
                left join (
                    select data_value.value, data_value.region_id
                    from data_value
                    join dataset on data_value.dataset_id = dataset.id
                    where dataset.name = %s
                ) data_value on data_value.region_id = region.id
                where region.division_id = %s
            """
            bind_variables = (0, dataset_name, division_id)
        else:
            # if --missing is not supplied, then missing regions are
            # filled with the global average density like the ocean.
            query = """
                select sum(data_value.value) / sum(region.area)
                from region
                join data_value on region.id = data_value.region_id
                join dataset on data_value.dataset_id = dataset.id
                where dataset.name = %s and region.division_id = %s
            """
            bind_variables = (dataset_name, division_id)
        
        if options.ignore_region:
            query += " and region.name <> %s"
            bind_variables += (options.ignore_region,)
        
        c.execute(query, bind_variables)
        return c.fetchone()[0]
    finally:
        c.close()

global_density = get_global_density()

# If there is no density at all on the whole map then we
# want all the regions to shrivel up to almost nothing.
if global_density is None or global_density == 0:
  global_density = 1.0

def decode_value_option(option_name, option_value):
  try:
    if not option_value:
      return None
    if option_value.endswith("%"):
      return float(option_value[:-1]) / 100 * global_density
    else:
      return float(option_value) / multiplier
  except ValueError:
    parser.error("Bad value for --%s: %s" % (option_name, option_value))

options_zero = decode_value_option("zero", options.zero)
options_missing = decode_value_option("missing", options.missing)
min_weight = options.min_area * global_density if options.min_area else None

def get_local_densities():
  c = db.cursor()
  try:
    c.execute("""
      select y, x, data_value.value / region.area density
         , region.name
         , region.area
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
      y, x, v, region_name, region_area = r
      if region_name and region_name == options.ignore_region:
        continue
      
      if v == 0 and options_zero:
        v = options_zero
      elif v is None and options_missing:
        v = options_missing
      
      if min_weight and v * region_area < min_weight:
        v = min_weight / region_area
      
      try:
        a[y][x] = v
      except IndexError:
        raise Exception("Grid point (%d,%d) is out of range (%d,%d)" % (x,y,X,Y))
    
    return a
    
  finally:
    c.close()

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


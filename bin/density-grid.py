#!/usr/bin/python
# -*- encoding: utf-8 -*-

from __future__ import division

import optparse
import re
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

if not options.map:
    parser.error("Missing option --map")
if not options.dataset:
    parser.error("Missing option --dataset")
if args:
    parser.error("Unexpected non-option arguments")

dataset_name = options.dataset
map_name = options.map

db_connection_data = []
if options.db_host:
    db_connection_data.append("host=" + options.db_host)
if options.db_name:
    db_connection_data.append(" dbname=" + options.db_name)
if options.db_user:
    db_connection_data.append(" user=" + options.db_user)
db = psycopg2.connect(" ".join(db_connection_data))

c = db.cursor()
c.execute("""
    select id from dataset where name = %s
""", (dataset_name,))
if c.fetchone() is None:
    print >>sys.stderr, "%s: Dataset '%s' does not exist" % (sys.argv[0], dataset_name)
    sys.exit(2)
c.close()

c = db.cursor()
c.execute("""
    select id, division_id, srid,
           width, height
    from map
    where name = %s
""", (map_name,))
r = c.fetchone()
if r is None:
    print >>sys.stderr, "%s: Dataset '%s' does not exist" % (sys.argv[0], dataset_name)
    sys.exit(2)
map_id, division_id, srid, X, Y = r
c.close()


# Parse the --zero and --missing options
def percentage(x, option_name):
  if x is None: return 0
  mo = re.match(r"^(\d+)%$", x)
  if mo is None:
    parser.error("Failed to parse %s option" % (option_name,))
  percent = float(mo.group(1))
  if percent < 0:
    parser.error("Value of %s option mustn't be negative" % (option_name,))
  return percent / 100

zero = percentage(options.zero, "--zero")
missing = percentage(options.missing, "--missing")

# Get the local densities
local_densities = [ [None for i in range(X+1)] for j in range(Y+1) ]
density_sum, n_normal, n_zero, n_missing = 0, 0, 0, 0

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
    
    for r in c.fetchall():
        y, x, v, region_name, region_area = r
        if region_name and region_name == options.ignore_region:
            continue
        
        try:
            local_densities[y][x] = v
            if v == 0:
              n_zero += 1
            elif v is None:
              n_missing += 1
              local_densities[y][x] = "missing"
            else:
              n_normal += 1
              density_sum += v
        except IndexError:
            raise Exception("Grid point (%d,%d) is out of range (%d,%d)" % (x,y,X,Y))

finally:
    c.close()

global_density = density_sum / (n_normal + (1-missing)*n_missing + (1-zero)*n_zero)

def d(x, y):
  v = local_densities[y][x]
  if v == 0:
    return zero * global_density
  elif v == "missing":
    return missing * global_density
  elif v is None:
    return global_density
  else:
    return v

padding = " ".join(["%.5f" % (global_density)] * X)
for y in range(Y):
    print padding, padding, padding
for y in range(Y):
    print padding, (" ".join(["%.5f"] * X)) % tuple((
      d(x, y) for x in range(X)
    )), padding
for y in range(Y):
    print padding, padding, padding


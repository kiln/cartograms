#!/usr/bin/python

# Create the counties of Northern Ireland

COUNTIES = [
  ("Antrim", "northern-ireland/antrim.wkt"),
  ("Armagh", "northern-ireland/armagh.wkt"),
  ("Down", "northern-ireland/down.wkt"),
  ("Fermanagh", "northern-ireland/fermanagh.wkt"),
  ("Londonderry", "northern-ireland/londonderry.wkt"),
  ("Tyrone", "northern-ireland/tyrone.wkt"),
]

import optparse
import psycopg2

parser = optparse.OptionParser(usage="%prog [options]")
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

if args:
  parser.error("Unexpected non-option argument")

db_connection_string = "host=" + options.db_host
if options.db_name:
    db_connection_string += " dbname=" + options.db_name
if options.db_user:
    db_connection_string += " user=" + options.db_user
db = psycopg2.connect(db_connection_string)

def contents(filename):
  """Get contents of file."""
  with open(filename, 'r') as f:
    return f.read()

for county_name, wkt_filename in COUNTIES:
  print "Inserting %s..." % (county_name,)
  c = db.cursor()
  try:
    c.execute("""
      insert into northern_ireland_county (name, the_geom)
        VALUES (%(county_name)s, ST_Multi( ST_GeomFromText(%(county_wkt)s, 4326) ))""", {
      "county_name": county_name,
      "county_wkt": contents(wkt_filename)
    })
  finally:
    c.close()

db.commit()
db.close()

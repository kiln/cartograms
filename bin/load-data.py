#!/usr/bin/python
# -*- encoding: utf-8 -*-

import csv
import optparse
import psycopg2
import sys

parser = optparse.OptionParser(usage="%prog [options] dataset csv division region-column value-column")
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
dataset_name, csv_filename, division_name, region_col, value_col = args

db_connection_string = "host=" + options.db_host
if options.db_name:
    db_connection_string += " dbname=" + options.db_name
if options.db_user:
    db_connection_string += " user=" + options.db_user
db = psycopg2.connect(db_connection_string)


def each(filename):
    f = open(filename, 'r')
    r = csv.reader(f)
    
    header = r.next()
    for row in r:
        yield dict(zip(header, [x.decode("utf-8") for x in row]))
    
    f.close()

class Col(str):
  """A column name, as opposed to a constant string.
  """
def as_seq(gen, *cols):
    for d in gen:
        yield tuple((
            d[col] if isinstance(col, Col) else col for col in cols
        ))

c = db.cursor()
c.execute("""
    insert into dataset (name, division_id) (select %s, division.id from division where name = %s)
""", (dataset_name, division_name))
c.close()

c = db.cursor()
c.execute("""
    select currval('dataset_id_seq'::regclass)
""")
dataset_id = c.fetchone()[0]
c.close()

for t in as_seq(each(csv_filename), dataset_id, Col(value_col), division_name, Col(region_col)):
    c = db.cursor()
    c.execute("""
            insert into data_value (
                dataset_id,
                division_id,
                region_id,
                value
            ) (
                select %s, division.id, region.id, %s
                from region
                join division on region.division_id = division.id
                where division.name = %s and region.name = %s
            )
        """, t
    )
    if c.rowcount == 0:
        print >>sys.stderr, "Region '{division_name}/{region_name}' not found in database".format(division_name=t[2], region_name=t[3])
    c.close()
db.commit()

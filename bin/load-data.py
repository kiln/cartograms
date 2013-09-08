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

parser.add_option("", "--print-loaded-rows-to",
                help="print loaded rows to this file")

(options, args) = parser.parse_args()
if len(args) != 5:
    parser.error("Wrong number of arguments")
dataset_name, csv_filename, division_name, region_col, value_col = args

db_connection_data = []
if options.db_host:
    db_connection_data.append("host=" + options.db_host)
if options.db_name:
    db_connection_data.append(" dbname=" + options.db_name)
if options.db_user:
    db_connection_data.append(" user=" + options.db_user)
db = psycopg2.connect(" ".join(db_connection_data))


def each(filename):
    global current_row, w
    
    f = open(filename, 'r')
    r = csv.reader(f)
    
    if options.print_loaded_rows_to:
        g = open(options.print_loaded_rows_to, 'w')
        w = csv.writer(g)
    else:
        w = None
    
    header = r.next()
    if w: w.writerow(header)
    for row in r:
        current_row = row
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
    if not t[1]:
      print >>sys.stderr, "Skipping '%s', because the value is blank" % (t[3],)
      continue
    c.execute("""
            insert into data_value (
                dataset_id,
                division_id,
                region_id,
                value
            ) (
                select %s, division.id, region.id, GREATEST(0, %s::numeric)
                from region
                join division on region.division_id = division.id
                where division.name = %s and region.name = %s
            )
        """, t
    )
    if c.rowcount == 0:
        print >>sys.stderr, "Region '{division_name}/{region_name}' not found in database".format(division_name=t[2], region_name=t[3])
    elif w:
        w.writerow(current_row)
    c.close()
db.commit()

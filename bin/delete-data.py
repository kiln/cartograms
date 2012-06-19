#!/usr/bin/python

import optparse
import sys
import psycopg2

parser = optparse.OptionParser(usage="%prog [options] dataset")
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
if len(args) != 1:
    parser.error("Wrong number of arguments")
dataset_name, = args

db_connection_string = "host=" + options.db_host
if options.db_name:
    db_connection_string += " dbname=" + options.db_name
if options.db_user:
    db_connection_string += " user=" + options.db_user
db = psycopg2.connect(db_connection_string)

c = db.cursor()
c.execute("""
  delete from data_value where dataset_id in (
    select id from dataset where name = %s
  )
""", (dataset_name,))
c.close()

c = db.cursor()
c.execute("""
  delete from dataset where name = %s
""", (dataset_name,))
c.close()

db.commit()

#!/usr/bin/python
# -*- encoding: utf-8 -*-
from __future__ import division

import optparse
import sys

import psycopg2

parser = optparse.OptionParser(usage="%prog [options]")
parser.add_option("-d", "--database", type="str", help="Database connection string (default %default)",
	default="dbname=robin")
parser.add_option("", "--shp-table", type="str", help="Name of  table")
parser.add_option("", "--topo-table", type="str", help="Name of topology table")
parser.add_option("", "--code-col", type="str",
	help="Name of code column in shp table (default %default)", default="code")
parser.add_option("", "--secondary-code-col", type="str",
	help="Name of secondary code column in shp table (if any)")
parser.add_option("", "--name-col", type="str",
	help="Name of name column in shp table (default %default)", default="name")
parser.add_option("", "--tolerance", type="float", help="Tolerance (default %default)", default=0.00000001)
parser.add_option("", "--batch-size", type="int", help="Batch size (default %default)", default=10)
parser.add_option("", "--commit-every", type="int", help="Commit every n rows (default %default)", default=100)

(options, args) = parser.parse_args()
if len(args) > 0:
	parser.error("Unexpected non-option argument: " + args[0])

if not options.shp_table:
	parser.error("--shp-table must be specified")
if not options.topo_table:
	parser.error("--topo-table must be specified")

db = psycopg2.connect(options.database)

# Get topology name and layer id for topo_table.topo
with db.cursor() as c:
	c.execute("""
		select topology.topology.name
		     , topology.layer.layer_id
		from topology.layer
		join topology.topology on topology.layer.topology_id = topology.topology.id
		where schema_name = 'public'
		and table_name = %(table_name)s
		and feature_column = 'topo'
	""", dict(table_name=options.topo_table))
	topology_name, layer_id = c.fetchone()

print ""

if options.secondary_code_col:
	sql = """
		insert into {topo_table_name} (code, name, {secondary_code_col}, topo, bbox) (
			select {shp_table_code_col}, {shp_table_name_col}, {secondary_code_col},
				topology.toTopoGeom(geom, %s, %s, %s),
				ST_Envelope(geom)
			from {shp_table_name}
			where {shp_table_code_col} in ({placeholders})
		)
	"""
else:
	sql = """
		insert into {topo_table_name} (code, name, topo, bbox) (
			select {shp_table_code_col}, {shp_table_name_col},
				topology.toTopoGeom(geom, %s, %s, %s),
				ST_Envelope(geom)
			from {shp_table_name}
			where {shp_table_code_col} in ({placeholders})
		)
	"""

def topologise(codes):
	if len(codes) == 0:
		return

	for code in codes:
		print "Loading %s..." % (code,)
	with db.cursor() as c:
		c.execute(sql.format(
			topo_table_name=options.topo_table,
			shp_table_name=options.shp_table,
			shp_table_code_col=options.code_col,
			shp_table_name_col=options.name_col,
			secondary_code_col=options.secondary_code_col,
			placeholders=", ".join([ "%s" for code in codes ])
		),
		(topology_name, layer_id, options.tolerance) + tuple(codes))

n = 0
codes = []
with db.cursor() as c:
	c.execute("""
		select {shp_table_code_col} from {shp_table_name}
	""".format(
		shp_table_name=options.shp_table,
		shp_table_code_col=options.code_col,
	))
	for code, in c:
		codes.append(code)
		n += 1
		if n % options.batch_size == 0:
			topologise(codes)
			print "Loaded %d rows..." % (n,)
			codes = []
		if n % options.commit_every == 0:
			db.commit()

	topologise(codes)
	print "Loaded %d rows..." % (n,)
	db.commit()

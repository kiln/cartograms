#!/usr/bin/python
# -*- encoding: utf-8 -*-

# Process a World Bank time series file, and extract the latest available number for
# each country.

import csv
import optparse
import re
import sys

def die(fmt, *args, **kwargs):
  if args and kwargs:
    raise Exception("Found both args and kwargs in call to die!")
  
  if args:
    s = fmt % args
  else:
    s = fmt % kwargs
  
  print >>sys.stderr, sys.argv[0] + ": " + s
  sys.exit(1)

def read_csv(filename, multiplier_by_country_code=None):
  with open(filename, 'r') as f:
    r = csv.reader(f)
  
    for i in range(options.skip):
        r.next()
  
    header = r.next()
    if header[0] == "Data Source" or header[0] == '\xef\xbb\xbf"Data Source"':
        r.next()
        header = r.next()
  
    if header[0] != "Country Name":
      die("First column header should be 'Country Name'")
    if header[1] != "Country Code":
      die("Second column header should be 'Country Code'")
  
    years = [ year for year in header[-1:1:-1] if re.match(r"^\d\d\d\d$", year) ]
    yield ["Country Name", "Country Code", "Year", "Value"]
  
    for row in r:
      d = dict(zip(header, row))
      year = next((year for year in years if re.search(r"\S", d[year])), None)
      value = d.get(year, None)
      if multiplier_by_country_code and value:
        value = float(value) * multiplier_by_country_code[d["Country Code"]]
      
      yield [
        d["Country Name"],
        d["Country Code"],
        year,
        d.get(year, None),
      ]

parser = optparse.OptionParser(usage="%prog [options] filename.csv")
parser.add_option("-s", "--skip", type="int", default=0,
                help="number of rows to skip before the header")
parser.add_option("", "--multiply-by",
                help="data file to multiply by (typically population)")

(options, args) = parser.parse_args()
if len(args) != 1:
  parser.error("Expected one argument")

multiplier_by_country_code = None
if options.multiply_by:
  multiplier_by_country_code = {}
  g = read_csv(options.multiply_by)
  header = g.next()
  for row in g:
    d = dict(zip(header, row))
    if d["Value"]:
      multiplier_by_country_code[d["Country Code"]] = float(d["Value"])

w = csv.writer(sys.stdout)
for row in read_csv(args[0], multiplier_by_country_code):
  w.writerow(row)

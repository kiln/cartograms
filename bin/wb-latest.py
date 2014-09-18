#!/usr/bin/python
# -*- encoding: utf-8 -*-

# Process a World Bank time series file, and extract the latest available number for
# each country.

import csv
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

if len(sys.argv) != 2:
  die("Expected one argument")

with open(sys.argv[1], 'r') as f:
  r = csv.reader(f)
  w = csv.writer(sys.stdout)
  
  header = r.next()
  if header[0] == "Data Source":
      r.next()
      header = r.next()
  
  if header[0] != "Country Name":
    die("First column header should be 'Country Name'")
  if header[1] != "Country Code":
    die("Second column header should be 'Country Code'")
  
  years = [ year for year in header[-1:1:-1] if re.match(r"^\d\d\d\d$", year) ]
  w.writerow(["Country Name", "Country Code", "Year", "Value"])
  
  for row in r:
    d = dict(zip(header, row))
    year = next((year for year in years if re.search(r"\S", d[year])), None)
    w.writerow([
      d["Country Name"],
      d["Country Code"],
      year,
      d.get(year, None),
    ])

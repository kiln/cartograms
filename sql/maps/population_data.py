import csv
import os
import sys

from county_region_list import (english_counties, welsh_counties, scottish_council_regions)

data_dir = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        os.path.pardir, os.path.pardir,
        "data"
    )
)

population_by_region = {}
name_by_region = {}
with open(os.path.join(data_dir, "population-by-region.csv")) as f:
    r = csv.reader(f)
    header = r.next()
    for row in r:
        code, name, population = row
        population_by_region[code] = int(population)


w = csv.writer(sys.stdout)
w.writerow(["County name", "Population"])
for county, parts in english_counties.items() + welsh_counties.items():
    population = sum([
        population_by_region[part[0]]
        for part in parts
    ])
    w.writerow([county, population])

for code, name in scottish_council_regions.items():
    w.writerow([name, population_by_region[code]])

w.writerow(["Greater London", population_by_region["E12000007"]])

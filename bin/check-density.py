#!/usr/bin/python
# -*- encoding: utf-8 -*-

import sys

for density_filename in sys.argv[1:]:
    with open(density_filename, 'r') as f:
        d = [
            map(float, line.split())
            for line in f
        ]

    ocean_density = d[0][0]

    land_density_sum = 0
    land_density_npts = 0
    for row in d:
        for x in row:
            if x != ocean_density:
                land_density_sum += x
                land_density_npts += 1

    mean_land_density = land_density_sum / land_density_npts
    print "File: {density_filename}".format(density_filename=density_filename)
    print "Ocean density: {ocean_density}".format(ocean_density=ocean_density)
    print "Mean land density: {mean_land_density}".format(mean_land_density=mean_land_density)
    print "Ratio: {ratio:.4}".format(ratio=mean_land_density/ocean_density)
    print

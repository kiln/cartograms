#!/usr/bin/python

# Check for places where the cart grid folds over itself
# XXXX This is buggy because it also picks up twisting, which is okay

import sys

import numpy

W, H = 1200, 1800
TOLERANCE = 3

a = numpy.fromfile(sys.argv[1], sep=' ').reshape(H+1, W+1, 2)

for x in range(1, W):
  for y in range(1, H):
    tx, ty = a[y][x]
    lx, ly = a[y][x-1]
    ux, uy = a[y-1][x]
    
    if lx > tx + TOLERANCE:
      print "(%d,%d) -> (%f,%f), but (%d,%d) -> (%f,%f)" % (x,y, tx,ty, x-1,y, lx, ly)
    if uy > ty + TOLERANCE:
      print "(%d,%d) -> (%f,%f), but (%d,%d) -> (%f,%f)" % (x,y, tx,ty, x,y-1, ux, uy)

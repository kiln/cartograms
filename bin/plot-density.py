#!/usr/bin/python

import sys
import PIL.Image, PIL.ImageDraw

filename = sys.argv[1]
with open(filename, 'r') as f:
  d = [ map(float, line.strip().split(" ")) for line in f ]

max_density = max(map(max, d))

height, width = len(d), len(d[0])
im = PIL.Image.new("RGBA", (width, height))
pa = im.load()

for x in xrange(width):
    for y in xrange(height):
        n = int(round(0xFFFFFFFF * d[y][x] / max_density))
        pa[(x, height - y - 1)] = ((n>>24)&0xFF, (n>>16)&0xFF, (n>>8)&0xFF, n&0xFF)

im.save(sys.stdout, "PNG")

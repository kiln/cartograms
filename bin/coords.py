#!/usr/bin/python
# -*- encoding: utf-8 -*-

import optparse
import psycopg2
import re
import sys

import utils

class Coords(object):
    u"""Convert coordinates from geographic coordinates to pixels
    on a particular rendered map – especially one rendered by as-png.py.
    
    It would be logical (and fairly easy) to extend this to support
    cartograms – at the moment it only works for undistorted map – but
    I shan’t do that right now, since I have no immediate need for it.
    """
    def get_parser(self):
        parser = optparse.OptionParser(usage="%prog [options]")
        
        # Database connection options:
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

        # Specifying the map
        parser.add_option("", "--map",
                        action="store",
                        help="the name of the map (required)")
        
        # How the map was rendered: options as passed to as-png.py
        parser.add_option("", "--stroke-width",
                          action="store", default=2, type="int",
                          help="width of strokes, in pixels (default %default)")
        parser.add_option("", "--width",
                          action="store", type="int",
                          help="width of output image")
        parser.add_option("", "--height",
                          action="store", type="int",
                          help="height of output image")
        parser.add_option("", "--box",
                          action="store",
                          help="fit image to box, e.g. 200x200")
        return parser
    
    def parse_args(self):
        parser = self.get_parser()
        (options, args) = parser.parse_args()
        
        if args:
            parser.error("Unexpected non-option argument: " + args[0])
        
        if not options.map:
            parser.error("You must specify --map")
        
        if options.box:
            if options.width:
                parser.error("You can't specify --box and --width")
            if options.height:
                parser.error("You can't specify --box and --height")
            if not re.match(r"^\d+x\d+$", options.box):
                parser.error("Failed to parse --box value: "+ options.box)
        
        return options
    
    def __init__(self, options=None):
        if options is None:
            self.options = self.parse_args()
        else:
            self.options = options
        self.db = self.db_connect()
        self.m = utils.Map(self.db, self.options.map)
        self._init_dimensions()
    
    def _init_dimensions(self):
        options = self.options
        
        self.x_min = self.m.x_min
        self.x_max = self.m.x_max
        self.y_min = self.m.y_min
        self.y_max = self.m.y_max
        
        aspect_ratio = (self.x_max - self.x_min) / (self.y_max - self.y_min)
        
        # If width and height are both specified, use them
        if options.width and options.height:
            self.output_width = options.width
            self.output_height = options.height
        
        # If only one of them is specified, retain the aspect ratio
        # of the map as defined in the database.
        elif options.width:
            self.output_width = options.width
            self.output_height = int(round(options.width / aspect_ratio))
        
        elif options.height:
            self.output_height = options.height
            self.output_width = int(round(options.height * aspect_ratio))
        
        elif options.box:
            mo = re.match(r"^(\d+)x(\d+)$", options.box)
            max_width, max_height = int(mo.group(1)), int(mo.group(2))
            box_ratio = max_width / max_height
            if box_ratio > aspect_ratio:
                # The height is the limiting factor
                self.output_height = max_height
                self.output_width = int(round(max_height * aspect_ratio))
            else:
                # The width is the limiting factor
                self.output_width = max_width
                self.output_height = int(round(max_width / aspect_ratio))
        
        # If neither is specified, use the dimensions of the map
        # as defined in the database.
        else:
            self.output_width = self.m.width
            self.output_width = self.m.height
    
        stroke_width = self.options.stroke_width
        input_width = self.x_max - self.x_min
        input_height = self.y_max - self.y_min
        width_ratio = (self.output_width - self.options.stroke_width) / input_width
        height_ratio = (self.output_height - self.options.stroke_width) / input_height
        self.matrix = [
            width_ratio, 0, 0, -height_ratio,
            -self.x_min * width_ratio + stroke_width/2, self.y_max * height_ratio + stroke_width/2,
        ]
    
    def db_connect(self):
        options = self.options
        db_connection_data = []
        if options.db_host:
            db_connection_data.append("host=" + options.db_host)
        if options.db_name:
            db_connection_data.append(" dbname=" + options.db_name)
        if options.db_user:
            db_connection_data.append(" user=" + options.db_user)
        return psycopg2.connect(" ".join(db_connection_data))
    
    def convert(self, latitude, longitude):
        a,b,c,d,e,f = self.matrix
        x, y = self.project(latitude, longitude)
        
        return a*x + b*y + e, c*x + d*y + f
    
    def project(self, latitude, longitude):
        c = self.db.cursor()
        try:
            c.execute("""
                select ST_X(p.p), ST_Y(p.p)
                from (
                    select ST_Transform(
                        ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326),
                        %(srid)s
                    ) p
                ) p
            """, {
                "latitude": latitude,
                "longitude": longitude,
                "srid": self.m.srid,
            })
            return c.fetchone()
        finally:
            c.close()

def _parse(line):
    mo = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", line)
    if mo is None:
        raise Exception("Failed to parse: " + line)
    return float(mo.group(1)), float(mo.group(2))

if __name__ == "__main__":
    coords = Coords()
    for line in sys.stdin:
        latitude, longitude = _parse(line)
        print "%d %d" % coords.convert(latitude, longitude)


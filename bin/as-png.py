#!/usr/bin/python

from __future__ import division

import math
import optparse
import re
import sys

import cairo
import PIL.Image, PIL.ImageDraw
import shapely.geometry, shapely.wkb
import psycopg2

import utils

class AsPNG(object):
    def __init__(self, options):
        self.options = options
        self.db = self.db_connect()
        self.m = utils.Map(self.db, options.map)
        if options.cart:
            self.interpolator = utils.Interpolator(options.cart, self.m)
        else:
            self.interpolator = None
        
        if options.output:
            self.out = options.output
        else:
            self.out = sys.stdout
        
        self.fill_colour = self._parse_colour(options.fill_colour)
        self.fill_colour_no_data = self._parse_colour(options.fill_colour_no_data)
        self.stroke_colour = self._parse_colour(options.stroke_colour)
        self.background_colour = self._parse_colour(options.background_colour)
        
        if options.srid:
            self.srid = options.srid
        else:
            self.srid = self.m.srid
        
        if options.region:
            bounds = self.region_bounds(options.region)
            self.x_min, self.y_min, self.x_max, self.y_max = bounds
        else:
            # TODO if --srid is specified then this is wrong
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
    
    def _parse_colour(self, colour_string):
        if colour_string == "None":
            return None
        r, g, b = int(colour_string[0:2], 16), int(colour_string[2:4], 16), int(colour_string[4:6], 16)
        return r/0xFF, g/0xFF, b/0xFF

    def region_bounds(self, region_name):
        c = self.db.cursor()
        try:
            c.execute("""
                select ST_XMin(x.box), ST_YMin(x.box)
                     , ST_XMax(x.box), ST_YMax(x.box)
                from (
                    select Box2D(ST_Transform(region.the_geom, %(srid)s)) as box
                    from region
                    where name = %(region_name)s
                    and division_id = %(division_id)s
                ) x
            """, {
                "srid": self.srid,
                "division_id": self.m.division_id,
                "region_name": region_name
            })
            return c.fetchone()
        finally:
            c.close()
    
    def render_region_paths(self, slide):
        c = self.db.cursor()
        try:
            params = {
                "srid": self.srid,
                "simplification": self.options.simplification,
                "dataset_name": self.options.dataset,
                "division_id": self.m.division_id,
            }
            if self.options.dataset:
                sql = """
                    select region.name
                             , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %(srid)s), %(simplification)s)) g
                             , exists(
                                    select *
                                    from data_value
                                    join dataset on data_value.dataset_id = dataset.id
                                    where dataset.name = %(dataset_name)s
                                    and data_value.region_id = region.id) has_data
                    from region
                    where region.division_id = %(division_id)s
                """
            else:
                sql = """
                    select region.name
                             , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %(srid)s), %(simplification)s)) g
                             , true
                    from region
                    where region.division_id = %(division_id)s
                """
            
            if self.options.region:
                sql += "and region.name = %(region_name)s"
                params["region_name"] = self.options.region
            
            c.execute(sql, params)
            
            for iso2, g, has_data in c.fetchall():
                fill_colour = self.fill_colour if has_data else self.fill_colour_no_data
                p = shapely.wkb.loads(str(g))
                if self.options.omit_small_islands:
                    p = self.omit_small_islands(p)
                self.render_multipolygon(p, fill_colour, slide)
                
        finally:
            c.close()
    
    def omit_small_islands(self, multipolygon):
        max_area = max([ polygon.area for polygon in multipolygon.geoms ])
        nonsmall_islands = [
            polygon for polygon in multipolygon.geoms
            if polygon.area > 0.05 * max_area
        ]
        if nonsmall_islands:
            multipolygon = shapely.geometry.MultiPolygon(nonsmall_islands)
            if self.options.region:
                # If we are mapping just one region, we may need to adjust the bounds
                # now we have removed small islands
                self.x_min, self.y_min, self.x_max, self.y_max = multipolygon.bounds
        
        return multipolygon
    
    def render_polygon_ring_cairo(self, ring, fill_colour=None, slide=1.0):
        if fill_colour is None:
            fill_colour = self.fill_colour
        
        first = True
        for x, y in ring.coords:
            if self.interpolator:
                x, y = self.interpolator(x, y, slide)
            if first:
                self.c.move_to(x, y)
                first = False
            else:
                self.c.line_to(x, y)
        
        self.c.close_path()
        if fill_colour:
            self.c.set_source_rgb(*fill_colour)
            if self.stroke_colour:
                self.c.fill_preserve()
            else:
                self.c.fill()
        
        if self.stroke_colour:
            self.c.set_source_rgb(*self.stroke_colour)
            self.c.stroke()

    def render_polygon_ring_pil(self, ring, fill_colour=None, slide=1.0):
        if fill_colour is None:
            fill_colour = self.fill_colour
        polygon_coords = []
        for x, y in ring.coords:
            if self.interpolator:
                x, y = self.interpolator(x, y, slide)
            polygon_coords.append((
                (x - self.x_min) * self.output_width / (self.x_max - self.x_min),
                self.output_height - (y - self.y_min) * self.output_height / (self.y_max - self.y_min),
            ))
            
        self.draw.polygon(polygon_coords, outline=self.stroke_colour, fill=fill_colour)

    def render_polygon_ring(self, *args, **kwargs):
        if self.options.cairo:
            self.render_polygon_ring_cairo(*args, **kwargs)
        else:
            self.render_polygon_ring_pil(*args, **kwargs)

    def render_polygon(self, polygon, fill_colour=None, slide=1.0):
        for ring in polygon.exterior:
            self.render_polygon_ring(ring, fill_colour, slide)

    def render_multipolygon(self, multipolygon, fill_colour=None, slide=1.0):
        for g in multipolygon.geoms:
            self.render_polygon_ring(g.exterior, fill_colour, slide)
            
            # XXXX This is not remotely correct, of course
            for interior in g.interiors:
                self.render_polygon_ring(interior, fill_colour, slide)
    
    def render_circles_cairo(self, slide=1.0):
        c = self.db.cursor()
        c.execute("""
            with t as (select ST_Transform(location, %s) p from {table_name})
            select ST_X(t.p), ST_Y(t.p) from t
        """.format(table_name=self.options.circles), (self.srid,) )
        
        r,g,b = self.circle_fill_colour
        self.c.set_source_rgba(r,g,b, self.options.circle_opacity)
        for x, y in c:
                if self.interpolator:
                    x, y = self.interpolator(x, y, slide)
                self.c.arc(x, y, self.options.circle_radius, 0, 2*math.pi)
                self.c.fill()
        c.close()

    def render_circles(self, *args, **kwargs):
        if self.options.cairo:
            self.render_circles_cairo(*args, **kwargs)
        else:
            raise Exception("Circles are not yet implemented in PIL mode")
    
    def render_map(self):
        if self.options.anim_frames:
            for frame in range(self.options.anim_frames):
                frame_filename = self.out % (frame,)
                print "Rendering frame to %s" % (frame_filename,)
                self.render_frame(frame / (self.options.anim_frames - 1), frame_filename)
        else:
            self.render_frame(1.0, self.out)
    
    def render_frame_cairo(self, slide, output_file):
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.output_width + self.options.stroke_width,
            self.output_height + self.options.stroke_width,
        )
        self.c = cairo.Context(surface)

        if self.background_colour:
            self.c.rectangle(0,0, self.output_width, self.output_height)
            self.c.set_source_rgb(*self.background_colour)
            self.c.fill()

        stroke_width = self.options.stroke_width
        input_width = self.x_max - self.x_min
        input_height = self.y_max - self.y_min
        width_ratio = self.output_width / input_width
        height_ratio = self.output_height / input_height
        mean_ratio = (width_ratio + height_ratio) / 2
        self.c.transform(cairo.Matrix(
            width_ratio, 0, 0, -height_ratio,
            -self.x_min * width_ratio + stroke_width/2, self.y_max * height_ratio + stroke_width/2,
        ))
        self.c.set_line_width(stroke_width / mean_ratio)

        self.render_region_paths(slide)
        if self.options.circles:
            self.render_circles(slide)

        surface.write_to_png(output_file)
        surface.finish()

    def render_frame_pil(self, slide, output_file):
        if self.options.overlay_on:
            image = PIL.Image.open(self.options.overlay_on)
        else:
            image = PIL.Image.new("RGB", (self.output_width, self.output_height), None)
        
        self.draw = PIL.ImageDraw.Draw(image)
        
        self.render_region_paths(slide)
        if self.options.circles:
            self.render_circles(slide)
        
        image.save(output_file, "PNG")

    def render_frame(self, *args, **kwargs):
            if self.options.cairo:
                self.render_frame_cairo(*args, **kwargs)
            else:
                self.render_frame_pil(*args, **kwargs)

def main():
    global options
    parser = optparse.OptionParser()
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

    parser.add_option("", "--map",
                      action="store",
                      help="the name of the map to use")
    parser.add_option("", "--cart",
                      action="store",
                      help="the name of the file containing the cartogram grid")
    parser.add_option("", "--dataset",
                      action="store",
                      help="the name of the dataset (used to mark which regions have data)")
    
    parser.add_option("-o", "--output",
                      action="store",
                      help="the name of the output file (defaults to stdout)")
    
    parser.add_option("", "--simplification",
                      action="store", default=1000,
                      help="how much to simplify the paths (default %default)")
    
    parser.add_option("", "--anim-frames",
                      action="store", default=None, type="int",
                      help="Number of frames of animation to produce")
    
    parser.add_option("", "--circles",
                      action="store",
                      help="the name of the table containing data points to plot")
    parser.add_option("", "--circle-radius",
                      action="store", default=500, type="int",
                      help="radius of circles (default %default)")
    parser.add_option("", "--circle-opacity",
                      action="store", default=0.1, type="float",
                      help="opacity of circles (default %default)")
    parser.add_option("", "--circle-fill-colour",
                      action="store", default="FF0000",
                      help="fill colour for circles (default %default)")
    
    parser.add_option("", "--cairo",
                      action="store_true", default=True,
                      help="use Cairo")
    parser.add_option("", "--pil",
                      action="store_false", dest="cairo",
                      help="use PIL")
    parser.add_option("", "--overlay-on",
                      action="store",
                      help="overlay the paths on the specified background image")
    
    parser.add_option("", "--background-colour",
                      action="store", default="9EC7F3",
                      help="background colour (default %default)")
    parser.add_option("", "--fill-colour",
                      action="store", default="F7D3AA",
                      help="fill colour (default %default)")
    parser.add_option("", "--fill-colour-no-data",
                      action="store", default="FFFFFF",
                      help="fill colour where there is no data (default %default)")
    parser.add_option("", "--stroke-colour",
                      action="store", default="A08070",
                      help="stroke colour (default %default)")
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
    
    parser.add_option("", "--region",
                      action="store",
                      help="map just the specified region")
    parser.add_option("", "--srid",
                      action="store", type=int,
                      help="override the map's SRID with the specified one")
    parser.add_option("", "--omit-small-islands",
                      action="store_true", default=False,
                      help="omit any regions that are less than 5% the size of the largest land mass")
    
    (options, args) = parser.parse_args()
    if args:
        parser.error("Unexpected non-option arguments")
    
    if not options.map:
        parser.error("Missing option --map")
    
    if options.anim_frames:
        if not options.cart:
            parser.error("Animation requires a --cart file")
        if not options.output:
            parser.error("Animation requires that you specify an output file template")
        try:
            options.output % (0,)
        except:
            parser.error("Output filename '%s' does not contain a %%d template" % (options.output,))
    
    if options.box:
        if options.width:
            parser.error("You can't specify --box and --width")
        if options.height:
            parser.error("You can't specify --box and --height")
        if not re.match(r"^\d+x\d+$", options.box):
            parser.error("Failed to parse --box value: "+ options.box)
    
    if options.overlay_on and options.cairo:
        parser.error("The --overlay-on option is only allowed in --pil mode")
    
    AsPNG(options=options).render_map()

main()

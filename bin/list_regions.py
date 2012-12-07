#!/usr/bin/python

import optparse
import psycopg2
import sys

"""
List the regions for a particular division, which may be specified
in various ways.
"""

class ListRegions(object):
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

        # Specifying the division: ONE of the following options
        # should be specified.
        parser.add_option("", "--division",
                        action="store",
                        help="the name of the division")
        parser.add_option("", "--map",
                        action="store",
                        help="or the name of the map")
        parser.add_option("", "--dataset",
                        action="store",
                        help="or the name of a dataset")
        
        # Output options
        parser.add_option("-0", "--zero",
                        action="store_true", default=False,
                        help="terminate lines with a NUL character, not a linefeed")
        
        return parser
    
    def parse_args(self):
        parser = self.get_parser()
        (options, args) = parser.parse_args()
        
        if args:
            parser.error("Unexpected non-option argument: " + args[0])
        
        number_of_specs = sum([
            options.division is not None,
            options.dataset is not None,
            options.map is not None,
        ])
        if number_of_specs == 0:
            parser.error("You must specify one of --division, --map or --dataset")
        if number_of_specs > 1:
            parser.error("You may specify only one of --division, --map and --dataset")
        
        return options
    
    def __init__(self, options=None):
        if options is None:
            self.options = self.parse_args()
        else:
            self.options = options
        self.db = self.db_connect()
        self.division_id = self.get_division_id()
    
    def region_names(self):
        for row in self.query_iterator("select name from region where division_id=%s", self.division_id):
            yield row[0]
    
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
    
    def get_division_id(self):
        options = self.options
        if options.division:
            return self.get_division_id_by_name(options.division)
        if options.map:
            return self.get_division_id_by_map_name(options.map)
        if options.dataset:
            return self.get_division_id_by_dataset_name(options.dataset)
        raise Exception("This should never happen")
    
    def simple_query(self, query, *args, **kwargs):
        if "error" in kwargs:
            error_message = kwargs["error"]
        else:
            error_message = "Query returned no results: " + query
        
        c = self.db.cursor()
        try:
            c.execute(query, args)
            row = c.fetchone()
        finally:
            c.close()
        
        if row is None:
            print >>sys.stderr("%s: %s" % (sys.argv[0], error_message))
            sys.exit(1)
        
        if len(row) > 1:
            raise Exception("Simple query returned >1 result")
        return row[0]
    
    def query_iterator(self, query, *args):
        c = self.db.cursor()
        try:
            c.execute(query, args)
            for row in c:
                yield row
        finally:
            c.close()
    
    def get_division_id_by_name(self, division_name):
        return self.simple_query(
            "select id from division where name = %s", division_name,
            error="No such division: " + division_name)

    def get_division_id_by_map_name(self, map_name):
        return self.simple_query(
            "select division_id from map where name = %s", map_name,
            error="No such map: " + map_name)

    def get_division_id_by_dataset_name(self, dataset_name):
        return self.simple_query(
            "select division_id from dataset where name = %s", dataset_name,
            error="No such dataset: " + dataset_name)
    
    def print_regions(self):
        for region_name in self.region_names():
            if self.options.zero:
                sys.stdout.write(region_name + "\0")
            else:
                print region_name


if __name__ == "__main__":
    ListRegions().print_regions()

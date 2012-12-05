#!/usr/bin/python

# Takes a CSV file whose first column is the country name,
# and adds a column for the ISO 3166-1 alpha-2 code, writing
# the augmented CSV file to stdout and reporting any failures
# to stderr.

import csv
import os
import re
import sys

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(os.path.join(BASE_DIR, "lib"))
import countries

def process_file(csv_file_name,
    country_name_column=0,
    code_column="Alpha-2",
    write_to=sys.stdout,
    input_delimiter=',', output_delimiter=',',
    has_header=True
):
    f = open(csv_file_name, 'rU')
    r = csv.reader(f, delimiter=input_delimiter)
    if not isinstance(write_to, file):
        write_to = open(write_to, 'w')
    w = csv.writer(write_to, delimiter=output_delimiter)
    
    if has_header:
        header = r.next()
        try:
            # Try country_name_column as a column number
            country_name_column_number = int(country_name_column)
        except ValueError:
            # If that fails, try it as a column name
            country_name_column_number = header.index(country_name_column)
            # (If that fails, we get a ValueError)
    
        header[1:1] = [code_column]
        w.writerow(header)
    else:
        country_name_column_number = int(country_name_column)
    
    for row in r:
        country = row[country_name_column_number]
        code = countries.alpha_2(country)
        if code is not None:
            row[1:1] = [code]
            w.writerow(row)
        else:
            print >>sys.stderr, "Failed to recognise '{country}': {row}".format(country=country, row=",".join(row))

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("", "--country-col", default=0,
                      help="number or name of country name column")
    parser.add_option("", "--code-col", default="Alpha-2",
                      help="name of the alpha-2 column we add")
    parser.add_option("", "--input-delimiter", default=',',
                      help="Field delimiter for input file (default %default)")
    parser.add_option("", "--output-delimiter", default=',',
                      help="Field delimiter for output file (default %default)")
    parser.add_option("", "--no-header", dest="has_header", action="store_false", default=True,
                      help="Input file has no header line")
    
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("Wrong number of arguments (%d, expected 1)" % len(args))
    
    process_file(args[0],
        country_name_column=options.country_col,
        code_column=options.code_col,
        input_delimiter=options.input_delimiter,
        output_delimiter=options.output_delimiter,
        has_header=options.has_header)

if __name__ == "__main__":
    main()

# This is used merely to generate some of the SQL in gb-counties.sql

import re

from county_region_list import (english_counties, welsh_counties)

def sql_str(s):
  return "NULL" if s is None else "'" + re.sub(r"'", "''", s) + "'"

def sql_seq(ss):
  return '(' + ", ".join([sql_str(s) for s in ss]) + ')'

S_CTY = """
insert into gb_county (name, the_geom) (
  select {name}, the_geom
  from county where code = {cty_code}
);
""".strip()

S_UTA_CTY = """
insert into gb_county (name, the_geom) (
  select {name}, ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = {cty_code})
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in {uta_codes}
);
""".strip()

S_UTA = """
insert into gb_county (name, the_geom) (
  select {name}, ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in {uta_codes}
);
""".strip()

S_MTD = """
insert into gb_county (name, the_geom) (
  select {name}, ST_Multi(ST_Union(the_geom))
  from unitary_region metropolitan_district
  where area_code = 'MTD'
  and code in {mtd_codes}
);
""".strip()

def _template(county_name, county_codes, metropolitan_district_codes, unitary_authority_codes):
  """Find the appropriate template.
  """
  if county_codes and len(county_codes) > 1:
    raise Exception("%s has more than one county?" % (county_name,))
  
  if metropolitan_district_codes:
    if county_codes or unitary_authority_codes:
      raise Exception("%s has county/unitary authority as WELL as a metropolitan district?" % (county_name,))
    return S_MTD
  elif county_codes and unitary_authority_codes:
    return S_UTA_CTY
  elif county_codes:
    return S_CTY
  elif unitary_authority_codes:
    return S_UTA
  else:
    raise Exception("%s has neither a county nor a unitary authority?" % (county_name,))

def print_sql_init():
    print """create temporary table gb_county (
  id serial PRIMARY KEY,
  name character varying(60) not null unique
);
select AddGeometryColumn('','gb_county','the_geom','27700','MULTIPOLYGON',2);"""

def print_sql_for_english_counties():
  for county_name, regions in english_counties.iteritems():
    region_codes = set(( region_code for (region_code, region_name) in regions ))
    county_codes = [region_code for region_code in region_codes if region_code.startswith("E10")]
    unitary_authority_codes = [region_code for region_code in region_codes if region_code.startswith("E06")]
    metropolitan_district_codes = [region_code for region_code in region_codes if region_code.startswith("E08")]
  
    print _template(county_name, county_codes, metropolitan_district_codes, unitary_authority_codes).format(
      name=sql_str(county_name),
      uta_codes=sql_seq(unitary_authority_codes),
      cty_code=sql_str(county_codes[0] if county_codes else None),
      mtd_codes=sql_seq(metropolitan_district_codes),
    )
    print
  
  # London
  print """insert into gb_county (name, the_geom) (select 'Greater London', the_geom from county where area_code = 'GLA');"""
  print


def print_sql_for_welsh_counties():
  for county_name, regions in welsh_counties.iteritems():
    region_codes = set(( region_code for (region_code, region_name_cy, region_name_en) in regions ))
    print S_UTA.format(name=sql_str(county_name), uta_codes=sql_seq(region_codes))
    print

def print_sql_for_scottish_council_areas():
  print """insert into gb_county (name, the_geom) (select name, the_geom from unitary_region where area_code = 'UTA' and code like 'S12%');"""
  print

def main():
  print_sql_init()
  print_sql_for_english_counties()
  print_sql_for_welsh_counties()
  print_sql_for_scottish_council_areas()

main()

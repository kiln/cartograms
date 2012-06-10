# This is used merely to generate some of the SQL in gb-counties.sq

import re

def sql_str(s):
  return "NULL" if s is None else "'" + re.sub(r"'", "''", s) + "'"

def sql_seq(ss):
  return '(' + ", ".join([sql_str(s) for s in ss]) + ')'

english_counties = {
  "Bedfordshire": [
    ["E06000055", "Bedford"],
    ["E06000056", "Central Bedfordshire"],
    ["E06000032", "Luton"]
  ],
  "Berkshire": [
    ["E06000036", "Bracknell Forest"],
    ["E06000037", "West Berkshire"],
    ["E06000038", "Reading"],
    ["E06000039", "Slough"],
    ["E06000040", "Windsor and Maidenhead"],
    ["E06000041", "Wokingham"]
  ],
  "Buckinghamshire": [
    ["E10000002", "Buckinghamshire County"],
    ["E06000042", "Milton Keynes"]
  ],
  "Cambridgeshire": [
    ["E10000003", "Cambridgeshire County"],
    ["E06000031", "City of Peterborough"]
  ],
  "Cheshire": [
    ["E06000049", "Cheshire East"],
    ["E06000050", "Cheshire West and Chester"],
    ["E06000006", "Halton"],
    ["E06000007", "Warrington"]
  ],
  "City of Bristol": [["E06000023", "City of Bristol"]],
  "Cornwall": [
    ["E06000052", "Cornwall"],
    ["E06000053", "Isles of Scilly"]
  ],
  "Cumbria": [["E10000006", "Cumbria County"]],
  "Derbyshire": [
    ["E10000007", "Derbyshire County"],
    ["E06000015", "City of Derby"]
  ],
  "Devon": [
    ["E10000008", "Devon County"],
    ["E06000026", "City of Plymouth"],
    ["E06000027", "Torbay"]
  ],
  "Dorset": [
    ["E10000009", "Dorset County"],
    ["E06000028", "Bournemouth"],
    ["E06000029", "Poole"]
  ],
  "Durham": [
    ["E06000047", "County Durham"],
    ["E06000005", "Darlington"],
    ["E06000001", "Hartlepool"],
    
    # /* and the twenty wards to the north of the Tees in Stockton-on-Tees */
    # ["E05001527", "Billingham Central Ward"],
    # ["E05001528", "Billingham East Ward"],
    # ["E05001529", "Billingham North Ward"],
    # ["E05001530", "Billingham South Ward"],
    # ["E05001531", "Billingham West Ward"],
    # ["E05001532", "Bishopsgarth and Elm Tree Ward"],
    # ["E05001533", "Eaglescliffe Ward"],
    # ["E05001534", "Fairfield Ward"],
    # ["E05001535", "Grangefield Ward"],
    # ["E05001536", "Hardwick Ward"],
    # ["E05001537", "Hartburn Ward"],
    # ["E05001541", "Newtown Ward"],
    # ["E05001542", "Northern Parishes Ward"],
    # ["E05001543", "Norton North Ward"],
    # ["E05001544", "Norton South Ward"],
    # ["E05001545", "Norton West Ward"],
    # ["E05001546", "Parkfield and Oxbridge Ward"],
    # ["E05001547", "Roseworth Ward"],
    # ["E05001549", "Stockton Town Centre Ward"],
    # ["E05001551", "Western Parishes Ward"],
    ["E06000004", "Stockton-on-Tees"] # pretend all of Stockton is in Durham
  ],
  "The East Riding of Yorkshire": [
    ["E06000011", "East Riding of Yorkshire"],
    ["E06000010", "City of Kingston upon Hull"]
  ],
  "East Sussex": [
    ["E10000011", "East Sussex County"],
    ["E06000043", "The City of Brighton and Hove"]
  ],
  "Essex": [
    ["E10000012", "Essex County"],
    ["E06000033", "Southend-on-Sea"],
    ["E06000034", "Thurrock"]
  ],
  "Gloucestershire": [
    ["E10000013", "Gloucestershire County"],
    ["E06000025", "South Gloucestershire"]
  ],
  "Hampshire": [
    ["E10000014", "Hampshire County"],
    ["E06000044", "City of Portsmouth"],
    ["E06000045", "City of Southampton"]
  ],
  "Herefordshire": [["E06000019", "County of Herefordshire"]],
  "Hertfordshire": [["E10000015", "Hertfordshire County"]],
  "Isle of Wight": [["E06000046", "Isle of Wight"]],
  "Kent": [
    ["E10000016", "Kent County"],
    ["E06000035", "Medway"]
  ],
  "Lancashire": [
    ["E10000017", "Lancashire County"],
    ["E06000008", "Blackburn with Darwen"],
    ["E06000009", "Blackpool"]
  ],
  "Leicestershire": [
    ["E10000018", "Leicestershire County"],
    ["E06000016", "City of Leicester"]
  ],
  "Lincolnshire": [
    ["E10000019", "Lincolnshire County"],
    ["E06000013", "North Lincolnshire"],
    ["E06000012", "North East Lincolnshire"]
  ],
  "Norfolk": [["E10000020", "Norfolk County"]],
  "Northamptonshire": [["E10000021", "Northamptonshire County"]],
  "North Yorkshire": [
    ["E10000023", "North Yorkshire County"],
    ["E06000002", "Middlesbrough"],
    ["E06000003", "Redcar and Cleveland"],
    ["E06000014", "York"],
    
    # /* and the six wards to the south of the Tees in Stockton-on-Tees */
    # ["E05001538", "Ingleby Barwick East"],
    # ["E05001539", "Ingleby Barwick West"],
    # ["E05001540", "Mandale and Victoria"],
    # ["E05001548", "Stainsby Hill"],
    # ["E05001550", "Village"],
    # ["E05001552", "Yarm"],
  ],
  "Northumberland": [["E06000048", "Northumberland"]],
  "Nottinghamshire": [
    ["E10000024", "Nottinghamshire"],
    ["E06000018", "City of Nottingham"]
  ],
  "Oxfordshire": [["E10000025", "Oxfordshire County"]],
  "Rutland": [["E06000017", "Rutland"]],
  "Shropshire": [
    ["E06000051", "Shropshire"],
    ["E06000020", "Telford and Wrekin"]
  ],
  "Somerset": [
    ["E10000027", "Somerset County"],
    ["E06000022", "Bath and North East Somerset"],
    ["E06000024", "North Somerset"]
  ],
  "Suffolk": [["E10000029", "Suffolk County"]],
  "Surrey": [["E10000030", "Surrey County"]],
  "Staffordshire": [
    ["E10000028", "Staffordshire County"],
    ["E06000021", "City of Stoke-on-Trent"]
  ],
  "Warwickshire": [["E10000031", "Warwickshire County"]],
  "West Sussex": [["E10000032", "West Sussex County"]],
  "Wiltshire": [
    ["E06000054", "Wiltshire"],
    ["E06000030", "Swindon"]
  ],
  "Worcestershire": [["E10000034", "Worcestershire County"]],
  
  "Greater Manchester": [
    ["E08000001", "Bolton District"],
    ["E08000002", "Bury District"],
    ["E08000003", "Manchester District"],
    ["E08000004", "Oldham District"],
    ["E08000005", "Rochdale District"],
    ["E08000006", "Salford District"],
    ["E08000007", "Stockport District"],
    ["E08000008", "Tameside District"],
    ["E08000009", "Trafford District"],
    ["E08000010", "Wigan District"]
  ],
  "Merseyside": [
    ["E08000011", "Knowsley District"],
    ["E08000012", "Liverpool District"],
    ["E08000013", "St. Helens District"],
    ["E08000014", "Sefton District"],
    ["E08000015", "Wirral District"]
  ],
  "South Yorkshire": [
    ["E08000016", "Barnsley District"],
    ["E08000017", "Doncaster District"],
    ["E08000018", "Rotherham District"],
    ["E08000019", "Sheffield District"]
  ],  
  "Tyne and Wear": [
    ["E08000020", "Gateshead District"],
    ["E08000021", "Newcastle upon Tyne District"],
    ["E08000022", "North Tyneside District"],
    ["E08000023", "South Tyneside District"],
    ["E08000024", "Sunderland District"]
  ],
  "West Midlands": [
    ["E08000025", "Birmingham District"],
    ["E08000026", "Coventry District"],
    ["E08000027", "Dudley District"],
    ["E08000028", "Sandwell District"],
    ["E08000029", "Solihull District"],
    ["E08000030", "Walsall District"],
    ["E08000031", "City of Wolverhampton District"]
  ],
  "West Yorkshire": [
    ["E08000032", "Bradford District"],
    ["E08000033", "Calderdale District"],
    ["E08000034", "Kirklees District"],
    ["E08000035", "Leeds District"],
    ["E08000036", "Wakefield District"]
  ],
  
  
  # "Greater London": [
  #   ["E09000001", "City and County of the City of London"],
  #   ["E09000002", "Barking and Dagenham London Boro"],
  #   ["E09000003", "Barnet London Boro"],
  #   ["E09000004", "Bexley London Boro"],
  #   ["E09000005", "Brent London Boro"],
  #   ["E09000006", "Bromley London Boro"],
  #   ["E09000007", "Camden London Boro"],
  #   ["E09000008", "Croydon London Boro"],
  #   ["E09000009", "Ealing London Boro"],
  #   ["E09000010", "Enfield London Boro"],
  #   ["E09000011", "Greenwich London Boro"],
  #   ["E09000012", "Hackney London Boro"],
  #   ["E09000013", "Hammersmith and Fulham London Boro"],
  #   ["E09000014", "Haringey London Boro"],
  #   ["E09000015", "Harrow London Boro"],
  #   ["E09000016", "Havering London Boro"],
  #   ["E09000017", "Hillingdon London Boro"],
  #   ["E09000018", "Hounslow London Boro"],
  #   ["E09000019", "Islington London Boro"],
  #   ["E09000020", "Kensington and Chelsea London Boro"],
  #   ["E09000021", "Kingston upon Thames London Boro"],
  #   ["E09000022", "Lambeth London Boro"],
  #   ["E09000023", "Lewisham London Boro"],
  #   ["E09000024", "Merton London Boro"],
  #   ["E09000025", "Newham London Boro"],
  #   ["E09000026", "Redbridge London Boro"],
  #   ["E09000027", "Richmond upon Thames London Boro"],
  #   ["E09000028", "Southwark London Boro"],
  #   ["E09000029", "Sutton London Boro"],
  #   ["E09000030", "Tower Hamlets London Boro"],
  #   ["E09000031", "Waltham Forest London Boro"],
  #   ["E09000032", "Wandsworth London Boro"],
  #   ["E09000033", "City of Westminster London Boro"]
  # ]
}

welsh_counties = {
  "Gwynedd": [
    ["W06000001", "Sir Ynys Mon", "Isle of Anglesey"],
    ["W06000002", "Gwynedd", "Gwynedd"]
  ],

  "Clwyd": [
    ["W06000003", "Conwy", "Conwy"],
    ["W06000004", "Sir Ddinbych", "Denbighshire"],
    ["W06000005", "Sir y Fflint", "Flintshire"],
    ["W06000006", "Wrecsam", "Wrexham"]
  ],

  "Dyfed": [
    ["W06000008", "Sir Ceredigion", "Ceredigion"],
    ["W06000009", "Sir Benfro", "Pembrokeshire"],
    ["W06000010", "Sir Gaerfyrddin", "Carmarthenshire"]
  ],

  "West Glamorgan": [
    ["W06000011", "Abertawe", "Swansea"],
    ["W06000012", "Castell-nedd Port Talbot", "Neath Port Talbot"]
  ],

  "South Glamorgan": [
    ["W06000014", "Bro Morgannwg", "the Vale of Glamorgan"],
    ["W06000015", "Caerdydd", "Cardiff"]
  ],

  "Gwent": [
    ["W06000018", "Caerffili", "Caerphilly"],
    ["W06000019", "Blaenau Gwent", "Blaenau Gwent"],
    ["W06000020", "Tor-faen", "Torfaen"],
    ["W06000021", "Sir Fynwy", "Monmouthshire"],
    ["W06000022", "Casnewydd", "Newport"]
  ],

  "Powys": [["W06000023", "Powys", "Powys"]],

  "Mid Glamorgan": [
    ["W06000013", "Pen-y-bont ar Ogwr", "Bridgend"],
    ["W06000016", "Rhondda Cynon Taf", "Rhondda Cynon Taf"],
    ["W06000024", "Merthyr Tudful", "Merthyr Tydfil"]
  ]
}


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

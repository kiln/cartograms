-- Assumes gb-counties.sql has already been loaded;
-- just copies it and adds the counties of Northern Ireland

create table northern_ireland_county (
  name varchar not null unique
);
SELECT AddGeometryColumn('','northern_ireland_county','the_geom','4326','MULTIPOLYGON',2);
-- Run northern-ireland-counties.py to populate northern_ireland_county

begin;
insert into division (name) values ('uk-counties');
insert into region (division_id, name, the_geom, area) (
    select uk_counties_division.id, gb_region.name, gb_region.the_geom, gb_region.area
    from region gb_region, division uk_counties_division
    where gb_region.division_id = (select id from division where name = 'gb-counties')
    and uk_counties_division.name = 'uk-counties'
);

insert into region (division_id, name, the_geom, area) (
    select uk_counties_division.id
         , northern_ireland_county.name
         , northern_ireland_county.the_geom
         , ST_Area(northern_ireland_county.the_geom)
    from division uk_counties_division, northern_ireland_county
    where uk_counties_division.name = 'uk-counties'
);
commit;

-- Obviously Ireland is not a UK county, but sometimes we want to draw it on the same map
-- so it’s useful to have it here.

-- Fetch http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/10m-admin-0-countries.zip
-- shp2pgsql -s 4326 -W LATIN1 ~/Downloads/10m-admin-0-countries/ne_10m_admin_0_countries | psql
insert into region (division_id, name, the_geom, area) (
  select uk_counties_division.id, 'Ireland',
         ne_10m_admin_0_countries.the_geom, ST_Area(ne_10m_admin_0_countries.the_geom)
  from division uk_counties_division
      , ne_10m_admin_0_countries
  where uk_counties_division.name = 'uk-counties'
  and ne_10m_admin_0_countries.name = 'Ireland'
);

select compute_breakpoints('uk-counties');


-- robin=> select ST_Extent(ST_Transform(the_geom, 27700)) from region where division_id = (select id from division where name = 'uk-counties');
--  BOX(-179492.868803394 5333.59922513456,655989.000960375 1220301.5004298)

insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) (
  select division.id,
  'os-uk-counties', 27700,
  -180000, 5000, 705500, 1305000,
  400, 600
  from division where name = 'uk-counties'
);
select populate_grid('os-uk-counties');
select grid_set_regions('os-uk-counties', 'uk-counties');

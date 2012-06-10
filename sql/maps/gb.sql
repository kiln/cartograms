-- Map of Great Britain

-- bdline_gb data downloaded from http://www.ordnancesurvey.co.uk/oswebsite/products/boundary-line/index.html

-- # Loading the county boundaries from the OS
-- $ shp2pgsql -s 27700 bdline_gb/data/county_region.shp county |psql
-- $ shp2pgsql -s 27700 bdline_gb/data/district_borough_unitary_region.shp unitary_region |psql

insert into division (name) values ('utas');
insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'os-britain', 27700,
  5500, -1000000, 5500 + 800000, -1000000 + 1035000,
  541, 700
);

select populate_grid('os-britain');

insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), code, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from county
);
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), code, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from unitary_region
    where area_code in ('UTA', 'MTD')
);
update region
set name = 'E12000007'
where name = '999999'
and division_id = (select id from division where name = 'utas');

select grid_set_regions('os-britain', 'utas');




insert into division (name) values ('districts');
insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'os-britain-districts', 27700,
  5500, -1000000, 5500 + 800000, -1000000 + 1035000,
  541, 700
);

insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), code, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from unitary_region
);

select populate_grid('os-britain-districts')
     , grid_set_regions('os-britain-districts', 'districts');

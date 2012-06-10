-- US States

-- $ curl -LO http://geocommons.com/overlays/21424.zip
-- $ (mkdir 21424 && cd 21424 && unzip ../21424.zip)
-- $ shp2pgsql -s 4326 21424/usa_state_shapefile.shx | psql

-- http://spatialreference.org/ref/esri/102003/postgis/
INSERT into spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext) values ( 9102003, 'esri', 102003, '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs ', 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["North_American_Datum_1983",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["longitude_of_center",-96],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],PARAMETER["latitude_of_center",37.5],UNIT["Meter",1],AUTHORITY["EPSG","102003"]]');

insert into division (name) values ('us-states');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), state_name, the_geom, ST_Area(the_geom) from usa_state_shapefile
);

-- robin=# select ST_Extent(ST_Transform(the_geom, 9102003)) from usa_state_shapefile where state_name not in ('Alaska', 'Hawaii');
--  BOX(-2354935.75 -1294963.875,2256319.25 1558806.125)

insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'usa-contiguous', 9102003,
  -2354935.75, -1294963.875, 2256319.25, 1558806.125,
  800, 500
);

select populate_grid('usa-contiguous')
     , grid_set_regions('usa-contiguous', 'us-states');



-- $ curl -LO http://www.nws.noaa.gov/geodata/catalog/national/data/s_01ja11.zip
-- $ (mkdir s_01ja11 && cd s_01ja11 && unzip ../s_01ja11.zip)
-- $ shp2pgsql -s 4326 s_01ja11/s_01ja11.shx | psql

-- select ST_Extent(ST_Transform(the_geom, 9102003)) from s_01ja11 where state not in ('AK', 'AH', 'AS', 'GU', 'HI', 'MP', 'PR', 'UM', 'VI');
--  BOX(-2356113.742898 -1337508.07561825,2258224.79945606 1565791.05687272)

delete from grid where division_id = (select id from division where name = 'us-states');
delete from region where division_id = (select id from division where name = 'us-states');
insert into region (division_id, name, the_geom, area) (
    select division.id, state, the_geom, ST_Area(the_geom)
    from s_01ja11
       , division
    where division.name = 'us-states'
);


delete from grid where map_id = (select id from map where name = 'usa-contiguous');
delete from map where name = 'usa-contiguous';
insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) (select
    division.id,
    'usa-contiguous', 9102003,
    -2356113.742898, -1337508.07561825, 2258224.79945606, 1565791.05687272,
    800, 500
  from division
  where name = 'us-states'
);

select populate_grid('usa-contiguous')
     , grid_set_regions('usa-contiguous', 'us-states');


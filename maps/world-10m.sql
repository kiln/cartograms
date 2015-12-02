-- High-resolution country outlines from Natural Earth, version 3.1.0

/*
  shp2pgsql -s 4326 ne_10m_admin_0_countries.shp ne_10m_admin_0_countries_3_1_0 | psql
*/

SELECT topology.CreateTopology('ne_10m_admin_0_countries_3_1_0_topo', 4326);

SELECT topology.DropTopoGeometryColumn('public', 'topo_ne_10m_admin_0_countries_3_1_0', 'topo');
DROP TABLE topo_ne_10m_admin_0_countries_3_1_0;

CREATE TABLE topo_ne_10m_admin_0_countries_3_1_0 (
    id serial not null primary key,
    code char(3) not null,
    iso_a2 char(3),
    name character varying(60)
);
SELECT topology.AddTopoGeometryColumn('ne_10m_admin_0_countries_3_1_0_topo', 'public', 'topo_ne_10m_admin_0_countries_3_1_0', 'topo', 'MULTIPOLYGON');
SELECT AddGeometryColumn('topo_ne_10m_admin_0_countries_3_1_0', 'bbox', 4326, 'POLYGON', 2);

/*
bin/topologise.py --shp-table=ne_10m_admin_0_countries_3_1_0 --topo-table=topo_ne_10m_admin_0_countries_3_1_0 --tolerance=0.00001 --tolerance-json='{"USA": 0.001}' --code-col=adm0_a3 --secondary-code-col=iso_a2 --name-col=name_long --batch-size=10 --commit-every=100

ogr2ogr -overwrite ne_10m_admin_0_countries_3_1_0.shp PG:dbname=robin -sql "select code, name, topology.ST_Simplify(topo, 0) from topo_ne_10m_admin_0_countries_3_1_0"
*/

CREATE TABLE ne_10m_admin_0_countries_3_1_0_toposimplified (
    id serial not null primary key,
    code char(3) not null,
    iso_a2 char(3),
    name character varying(60)
);
SELECT AddGeometryColumn('ne_10m_admin_0_countries_3_1_0_toposimplified', 'geom', 4326, 'MULTIPOLYGON', 2);

insert into ne_10m_admin_0_countries_3_1_0_toposimplified (
    code, iso_a2, name, geom
) (
    select code, iso_a2, name, topology.ST_Simplify(topo, 0)
    from topo_ne_10m_admin_0_countries_3_1_0
);

delete from grid where division_id = (select id from division where name = 'countries-10m-3.1.0');
delete from data_value where division_id = (select id from division where name = 'countries-10m-3.1.0');
delete from dataset where division_id = (select id from division where name = 'countries-10m-3.1.0');
delete from map where division_id = (select id from division where name = 'countries-10m-3.1.0');
delete from region where division_id = (select id from division where name = 'countries-10m-3.1.0');
delete from division where name = 'countries-10m-3.1.0';

insert into division (name) values ('countries-10m-3.1.0');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), iso_a2, geom, ST_Area(geom)
    from ne_10m_admin_0_countries_3_1_0_toposimplified
    where iso_a2 <> '-99'
    and code not in ('IND', 'KAZ')
);

-- The Baikonur Cosmodrome in Kazakhstan is leased to Russia, but for cartogram
-- purposes it makes more sense to include it in Kazakhstan.
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'KZ'
         , ST_Union(kaz.geom, kab.geom)
         , ST_Area(ST_Union(kaz.geom, kab.geom))
    from ne_10m_admin_0_countries_3_1_0_toposimplified kaz
       , ne_10m_admin_0_countries_3_1_0_toposimplified kab
    where kaz.code = 'KAZ'
    and kab.code = 'KAB'
);

-- To avoid leaving a hole in the map, we need to do something with the
-- Siachen Glacier in Kashmir, which is claimed by both India and Pakistan.
-- There isn’t an obvious good solution to this, so for now let’s arbitrarily
-- combine it with India.
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'IN'
         , ST_Union(ind.geom, kas.geom)
         , ST_Area(ST_Union(ind.geom, kas.geom))
    from ne_10m_admin_0_countries_3_1_0_toposimplified ind
       , ne_10m_admin_0_countries_3_1_0_toposimplified kas
    where ind.code = 'IND'
    and kas.code = 'KAS'
);


-- There are some surprising omissions in the iso_a2 column in this version
-- of the Natural Earth data
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'NO', ST_Union(geom), ST_Area(ST_Union(geom))
    from ne_10m_admin_0_countries_3_1_0_toposimplified
    where code = 'NOR'
);
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'FR', ST_Union(geom), ST_Area(ST_Union(geom))
    from ne_10m_admin_0_countries_3_1_0_toposimplified
    where code = 'FRA'
);
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'XK', ST_Union(geom), ST_Area(ST_Union(geom))
    from ne_10m_admin_0_countries_3_1_0_toposimplified
    where code = 'KOS'
);

select compute_breakpoints('countries-10m-3.1.0');

insert into map (
  division_id,
  name, srid,
  x_min, x_max,
  y_min, y_max,
  width, height
) (
  select currval('division_id_seq'),
  'world-10m-3.1.0-robinson', 954030,
  ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(-180, 0), 4326), 954030)),
  ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(180, 0), 4326), 954030)),
  ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(0, -90), 4326), 954030)),
  ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(0, 90), 4326), 954030)),
  500, 250
);

select populate_grid('world-10m-3.1.0-robinson');
select grid_set_regions('world-10m-3.1.0-robinson', 'countries-10m-3.1.0');


/*
-- Subdivided countries, used for the Guardian Travel Maps
insert into division (name) values ('subdivided-countries-10m');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), iso_a2, ST_Union(the_geom), ST_Area(ST_Union(the_geom))
    from ne_10m_admin_0_countries
    where iso_a2 <> '-99'
    group by iso_a2
);

-- Divide the US into Alaska and the rest of the US
create temporary table us_parts as select (q.d).* from (
  select ST_Dump(the_geom) d
  from region
  where division_id = (select id from division where name = 'subdivided-countries-10m')
  and name = 'US'
) q;

update region set the_geom = (
  select ST_Collect(geom) from us_parts where path[1] <> 313
), area = (select ST_Area(ST_Collect(geom)) from us_parts where path[1] <> 313)
where division_id = (select id from division where name = 'subdivided-countries-10m')
and name = 'US';

insert into region (division_id, name, the_geom, area) (
  select (select id from division where name = 'subdivided-countries-10m')
       , 'AK'
       , (select ST_Collect(geom) from us_parts where path[1] = 313)
       , (select ST_Area(geom) from us_parts where path[1] = 313)
);

drop table us_parts;

-- Divide Norway into Svalbard and the rest of Norway
create temporary table no_parts as select (q.d).* from (
  select ST_Dump(the_geom) d
  from region
  where division_id = (select id from division where name = 'subdivided-countries-10m')
  and name = 'NO'
) q;

update region set the_geom = (
  select ST_Collect(geom) from no_parts where ST_Ymin(geom) <= 75
), area = (select ST_Area(ST_Collect(geom)) from no_parts where ST_Ymin(geom) <= 75)
where division_id = (select id from division where name = 'subdivided-countries-10m')
and name = 'NO';

insert into region (division_id, name, the_geom, area) (
  select (select id from division where name = 'subdivided-countries-10m')
       , 'SJ'
       , (select ST_Collect(geom) from no_parts where ST_Ymin(geom) > 75)
       , (select ST_Area(ST_Collect(geom)) from no_parts where ST_Ymin(geom) > 75)
);

drop table no_parts;

select compute_breakpoints('subdivided-countries-10m');

insert into map (
  division_id,
  name, srid,
  x_min, x_max,
  y_min, y_max,
  width, height
) (
  select currval('division_id_seq'),
  'world-10m-3.1.0-robinson-subdivided', 954030,
  ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(-180, 0), 4326), 954030)),
  ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(180, 0), 4326), 954030)),
  ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(0, -90), 4326), 954030)),
  ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(0, 90), 4326), 954030)),
  500, 250
);

select populate_grid('world-10m-3.1.0-robinson-subdivided');
select grid_set_regions('world-10m-3.1.0-robinson-subdivided', 'subdivided-countries-10m');
*/


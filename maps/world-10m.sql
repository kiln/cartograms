-- High-resolution country outlines from Natural Earth, version 3.1.0

insert into division (name) values ('countries-10m-3.1.0');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), iso_a2, ST_Union(geom), ST_Area(ST_Union(geom))
    from ne_10m_admin_0_countries_3_1_0
    where iso_a2 <> '-99'
    group by iso_a2
);

-- There are some surprising omissions in the iso_a2 column in this version
-- of the Natural Earth data
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'NO', ST_Union(geom), ST_Area(ST_Union(geom))
    from ne_10m_admin_0_countries_3_1_0
    where name = 'Norway'
);
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'FR', ST_Union(geom), ST_Area(ST_Union(geom))
    from ne_10m_admin_0_countries_3_1_0
    where name = 'France'
);
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), 'XK', ST_Union(geom), ST_Area(ST_Union(geom))
    from ne_10m_admin_0_countries_3_1_0
    where name = 'Kosovo'
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


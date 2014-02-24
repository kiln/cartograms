-- High-resolution country outlines from Natural Earth

insert into division (name) values ('countries-10m');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), iso_a2, ST_Union(the_geom), ST_Area(ST_Union(the_geom))
    from ne_10m_admin_0_countries
    where iso_a2 <> '-99'
    group by iso_a2
);
select compute_breakpoints('countries-10m');

insert into map (
  division_id,
  name, srid,
  x_min, x_max,
  y_min, y_max,
  width, height
) (
  select currval('division_id_seq'),
  'world-10m-robinson', 954030,
  ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(-180, 0), 4326), 954030)),
  ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(180, 0), 4326), 954030)),
  ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(0, -90), 4326), 954030)),
  ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(0, 90), 4326), 954030)),
  500, 250
);

select populate_grid('world-10m-robinson');
select grid_set_regions('world-10m-robinson', 'countries-10m');

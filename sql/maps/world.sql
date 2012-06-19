-- World map

-- $ shp2pgsql -W LATIN1 -s 4326 TM_WORLD_BORDERS-0/TM_WORLD_BORDERS-0.3.shp country | psql

insert into division (name) values ('countries');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), iso2, the_geom, ST_Area(the_geom) from country
);
select compute_breakpoints('countries');

-- All the vertices are *very* close to grid-points on a 1E-6 grid,
-- so presumably were snapped to this grid at some point but have
-- drifted slightly due to accumulated errors of some sort when the
-- shape files were being prepared. Snapping back to the grid helps the
-- borders of neighbouring countries to match precisely where they should.
update region
set the_geom = ST_SnapToGrid(the_geom, 1E-6)
  , area = ST_Area(ST_SnapToGrid(the_geom, 1E-6))
where division_id = currval('division_id_seq');


insert into map (
  division_id,
  name, srid,
  x_min, x_max,
  y_min, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'world-robinson', 954030,
  -17005833.3305252, 17005833.3305252,
  -8625154.47184994, 8625154.47184994,
  500, 250;
  
);

select populate_grid('world-robinson');
select grid_set_regions('world-robinson', 'countries');

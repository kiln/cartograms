create or replace function populate_grid (
  map_name varchar
) returns void as $$
begin
  insert into grid (
    map_id, division_id, x, y, pt_4326
  ) (
      with map as (
          select * from map where name = map_name
      ),
      pregrid as (
          select map.id map_id
               , map.division_id
               , xs.x, ys.y
               , (map.x_max - map.x_min) * xs.x / map.width  + map.x_min mx
               , (map.y_max - map.y_min) * ys.y / map.height + map.y_min my
               , map.srid
          from map
             , (select generate_series(0, width)  x from map) xs
             , (select generate_series(0, height) y from map) ys
      )
      select map_id, division_id
           , x, y
           , ST_Transform(
               ST_SetSRID(
                 ST_MakePoint(mx, my)
                 , srid
               ), 4326
             ) pt_4326
      from pregrid
  );
end;
$$ language 'plpgsql';

create or replace function grid_set_regions(
  map_name varchar,
  division_name varchar
) returns void as $$
  declare
    r record;
  begin
    for r in select generate_series(0, height) i from map where name = map_name loop
      raise notice 'Updating grid row y=%', r.i;
      update grid
      set region_id = region.id
      from region
      join division on region.division_id = division.id
         , map
      where grid.map_id = map.id
      and division.name = division_name
      and map.name = map_name
      and ST_Contains(region.the_geom, grid.pt_4326)
      and grid.y = r.i;
    end loop;
  end;
$$ language 'plpgsql';


create or replace function compute_breakpoints(
  division_name varchar
) returns void as $$
  declare
    target_division_id integer;
  begin
    select into target_division_id id from division where name = division_name;
    
    update region
      set breakpoints = (
        select ST_Union(
          CASE GeometryType(x.border)
            WHEN 'POINT' THEN
              x.border
            WHEN 'LINESTRING' THEN
              ST_Boundary(x.border)
            WHEN 'MULTILINESTRING' THEN
              ST_Boundary(ST_LineMerge(x.border))
          END
        )
        from (
          select ST_Intersection(ST_Boundary(region.the_geom), ST_Boundary(neighbour.the_geom)) border
          from region neighbour
          where ST_Touches(region.the_geom, neighbour.the_geom)
          and neighbour.division_id = target_division_id
        ) x
      )
    where division_id = target_division_id;
  end;
$$ language 'plpgsql';

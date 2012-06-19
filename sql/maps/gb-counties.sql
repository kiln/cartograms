insert into division (name) values ('gb-counties');

insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), code, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from county
);

-- begin output from gb-counties.py --
create temporary table gb_county (
  id serial PRIMARY KEY,
  name character varying(60) not null unique
);
select AddGeometryColumn('','gb_county','the_geom','27700','MULTIPOLYGON',2);
insert into gb_county (name, the_geom) (
  select 'Merseyside', ST_Multi(ST_Union(the_geom))
  from unitary_region metropolitan_district
  where area_code = 'MTD'
  and code in ('E08000013', 'E08000012', 'E08000011', 'E08000015', 'E08000014')
);

insert into gb_county (name, the_geom) (
  select 'Oxfordshire', the_geom
  from county where code = 'E10000025'
);

insert into gb_county (name, the_geom) (
  select 'Greater Manchester', ST_Multi(ST_Union(the_geom))
  from unitary_region metropolitan_district
  where area_code = 'MTD'
  and code in ('E08000010', 'E08000004', 'E08000005', 'E08000006', 'E08000007', 'E08000001', 'E08000002', 'E08000003', 'E08000008', 'E08000009')
);

insert into gb_county (name, the_geom) (
  select 'Kent', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000016')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000035')
);

insert into gb_county (name, the_geom) (
  select 'Bedfordshire', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000055', 'E06000056', 'E06000032')
);

insert into gb_county (name, the_geom) (
  select 'West Yorkshire', ST_Multi(ST_Union(the_geom))
  from unitary_region metropolitan_district
  where area_code = 'MTD'
  and code in ('E08000035', 'E08000034', 'E08000036', 'E08000033', 'E08000032')
);

insert into gb_county (name, the_geom) (
  select 'Warwickshire', the_geom
  from county where code = 'E10000031'
);

insert into gb_county (name, the_geom) (
  select 'Dorset', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000009')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000028', 'E06000029')
);

insert into gb_county (name, the_geom) (
  select 'Hertfordshire', the_geom
  from county where code = 'E10000015'
);

insert into gb_county (name, the_geom) (
  select 'Norfolk', the_geom
  from county where code = 'E10000020'
);

insert into gb_county (name, the_geom) (
  select 'Herefordshire', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000019')
);

insert into gb_county (name, the_geom) (
  select 'Shropshire', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000020', 'E06000051')
);

insert into gb_county (name, the_geom) (
  select 'Cambridgeshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000003')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000031')
);

insert into gb_county (name, the_geom) (
  select 'Rutland', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000017')
);

insert into gb_county (name, the_geom) (
  select 'Lancashire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000017')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000008', 'E06000009')
);

insert into gb_county (name, the_geom) (
  select 'Derbyshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000007')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000015')
);

insert into gb_county (name, the_geom) (
  select 'Surrey', the_geom
  from county where code = 'E10000030'
);

insert into gb_county (name, the_geom) (
  select 'West Midlands', ST_Multi(ST_Union(the_geom))
  from unitary_region metropolitan_district
  where area_code = 'MTD'
  and code in ('E08000028', 'E08000029', 'E08000026', 'E08000027', 'E08000025', 'E08000031', 'E08000030')
);

insert into gb_county (name, the_geom) (
  select 'Buckinghamshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000002')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000042')
);

insert into gb_county (name, the_geom) (
  select 'Durham', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000047', 'E06000001', 'E06000004', 'E06000005')
);

insert into gb_county (name, the_geom) (
  select 'City of Bristol', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000023')
);

insert into gb_county (name, the_geom) (
  select 'Northamptonshire', the_geom
  from county where code = 'E10000021'
);

insert into gb_county (name, the_geom) (
  select 'Berkshire', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000039', 'E06000038', 'E06000040', 'E06000041', 'E06000037', 'E06000036')
);

insert into gb_county (name, the_geom) (
  select 'Hampshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000014')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000044', 'E06000045')
);

insert into gb_county (name, the_geom) (
  select 'Isle of Wight', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000046')
);

insert into gb_county (name, the_geom) (
  select 'Somerset', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000027')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000024', 'E06000022')
);

insert into gb_county (name, the_geom) (
  select 'Worcestershire', the_geom
  from county where code = 'E10000034'
);

insert into gb_county (name, the_geom) (
  select 'West Sussex', the_geom
  from county where code = 'E10000032'
);

insert into gb_county (name, the_geom) (
  select 'Lincolnshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000019')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000013', 'E06000012')
);

insert into gb_county (name, the_geom) (
  select 'Cornwall', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000053', 'E06000052')
);

insert into gb_county (name, the_geom) (
  select 'East Sussex', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000011')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000043')
);

insert into gb_county (name, the_geom) (
  select 'Devon', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000008')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000026', 'E06000027')
);

insert into gb_county (name, the_geom) (
  select 'Wiltshire', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000054', 'E06000030')
);

insert into gb_county (name, the_geom) (
  select 'Northumberland', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000048')
);

insert into gb_county (name, the_geom) (
  select 'Staffordshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000028')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000021')
);

insert into gb_county (name, the_geom) (
  select 'Cheshire', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000007', 'E06000006', 'E06000050', 'E06000049')
);

insert into gb_county (name, the_geom) (
  select 'Gloucestershire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000013')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000025')
);

insert into gb_county (name, the_geom) (
  select 'Leicestershire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000018')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000016')
);

insert into gb_county (name, the_geom) (
  select 'Tyne and Wear', ST_Multi(ST_Union(the_geom))
  from unitary_region metropolitan_district
  where area_code = 'MTD'
  and code in ('E08000024', 'E08000022', 'E08000023', 'E08000020', 'E08000021')
);

insert into gb_county (name, the_geom) (
  select 'South Yorkshire', ST_Multi(ST_Union(the_geom))
  from unitary_region metropolitan_district
  where area_code = 'MTD'
  and code in ('E08000019', 'E08000018', 'E08000017', 'E08000016')
);

insert into gb_county (name, the_geom) (
  select 'The East Riding of Yorkshire', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000011', 'E06000010')
);

insert into gb_county (name, the_geom) (
  select 'Essex', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000012')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000034', 'E06000033')
);

insert into gb_county (name, the_geom) (
  select 'Suffolk', the_geom
  from county where code = 'E10000029'
);

insert into gb_county (name, the_geom) (
  select 'Cumbria', the_geom
  from county where code = 'E10000006'
);

insert into gb_county (name, the_geom) (
  select 'North Yorkshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000023')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000002', 'E06000003', 'E06000014')
);

insert into gb_county (name, the_geom) (
  select 'Nottinghamshire', ST_Multi(ST_Union(
    ST_Union(unitary_region.the_geom),
    (select the_geom from county where area_code = 'CTY' and code = 'E10000024')
  ))
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('E06000018')
);

insert into gb_county (name, the_geom) (select 'Greater London', the_geom from county where area_code = 'GLA');

insert into gb_county (name, the_geom) (
  select 'South Glamorgan', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000015', 'W06000014')
);

insert into gb_county (name, the_geom) (
  select 'Clwyd', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000003', 'W06000004', 'W06000005', 'W06000006')
);

insert into gb_county (name, the_geom) (
  select 'Gwynedd', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000001', 'W06000002')
);

insert into gb_county (name, the_geom) (
  select 'Gwent', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000022', 'W06000020', 'W06000021', 'W06000019', 'W06000018')
);

insert into gb_county (name, the_geom) (
  select 'Powys', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000023')
);

insert into gb_county (name, the_geom) (
  select 'Mid Glamorgan', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000016', 'W06000013', 'W06000024')
);

insert into gb_county (name, the_geom) (
  select 'Dyfed', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000008', 'W06000009', 'W06000010')
);

insert into gb_county (name, the_geom) (
  select 'West Glamorgan', ST_Multi(
    ST_Union(unitary_region.the_geom)
  )
  from unitary_region
  where unitary_region.area_code = 'UTA'
  and unitary_region.code in ('W06000012', 'W06000011')
);

insert into gb_county (name, the_geom) (select name, the_geom from unitary_region where area_code = 'UTA' and code like 'S12%');

-- end output --

insert into region (division_id, name, the_geom, area) (
    select division.id, gb_county.name, ST_Transform(gb_county.the_geom, 4326), ST_Area(ST_Transform(gb_county.the_geom, 4326))
    from gb_county
       , division
    where division.name = 'gb-counties'
);
select compute_breakpoints('gb-counties');

insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) (
  select division.id,
  'os-britain-counties', 27700,
  5500, 5000, 705500, 1305000,
  700, 1300
  from division where name = 'gb-counties'
);
select populate_grid('os-britain-counties');
select grid_set_regions('os-britain-counties', 'gb-counties');

insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) (
  select division.id,
  'os-britain-counties-coarse', 27700,
  5500, 5000, 705500, 1305000,
  350, 650
  from division where name = 'gb-counties'
);
-- select populate_grid('os-britain-counties-coarse');
-- select grid_set_regions('os-britain-counties-coarse', 'gb-counties');
insert into grid ( map_id, division_id, x, y, pt_4326, region_id ) (
    select coarse_map.id, grid.division_id, grid.x/2, grid.y/2, grid.pt_4326, grid.region_id
    from grid, map coarse_map
    where map_id = (select id from map where name = 'os-britain-counties')
    and x%2 = 0 and y%2 = 0
    and coarse_map.name = 'os-britain-counties-coarse'
);

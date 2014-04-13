#!/bin/bash

# Extract the region grid for a map in CSV format.

set -e

map=$1
height=$(psql -At <<-SQL
select height from map where name = '$map'
SQL)

if [ -z $height ]
then
	echo>&2 "No such map: $map"
	echo>&2
	echo>&2 "Possible maps are:"
	psql -At <<-SQL | sed 's/^/ * /' >&2
	select name from map
	SQL
	exit 1
fi

tmpdir=$(mktemp -d /tmp/XXXXXXXXXXXX)
for y in $(seq 0 $[$height - 1])
do
	echo >&2 "Extracting row $y..."
	cat <<-SQL | psql > /dev/null
		\a\t
		\o $tmpdir/row$y
		select COALESCE(region.name, '')
		from grid left join region on grid.region_id = region.id
		where grid.map_id = (select id from map where name = '$map')
		and grid.y = $y
		order by grid.x
		;
		\o
	SQL
	perl -e 'chomp(@a=<>); print join(",", @a), "\n"' $tmpdir/row$y
done

rm -rf "$tmpdir"

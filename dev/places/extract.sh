#!/usr/bin/env bash
# Builds the tiles of quest places for France from OpenStreetMap (Geofabrik extract) into $1.
# Needs osmium-tool and node. About 10 minutes on a GitHub runner; run once a month.
# The tag filter matches QuestGeo.overpassQuery, so both paths see the same places.
set -euo pipefail
OUT=${1:-places-data}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
curl -sSfL --retry 3 -A "MaQueteDeChevalier/1.0 (monthly extract)" -o "$WORK/france.osm.pbf" https://download.geofabrik.de/europe/france-latest.osm.pbf
osmium tags-filter "$WORK/france.osm.pbf" \
  nwr/amenity=place_of_worship,fountain,townhall \
  nwr/man_made=water_well \
  nwr/historic=city_gate,castle,tower,ruins,fort,manor,monument,memorial,archaeological_site \
  nwr/leisure=park,playground,garden \
  nwr/place=square \
  nwr/tourism=artwork,viewpoint \
  -o "$WORK/places.osm.pbf" --overwrite
rm -f "$WORK/france.osm.pbf"
osmium export "$WORK/places.osm.pbf" -f geojsonseq -a type,id -o "$WORK/places.geojsonseq" --overwrite
node "$(dirname "$0")/build.mjs" "$WORK/places.geojsonseq" "$OUT"

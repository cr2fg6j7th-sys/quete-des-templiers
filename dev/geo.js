/* GEO-START
   Map helpers shared by the browser and the server: the OpenStreetMap query for places
   around a start point, and distances. The browser fetches the places itself; only the
   server chooses the stops. */

const QuestGeo = (() => {
  const SEARCH_RADIUS = 700;     // metres around the start point
  // Public OpenStreetMap (Overpass) servers, often busy: the main one first, then two mirrors.
  const SERVERS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"];

  function overpassQuery(lat, lon, r = SEARCH_RADIUS) {
    const a = `(around:${r},${lat.toFixed(6)},${lon.toFixed(6)})`;
    return `[out:json][timeout:25];(
nwr${a}["amenity"="place_of_worship"];
nwr${a}["amenity"~"^(fountain|townhall|watering_place|lavoir|fire_station|library|school|post_box)$"];
nwr${a}["man_made"~"^(water_well|cross|water_tower|watermill|windmill)$"];
nwr${a}["historic"~"^(city_gate|castle|tower|ruins|fort|manor|monument|memorial|archaeological_site|wayside_chapel|fountain|wayside_cross|mill|building|house|farm)$"];
nwr${a}["leisure"~"^(park|playground|garden|pitch|stadium)$"];
nwr${a}["place"="square"];
nwr${a}["tourism"~"^(artwork|viewpoint)$"];
nwr${a}["building"="chapel"]["name"];
node${a}["natural"="tree"]["name"];
node${a}["natural"="tree"]["denotation"~"^(natural_monument|landmark)$"];
nwr${a}["heritage"]["building"]["name"];
);out center tags;`;
  }

  function dist(a, b) {
    const R = 6371000, r = x => x * Math.PI / 180;
    const dLat = r(b.lat - a.lat), dLon = r(b.lon - a.lon);
    const q = Math.sin(dLat / 2) ** 2 + Math.cos(r(a.lat)) * Math.cos(r(b.lat)) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(q));
  }

  function bearing(a, b) {
    const r = x => x * Math.PI / 180;
    const y = Math.sin(r(b.lon - a.lon)) * Math.cos(r(b.lat));
    const x = Math.cos(r(a.lat)) * Math.sin(r(b.lat)) - Math.sin(r(a.lat)) * Math.cos(r(b.lat)) * Math.cos(r(b.lon - a.lon));
    const deg = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
    return ["le nord", "le nord-est", "l'est", "le sud-est", "le sud", "le sud-ouest", "l'ouest", "le nord-ouest"][Math.round(deg / 45) % 8];
  }

  // Keep only what the server needs from an Overpass answer: smaller upload, no geometry.
  function slim(elements) {
    return (elements || []).map(e => ({ type: e.type, id: e.id, lat: e.lat, lon: e.lon, center: e.center, tags: e.tags }))
      .filter(e => e.tags);
  }

  return { SEARCH_RADIUS, SERVERS, overpassQuery, dist, bearing, slim };
})();
if (typeof module !== "undefined") module.exports = QuestGeo;
/* GEO-END */

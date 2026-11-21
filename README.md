# Kelana Jaya LRT in 3D

An interactive 3D model of Kuala Lumpur's driverless Kelana Jaya Line (Line 5).
Live at https://kelana-jaya-lrt.vercel.app — Vercel redeploys on every push to the default branch.

Made by someone who has ridden the line for ten years, with Claude.

## How it is built

Everything is one file: `index.html`. No build step, no dependencies to install.
It loads three.js 0.187 as an ES module from jsdelivr (`<script type="module">`) and holds the styles, markup, map data and code inline.
Newer three.js manages colour itself: hex colours are read as ordinary screen colours, canvas textures are marked sRGB with `canvasTex`,
and light strengths are multiplied by π to match how r128 used to light the scene.
To change the model, edit `index.html` and push.

The script inside is in sections, each with a `/* ---------- name ---------- */` header, in this order:
the line (station table and centreline), materials, track sweep, ground and city, land (roads, rivers,
parks, other lines, cars), stations, passengers, trains, depot, train control, labels, layers, theme,
weather, camera, parts and info cards, how-it-runs steps, line list and next-trains board, sound, main loop.

Key ideas:

- **Scale.** Station positions are real, but the whole map is shrunk to about a third (`SC = .35`) so a ride
  takes minutes. Trains, track, stations and the depot are full size. Buildings and roads shrink with the map.
- **Track.** `cAt(u)` gives the centreline at distance `u`; `TP(u, dir)` gives the track a train is on.
  Two tracks, left-hand running, a crossover at each end.
- **Trains.** `stepTrain` is the automatic driver: speed limits for curves, a moving-block gap to the train
  ahead, station stops. `poseTrain` places the cars and bogies.
- **What's here.** Tap the ground (or empty map in Whole line) and `whatsHere(x, z)` fills the card: what the ground is, the
  three nearest stations with interchanges, other railways, named buildings and landmarks. Distances are words, not numbers
  (`walkWords`), measured in the real city (map distance / `SC`), with compass directions.
- **Lifelike light** (Controls tab, on by default, remembered per browser). Adds a graded sky dome with a sun glow, sky
  reflections (`scene.environment` from a PMREM of the sky), soft sun shadows in a box that follows the camera, and ACES tone mapping.
  Turning it off drops the shadows, reflections, sky and tone mapping, for slower devices. Brightness, reflections, fill, sun and fog distance
  are in `LOOK`; `lrtDebug.LOOK` and `lrtDebug.applyTheme()` let you tune them live. Touch devices get a smaller shadow map.
- **`window.lrtDebug`** exposes the trains and a `step(n, dt)` function for testing without waiting.

## Where the facts come from

| Thing | Source |
|---|---|
| Station order, coordinates, levels, platform types | Wikipedia, "Kelana Jaya Line" |
| Route between stations | OpenStreetMap, via Wikimedia's map service |
| Depot tracks and buildings | OpenStreetMap |
| Buildings, roads, rivers, parks, other lines | OpenStreetMap (Malaysia extract) |
| Power rails, reaction rail, walkway, red panels, livery, signs, tickers | the owner's own photos and notes |
| Door and announcement chimes | measured from the owner's recordings; door timing tuned by ear |
| Tunnel bores, substations, headway | IEM report of a 2010 visit to Subang Depot |

Map data © OpenStreetMap contributors.

## Known approximations

- Building, road and river shapes are simplified; buildings are plain blocks.
- Merdeka 118's position is from memory, not from map data.
- Train fleet numbers on the windscreens are invented.
- Where trains park in the depot, and the ramp to the main line, are not from the map.
- Ticker and next-train minutes are estimated from distance.
- The older two-car trains were withdrawn in 2023; they are kept as a heritage touch.
- Sound has only been checked by the owner's ear, and the Malay voice depends on the device.

## Hidden things

- Tap the amber next-station display five times.
- Tap the title five times.

## Ideas not built yet

A lighter, less washed-out depot in lifelike light · Flyovers lifted off the ground · the station buildings in more detail · proper shapes for more landmarks ·
other lines' stations and trains · solid car walls with real window openings for the inside view ·
keeping rivers visible in the underground cutaway.

## tools/

Reference scripts used to prepare the embedded data (they expect a local OpenStreetMap extract and
were run from a scratch folder, so paths need adjusting): route matching, building, land and rail
extraction, depot layout, and the chime analysis. `tools/data/` has the station coordinates and route waypoints.

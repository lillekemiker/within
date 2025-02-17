# Within take-home project

## Project Overview

This project is aiming to create a route planner for getting from one geographic
location to another by car, bike or walking. While the implementation is not limited
to movement with a single city, large routes for inter-city movement will rely on
collecting large amounts of street data from a traffic limited public API
(https://nominatim.openstreetmap.org/search).

### Current implementation

The routing problem was broken down into the following segments:

#### Identify the origin and destination points

Origin and destination locations are entered from the user in free text form.
This needs to be parsed and translated to longitude and latidude for each.
The Nominatim API supports a certain degree of parsing and being the simplest solution
this is attempted first. In case it fails (for instance if an input address is
abbreviated ast `st` rather than `street`), an address sanitizing step is taken
using the OpenAI API (an OpenAI API key will need to be available for this to work).
Once the sanitized address is available, the Nominatim API is tried again with this.
If this also fails, there is a final fallback mechanism asking the OpenAI API to
provide a latitude and longitude for the location. This is not a particularly
reliable source, though, so it is only used as a final fallback option.

#### Relevant map selection

The street map data is supplied by OpenStreetMap using the OSMNX library. In order
to only download the relevant section of the map data, the midway point between
the starting point and the destination is calculated as well as the direct distance 
between the two point. Finally the API is requested of all map data within the
circle defined by the midway point as center and the direct distance as diameter.
This is not viable for very large distances between origin and destination.
(See `Next steps` (6) regarding remedying this).

#### Finding shortest route

The OSMNX library currently supports finding the shortest route between to nodes
on the graph using either Yen's or Dijkstra’s algorithm. The former can return k
results, while the latter only produces one. For this reason, the Yen's algorithm
option is used. The function call to `osmnx.routing.k_shortest_paths()` allows for
a `weight` parameter that lets the optimization minimize for any edge attribute.
By default, this is the edge length. However, it can easily be substituded for
other parameters such as travel time.

#### Summarizing routing steps

Once a route has been found, it consists of a set of sequential nodes with connecting
edges. For a human readable output, this needs to be turned into text instructions.
This follows a few steps

* Instructions should include how far to travel before the next instruction
* Looping through the nodes, as long as they are all on the same street, going in the
  same direction, we just sum up the distance across nodes, and create a single instruction
  for them all.
* The first instruction should start with "Head [direction]"
* Following directions should start relative direction changes such as "Turn right"
  or "Bear left" depending on the relative change in direction and how sharp the
  turn is.
* Global cardinal bearing should be included
* Final instruction should be "Arriving at destination"

#### Visualizing the route on a map

While OSMNX has built-in graph and route visualization methods, none of them lends
themselves well to plotting a route on an existing map. Instead the `plotly`
package is used as it has built-in functionality for pulling map data from OpenStreetMap
and routes can be plotted easily using (latitude, longitude) coordinates for nodes
along the path. Additionally the plot is interactive in the browser and will let
the user zoom and pan as desired.


### Next steps

(Not necessarily in this order)

1. Travel time optimization. The OSMNX library graph supports the addition of
   travel times for edges as well as calculating these based on average speed by
   street type and edge length.
   Initially this can be applied and an option to optimize route based on travel
   time rather than distance can be added trivially.
2. Optimize for hills. OSMNX includes support for elevation data and a feature
   lacking in most other route optimizers is optimizing for a bike route with either
   the least or the most elevation changes, depending on ease vs work out
3. Adding traffic flow. Traffic flow data can be optained using the
   [TomTom API](https://developer.tomtom.com/traffic-api/documentation/traffic-flow/flow-segment-data), 
   the
   [Microsoft Traffic API](https://www.microsoft.com/en-us/maps/azure/data-insights/traffic)
   or the
   [Google Maps Traffic API](https://outscraper.com/google-maps-traffic-api/).
   All of these have free tiers for initial development, as well as paid tiers for
   business use.
   The TomTom API supplies current speed output directly mapped to EPSG:4326 projeced
   latitude/longitude points that this project currently uses. These could easily
   be applied to the existing code, offering route optimizing for current traffic
   conditions.
4. Based on historical data from the TomTom API this could similarly be implemented
   for other times of day in the future. Traffic flow prediction could be based
   on time of day as well as day of the week when provided by the user, using
   average or median data across past dates for the given time slot.
   Or if no time slot is provided, across all historical data.
5. Walking and biking directions often lack street names since walking paths are
   often not named. The experience might be improved by adding relative bearing
   changes when turning onto an unnamed road.
6. Currently routes between points far away from each other request too much map
   data for the API to respond in a timely manner. This could potentially be reduced
   by instead setting a max diameter for individual requests and requesting
   multiple map segments along the direct line betweeen starting point and destination.
7. Adding nodes to the street graph for exact  starting point and destination.
   Currently the route will start and end at the nearest nodes on the graph. If
   these are on an edge, at better solution would be to add in new nodes for these
   spots and replacing the edge with new ones from the new node to the nodes of
   the original edge.
8. Implement API server interface in place of the current CLI
9. Implement a front end for interacting with the API in (4)


### Productionizing

The implementation currently relies on public, free Nominatim API for OpenStreetMap
and this comes with many limitations. However, they let you serve your own copy
the API including all data. For production use, the first step would be to set
this up for production use.
The API server version implemented in "Next steps" point 4 as well as the Nominatim
API should be containerized allowing scaling through kubernetes clusters based
on traffic.
For the solution with the highest accuracy, I would recommend continued, paid
use of the third party API for traffic data. Historical data could be cached through
a local server to reduce third party requests. However, the cost of running this
caching layer could easily end up becoming higher than the cost of repeating third
party API requests. Additionally it would not work for real time data regardless.


## Local Installation

```sh
# Install as package
pip install .

# ...or install with visual support
pip install '.[map]'

# Install dev dependencies (for tests etc.)
pip install '.[dev]'

# Setup pre-commit hooks
pre-commit install
```

### API keys

Not all requests will need to interact with the OpenAI API but to support this
feature, an API key will need to be supplied via the `OPENAI_API_KEY` environment
variable:

```sh
export OPENAI_API_KEY='<YOUR_API_KEY_HERE>'
```

## Running the code

The entry point for running the code is the `run` command:

```
usage: run [-h] --start START --destination DESTINATION [--transport-mode {all_public,bike,drive,drive_service,walk}] [--num-suggestions NUM_SUGGESTIONS] [--show-map]

options:
  -h, --help            show this help message and exit
  --start START         Start address
  --destination DESTINATION
                        Where you want to go
  --transport-mode {bike,drive,walk}
                        Mode of transpotation
  --num-suggestions NUM_SUGGESTIONS
  --show-map            Visualize route on map
```

For example:

```sh
run \
    --start 'Madison Square Center' \
    --destination '1071 5th Ave, New York' \
    --transport-mode walk \
    --num-suggestions 1 \
    --show-map
```

For the `--show-map` argument to work, it is necessary to install the package
with visual support (see Installation above)


## Development

This code base uses `black`, `flake8`, and `isort` for code style, `mypy` for type
hint enforcement and `pytest` with code coverage to ensure all code is thorougly
tested. External API calls are mocked in tests.

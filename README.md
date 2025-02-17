# within

## Installation

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

## Running the code

The entry point for running the code is the `run` command:

```
usage: run [-h] --start START --destination DESTINATION [--transport-mode {all_public,bike,drive,drive_service,walk}] [--num-suggestions NUM_SUGGESTIONS] [--show-map]

options:
  -h, --help            show this help message and exit
  --start START         Start address
  --destination DESTINATION
                        Where you want to go
  --transport-mode {all_public,bike,drive,drive_service,walk}
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
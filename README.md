# GeoName Wrapper

## Overview

`geoname-wrapper` is a command-line scraper for
the [GeoNames advanced search](http://www.geonames.org/advanced-search.html). It filters results by continent, ISO
country code, and feature class, then exports the selected fields in JSON, CSV, or raw console output. The tool
paginates through GeoNames search results, normalizes column names to snake_case, and converts latitude/longitude values
from DMS to decimal degrees.

## Features

- Filter queries by continent, two-letter country code, and GeoNames feature class (cities, rivers, mountains, etc.).
- Choose the columns you want to keep; names are normalized automatically.
- Export results to JSON (`output.json`), CSV (`output.csv`), or inspect them directly in the terminal.
- Pagination continues until the requested limit is met or no additional pages are available.

## Requirements

- Python 3.12+
- Dependencies: `requests`, `beautifulsoup4`, `unidecode`
    - `unidecode` is already listed in `pyproject.toml`. Install the remaining dependencies when setting up the
      environment.

### Install with `uv`

```bash
# Create and activate a virtual environment
uv sync
```

## Usage

Run the CLI from the project root:

```bash
python main.py --help
```

```
Scrape and filter geographical data from http://www.geonames.org/, and save it in output file.

optional arguments:
   -h, --help            show this help message and exit
  -ct {EU,AF,AS,OC,NA,SA}, --continent {EU,AF,AS,OC,NA,SA}
                        Continent code. Default: ''
  -c COUNTRY, --country COUNTRY
                        ISO Code of your country (e.g: CM for Cameroon). Default: ''
  -f {country,stream_lake,parks_area,city,road_railroad,spot_building_farm,mountain_hill,undersea,forest_heath}, --feature-class {country,stream_lake,parks_area,city,road_railroad,spot_building_farm,mountain_hill,undersea,forest_heath}
                        Type of feature to search for. Default: city
  -s FIELDS [FIELDS ...], --fields FIELDS [FIELDS ...]
                        List of fields to include in the output (e.g, name, latitude)
  -t {csv,json,raw}, --output-format {csv,json,raw}
                        The output format. Default: json
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        The output file. Default: output.[format]
  -l LIMIT, --limit LIMIT
                        The number of items to retrieve
```

## Examples

Fetch the first 50 cities in Cameroon, keep name and coordinates, and save them to JSON:

```bash
python main.py -c CM -f city -s name latitude longitude -t json -l 50
```

List parks across Europe and print the full raw records to the terminal:

```bash
python main.py -ct EU -f parks_area -t raw
```

Create a CSV of mountains in South America with custom fields:

```bash
python main.py -ct SA -f mountain_hill -s name country latitude longitude feature_class -t csv
```

## Output Formats

- `json` (default): writes `output.json` with UTF-8 encoding.
- `csv`: writes `output.csv` and includes a header row.
- `raw`: prints the filtered records using `pprint`.

Files are created in the working directory unless you modify `utils.output_data` to pass a custom path.

## How It Works

- `main.py` handles the CLI arguments, sanitizes user-specified column names, and calls `utils.scrape_geonames`.
- `utils.scrape_geonames` builds the GeoNames URL, paginates through search results, parses the table with
  BeautifulSoup, and collects rows via `extract_table_data`.
- `utils.dms_to_gps_coordinates` converts DMS strings (e.g., `E 9° 56′ 25''`) into decimal floats.
- `enums.py` maps descriptive feature class names to GeoNames codes and provides continent shortcuts.
- `collect_cities.sh` is a bash script which allows you to collect cities of more than 200 countries in a json file.

## Troubleshooting

- GeoNames rate limits aggressive scraping; the script sleeps one second between requests, but HTTP errors can still
  occur. Retry later if needed.
- If GeoNames changes column names, adjust the `--fields` you request or update the scraper to accommodate the new
  layout.
- Ensure all dependencies listed above are installed in the active environment; missing libraries will cause import or
  runtime errors.

import re
import csv
import time
import json
import requests
from pprint import pprint
from unidecode import unidecode

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

from enums import FEATURE_CLASSES


def to_pythonic_string(s: str) -> str:
    """
        Converts a column header string into a clean, snake_case Pythonic variable name.
    """
    return "_".join(unidecode(s).split()).lower()


def extract_table_data(table_soup: BeautifulSoup, columns: List[str]) -> List[Dict[str, Any]]:
    """
        Extracts data rows from a given BeautifulSoup table element.
    """
    tr_tags = table_soup.find_all('tr')
    all_rows_data = []

    # Start from the row immediately after the header/title rows
    # The first row is the actual header
    # The last row is just a colspan
    # The data starts from the second row (index 1)

    # We will skip the first row, which is not city data rows
    for index, row in enumerate(tr_tags):
        # Skip the title and header rows (indices 0 and 1)
        if index == 0 or index == len(tr_tags) - 1:
            continue

        td_tags = row.find_all('td')

        # Ensure we have enough td tags to match our expected columns
        # There is an extra <td> for the item number link at the start. We can ignore it
        # We start counting column data from the second <td> tag (index 1 in td_tags).

        row_data = {}

        # to match the columns list which starts with 'Name'.
        for col_index, column_name in enumerate(columns):

            # The td tags list index starts at 0 for the first column (which is the index/map image),
            # while the columns list starts at 'Name' (which is the second data cell).
            td_index = col_index + 1

            # Shifting the table from 1 element to the right
            if td_index >= len(td_tags):
                break

            raw_text = td_tags[td_index].get_text(strip=True, separator='\n')

            # For 'Name' column only get the main name in the first line
            if to_pythonic_string(column_name) == 'name':
                final_text = raw_text.split('\n')[0].strip()
            elif to_pythonic_string(column_name) in ('latitude', 'longitude'):
                final_text = dms_to_gps_coordinates(raw_text)
            else:
                final_text = raw_text.strip()

            row_data[to_pythonic_string(column_name)] = final_text

        # Only append rows that actually contain extracted data
        if row_data:
            all_rows_data.append(row_data)

    return all_rows_data


def output_data(data: List[Dict[str, Any]], fields: List[str], fmt: str, output_file: str | None = None):
    """
        Prints or saves the extracted data in the expected format
    """

    # Filter data first
    filtered_data = []
    for record in data:
        new_record = {}

        for field in fields:
            if field in record:
                new_record[field] = record[field]

        if new_record:
            filtered_data.append(new_record)

    if not filtered_data:
        print('No data to output after filtering field')
        return

    # Handle the output format
    if fmt == 'raw':
        pprint(filtered_data)

    elif fmt == 'json':
        outfile = output_file or 'output.json'
        json_output = json.dumps(filtered_data, indent=4, ensure_ascii=False)
        with open(outfile, 'w') as json_file:
            json_file.write(json_output)

        print(f'Output written at: {outfile}')

    elif fmt == 'csv':
        outfile = output_file or 'output.csv'

        fieldnames = fields if fields else filtered_data[0].keys()

        with open(outfile, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_data)

        print(f'Output written at: {outfile}')


def scrape_geonames(
        country_code: Optional[str] = '',
        continent: Optional[str] = '', feature_class: Optional[str] = '',
        fields: List[str] = None,
        output_format: Optional[str] = 'json',
        output_file: Optional[str] = '',
        limit: Optional[int] = 100
):
    """
        Main scraping function
    """

    # 1. Build URL with filters
    base_url = 'http://www.geonames.org/advanced-search.html?'
    feature_code = FEATURE_CLASSES.get(feature_class, 'P')

    filters = f'country={country_code.upper()}&featureClass={feature_code}'
    if continent:
        filters += f'&continentCode={continent.upper()}'

    current_url = base_url + filters

    all_extracted_data = []
    page_count = 1

    columns: Optional[List[str]] = None

    while current_url and len(all_extracted_data) < limit:
        print(f"--- Fetching page {page_count} from: {current_url} ---")
        time.sleep(1)
        try:
            response = requests.get(current_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {current_url}: {e}")
            break

        html_doc = response.content.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html_doc, 'html.parser')

        # Find the table containing the results.
        # The first 'restable' is for search filters, the second is for results.
        res_tables = soup.find_all('table', class_='restable')

        if len(res_tables) < 2:
            print("No results table found on the page. Stopping pagination.")
            break

        data_table = res_tables[1]

        # 2. Extract Column Headers
        if columns is None:
            header_row = data_table.find('tr', recursive=False)

            # If header row is found, extract the column names
            if header_row and header_row.find('th'):
                columns = [col.get_text(strip=True) for col in header_row.find_all('th') if col.get_text(strip=True)]
            else:
                # Fallback to a hardcoded list or stop if the header isn't found
                print(
                    "Could not find table headers. Using default columns: ['Name', 'Country', 'Feature class', 'Latitude', 'Longitude']")
                columns = ['', 'Name', 'Country', 'Feature class', 'Latitude', 'Longitude']  # The first 'th' is empty
                columns = columns[
                    1:]  # We only care about the data columns, I let this like that to don't forget that first column.
        # 3. Extract Data from the Current Page
        current_page_data = extract_table_data(data_table, columns)
        all_extracted_data.extend(current_page_data)
        print(
            f"Extracted {len(current_page_data)} records from page {page_count}. Total records: {len(all_extracted_data)}")

        # 4. Find the 'next' link for pagination

        # In GeoNames, the "next" link is often at the bottom of the page in the main body.
        next_link = soup.find('a', string=re.compile(r'next', re.IGNORECASE), href=True)

        if next_link:
            # Construct the full URL for the next page
            next_path = next_link['href']
            # The URL structure is typically: advanced-search.html?country=CM&featureClass=P&startRow=xx

            # Check if the href is an absolute URL (starts with http)
            if next_path.startswith('http'):
                current_url = next_path
            else:
                # Reconstruct the URL for the next page based on the base URL and the new 'startRow' parameter
                # We know that the next only contains the path and the query params, but we ensure that even if it
                # changes later, we can still manage.

                # Safety check to prevent duplicating the base path if not necessary
                if next_path.startswith('?'):
                    current_url = base_url.split('?')[0] + next_path
                elif next_path.startswith('/'):
                    # If it starts with a slash, it's relative to the domain root
                    current_url = response.url.split('://')[0] + '://' + response.url.split('/')[2] + next_path
                else:
                    # If it's just parameters (like &start=21), replace the old query string
                    current_url = base_url.split('?')[0] + '?' + next_path

            page_count += 1
        else:
            # If no 'next' link is found, we're on the last page.
            print("Reached the last page (no 'next' link found). Stopping.")
            current_url = None  # Set current_url to None to break the while loop

    # 5. Output the final result
    print("\n" + "=" * 50)
    print(f"Finished. Extracted a total of {len(all_extracted_data[:limit])} records.")

    # Convert requested fields to pythonic format for filtering
    pythonic_fields = [to_pythonic_string(f) for f in fields]

    output_data(all_extracted_data[:limit], pythonic_fields, output_format, output_file)


def dms_to_gps_coordinates(dms_string: str) -> float:
    """
    Converts a DMS string (e.g., "E 9° 56′ 25''" or "W 10° 30' 00") to a float.

    The regex handles single quote ('), backtick (`), and prime/double prime (′/″) symbols.
    """
    match = re.match(
        r"([NSEW])\s*(\d+)[°\s]*(\d+)['`′\s]*(\d+)[\"″']*",  # Added '`' and prime symbols
        dms_string.strip(),
        re.IGNORECASE
    )

    if not match:
        raise ValueError(f"Invalid DMS format for input: '{dms_string}'. Expected format: 'D DD MM SS'")

    direction = match.group(1).upper()
    degrees = int(match.group(2))
    minutes = int(match.group(3))
    seconds = int(match.group(4))

    # Calculate the decimal value
    decimal_value = float(degrees) + (float(minutes) / 60) + (float(seconds) / 3600)

    # Apply sign convention: S and W are negative
    if direction in ('S', 'W'):
        return -decimal_value

    return decimal_value

#!/bin/bash

# --- Configuration ---

# 1. Define the Python script name (assuming it's in the current directory)
PYTHON_SCRIPT="geoname_wrapper/main.py"

# 2. Define the list of countries (ISO 2-letter codes) you want to scrape
# To add or remove countries, modify this list.
COUNTRIES=(
    "AD" "AE" "AF" "AG" "AI" "AL" "AM" "AN" "AO" "AQ"
    "AR" "AS" "AT" "AU" "AW" "AZ" "BA" "BB" "BD" "BE"
    "BF" "BG" "BH" "BI" "BJ" "BM" "BN" "BO" "BR" "BS"
    "BT" "BV" "BW" "BY" "BZ" "CA" "CC" "CD" "CF" "CG"
    "CH" "CI" "CK" "CL" "CM" "CN" "CO" "CR" "CU" "CV"
    "CX" "CY" "CZ" "DE" "DJ" "DK" "DM" "DO" "DZ" "EC"
    "EE" "EG" "EH" "ER" "ES" "ET" "FI" "FJ" "FK" "FM"
    "FO" "FR" "GA" "GB" "GD" "GE" "GF" "GG" "GH" "GI"
    "GL" "GM" "GN" "GP" "GQ" "GR" "GS" "GT" "GU" "GW"
    "GY" "GZ" "HK" "HM" "HN" "HR" "HT" "HU" "ID" "IE"
    "IL" "IM" "IN" "IO" "IQ" "IR" "IS" "IT" "JE" "JM"
    "JO" "JP" "KE" "KG" "KH" "KI" "KM" "KN" "KP" "KR"
    "KW" "KY" "KZ" "LA" "LB" "LC" "LI" "LK" "LR" "LS"
    "LT" "LU" "LV" "LY" "MA" "MC" "MD" "ME" "MG" "MH"
    "MK" "ML" "MM" "MN" "MO" "MP" "MQ" "MR" "MS" "MT"
    "MU" "MV" "MW" "MX" "MZ" "NA" "NC" "NE" "NF" "NG"
    "NI" "NL" "NO" "NP" "NR" "NU" "NZ" "OM" "PA" "PE"
    "PF" "PG" "PH" "PK" "PL" "PM" "PN" "PR" "PS" "PT"
    "PW" "PY" "QA" "RE" "RO" "RS" "RU" "RW" "SA" "SB"
    "SC" "SD" "SE" "SG" "SH" "SI" "SJ" "SK" "SL" "SM"
    "SN" "SO" "SR" "ST" "SV" "SY" "SZ" "TC" "TD" "TF"
    "TG" "TH" "TJ" "TK" "TL" "TM" "TN" "TO" "TR" "TT"
    "TV" "TW" "TZ" "UA" "UG" "UM" "US" "UY" "UZ" "VA"
    "VC" "VE" "VG" "VI" "VN" "VU" "WF" "WS" "XK" "YE"
    "YT" "ZA" "ZM" "ZW"
)

# 3. Define the output directory and ensure it exists
OUTPUT_DIR="scraped_data"
mkdir -p "$OUTPUT_DIR"

# 4. Define the scraping arguments
FEATURE_CLASS="city"
OUTPUT_FORMAT="json"
FIELDS="name latitude longitude"

# --- Execution Setup ---

# We assume the Python script writes to this fixed filename when -o json is used.
PYTHON_SCRAPER_OUTPUT_FILE="output.json"

echo "Starting GeoName City Scraper for ${#COUNTRIES[@]} countries..."
echo "Output directory: $OUTPUT_DIR"
echo "--------------------------------------------------"

FINAL_OUTPUT_FILE="${OUTPUT_DIR}/all_cities_consolidated.json"
TEMP_DIR=$(mktemp -d)

echo "Consolidating all results into: $FINAL_OUTPUT_FILE"
echo "--------------------------------------------------"

CONSOLIDATED_JSON="{"
FIRST_COUNTRY=true

# Loop through each country code in the list
for COUNTRY in "${COUNTRIES[@]}"; do

    TEMP_JSON_FILE="${TEMP_DIR}/${COUNTRY}_data.json"

    echo "Processing country: $COUNTRY"

    # --- UPDATED LOGIC ---
    # 1. Run the Python script WITHOUT redirecting stdout (as it writes to a file)
    python3 "$PYTHON_SCRIPT" \
        -c "$COUNTRY" \
        -f "$FEATURE_CLASS" \
        -t "$OUTPUT_FORMAT" \
        -s $FIELDS

    PYTHON_EXIT_CODE=$?
    # --- END UPDATED LOGIC ---

    # Check the exit status of the previous command
    if [ $PYTHON_EXIT_CODE -eq 0 ]; then

        # Check if the Python script created the expected output file
        if [ -f "$PYTHON_SCRAPER_OUTPUT_FILE" ]; then

            # Move the output file to the temporary location for consolidation
            mv "$PYTHON_SCRAPER_OUTPUT_FILE" "$TEMP_JSON_FILE"

            # Check if the file was created and has content (must be more than "[]" which is 2 chars)
            if [ -s "$TEMP_JSON_FILE" ] && [ "$(wc -c < "$TEMP_JSON_FILE" | tr -d ' ')" -gt 2 ]; then

                JSON_ARRAY_CONTENT=$(cat "$TEMP_JSON_FILE")

                if [ "$FIRST_COUNTRY" = false ]; then
                    CONSOLIDATED_JSON+=",
"
                fi

                CONSOLIDATED_JSON+="\"$COUNTRY\": ${JSON_ARRAY_CONTENT}"

                FIRST_COUNTRY=false

                echo "   [SUCCESS] Data collected."
            else
                echo "   [WARNING] Scraper ran successfully, but no data found for $COUNTRY (or file was empty after creation)."
            fi
        else
            echo "   [ERROR] Python script succeeded (exit code 0) but did not create the expected output file ($PYTHON_SCRAPER_OUTPUT_FILE)."
        fi
    else
        # This error message now usually follows the detailed Python error printout.
        echo "   [ERROR] The Python script failed for country $COUNTRY. See the traceback above for details."
    fi

    echo "---"

done

# Finalize the JSON structure with the closing brace
CONSOLIDATED_JSON+="
}"

# Write the final consolidated JSON string to the output file
echo "$CONSOLIDATED_JSON" > "$FINAL_OUTPUT_FILE"

# Clean up the temporary directory
rm -rf "$TEMP_DIR"

echo "Scraping complete. All data consolidated and saved in: '$FINAL_OUTPUT_FILE'."

#!/bin/bash

# === USER INPUT ===
YEAR=2025
# MONTH=02  # Month is no longer strictly needed for this download logic,
            # as we are downloading all .nc files from the YEAR's directory.
            # You can keep it if other parts of your workflow use it, or remove it.
# ===================

# Base URL for accessing TROPESS CH4 Summary data
# This URL points to the directory for the specified YEAR
BASE_URL="https://tropess.gesdisc.eosdis.nasa.gov/data/TROPESS_Summary/TRPSYL2CH4AIRSFS.1/${YEAR}"

# Output directory (flat)
OUTPUT_DIR="./1-data"
mkdir -p "$OUTPUT_DIR"

# Start total timer
TOTAL_START=$(date +%s)

echo "Starting download of all .nc files for ${YEAR} from ${BASE_URL}/ ..."

# The original loop for downloading specific files per day is replaced by this:
# This wget command will:
#   -r: recursively download
#   -np: not ascend to the parent directory
#   -nH: not create host-prefixed directories
#   -nd: not create directories; download all files to OUTPUT_DIR (flat structure)
#   -A "*.nc": accept only files ending with .nc
#   --continue: resume aborted downloads
#   The authentication options are kept as in your original script.
wget --continue --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies \
     --auth-no-challenge=on --netrc \
     -r -np -nH -nd -A "*.nc" \
     "${BASE_URL}/" -P "$OUTPUT_DIR"

# Check wget exit status (optional but good practice)
if [ $? -eq 0 ]; then
    echo "Download command completed successfully."
else
    echo "Download command failed with exit status $?. This might occur if the server doesn't support recursive listing as expected or if there are no .nc files."
    # You might want to add more detailed error handling or logging here
fi

TOTAL_END=$(date +%s)
ELAPSED=$((TOTAL_END - TOTAL_START))
echo "Download process completed in $ELAPSED seconds."

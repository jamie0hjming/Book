#!/bin/sh
# Run Doxygen from the project directory so relative INPUT paths resolve.
cd "$(dirname "$0")" || exit 1
doxygen Doxyfile 2>&1

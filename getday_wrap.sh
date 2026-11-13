#!/bin/bash
cd /usr/local/scripts/octopus-data || exit 1
source /usr/local/scripts/octopus-data/octopus.env
/home/james/.local/bin/uv run python /usr/local/scripts/octopus-data/getday.py $(date -d "Yesterday" "+%Y-%m-%d") > /usr/local/scripts/octopus-data/getday.log 2>&1

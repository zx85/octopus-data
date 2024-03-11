#!/bin/bash

source /usr/local/scripts/octopus-data/octopus.env
/usr/bin/python3 /usr/local/scripts/octopus-data/getday.py $(date -d "Yesterday" "+%Y-%m-%d") > /usr/local/scripts/octopus-data/getday.log 2>&1

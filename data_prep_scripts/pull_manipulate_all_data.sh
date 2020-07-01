#!/usr/bin/env bash

echo "Pulling JHU: "$(date)
python /Users/CharlesFederici/corona_python/data_prep_scripts/pull_manipulate_jhu.py
echo "Pulling testing: "$(date)
python /Users/CharlesFederici/corona_python/data_prep_scripts/pull_testing.py
echo "Uploading to mongo: "$(date)
python /Users/CharlesFederici/corona_python/data_prep_scripts/create_app_plots.py

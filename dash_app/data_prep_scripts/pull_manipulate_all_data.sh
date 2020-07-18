#!/usr/bin/env bash

#echo "Pulling JHU: "$(date)
python data_prep_scripts/pull_manipulate_jhu.py
#echo "Pulling testing: "$(date)
python data_prep_scripts/pull_testing.py
# echo "Uploading to mongo: "$(date)
python data_prep_scripts/create_app_plots.py

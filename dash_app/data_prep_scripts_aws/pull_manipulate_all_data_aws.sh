#!/usr/bin/env bash

export AWS_KEY=$1
export AWS_KEY_DYNAMO=$2

echo "Pulling JHU: "$(date)
python pull_manipulate_jhu_aws.py
echo "Pulling testing: "$(date)
python pull_testing_aws.py
echo "Uploading to mongo: "$(date)
python create_app_plots_aws.py

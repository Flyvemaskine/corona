#!/usr/bin/env python3

from dotenv import load_dotenv

import boto3
import os
import pandas as pd
import re

load_dotenv(os.path.join(os.getcwd(),"vars.env"))

AWS_KEY = os.getenv('AWS_KEY')
AWS_SECRET=os.getenv('AWS_SECRET')

def fix_date(date):
    date = str(date)
    return(date[0:4]+"-" + date[4:6] + "-" + date[6:8])

print("Pulling testing data")
testing_df = pd.read_csv("https://covidtracking.com/api/v1/states/daily.csv")
# tracking_df['date'] = pd.to_datetime(tracking_df['date'], format='%Y%m%d')
testing_df['date'] = testing_df['date'].apply(fix_date)
testing_df = testing_df[['date', 'state', 'positive',
                           'negative', 'positiveIncrease',
                           'negativeIncrease','dataQualityGrade']]

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_KEY,
                  aws_secret_access_key=AWS_SECRET,
                  region_name='us-east-2')

s3.put_object(Bucket="us-corona-tracking-data",
              Key="testing.csv",
              Body=testing_df.to_csv(index=False))


print("Upload Complete")

#!/usr/bin/env python3

import pandas as pd
from pymongo import MongoClient
import re

env_vars = open("/Users/CharlesFederici/corona_python/dash_app/vars.env", "r")
mongo_write = re.search(r'.*=(.*)\n',env_vars.readlines()[0])[1]
mongo_client_uri = "mongodb://crfederici:" + mongo_write + "@ds263248.mlab.com:63248/heroku_7ggf57x7?retryWrites=false"

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

tracking_df_dict = testing_df.to_dict(orient="records")

print("Uploading to Mongo")
client = MongoClient(mongo_client_uri)
db=client["heroku_7ggf57x7"]
testing_df_collection = db['testing_df']
testing_df_collection.drop()
testing_df_collection.insert_many(tracking_df_dict)

client.close()
print("Upload Complete")
# tracking_df[['date', 'state', 'positive',
#              'negative', 'positiveIncrease',
#              'negativeIncrease','dataQualityGrade']] \
#     .to_csv("/Users/CharlesFederici/corona_python/data/testing.csv")

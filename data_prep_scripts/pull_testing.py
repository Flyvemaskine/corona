#!/usr/bin/env python3

import pandas as pd


tracking_df = pd.read_csv("https://covidtracking.com/api/v1/states/daily.csv")
tracking_df['date'] = pd.to_datetime(tracking_df['date'], format='%Y%m%d')

tracking_df[['date', 'state', 'positive',
             'negative', 'positiveIncrease',
             'negativeIncrease','dataQualityGrade']] \
    .to_csv("/Users/CharlesFederici/corona_python/data/testing.csv")

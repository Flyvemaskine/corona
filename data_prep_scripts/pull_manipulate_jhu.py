#!/usr/bin/env python3

import pandas as pd
import datetime as dt
import seaborn as sns
import os
import subprocess
import matplotlib.pyplot as plt
import re
import numpy as np

state = pd.read_csv('/Users/CharlesFederici/corona_python/admin/states.csv')

# Step 1: Refresh Github
subprocess.Popen('git -C /Users/CharlesFederici/corona_python/data/COVID-19 pull', shell=True)


# Step 2: Read in case reports from Github
folder_location = '/Users/CharlesFederici/corona_python/data/COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/'

files_to_read = os.listdir(folder_location)
case_reports_a = []
case_reports_b = []
for file_to_read in files_to_read:
    # remove .md and .gitignore
    if re.match(r'.*.csv', file_to_read):
        df = pd.read_csv(folder_location + file_to_read)
        file_date = re.search(r"(.*)\.csv", file_to_read)
        df['report_date'] = pd.to_datetime(file_date.group(1))
        # reports before 3-21 have a different format
        if pd.to_datetime(file_date.group(1)) <= pd.to_datetime("2020-03-21"):
            case_reports_a.append(df)
        else:
            case_reports_b.append(df)
case_reports_a = pd.concat(case_reports_a, axis=0, ignore_index=True)
case_reports_b = pd.concat(case_reports_b, axis=0, ignore_index=True)

# Step 3: Bind Rows on two halves of data
case_reports_a=case_reports_a.rename(str.lower, axis='columns') \
                             .rename(columns={'province/state':'province_state',
                                              'country/region':'country_region'}) \
                             [['province_state', 'country_region', 'confirmed',
                               'deaths', 'recovered', 'report_date', 'latitude',
                               'longitude']]
case_reports_b=case_reports_b.rename(str.lower, axis='columns') \
                             .rename(columns={'lat':'latitude',
                                              'long_':'longitude'}) \
                             .groupby(['province_state','country_region','report_date'], as_index=False) \
                             .agg({'confirmed':'sum',
                                   'deaths':'sum',
                                   'recovered':'sum',
                                   'longitude':'mean',
                                   'latitude':'mean'}) \
                             [['province_state', 'country_region', 'confirmed',
                               'deaths', 'recovered', 'report_date', 'latitude',
                               'longitude']]
case_reports_joined = pd.concat([case_reports_a, case_reports_b], axis=0)

# Step 4: Create Incrementals
case_reports_prior_day = case_reports_joined.copy()
case_reports_prior_day['report_date'] = case_reports_prior_day['report_date'] + dt.timedelta(days=1)
case_reports_prior_day = case_reports_prior_day.rename({'confirmed':'confirmed_pd',
                                                        'deaths':'deaths_pd',
                                                        'recovered':'recovered_pd'}, axis="columns") \
                                               .drop(['latitude', 'longitude'], axis=1)
case_reports_joined = case_reports_joined.merge(case_reports_prior_day,
                                                left_on=['province_state','country_region','report_date'],
                                                right_on=['province_state','country_region','report_date'])
case_reports_joined['incremental_confirmed'] = case_reports_joined['confirmed'] - case_reports_joined['confirmed_pd']
case_reports_joined['incremental_deaths'] = case_reports_joined['deaths'] - case_reports_joined['deaths_pd']
case_reports_joined['incremental_recovered'] = case_reports_joined['recovered'] - case_reports_joined['recovered_pd']

def make_keep_col(df, province_col, country_col):
    df['keep'] = np.where(df[country_col] == 'US',
                          np.where(df[province_col].isin(state.State),
                                   1, 0),1)
    return(df)

case_reports_joined = make_keep_col(case_reports_joined, 'province_state', 'country_region')

#Step 5: Create country set
case_reports_country = case_reports_joined[case_reports_joined['keep'] == 1] \
                            .groupby(['country_region', 'report_date']) \
                            .agg({'confirmed':'sum',
                                  'deaths':'sum',
                                  'recovered':'sum',
                                  'incremental_confirmed':'sum',
                                  'incremental_deaths':'sum',
                                  'incremental_recovered':'sum'})

case_reports_states=case_reports_joined[(case_reports_joined['country_region']=='US') & (case_reports_joined['keep']==1)]

case_reports_country.to_csv('/Users/CharlesFederici/corona_python/data/by_country.csv')
case_reports_states.to_csv('/Users/CharlesFederici/corona_python/data/by_state.csv')

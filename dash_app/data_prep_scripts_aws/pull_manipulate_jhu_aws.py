#!/usr/bin/env python3

from dotenv import load_dotenv
import boto3
import datetime as dt
import numpy as np
import os
import pandas as pd
from pymongo import MongoClient
import re
import subprocess


load_dotenv(os.path.join(os.getcwd(),"vars.env"))

AWS_KEY = os.getenv('AWS_KEY')
AWS_SECRET=os.getenv('AWS_SECRET')

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_KEY,
                  aws_secret_access_key=AWS_SECRET,
                  region_name='us-east-2')

state = s3.get_object(Bucket="us-corona-tracking-data", Key="states.csv")
state = pd.read_csv(state['Body'])

def add_days_to_text(text_date, delta):
    return((pd.to_datetime(text_date) + dt.timedelta(days=delta)).strftime("%Y-%m-%d"))

def get_current_df():
    try:
        obj = s3.get_object(Bucket="us-corona-tracking-data", Key="jhu.csv")
        out = pd.read_csv(obj['Body'])
    except:
        out = pd.DataFrame()
    return(out)


def find_missing(current_df):
    def get_latest_date(date_diff = 1):
        return((dt.datetime.now() - dt.timedelta(hours=6, days=date_diff)).strftime("%Y-%m-%d"))
    def find_dates_in_df(current_df):
        if current_df.empty:
            out = []
        else:
            out = current_df['report_date'].unique().tolist()
        return (out)

    def create_date_range(start_date, end_date, date_format = "%Y-%m-%d"):
        """Takes string form dates, creates range by day"""
        start = dt.datetime.strptime(start_date, date_format).date()
        end = dt.datetime.strptime(end_date, date_format).date()

        out = [start]
        date_iter = start
        while True:
            date_iter = date_iter + dt.timedelta(days = 1)
            if date_iter > end:
                break
            out.append(date_iter)
        out = [date.strftime("%Y-%m-%d") for date in out]
        return(out)

    def find_missing_dates(is_this, in_this):
        return(list(set(in_this)-set(is_this)))
    latest_date_avail = get_latest_date(1)
    existing_dates = find_dates_in_df(current_df)

    overall_date_range = create_date_range("2020-01-23", latest_date_avail)

    missing_dates = find_missing_dates(existing_dates, overall_date_range)
    return(missing_dates)


def pull_missing(current_df, missing_dates):
    if not missing_dates:
        print("Missing date field is empty")
        return None
    def pull_day(date):
        print("Pulling " + date)
        date_for_github = date[5:7] + "-"+ date[8:10] + "-" + date[0:4]
        github_path = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/" + date_for_github + ".csv"
        return(pd.read_csv(github_path))

    def standardize_columns(df, date):
        df['report_date'] = pd.to_datetime(date)
        if pd.to_datetime(date) <= pd.to_datetime("2020-03-21"):
            df['latitude'] = 'NA'
            df['longitude'] = 'NA'
            df = df.rename(str.lower, axis='columns') \
                                 .rename(columns={'province/state':'province_state',
                                                  'country/region':'country_region'}) \
                                 [['province_state', 'country_region', 'confirmed',
                                   'deaths', 'recovered', 'report_date']]
        else:
            df['Province_State'] = df["Province_State"].fillna("NA")
            df = df.rename(str.lower, axis='columns') \
                                 .rename(columns={'lat':'latitude',
                                                  'long_':'longitude'}) \
                                 .groupby(['province_state','country_region','report_date'], as_index=False) \
                                 .agg({'confirmed':'sum',
                                       'deaths':'sum',
                                       'recovered':'sum'}) \
                                 [['province_state', 'country_region', 'confirmed',
                                   'deaths', 'recovered', 'report_date']]
        df = df.groupby(['province_state','country_region','report_date'], as_index=False) \
               .agg({'confirmed':'sum',
                     'deaths':'sum',
                     'recovered':'sum'})
        return(df)

    def basic_data_transforms(df):
        df["country_region"] = df["country_region"].str.replace(r'(.*)?(Korea)(.*)?', "South Korea")
        df["country_region"] = df["country_region"].str.replace(r'(.*)?(China)(.*)?', "China")
        df['keep'] = np.where(df['country_region'] == 'US',
                              np.where(df['province_state'].isin(state.State),
                                   1, 0),1)
        df = df.fillna(0)
        return(df)

    def add_incrementals(df, date):
        prior_day = add_days_to_text(date, -1)
        df_pd = pull_day(prior_day)
        df_pd = standardize_columns(df_pd, prior_day).drop(['report_date'], axis=1)
        df_pd = basic_data_transforms(df_pd).drop(['keep'], axis=1)
        df_pd = df_pd.rename({'confirmed':'confirmed_pd','deaths':'deaths_pd','recovered':'recovered_pd'}, axis="columns")

        df_joined = df.merge(df_pd, how='left', left_on=['province_state','country_region'], right_on=['province_state','country_region'])
        df_joined['incremental_confirmed'] = df_joined['confirmed'] - df_joined['confirmed_pd']
        df_joined['incremental_deaths'] = df_joined['deaths'] - df_joined['deaths_pd']
        df_joined['incremental_recovered'] = df_joined['recovered'] - df_joined['recovered_pd']
        return(df_joined)

    def pull_days(date_range):
        out = []
        for date in date_range:
            df = pull_day(date)
            df = standardize_columns(df, date)
            df = basic_data_transforms(df)
            df = add_incrementals(df, date)
            out.append(df)
        return(pd.concat(out, axis = 0))

    out = pull_days(missing_dates)
    if current_df.empty:
        out = out
    else:
        out = current_df.append(out)
    return(out)

def create_by_state(df):
    df=df[(df['country_region']=='US') & (df['keep']==1)]
    return(df)

def create_by_country(df):
    df = df.copy()[(df['keep'] == 1) | (df['province_state'] == "Recovered")] \
        .groupby(['country_region', 'report_date'], as_index=False) \
        .agg({'confirmed':'sum',
              'deaths':'sum',
              'recovered':'sum',
              'incremental_confirmed':'sum',
              'incremental_deaths':'sum',
              'incremental_recovered':'sum'})
    df['active'] = df['confirmed'] - df['deaths'] - df['recovered']
    df['incremental_active'] = df['incremental_confirmed'] - df['incremental_deaths'] - df['incremental_recovered']
    return(df)

def upload_to_aws(bucket, path, df_to_upload):
    if df_to_upload is None:
        print("Dataframe is empty")
        return None
    s3.put_object(Bucket=bucket,
              Key=(path+".csv"),
              Body=df_to_upload.to_csv(index=False))
    pass





current_df= get_current_df()
missing_dates = find_missing(current_df)
df_to_upload = pull_missing(current_df, missing_dates)
upload_to_aws("us-corona-tracking-data", 'jhu', df_to_upload)

by_state = create_by_state(df_to_upload)
by_country = create_by_country(df_to_upload)

upload_to_aws("us-corona-tracking-data", 'by_state_table', by_state)
upload_to_aws("us-corona-tracking-data", 'by_country_table', by_country)

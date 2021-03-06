#!/usr/bin/env python3

import boto3
import copy
from decimal import Decimal
from dotenv import load_dotenv
import json
from datetime import date, datetime
import numpy as np
import os
import pandas as pd
from pymongo import MongoClient
import re
import subprocess
from urllib.request import urlopen
import pickle

# AWS Admin #################################################################

load_dotenv(os.path.join(os.getcwd(),"vars.env"))

AWS_KEY=os.getenv('AWS_KEY')
AWS_SECRET=os.getenv('AWS_SECRET')


json_path = os.path.join(os.getcwd(),"example_master.json")
with open(json_path, "r") as read_file:
    example_json = json.load(read_file)

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_KEY,
                  aws_secret_access_key=AWS_SECRET,
                  region_name='us-east-2')

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


# Testing Prework #############################################################
obj = s3.get_object(Bucket="us-corona-tracking-data", Key="testing.csv")
testing = pd.read_csv(obj['Body'])
testing = testing[testing['date']>= "2020-03-10"]
states = s3.get_object(Bucket="us-corona-tracking-data", Key="states.csv")
states = pd.read_csv(states['Body']) \
            .rename({"State":'state_full'}, axis="columns")

## Add full state name, cleanup data grades, add test counts + positive rate
testing = testing.merge(states, how="left", left_on=['state'], right_on=["Abbreviation"])
testing['dataQualityGrade'] = testing['dataQualityGrade'].str.extract(r'([A-Z])')
testing['dataQualityGrade'] = testing['dataQualityGrade'].fillna('NA')


testing_cw = testing.groupby('date', as_index=False).sum()
testing_cw['state'] = "CW"
testing_cw['Abbreviation'] = "CW"
testing_cw['state_full'] = "Countrywide"
testing_cw['dataQualityGrade'] = "A"

testing = pd.concat([testing, testing_cw], axis=0)

testing['tests'] = testing['totalTestResults']
testing['positive_rate'] = testing['positive'] / testing['tests']
testing['incremental_tests'] = testing['totalTestResultsIncrease']
testing['incremental_positive_rate'] = testing['positiveIncrease'] / (testing['incremental_tests'])


data_quality_color_mapping = {'F':"#FFFAFD", 'NA':"#FFFAFD",'D': '#E7BFD3', 'C':'#CF85AA', 'B':'#B74B81', 'A':'#9F1158'}
testing['data_quality_grade_colors'] = testing['dataQualityGrade'].replace(data_quality_color_mapping)
testing['dataQualityGrade'] = testing[['dataQualityGrade', 'state']].apply(lambda x: "NA" if x.state == "CW" else x.dataQualityGrade, axis=1)


## Create hovers text

def create_hover_text_rate(date, positive_rate, data_quality_score, incremental):
    #  Date:2020-06-18 <br> Positive Rate: 5.1% <br> Data Quality: A
    date_tag = "Date: " + date
    if incremental:
        positive_tag = "Incremental Positive Rate: " + np.round_(positive_rate*100, 1).astype(str) + "%"
    else:
        positive_tag  = "Cumulative Positive Rate: " + np.round_(positive_rate*100, 1).astype(str) + "%"
    data_quality_tag = "Data Quality Grade: " + data_quality_score
    return(date_tag + "<br>" + positive_tag + "<br>" + data_quality_tag)


def create_hover_text_counts(date, counts, data_quality_score, incremental):
    #  Date:2020-06-18 <br> Incremental Test: 500 <br> Data Quality: A
    date_tag = "Date: " + date
    if incremental:
        tests_tag = "Incremental Tests: " + np.round((counts/1000), 3).astype(str) + " K"
    else:
        tests_tag  = "Cumulative Tests: " + np.round((counts/1000), 3).astype(str) + " K"
    data_quality_tag = "Data Quality Grade: " + data_quality_score
    return(date_tag + "<br>" + tests_tag + "<br>" + data_quality_tag)

testing["positive_rate_flag"] = create_hover_text_rate(testing["date"], testing["positive_rate"], testing['dataQualityGrade'], False)
testing["incremental_positive_rate_flag"] = create_hover_text_rate(testing["date"], testing["incremental_positive_rate"], testing['dataQualityGrade'], True)
testing["tests_flag"] = create_hover_text_counts(testing["date"], testing["tests"], testing['dataQualityGrade'], False)
testing["incremental_tests_flag"] = create_hover_text_counts(testing["date"], testing["incremental_tests"], testing['dataQualityGrade'], True)


def create_testing_rate_plot(df, example_json, state, incremental):
    if incremental == "incremental":
        rate_metric = "incremental_positive_rate"
        tests_metric = "incremental_tests"
        rate_flag = rate_metric + "_flag"
        tests_flag = tests_metric + "_flag"
    else:
        rate_metric = "positive_rate"
        tests_metric = "tests"
        rate_flag = rate_metric + "_flag"
        tests_flag = tests_metric + "_flag"

    df = df[df['state_full'] == state]
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)

    df[rate_metric] = np.where(df[rate_metric] >= 1, np.nan, df[rate_metric])

    out_json = copy.deepcopy(example_json["incremental_plots"]["testing_rate"])

    out_json['data'][0]["x"] = df["date"].tolist()
    out_json['data'][0]["y"] = df[tests_metric].apply(str).apply(Decimal).tolist()
    out_json['data'][0]["type"] = "bar"
    out_json['data'][0]["opacity"] = Decimal("0.5")
    out_json['data'][0]["name"] = "Tests"
    out_json['data'][0]["yaxis"] = "y2"
    out_json['data'][0]["showlegend"] = False
    out_json['data'][0]["marker"] = {}
    out_json['data'][0]["marker"]['color'] = df['data_quality_grade_colors'].tolist()
    out_json['data'][0]["hoverinfo"] = "text"
    out_json['data'][0]["hovertext"] = df[tests_flag].tolist()


    out_json['data'].append({})
    out_json['data'][1]['x'] = df["date"].tolist()
    out_json['data'][1]['y'] = df[rate_metric].apply(str).apply(Decimal).tolist()

    out_json['data'][1]["type"] = "scatter"
    out_json['data'][1]["mode"] = "markers+lines"
    out_json['data'][1]["name"] = "Positive Rate"
    out_json['data'][1]["yaxis"] = "y"
    out_json['data'][1]["showlegend"] = False
    out_json['data'][1]["marker"] = {}
    out_json['data'][1]["line"] = {}
    out_json['data'][1]["line"]['color'] = '#9F1158'
    out_json['data'][1]["marker"]['color'] = df['data_quality_grade_colors'].tolist()
    out_json['data'][1]["hoverinfo"] = "text"
    out_json['data'][1]["hovertext"] = df[rate_flag].tolist()

    out_json['layout']['yaxis']['title'] = "Positive Rate"
    out_json['layout']['yaxis2'] = {}
    out_json['layout']['yaxis2']['title'] = "Tests"
    out_json['layout']['yaxis2']['overlaying'] = "y"
    out_json['layout']['yaxis2']['side'] = "right"
    out_json['layout']['yaxis2']['rangemode'] = "nonnegative"

    return(out_json)


## Confirmed Cases/ Deaths prework ###########################################

obj = s3.get_object(Bucket="us-corona-tracking-data", Key="by_state_table.csv")
by_state = pd.read_csv(obj['Body'])
by_state = by_state[by_state['report_date'] >= "2020-03-10"]
by_state = by_state.drop(['country_region',
                          'recovered_pd', 'confirmed_pd', 'deaths_pd'], axis = 1) \
                    .sort_values(["province_state", 'report_date'])

by_state_cw = by_state.groupby('report_date', as_index=False).sum()
by_state_cw['province_state'] = "Countrywide"
by_state = pd.concat([by_state, by_state_cw], axis=0)



def create_plot_cases(df, example_json, state, confirmed_or_deaths, incremental):
    df = df[df['province_state'] == state]
    if confirmed_or_deaths == "deaths":
        out_json = copy.deepcopy(example_json["incremental_plots"]["deaths"])
        fill_color = "#11589F"
    else:
        out_json = copy.deepcopy(example_json["incremental_plots"]["confirmed"])
        fill_color = "#589F11"

    if incremental == "incremental":
        confirmed_or_deaths = incremental + "_" + confirmed_or_deaths

    df[confirmed_or_deaths] = df[confirmed_or_deaths].apply(str).apply(Decimal)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    out_json["data"][0]["x"] = df['report_date'].tolist()
    out_json["data"][0]["y"] = df[confirmed_or_deaths].tolist()
    out_json['data'][0]["marker"] = {}
    out_json['data'][0]["marker"]['color'] = fill_color
    return(out_json)


## Create Plots
state_list=by_state['province_state'].unique().tolist()

plots_for_dynamo = []
for state in state_list:
    out = {}
    confirmed_plot = create_plot_cases(by_state, example_json, state, "confirmed", "incremental")
    deaths_plot = create_plot_cases(by_state, example_json, state, "deaths", "incremental")
    testing_plot = create_testing_rate_plot(testing, example_json, state, "incremental")
    out["incremental_plots"] = {"confirmed": confirmed_plot,
                                "deaths": deaths_plot,
                                "testing": testing_plot}

    confirmed_plot = create_plot_cases(by_state, example_json, state, "confirmed", "cumulative")
    deaths_plot = create_plot_cases(by_state, example_json, state, "deaths", "cumulative")
    testing_plot = create_testing_rate_plot(testing, example_json, state, "cumulative")
    out["cumulative_plots"] = {"confirmed": confirmed_plot,
                                "deaths": deaths_plot,
                                "testing": testing_plot}
    out['state_name'] = state
    plots_for_dynamo.append(out)





##  AWS Stuff to create_plots
#Using the resource here because it's less picky about datatypes.
    #client forces you to specify datatypes for each element
#Delete old entries

# Add New Entries
for plot in plots_for_dynamo:
    state_name = plot['state_name']
    print("Adding plot to bar_plots bucket:" + state_name)
    s3.put_object(Bucket="us-corona-tracking-plots",
                  Key=state_name+"_barplot.pkl",
                  Body=pickle.dumps(plot))




### Create maps ###############################################################
testing['date']=pd.to_datetime(testing['date'])
by_state['report_date']=pd.to_datetime(by_state['report_date'])
state_table = by_state.merge(testing,
                             how="left",
                             left_on=["province_state", 'report_date'],
                             right_on=['state_full', 'date'])
date_filter = min([max(by_state['report_date']), max(testing['date'])])

cumulative_table = state_table[state_table['date'] == date_filter][['province_state', 'report_date','confirmed', 'deaths', 'positive_rate', 'dataQualityGrade', "Abbreviation"]]
cumulative_table['positive_rate'] = np.round_(cumulative_table['positive_rate']*100, 1)
cumulative_table = cumulative_table.rename({'province_state':'State', 'report_date':"Date", 'confirmed':'Cases', 'deaths':'Deaths', 'positive_rate':'%Positive', 'dataQualityGrade':'Testing-Data-Quality', 'Abbreviation':'id'},axis='columns')
cumulative_table['Incremental'] = "Cumulative"


incremental_table = state_table[state_table['date'] == date_filter][['province_state', 'report_date','incremental_confirmed', 'incremental_deaths', 'incremental_positive_rate', 'dataQualityGrade', 'Abbreviation']]
incremental_table['incremental_positive_rate'] = np.round_(incremental_table['incremental_positive_rate']*100, 1)
incremental_table = incremental_table.rename({'province_state':'State', 'report_date':"Date", 'incremental_confirmed':'Cases', 'incremental_deaths':'Deaths', 'incremental_positive_rate':'%Positive', 'dataQualityGrade':'Testing-Data-Quality', "Abbreviation":"id"},axis='columns')
incremental_table['Incremental'] = "Incremental"

df_for_s3 = cumulative_table.append(incremental_table)
df_for_s3 = df_for_s3[df_for_s3["id"]!="CW"]

s3.put_object(Bucket="us-corona-tracking-data",
              Key="df_for_maps.csv",
              Body=df_for_s3.to_csv(index=False))
print("uploading maps to s3")

#!/usr/bin/env python3

import copy
import json
import numpy as np
import os
import pandas as pd
from pymongo import MongoClient
import re
import subprocess

def select_star_mongo(mongo_database, collection):
    mongo_query_out = [doc for doc in mongo_database[collection].find({}, {'_id':0})]
    return (pd.DataFrame(mongo_query_out))


env_vars = open("/Users/CharlesFederici/corona_python/dash_app/vars.env", "r")
mongo_write = re.search(r'.*=(.*)\n',env_vars.readlines()[0])[1]
mongo_client_uri = "mongodb://crfederici:" + mongo_write + "@ds263248.mlab.com:63248/heroku_7ggf57x7?retryWrites=false"
client = MongoClient(mongo_client_uri)
db=client["heroku_7ggf57x7"]


# Testing Setup
testing = select_star_mongo(db, 'testing_df')
# testing = pd.read_csv("/Users/CharlesFederici/corona_python/data/testing.csv")
states = pd.read_csv("dash_app/states.csv").rename({"State":'state_full'}, axis="columns")

## Add full state name, cleanup data grades, add test counts + positive rate
testing = testing.merge(states, how="left", left_on=['state'], right_on=["Abbreviation"])
testing['dataQualityGrade'] = testing['dataQualityGrade'].str.extract(r'([A-Z])')
testing['dataQualityGrade'] = testing['dataQualityGrade'].fillna('NA')

testing['tests'] = testing['positive'] + testing['negative']
testing['positive_rate'] = testing['positive'] / testing['tests']
testing['incremental_tests'] = testing['positiveIncrease'] + testing['negativeIncrease']
testing['incremental_positive_rate'] = testing['positiveIncrease'] / (testing['positiveIncrease'] + testing['negativeIncrease'])


## Create mappings for colors for data quality
blue_color_mapping = {'F':"#eff3ff", 'NA':"#eff3ff", 'D': '#bdd7e7', 'C':'#6baed6', 'B':'#3182bd', 'A':'#08519c'}
green_color_mapping = {'F':"#edf8e9", 'NA':"#edf8e9",'D': '#bae4b3', 'C':'#74c476', 'B':'#31a354', 'A':'#006d2c'}
testing['positive_rate_color'] = testing['dataQualityGrade'].replace(blue_color_mapping)
testing['incremental_positive_rate_color'] = testing['dataQualityGrade'].replace(green_color_mapping)

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

## Create testing plots functions

def create_testing_rate_plot(df, example_json, state, incremental):
    df = df[df['state_full'] == state]
    out_json = copy.deepcopy(example_json["incremental_plots"]["testing_rate"])

    out_json['data'][0]['x'] = df["date"].tolist()
    out_json['data'][0]['y'] = df["positive_rate"].tolist()

    out_json['data'][0]["type"] = "scatter"
    out_json['data'][0]["mode"] = "markers+lines"
    # example_json["plot_contents"]['data'][0]["name"] = "Positive Rate"
    out_json['data'][0]["showlegend"] = False
    out_json['data'][0]["marker"] = {}
    out_json['data'][0]["line"] = {}
    out_json['data'][0]["line"]['color'] = '#bdd7e7'
    out_json['data'][0]["marker"]["color"] = df["positive_rate_color"].tolist()
    out_json['data'][0]["hoverinfo"] = "text"
    out_json['data'][0]["hovertext"] = df["positive_rate_flag"].tolist()

    out_json['data'].append({})
    out_json['data'][1]["x"] = df["date"].tolist()
    out_json['data'][1]["y"] = df["incremental_positive_rate"].tolist()
    out_json['data'][1]["type"] = "scatter"
    out_json['data'][1]["mode"] = "markers+lines"
    #out_json]['data'][1]["name"] = "Incremental Positive Rate"
    out_json['data'][1]["showlegend"] = False
    out_json['data'][1]["marker"] = {}
    out_json['data'][1]["line"] = {}
    out_json['data'][1]["line"]['color'] = '#bae4b3'
    out_json['data'][1]["marker"]["color"] = df["incremental_positive_rate_color"].tolist()
    out_json['data'][1]["hoverinfo"] = "text"
    out_json['data'][1]["hovertext"] = df["incremental_positive_rate_flag"].tolist()

    if incremental == "incremental":
        out_json['data'][0]["marker"]["size"] = 4
    else:
        out_json['data'][1]["marker"]["size"] = 4

    return(out_json)

def create_tests_administered_plot(df, example_json, state, incremental):
    df = df[df['state_full'] == state]
    if incremental == 'incremental':
        colors = df["incremental_positive_rate_color"].tolist()
        tests = df["incremental_tests"].tolist()
        flags = df["incremental_tests_flag"].tolist()
    else:
        colors = df["positive_rate_color"].tolist()
        tests = df["tests"].tolist()
        flags = df["tests_flag"].tolist()

    out_json = copy.deepcopy(example_json["incremental_plots"]["tests_administered"])

    out_json['data'][0]['x'] = df["date"].tolist()
    out_json['data'][0]['y'] = tests

    out_json['data'][0]["marker"] = {}
    out_json['data'][0]["marker"]['color'] = colors
    out_json['data'][0]["hoverinfo"] = "text"
    out_json['data'][0]["hovertext"] = flags

    return(out_json)


by_state = select_star_mongo(db, "by_state_table")
by_state = by_state.drop(['country_region',
                          'recovered_pd', 'confirmed_pd', 'deaths_pd'], axis = 1) \
                    .sort_values(["province_state", 'report_date'])


states = by_state.province_state.unique().tolist()


def create_plot_cases(df, example_json, state, confirmed_or_deaths, incremental):
    df = df[df['province_state'] == state]
    if confirmed_or_deaths == "deaths":
        out_json = copy.deepcopy(example_json["incremental_plots"]["deaths"])
    else:
        out_json = copy.deepcopy(example_json["incremental_plots"]["confirmed"])

    if incremental == "incremental":
        confirmed_or_deaths = incremental + "_" + confirmed_or_deaths

    out_json["data"][0]["x"] = df['report_date'].tolist()
    out_json["data"][0]["y"] = df[confirmed_or_deaths].tolist()
    out_json['data'][0]["marker"] = {}
    out_json['data'][0]["marker"]['color'] = '#494847'
    return(out_json)



with open("/Users/CharlesFederici/corona_python/example_master.json", "r") as read_file:
    example_json = json.load(read_file)

state_for_mongo = []

for state in states:
    state_json = copy.deepcopy(example_json)
    state_json["state_name"] = state

    for incremental in ['incremental', 'cumulative']:
        plot_type = incremental + "_plots"
        state_json[plot_type]['tests_administered'] = create_tests_administered_plot(testing, example_json, state, incremental)
        state_json[plot_type]['testing_rate'] =create_testing_rate_plot(testing, example_json, state, incremental)
        state_json[plot_type]['confirmed'] =create_plot_cases(by_state, example_json, state, "confirmed", incremental)
        state_json[plot_type]['deaths'] =create_plot_cases(by_state, example_json, state, "deaths", incremental)
    state_for_mongo.append(state_json)


# Country stuff

## Data prep
by_country = select_star_mongo(db, 'by_country_table')
by_country = by_country.sort_values(["country_region", 'report_date'])
def create_plot_cases_us(df, example_json, country, confirmed_or_deaths, incremental):
    df = df[df['country_region'] == country]

    out_json = copy.deepcopy(example_json["incremental_plots"]["deaths"])

    if incremental == "incremental":
        out_json["data"][0]["y"] = df["incremental_"+confirmed_or_deaths].tolist()
    else:
        out_json["data"][0]["y"] = df[confirmed_or_deaths].tolist()

    out_json["data"][0]["x"] = df['report_date'].tolist()

    out_json['data'][0]["marker"] = {}
    out_json['data'][0]["marker"]['color'] = '#494847'

    if confirmed_or_deaths == 'confirmed':
        out_json["layout"]['yaxis']['title'] = "Confirmed Cases"
    elif confirmed_or_deaths == 'deaths':
        out_json["layout"]['yaxis']['title'] = "Deaths"
    elif confirmed_or_deaths == 'recovered':
        out_json["layout"]['yaxis']['title'] = "Recovered"
    elif confirmed_or_deaths == 'active':
        out_json["layout"]['yaxis']['title'] = "Active Cases"

    return(out_json)

metrics = ['confirmed', 'deaths', 'recovered', 'active']
countries = by_country.country_region.unique().tolist()
country_for_mongo = []

for country in countries:
    incrementals = {metric:create_plot_cases_us(by_country, example_json, country, metric, "incremental") for metric in metrics}
    cumulatives = {metric:create_plot_cases_us(by_country, example_json, country, metric, "cumulative") for metric in metrics}
    country_plot = {'country_name':country,'incremental_plots':incrementals, 'cumulative_plots':cumulatives}
    country_for_mongo.append(country_plot)


# State Summary table for Mongo
testing['date']=pd.to_datetime(testing['date'])
state_table = by_state.merge(testing, how="left", left_on=["province_state", 'report_date'], right_on=['state_full', 'date'])
date_filter = min([max(by_state['report_date']), max(testing['date'])])

cumulative_table = state_table[state_table['date'] == date_filter][['province_state', 'report_date','confirmed', 'deaths', 'positive_rate', 'dataQualityGrade']]
cumulative_table['positive_rate'] = np.round_(cumulative_table['positive_rate']*100, 1)
cumulative_table = cumulative_table.rename({'province_state':'State', 'report_date':"Date", 'confirmed':'Cases', 'deaths':'Deaths', 'positive_rate':'%Positive', 'dataQualityGrade':'Testing-Data-Quality'},axis='columns')
cumulative_table['Incremental'] = "Cumulative"


incremental_table = state_table[state_table['date'] == date_filter][['province_state', 'report_date','incremental_confirmed', 'incremental_deaths', 'incremental_positive_rate', 'dataQualityGrade']]
incremental_table['incremental_positive_rate'] = np.round_(incremental_table['incremental_positive_rate']*100, 1)
incremental_table = incremental_table.rename({'province_state':'State', 'report_date':"Date", 'incremental_confirmed':'Cases', 'incremental_deaths':'Deaths', 'incremental_positive_rate':'%Positive', 'dataQualityGrade':'Testing-Data-Quality'},axis='columns')
incremental_table['Incremental'] = "Incremental"

state_table_for_mongo = cumulative_table.append(incremental_table).to_dict("records")



by_state_collection = db['by_state']
by_state_collection.drop()
by_state_collection.insert_many(state_for_mongo)

by_country_collection = db['by_country']
by_country_collection.drop()
by_country_collection.insert_many(country_for_mongo)

state_table_collection = db['state_table']
state_table_collection.drop()
state_table_collection.insert_many(state_table_for_mongo)

client.close()

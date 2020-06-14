import pandas as pd
import os
import subprocess

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
                             [['province_state', 'country_region', 'confirmed',
                               'deaths', 'recovered', 'report_date', 'latitude',
                               'longitude']]
case_reports_joined = pd.concat([case_reports_a, case_reports_b], axis=0)

FROM python:3.7.6
LABEL maintainer "Charlie Federici <crfederici@gmail.com>"

RUN mkdir data_prep_scripts_aws
WORKDIR data_prep_scripts_aws

COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY . .



ENTRYPOINT ["bash", "pull_manipulate_all_data_aws.sh"]

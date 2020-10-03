FROM python:3.7.6
LABEL maintainer "Charlie Federici <crfederici@gmail.com>"

RUN mkdir dash_app
WORKDIR dash_app

COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY . .

EXPOSE 8000

CMD ["gunicorn", "--workers=1", "--threads=1", "-b 0.0.0.0:8000", "index:server"]

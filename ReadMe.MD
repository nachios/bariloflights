# Bariloflights


## Introduction

This project consist on an specific situation I am/was in. I live in San Carlos de Bariloche, Rio Negro, Argentina, and I need to be at San Isidro, Buenos Aires, Argentina by the time of the Superbowl game in 2025 so I can organize an event I make every year. [More info](https://www.instagram.com/nachosuperbowl/)

In order to get there we need to track the flights available from Bariloche's airport to Aeroparque aiport in Ciudad de Buenos Aires so we buy the tickets in the cheaper flights possible. Our objective is to track the prices through time and not have the price information in the last snapshot, so we can forecast when it's the best day to make the purchase.

## Getting started

To get started, you will need to have installed and running Docker Desktop for the Airflow `docker-compose.yaml` and the build with the `Dockerfile`, and Poetry for dependecy management with the `pyproyect.toml`.

To start you have to run the following bash commands in your terminal:
```bash
  git clone https://github.com/nachios/bariloflights.git
  echo -e "AIRFLOW_UID=$(id -u)" > .env
  docker compose up airflow-init
```

For more information, it can be found in the [Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#initializing-environment)

When it finished the first docker command you can run the following to bring the rest of the containers.
```bash
docker compose down
docker compose up -d
```

These commands will build and start all docker containers needed for this project.

The next step would be logging in the Airflow webserver and set the connection and variables credentials that can be found in [the environment variables section](#environment-variables). This is crucial to the application operation.

## Environment Variables

All environment variables used in this project, except one, are set directly in the Airflow UI/Webserver. The API credentials are created as Variables and the Redshift credentials are inserted as a Connection. 

The `AIRFLOW_UID` is the only set outside of the Airflow UI/Webserver.

In this project you will have to work with RapidAPI and CurrencyAPI which can be obtained free with certain limits on their platforms ([More information in the API documentation section](#api-documentation)). These two are our sources of information and our destination is a AWS Redshift database.

You can find below all the environment variables that should exist in this project.

- `RAPIDAPI_KEY`
- `RAPIDAPI_HOST`
- `RAPIDAPI_BASE_URL`
- `REDSHIFT_USER`
- `REDSHIFT_PASSWORD`
- `REDSHIFT_HOST`
- `REDSHIFT_PORT`
- `REDSHIFT_DB`
- `CURRENCYAPI_TOKEN`
- `AIRFLOW_UID`

## Database Model

It's important to refer to the database model necessary to run this project in the AWS Redshift. 

The model consists of a star schema with two fact tables called `flights_daily_snapshots` and `usd_daily_exchange_rate`, a scd table called `flights` and two dimension tables which `airlines` and `airports`. 

Our main fact table is the `flights_daily_snapshots` which has the information obtained from the API for each day and it's complemented by the other fact table `usd_daily_exchange_rate` to help get the prices in the local currency (ARS) instead of the one obtained by the API (USD). 

The `flights` table contains for each flight basic information like origin, destination, departure date and the airline and if the flight is active or not. This last data is defined when the flight code in that departure date doesn't exist in the last snapshot, so we can check which flight codes on that date are still available or not.

The two dimension tables `airlines` and `airports` which have the information from the airport and airlines codes that are available in the fact table.

## About the Airflow DAGs

There are 3 DAGs configured in this project, which have in total 5 tasks. 

Getting into more details of the DAGs, there are 4 tasks which are PythonOperators and the last 1 is a TriggerDagRunOperator. All scheduled DAGs have `catchup=False` because we get the information that it's available at a certain moment and we can't past information.

The first is the `bariloflights_dag` which is the more complex of the three (which has 3 tasks) and it's the only DAG that has a _schedule_interval_ with a cron expression which is `0 22 * * *` (this means that runs at 19hs UTC-3). It starts creating the request to the RapidAPI endpoint to get the flights information from certain dates and routes and saves the information in a parquet file. After that the second task reads the parquet file and apply certain transformations needed with pandas and inserts this new information in the `flights_daily_snapshots` table. The last task is the TriggerDagRunOperator which triggers the next DAG (this only executes when the previous tasks run with a success status). 

The second is the `distinct_bariloflights_dag` which was triggered by the first DAG, and consisted of the first task which gets the distinct values of the flight on each day and inserts the information into the `flights` table.

The last is the `get_exchange_rate_dag` which only makes the request to the CurrencyAPI for the USDvsARS exchange rate and loads the information into the `usd_daily_exchange_rate`. This is triggered by the scheduler at `5 0 * * *` (21.05hs UTC-3). It's later because the API brings the exchange rate value of the previous day in UTC.

In conclusion, these DAGs are executed automatically, whenever the service is up and it applies all their conditions (like the _schedule_interval_)

## Testing

We have two unit tests in this project. Both tests are essential to check if the python scripts are making the core tasks of transformation or actions needed in this project.

The first one is the `test_transform_booking_flights`. This checks if the values are transformed correctly into the correct values (after their transformations) and their data types. It's very important because later this function makes the insert into the database and we are trying to avoid an issue in the insertion because of wrong data types.

The second is the `test_distinct_flights`. This one focus on a particular action that is done by the original script which is to check if the flight codes that are recorded into the table, are active or not, that we have defined [in the Database Model section](database-model).

## Github Actions

The repository has two specific github actions that are executed after each push and pull request.

The first one is solely for linting all the project python files in order to have a more readable code and maintaing the best practices.

The second consists of two unit tests which check that the transformation scripts are executing correctly it's function in the pipeline process.

## Metabase

In the docker compose a Metabase service is created as well. This Metabase has a Dashboard containing different KPIs and visualizations to track easily the information that is obtained with the project. Like how many flights have been tracked, filtered by the province of origin, the airline, and much more that can help us decide when it's a good moment to make the purchase.

To access the metabase instance you have to provide the following credentials:
- Mail: ``
- Pass: ``

## API Documentation
To get more information about the APIs used in this project, you can look out more information here:
- [Currency API](https://currencyapi.com/docs/latest)
- [Rapid API - Booking](https://rapidapi.com/ntd119/api/booking-com18/playground/apiendpoint_25a38c11-6fe2-4d0f-83cb-9cb905e4ba29)

## Tools

These are the principal tools that have been used in this project.

![](https://img.shields.io/badge/amazon-redshift-8C4FFF?logo=amazonredshift&logoColor=white)

![](https://img.shields.io/badge/apache-airflow-017CEE?logo=apacheairflow)

![](https://img.shields.io/badge/python-3776AB?logo=python&logoColor=ffd343)

![](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)

![](https://img.shields.io/badge/poetry-60A5FA?logo=poetry&logoColor=blue)

![](https://img.shields.io/badge/rapidapi-0055DA?logo=rapid)

![](https://img.shields.io/badge/booking-white?logo=data:image/png;base64,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)

![](https://img.shields.io/badge/currencyapi-2563eb?logo=data:image/png;base64,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)
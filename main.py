import argparse
import datetime
import time

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', '-host', type=str, help='PostgreSQL host',
                        default='rc1a-hlu228zf6yj3p5ao.mdb.yandexcloud.net')
    parser.add_argument('--port', '-p', type=str, help='PostgreSQL port', default='6432')
    parser.add_argument('--dbname', '-d', type=str, help='PostgreSQL dbname', default='TestDB')
    parser.add_argument('--user', '-u', type=str, help='PostgreSQL user', default='Anastasia')
    parser.add_argument('--password', '-pw', type=str, help='PostgreSQL password', default='')
    parser.add_argument('--target_session_attrs', '-t', type=str, help='PostgreSQL target_session_attrs',
                        default='read-write')
    parser.add_argument('--sslmode', '-s', type=str, help='PostgreSQL sslmode', default='verify-full')
    parser.add_argument('--table_name', '-table_name', type=str, help='PostgreSQL table_name', default='final')
    parser.add_argument('--numeric_categories', '-n', type=bool, help='PostgreSQL numerate categories', default=False)
    parser.add_argument('--path_to_data', '-path', type=str, help='PostgreSQL path_to_data', default='final.csv')
    args = parser.parse_args()

    columns_categories = ["TERRITORY_CODE", "TERRITORY_NAME", "TRIP_TYPE", "DATE_OF_ARRIVAL",
                          "VISIT_TYPE", "HOME_COUNTRY", "HOME_REGION", "HOME_CITY", "GOAL", "GENDER", "AGE", "INCOME"]
    columns_digits = ["DAYS_CNT", "VISITORS_CNT", "SPENT"]
    time_to_int = lambda date: time.mktime(datetime.datetime.strptime(date, "%Y-%m-%d").timetuple())

    data = pd.read_csv("final.csv")

    # заполняем пропущенные данные: для категориальных - исп. моду, а для числовых - среднее:

    for column in columns_categories:
        data[column] = data[column].replace(column, np.nan)
        data_without_nans = data[column].dropna()
        mode_value = data_without_nans.mode().values[0]
        data[column] = data[column].fillna(mode_value).astype(str)

    for column in columns_digits:
        data[column] = pd.to_numeric(data[column].replace(column, np.nan))
        data_without_nans = data[column].dropna()
        mean_value = data_without_nans.mean()
        data[column] = data[column].fillna(mean_value)

    # округляем значения для числовых признаков, кроме SPENT:

    for column in columns_digits[:-1]:
        data[column] = data[column].apply(np.round).astype(int)

    # удаляем выбросы:

    data['SPENT_PER_PERSON'] = data['SPENT'] / data['DAYS_CNT']
    mean, std = data['SPENT_PER_PERSON'].mean(), data['SPENT_PER_PERSON'].std()
    data = data[(data['SPENT_PER_PERSON'] >= mean - 2 * std) & (data['SPENT_PER_PERSON'] <= mean + 2 * std)]

    # заменяем категории на идентификаторы:

    if args.numeric_categories:
        for column in columns_categories:
            categories = data[column].unique()
            data[column].replace(categories, range(len(categories)), inplace=True)

        # преобразуем время прибытия в числовой показатель:

        data.DATE_OF_ARRIVAL = data.DATE_OF_ARRIVAL.replace('DATE_OF_ARRIVAL', np.nan)
        data.DATE_OF_ARRIVAL = data.DATE_OF_ARRIVAL.apply(
            lambda date: time_to_int(date) if date is not np.nan else np.nan)

    engine = create_engine(f'postgresql://{args.user}:{args.password}@{args.host}:{args.port}/{args.dbname}',
                           echo=False)
    data.to_sql(args.table_name, con=engine, if_exists='append', index=False)

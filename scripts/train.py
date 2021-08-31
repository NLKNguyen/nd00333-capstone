import typer  # CLI argument handling
from typing import Optional
from common import CommonOptions, CommonFormats, Format
from get_data import get_data, GetDataOptions  # , date_format, time_format

from datetime import datetime
import glob
import re


class TrainOptions(object):
    TargetOption = typer.Option("close")


"""
 if call from CLI, train model to save to pickle file
 if cache exist, e.g. AAPL.day.100.2021-08-27.0400.model.pkl, load and return
 if not, train and save

 if use train function only, if df is provided then use it, otherwise, call get data
"""


def train(df, target,
          symbol, period, ticks,          
          use_cache, refresh_cache, timestamp,
          verbose):
    # make a time series from a data column to forecast, along with a required 'time' column
    if verbose:
        print('*' * 80)
        print(
            f" Train forecasting model on '{target}' column of the input data")
        print('*' * 80)

    result = None

    if use_cache and not refresh_cache:
        result = (1, 2, 3)
        glob_pattern = Format.cacheModelFileGlobPattern(
            symbol, period, ticks, target)
        cached_files = glob.glob(glob_pattern, recursive=False)

        # sort by name in reverse which means the file with latest time stamp comes first
        cached_files.sort(reverse=True)
        print(cached_files)

        for file_name in cached_files:
            # extract the date and time in the file name to compare
            regex_pattern = Format.cacheModelFileRegexPattern(
                symbol, period, ticks, target)
            match = re.match(regex_pattern, file_name)
            print(file_name, regex_pattern)

            groups = match.groups()
            if len(groups) == 1:
                cached_timestamp = groups[0]
                cached_datetime = datetime.strptime(
                    cached_timestamp, CommonFormats.TimestampFormat)
                print(cached_timestamp, cached_datetime)
            #     cached_date_str = groups[0]
            #     cached_time_str = groups[1]
            #     cached_date = datetime.strptime(
            #         cached_date_str, CommonFormats.DateFormat).date()  # only use date section
            #     cached_time = datetime.strptime(
            #         cached_time_str, CommonFormats.TimeFormat).time()  # only use time section

        pass

    if result is None:
        if verbose:
            print('> prepare environment...')

        import numpy as np
        import pandas as pd  # data frames
        import joblib  # to dump objects to files

        from kats.consts import TimeSeriesData
        from kats.models.prophet import ProphetModel, ProphetParams

        print(
            f"> create time series data based on 'time' and '{target}' columns")
        ts = TimeSeriesData(df[['time', target]])

        # create a model param instance
        # additive mode gives worse results
        params = ProphetParams(seasonality_mode='multiplicative')

        if verbose:
            print('> begin training...')
        # create a prophet model instance
        model = ProphetModel(ts, params)
        if verbose:
            print('> training is complete')

        metrics = dict()

        result = (model, metrics, timestamp)

        if use_cache:
            cached_label = Format.cacheLabel(symbol, period, ticks)
            cached_file = Format.cacheModelFileName(
                cached_label, timestamp, target)
            # cached_file = f"{Format.cacheLabel(symbol, period, ticks)}.{timestamp}.pkl"
            if verbose:
                print(f"> save cached model file", cached_file)

            joblib.dump(result, cached_file)

    if verbose:
        # print("> cached file:", result[1][0])
        print("> timestamp:", result[2])
        # print("> preview data")
        # print(result[0].head())
        print('*' * 80)
        print()
        print()

    return result


def main(
    target: Optional[str] = TrainOptions.TargetOption,

    symbol: Optional[str] = CommonOptions.SymbolOption,
    period: Optional[str] = CommonOptions.PeriodOption,
    ticks: Optional[int] = CommonOptions.TicksOption,

    use_cache: Optional[bool] = CommonOptions.UseCache,
    refresh_cache: Optional[bool] = CommonOptions.RefreshCache,
    minimum_cache_timestamp: Optional[datetime] = CommonOptions.MinimumCacheTimestamp,

    api_endpoint: Optional[str] = GetDataOptions.ApiEndpoint,
    api_key_id: Optional[str] = GetDataOptions.ApiKeyId,
    api_secret_key: Optional[str] = GetDataOptions.ApiSecretKey,

    # accept_cache_date: Optional[datetime] = GetDataOptions.AcceptCacheDate,
    # accept_cache_time: Optional[datetime] = GetDataOptions.AcceptCacheTime,

    verbose: Optional[bool] = CommonOptions.Verbose
):
    (df, timestamp) = get_data(symbol, period, ticks,
                               use_cache, refresh_cache, minimum_cache_timestamp,
                               #    accept_cache_date, accept_cache_time,
                               api_endpoint, api_key_id, api_secret_key,
                               verbose)

    return train(df, target,
                 symbol, period, ticks,
                 use_cache, refresh_cache, timestamp,
                 verbose)


if __name__ == "__main__":
    typer.run(main)

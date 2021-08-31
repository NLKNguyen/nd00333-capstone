import typer
import alpaca_trade_api as alpaca
from datetime import datetime
from typing import Optional
import glob
import re
import pandas as pd
from common import CommonOptions, CommonFormats, Format


class GetDataOptions(object):
    """
        get_data CLI options and their default value.
        These can be shared to other programs that want to replicate the CLI option to forward
        to the get_data function call.
    """
    # SymbolOption = typer.Option("AAPL")
    # PeriodOption = typer.Option("day")
    # TicksOption = typer.Option(100)

    ApiEndpoint = typer.Option(
        "https://paper-api.alpaca.markets", envvar="ALPACA_API_ENDPOINT")
    ApiKeyId = typer.Option(
        "PK5R9YDUGWGEBR9K0G5W", envvar="ALPACA_API_KEY_ID")
    ApiSecretKey = typer.Option(
        "9wI2LFDsGvfpuSouXY6a05XglcDJcUcZQy2i2zr1", envvar="ALPACA_API_SECRET_KEY")

    AcceptCacheDate = typer.Option(
        datetime.today().strftime(CommonFormats.DateFormat), formats=[CommonFormats.DateFormat])
    AcceptCacheTime = typer.Option(
        "0000", formats=[CommonFormats.TimeFormat])
    # Verbose = typer.Option(True)


# today = datetime.today()
# today_date = today.strftime(CommonFormats.DateFormat)
# today_start_time = "0000"
# today_start_time = today.strftime(CommonFormats.TimeFormat)


def get_data(
    symbol: str = None,
    period: str = None,
    ticks: int = None,

    use_cache: bool = None,
    refresh_cache: bool = None,
    minimum_cache_timestamp: datetime = None,
    # accept_cache_date: datetime = None,
    # accept_cache_time: datetime = None,

    api_endpoint: str = None,
    api_key_id: str = None,
    api_secret_key: str = None,

    verbose: bool = None
):

    # accept_cache_date = accept_cache_date.date()  # only use date section
    # accept_cache_time = accept_cache_time.time()  # only use time section

    if verbose:
        print('*' * 80)
        print(
            f" Get historical data of '{symbol}' symbol in '{period}' period for {ticks} ticks")
        print('*' * 80)
        # typer.echo(
        #     f"{symbol} {period} {api_endpoint} {api_key_id} {api_secret_key} {accept_cache_date} {accept_cache_time}")

    result = None
    latest_cached_file = None
    timestamp = None

    if use_cache and not refresh_cache:  # find if a valid cache exist to load, unless need to refresh cache
        # use naming convention to find cached files for the requested data

        glob_pattern = Format.cacheDataFileGlobPattern(symbol, period, ticks)
        cached_files = glob.glob(glob_pattern, recursive=False)

        # sort by name in reverse which means the file with latest time stamp comes first
        cached_files.sort(reverse=True)

        for file_name in cached_files:
            # extract the date and time in the file name to compare
            regex_pattern = Format.cacheDataFileRegexPattern(
                symbol, period, ticks)
            match = re.match(regex_pattern, file_name)
            # print(file_name, regex_pattern)

            groups = match.groups()
            if len(groups) == 1:
                cached_timestamp = groups[0]
                cached_datetime = datetime.strptime(
                    cached_timestamp, CommonFormats.TimestampFormat)

                # cached_date_str = groups[0]
                # cached_time_str = groups[1]
                # cached_date = datetime.strptime(
                #     cached_date_str, CommonFormats.DateFormat).date()  # only use date section
                # cached_time = datetime.strptime(
                #     cached_time_str, CommonFormats.TimeFormat).time()  # only use time section

                # print(file_name, cached_date, cached_time)
                # if cached_date > accept_cache_date or (cached_date == accept_cache_date and cached_time >= accept_cache_time):
                if cached_datetime >= minimum_cache_timestamp:
                    cached_file = file_name
                    timestamp = minimum_cache_timestamp.strftime(
                        CommonFormats.TimestampFormat)
                    # timestamp = Format.cacheTimestamp(
                    #     cached_date_str, cached_time_str)

                    if verbose:
                        print('> load cached data file', cached_file)

                    ohlcv = pd.read_csv(cached_file)
                    ohlcv.index = pd.DatetimeIndex(ohlcv['time'])

                    result = (ohlcv, timestamp)
                    break
                elif latest_cached_file is None:
                    # track this to check again after downloading in case there is no new data since this cache
                    latest_cached_file = file_name

    if result is None:  # cache is not used; need to download
        if verbose:
            print('> request data from Alpaca API')

        api = alpaca.REST(api_key_id, api_secret_key, api_endpoint)
        ohlcv = api.get_barset(symbol, period, limit=ticks).df[symbol]

        # extract time index to 'time' column without timezone (just use local time) because some
        # libraries used later either expect 'time' column or can't handle timezome
        ohlcv.insert(0, 'time', ohlcv.index.tz_convert(None).to_pydatetime())

        last_time = ohlcv['time'].iloc[-1]
        timestamp = last_time.strftime(CommonFormats.TimestampFormat)

        if use_cache:
            cached_label = Format.cacheLabel(symbol, period, ticks)
            cached_file = Format.cacheDataFileName(cached_label, timestamp)

            # cached_file = f"{Format.cacheLabel(symbol, period, ticks)}.{timestamp}.history.csv"

            # if the supposed file name is identical to the latest cached file, it means no new data since then.
            # so, better use a new file name with the provided accept_cache_date and accept_cache_time because
            # that will prevent future requests that don't provide any new data. This usually happens in weekends.
            if cached_file == latest_cached_file:                
                # only apply to accept_cache_date/time that is in the past. We can't assume no changes in future.
                # if accept_cache_date < now.date() or (accept_cache_date == now.date() and accept_cache_time < now.time()):
                if minimum_cache_timestamp <= datetime.now():
                    # new_cache_date = accept_cache_date.strftime(
                    #     CommonFormats.DateFormat)
                    # new_cache_time = accept_cache_time.strftime(
                    #     CommonFormats.TimeFormat)

                    timestamp = minimum_cache_timestamp.strftime(
                        CommonFormats.TimestampFormat)
                    # timestamp = Format.cacheTimestamp(
                    #     new_cache_date, new_cache_time)
                    cached_file = Format.cacheDataFileName(
                        cached_label, timestamp)

            if verbose:
                print('> save cached data file', cached_file)
            ohlcv.to_csv(cached_file, index=False)

        result = (ohlcv, timestamp)

    if verbose:
        # print("> cached file:", result[1][0])

        print("> preview head")
        print(result[0].head())
        print()
        print("> preview tail")
        print(result[0].tail())
        # last_rows = result[0].tail()
        # print(last_rows.to_string(header=False))
        # last_rows.index.name = '...'
        # print(last_rows.rename(columns={col: "" for col in last_rows}))
        print()
        print("> timestamp:", result[1])
        print('*' * 80)
        print()
        print()

    return result


def main(
    symbol: Optional[str] = CommonOptions.SymbolOption,
    period: Optional[str] = CommonOptions.PeriodOption,
    ticks: Optional[int] = CommonOptions.TicksOption,

    use_cache: Optional[bool] = CommonOptions.UseCache,
    refresh_cache: Optional[bool] = CommonOptions.RefreshCache,
    minimum_cache_timestamp: Optional[datetime] = CommonOptions.MinimumCacheTimestamp,

    # accept_cache_date: Optional[datetime] = GetDataOptions.AcceptCacheDate,
    # accept_cache_time: Optional[datetime] = GetDataOptions.AcceptCacheTime,

    api_endpoint: Optional[str] = GetDataOptions.ApiEndpoint,
    api_key_id: Optional[str] = GetDataOptions.ApiKeyId,
    api_secret_key: Optional[str] = GetDataOptions.ApiSecretKey,

    verbose: Optional[bool] = CommonOptions.Verbose,
):
    get_data(symbol, period, ticks,
             use_cache, refresh_cache, minimum_cache_timestamp,
            #  accept_cache_date, accept_cache_time,
             api_endpoint, api_key_id, api_secret_key,
             verbose)


if __name__ == "__main__":
    typer.run(main)

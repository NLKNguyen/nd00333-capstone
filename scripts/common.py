import typer
from datetime import datetime
import re


class CommonFormats(object):
    """
        string formats that are often used
    """
    DateFormat = "%Y-%m-%d"
    TimeFormat = "%H%M"
    TimestampFormat = f"{DateFormat}.{TimeFormat}"


class CommonOptions(object):
    """
        common CLI options and their default value.
        These can be reused among the programs.
    """
    SymbolOption = typer.Option("AAPL")
    PeriodOption = typer.Option("day")
    TicksOption = typer.Option(100)
    UseCache = typer.Option(True)
    RefreshCache = typer.Option(False)
    MinimumCacheTimestamp = typer.Option(datetime.today().strftime(CommonFormats.TimestampFormat),
                                         formats=[CommonFormats.TimestampFormat])
    Verbose = typer.Option(True)


class Format(object):
    @staticmethod
    def cacheLabel(symbol, period, ticks, sep='.'):
        return f"{symbol}{sep}{period}{sep}{ticks}"

    @staticmethod
    def cacheTimestamp(date_str, time_str, sep='.'):
        return f"{date_str}{sep}{time_str}"

    @staticmethod
    def cacheDataFileName(label, timestamp):
        timestamp_str = timestamp.strftime(CommonFormats.TimestampFormat)
        return f"{label}.{timestamp_str}.history.csv"

    @staticmethod
    def cacheDataFileGlobPattern(symbol, period, ticks) -> str:
        return f"{Format.cacheLabel(symbol, period, ticks)}.*.*.history.csv"

    # @staticmethod
    # def cacheDataFileRegexPattern(symbol, period, ticks) -> str:
    #     return '{label}\\.([^\\.]+\\.[^\\.]+)\\.history\\.csv'.format(
    #         label=Format.cacheLabel(symbol, period, ticks, sep='\\.'))

    @staticmethod
    def extractDataFileTimestamp(symbol, period, ticks, file_name) -> datetime:
        # regex_pattern = Format.cacheDataFileRegexPattern(symbol, period, ticks)
        regex_pattern = '{label}\\.([^\\.]+\\.[^\\.]+)\\.history\\.csv'.format(
            label=Format.cacheLabel(symbol, period, ticks, sep='\\.'))
        match = re.match(regex_pattern, file_name)
        groups = match.groups()
        if len(groups) == 1:
            return datetime.strptime(groups[0], CommonFormats.TimestampFormat)
        return None

    @staticmethod
    def cacheModelFileName(label, timestamp, target):
        timestamp_str = timestamp.strftime(CommonFormats.TimestampFormat)
        return f"{label}.{timestamp_str}.model.{target}.pkl"

    @staticmethod
    def cacheModelFileGlobPattern(symbol, period, ticks, target):
        return f"{Format.cacheLabel(symbol, period, ticks)}.*.*.model.{target}.pkl"

    # @staticmethod
    # def cacheModelFileRegexPattern(symbol, period, ticks, target):
    #     return '{label}\\.([^\\.]+\\.[^\\.]+)\\.model\\.{target}\\.pkl'.format(
    #         label=Format.cacheLabel(symbol, period, ticks, sep='\\.'),
    #         target=target)

    @staticmethod
    def extractModelFileTimestamp(symbol, period, ticks, target, file_name) -> datetime:
        # regex_pattern = Format.cacheDataFileRegexPattern(symbol, period, ticks)
        regex_pattern = '{label}\\.([^\\.]+\\.[^\\.]+)\\.model\\.{target}\\.pkl'.format(
                        label=Format.cacheLabel(
                            symbol, period, ticks, sep='\\.'),
                        target=target)
        match = re.match(regex_pattern, file_name)
        groups = match.groups()
        if len(groups) == 1:
            return datetime.strptime(groups[0], CommonFormats.TimestampFormat)
        return None

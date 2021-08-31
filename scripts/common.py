import typer
from datetime import datetime


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
        return f"{label}.{timestamp}.history.csv"

    @staticmethod
    def cacheDataFileGlobPattern(symbol, period, ticks):
        return f"{Format.cacheLabel(symbol, period, ticks)}.*.*.history.csv"

    @staticmethod
    def cacheDataFileRegexPattern(symbol, period, ticks):
        return '{label}\\.([^\\.]+\\.[^\\.]+)\\.history\\.csv'.format(
            label=Format.cacheLabel(symbol, period, ticks, sep='\\.'))

    @staticmethod
    def cacheModelFileName(label, timestamp, target):
        return f"{label}.{timestamp}.model.{target}.pkl"

    @staticmethod
    def cacheModelFileGlobPattern(symbol, period, ticks, target):
        return f"{Format.cacheLabel(symbol, period, ticks)}.*.*.model.{target}.pkl"

    @staticmethod
    def cacheModelFileRegexPattern(symbol, period, ticks, target):
        return '{label}\\.([^\\.]+\\.[^\\.]+)\\.model\\.{target}\\.pkl'.format(
            label=Format.cacheLabel(symbol, period, ticks, sep='\\.'),
            target=target)

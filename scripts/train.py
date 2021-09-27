from typing import Optional
import typer  # CLI argument handling
import joblib
import pandas as pd
import numpy as np
import os

from kats.consts import TimeSeriesData
from kats.models.prophet import ProphetModel, ProphetParams
from kats.utils.backtesters import BackTesterRollingWindow

from azureml.core.workspace import Workspace
from azureml.core import Run, Dataset


run = Run.get_context()
ws = run.experiment.workspace
dataset_name = 'ETHBTC'
dataset = Dataset.get_by_name(workspace=ws, name=dataset_name)

df = dataset.to_pandas_dataframe()

# test local file
# file = 'ETHBTC.daily.10000.2021-09-08.0000.history.csv'
# df = pd.read_csv(file)


def get_data(df):
    # only do univariate forecasting on closing price
    close_df = df[['time', 'close']]
    # close_df.index = pd.DatetimeIndex(close_df['time'])

    train_data = close_df.iloc[:-50]
    test_data = close_df.iloc[-50:]
    
    return (train_data, test_data)


train_data, test_data = get_data(df)


def main(
    changepoint_prior_scale: Optional[float] = None,
    seasonality_prior_scale: Optional[float] = None
):

    print('*' * 80)
    print(f"(train.py) Train forecasting model")
    print('*' * 80)

    print(f"> create time series data from data frame")

    ts = TimeSeriesData(train_data)

    hyperparameters = dict()
    hyperparameters['seasonality_mode'] = 'multiplicative'

    if changepoint_prior_scale is not None:
        hyperparameters['changepoint_prior_scale'] = changepoint_prior_scale

    if seasonality_prior_scale is not None:
        hyperparameters['seasonality_prior_scale'] = seasonality_prior_scale

    params = ProphetParams(**hyperparameters)

    print('> begin training...')

    # create a prophet model instance
    model = ProphetModel(ts, params)

    # fit the model with training data
    model.fit()

    print('> training is complete')

    os.makedirs('outputs', exist_ok=True)
    model_file = './outputs/hyperdrive_model.pkl'

    print(f"> save cached model file {model_file}")

    joblib.dump(model, model_file)

    print('> prepare for validation')

    # map some allowed error method to the equivalence names in Azure ML
    error_method_labels = dict(
        mape='mean_absolute_percentage_error',
        mae='mean_absolute_error',
        rmse='root_mean_squared_error'       
    )

    backtester = BackTesterRollingWindow(
        error_methods=list(error_method_labels.keys()),
        data=ts,
        params=params,
        train_percentage=75,
        test_percentage=25,
        sliding_steps=3,
        model_class=ProphetModel)

    print('> validate...')

    backtester.run_backtest()

    print("> metrics:")
    for method, value in backtester.errors.items():
        method_label = error_method_labels[method]
        print(method_label, '=', value)
        run.log(method_label, float(value))    

    # calculate normalized_root_mean_squared_error based on the RMSE result
    # nrmse_label = 'normalized_root_mean_squared_error'
    # nrmse_value = backtester.errors['rmse'] / (train_data['close'].max() - train_data['close'].min())
    # print(nrmse_label, '=', nrmse_value)
    # run.log(nrmse_label, float(nrmse_value))

    print()
    print('*' * 80)


if __name__ == "__main__":
    typer.run(main)

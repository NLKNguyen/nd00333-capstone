Crypto Forecasting With Azure ML
================================

This is a capstone project for Udacity Nanodegree: Azure Machine Learning Engineer. It demonstrates the usage of Azure ML platform to forecast the price of a crypto pair, Ethereum/Bitcoin as an example dataset. 

We will examine 2 approaches: using HyperDrive to tune a manually prepared model training, and using AutoML to automate the entire process. Then, we will pick the best model and deploy as a web service to do real time forecasting.

**Table of Contents**

- [Workflow](#workflow)
    - [0. Project set up and installation](#0-project-set-up-and-installation)
    - [1. Choose a dataset](#1-choose-a-dataset)
    - [2. Import dataset into the workspace](#2-import-dataset-into-the-workspace)
    - [3. Train model using HyperDrive](#3-train-model-using-hyperdrive)
    - [4. Train model using AutoML](#4-train-model-using-automl)
    - [5. Compare model performance](#5-compare-model-performance)
    - [6. Deploy best model](#6-deploy-best-model)
    - [7. Test model endpoint](#7-test-model-endpoint)
- [Clean Up Resources](#clean-up-resources)
- [Screen Recording](#screen-recording)
- [Future Improvements](#future-improvements)


# Workflow

Here is the workflow overview of the project.

![](img/2021-09-26-15-15-17.png)

Section outline:

- [0. Project set up and installation](#0-project-set-up-and-installation)
- [1. Choose a dataset](#1-choose-a-dataset)
- [2. Import dataset into the workspace](#2-import-dataset-into-the-workspace)
- [3. Train model using HyperDrive](#3-train-model-using-hyperdrive)
- [4. Train model using AutoML](#4-train-model-using-automl)
- [5. Compare model performance](#5-compare-model-performance)
- [6. Deploy best model](#6-deploy-best-model)
- [7. Test model endpoint](#7-test-model-endpoint)

## 0. Project set up and installation

Below is instructions to set up Azure ML environment to host the Jupyter Notebooks in this repository
### 0.1. Login to Azure in the CLI and install ML extension
```powershell
az login

# Azure ML CLI v1
# az extension add -n azure-cli-ml

# To use v2 instead, remove the old ones
# az extension remove -n azure-cli-ml
# az extension remove -n ml

# Add Azure ML CLI v2
az extension add -n ml

az version
# {
#   "azure-cli": "2.27.0",
#   "azure-cli-core": "2.27.0",
#   "azure-cli-telemetry": "1.0.6",
#   "extensions": {
#     "ml": "2.0.1a5"
#   }
# }
```

### 0.2. Create Azure ML Workspace
```powershell
# create resource group
az group create -l westus -n Nanodegree

# set default current working resource group and workspace to avoid retyping
az configure --defaults group="Nanodegree" workspace="Capstone"

az ml workspace create
```

![](/img/2021-09-10-00-20-23.png)


### 0.3. Create service principal account to add to the workspace
```powershell
az ad sp create-for-rbac --sdk-auth --name ml-auth

# get object Id of the service principal programmatically (using jq tool)
$clientId = az ad sp create-for-rbac --sdk-auth --name ml-auth | jq .clientId 
$objectId = az ad sp show --id $clientId | jq .objectId
```

![](img/2021-09-10-00-29-51.png)


### 0.4. Share workspace to the new service principal account

```powershell
az ml workspace share --user $objectId --role owner
```
![](img/2021-09-10-00-29-18.png)


### 0.5. Create Compute Instance for Jupyter Notebook

```powershell
az ml compute create --name capstone-notebook --size Standard_D2s_v3 --type ComputeInstance
```

![](img/2021-09-15-17-27-13.png)

![](img/2021-09-15-17-25-48.png)

<!-- #### 0.6. Create Azure ML Compute cluster

```powershell
az ml compute create --name capstone-cluster --size Standard_D2s_v3 --min-instances 0 --max-instances 3 --type AmlCompute
```

![](img/2021-09-26-21-48-10.png) -->


# 1. Choose a dataset

### Overview

I use historical price data of ETHBTC (Ethereum/Bitcoin) crypto pair in daily period for over 3 years. The data is downloaded from Binance.us, and it is uploaded to my Azure ML workspace to register as a Dataset.

It is a time series dataset that includes a time column, OHLC columns, and volume column.

* time: the daily time period
* open: the opening price of a period
* high: the highest price in a period
* low: the lowest price in a period
* close: the closing price of a period 
* volume: the buy/sell amounts of the market in a period

### Task

My goal is to forecast the future price of ETHBTC. Since this is a time series data, the `time` column is a required feature. For the purpose of this project, I will only target the `close` price to forecast. In other words, this is a univariate analysis where the other value features are not considered in the model.

### Access

The data is uploaded as a Dataset in Azure ML Studio, and it can be accessed by name using Python SDK. A copy of the time series data is stored as a CSV file in this project repository.

# 2. Import dataset into the workspace
![](img/2021-09-11-14-56-48.png)

![](img/2021-09-11-14-58-44.png)


Preview access in Jupyter Notebook

![](img/2021-09-26-20-03-34.png)


# 3. Train model using HyperDrive

Full notebook: [hyperparameter_tuning.ipynb](hyperparameter_tuning.ipynb)


I use Facebook Prophet model to forecast the close price. Two hyperparameters are used for tuning with HyperDrive, each is a discrete option in a random set of 5:

+ `--changepoint-prior-scale` that dictates the flexibility of the automatic changepoint selection. Large values will allow many changepoints, small values will allow few changepoints.
+ `--seasonality-prior-scale` that dictates the strength of the seasonality model. Larger values allow the model to fit larger seasonal fluctuations, smaller values dampen the seasonality.

The termination policy is Bandit Policy that is based on slack factor/slack amount and evaluation interval. The general purpose is to avoid burning the computation resource on the training processes that are unlikely to yield better result. 


The performance metric is Root Mean Squared Error, which means the lower the better; therefore, the primary metric goal is set to `MINIMIZE`.

The custom train environment that has all necessary dependencies is configured through the provided Dockerfile.


#### Configure and submit a HyperDrive experiment

![](img/2021-09-26-16-11-05.png)

#### Show run details

![](img/2021-09-23-20-05-25.png)

![](img/2021-09-22-20-00-53.png)

![](img/2021-09-22-20-02-14.png)

#### Best model

![](img/2021-09-22-20-04-45.png)


#### Common performance metric


RMSE: 0.013

We use root mean squared error as a performance metric to compare this HyperDrive model with the AutoML model below.


# 4. Train Model Using AutoML

Full notebook: [automl.ipynb](automl.ipynb)

We use the same train data that has only time and close price column to build the forecasting model. Here we configure a forecasting task for Azure AutoML and submit the experiment.

In the ForecastingParameters, we set the time column name the same as the `time` column in our train data. Because the training data is in daily period, we set the frequency as daily, `freq='D'`. Finally, we set the forecast horizon as `20` days in the future that we plan to train the model for. In practice, we don't need nor want a very long forecast into the future price because it will not be accurate in a highly volatile financial system such as cryptos. As soon as we have new price data, we should train again.

The supplied train data only contains `time` column and a target column `close` price in order to only do univariate forecasting.

Regarding the evaluation metric, we pick the default for AutoML forecasting task which is `normalized_root_mean_squared_error`, but afterward we can extract `root_mean_squared_error` that is part of the available metrics of the trained model because we need to compare with the HyperDrive model on the same metric.

The rest of the configurations for the AutoML is not domain specific and can be changed as will. That only gives room for the experiment.

#### Configure and submit an AutoML experiment
![](img/2021-09-26-15-27-51.png)


#### Show run details
![](img/2021-09-23-21-20-18.png)

#### Best model

The best model is trained with a Decision Tree regression algorithm and having the data standardized by a Robust Scaler, which is based on percentiles and are therefore not influenced by a few number of very large marginal outliers. 

![](img/2021-09-27-20-24-17.png)

<!-- ![](img/2021-09-23-21-30-02.png) -->

The hyperparameters are as follows:

**Robust Scaler** data transformation

```json
{
    "class_name": "RobustScaler",
    "module": "sklearn.preprocessing",
    "param_args": [],
    "param_kwargs": {
        "quantile_range": [
            10,
            90
        ],
        "with_centering": false,
        "with_scaling": false
    },
    "prepared_kwargs": {},
    "spec_class": "preproc"
}
```

**Decision Tree** training algorithm

```json
{
    "class_name": "DecisionTreeRegressor",
    "module": "sklearn.tree",
    "param_args": [],
    "param_kwargs": {
        "criterion": "mse",
        "max_features": null,
        "min_samples_leaf": 0.006781961770526707,
        "min_samples_split": 0.0008991789964660114,
        "splitter": "best"
    },
    "prepared_kwargs": {},
    "spec_class": "sklearn"
}
```

<!-- And the configuration settings of the experiment

![](img/2021-09-27-20-28-25.png) -->

#### All available performance metrics

![](img/2021-09-23-21-30-12.png)

These information can also be extracted programmatically.

![](img/2021-09-23-21-22-19.png)

#### Common performance metric


RMSE: 0.003
# 5. Compare model performance

Based on the RMSE metrics, the AutoML model (RMSE=0.003) appears to have 3 times lower error than the HyperDrive model (RMSE=0.01). This is just a rough comparison because the exact comparison is hard to conduct due to differences on how AutoML evaluates and how the HyperDrive train script evaluates. However, with a factor of 3, that probably covers the margin of error in the comparison method and gives confidence in the AutoML model; therefore, we will choose the AutoML model as best model to deploy.

# 6. Deploy Best Model

Here we go through the steps to register the model and configure the inference enpoint to deploy as a web service on Azure Container Instance.

### Register the model

![](img/2021-09-25-14-27-06.png)


### Prepare scoring script 

A sample scoring script can be downloaded from the model outputs directory

![](img/2021-09-25-14-36-19.png)

### Configure inference endpoint 

Use the same environment as the model and entry script as the downloaded scoring script

![](img/2021-09-25-14-27-34.png)

#### Deploy to Azure Container Instance

![](img/2021-09-26-15-04-48.png)

### View active web service endpoint 

![](img/2021-09-25-14-21-40.png)

![](img/2021-09-25-14-25-01.png)

# 7. Test Model Endpoint

Since this is a univariate forecasting on the `close` price, the only input needed is the `time` value, and the time should be in the future of the train dataset (2021-09-08) and up to 20 days in the horizon. In other words, any day from 2021-09-09 to 2021-09-28 will be valid. Usually, the nearer in the future, the higher the confidence.

Example data format of the JSON request body:

```json
"data":
[
    {
        "time": "2021-09-10T00:00:00.000Z",
    }
],
```

Example response, in which the forecasted close price is in the value of `forecast` property:

```json
{
    "forecast": [
        0.0648978
    ],
    "index": [
        {
            "time": 1631232000000,
            "_automl_dummy_grain_col": "_automl_dummy_grain_col"
        }
    ]
}
```

#### Test live web service using UI
![](img/2021-09-25-14-38-38.png)

#### Test live web service using local test script
![](img/2021-09-25-14-37-49.png)


# Clean Up Resources
### Delete web services

![](img/2021-09-27-12-35-09.png)

No more web service endpoint is available after the deletion.

![](img/2021-09-27-12-37-22.png)
### Delete compute resources

![](img/2021-09-27-12-36-37.png)


No more cluster is available after the deletion.

![](img/2021-09-27-12-39-22.png)

# Screen Recording

[Screencast video](https://youtu.be/1sywHzjvwxc) demonstrating the live model deployed as a web service to handle forecast request.

# Future Improvements

+ Apply multivariate forecasting using multiple available features such open, high, low, and volume instead of just only close price. This will surely improve the prediction quality. Furthermore, we can combine other time series data such as other cryptos, stock index data, and inflation data, as they might affect the price movement of the target crypto. An algorithm I have in mind is Vector Autoregression if I write a local training script, and for AutoML I simply not exclude the other features because the AutoML forecasting task will apply multivariate by default. 

+ Increasing experiment timeout and number of cross validation for AutoML can also help find better performance model.

+ For a real financial forecasting platform, it's necessary to have a frequent retrain whenever new price data is available, so we can set up a pipeline that automatically downloads new price data and trigger a retrain.
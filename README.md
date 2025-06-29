# PV Prediction

This repository contains the code for an energy production prediction of a photovoltaic system.

## Setup

### Install Python

If not already installed, install Python. The recommended way is to use [pyenv](https://github.com/pyenv/pyenv), which allows multiple parallel Python installations which can be automatically selected per project you're working on.

```shell
# Install Python if necessary
pyenv install 3.12
pyenv local 3.12
```

### Install Poetry

If not already installed, get Poetry according to <https://python-poetry.org/docs/#installation>.
If your are new to Poetry, you may find <https://python-poetry.org/docs/basic-usage/> interesting.

### Setup Environment

```shell
# Create venv and install all dependencies
poetry env use 3.12
poetry install

# add pre-commit hooks
poetry run pre-commit install

# load the environment variables (see section Environment Variables below)
source env.sh
```

## Usage

### Locally

```shell
# extracting fronius data
poetry run extract-fronius-data

```

The following environment variables may be used to configure `pv_prediction`:

| Environment Variable | Purpose | Default Value | Allowed Values |
|----------------------|-|-|-|
| LOG_LEVEL            | Sets the default log level [here](src/pr_prediction/common/logging.py). | "INFO" | See [Python Standard Library API-Reference](https://docs.python.org/3/library/logging.html#logging-levels) |
| FRONIUS_IP | IP Adress of Fronius converter | "" | - |
| METEO_USERNAME | Username for the meteomatics API | "" | Sign up for a free account [here](https://www.meteomatics.com/en/sign-up-weather-api-free-basic-account/) |
| METEO_PASSWORD | Password for the meteomatics API | "" | Sign up for a free account [here](https://www.meteomatics.com/en/sign-up-weather-api-free-basic-account/) |


#### Credentials

Create a file called env.sh. Place exports for all the environment variables inside of it, e.g.:
```shell
export FRONIUS_IP=SOME_IP
export METEO_USERNAME=SOME_USERNAME
export METEO_PASSWORD=SOME_PASSWORD
```
Then, execute the bash file via the CLI as follows:
```shell
source env.sh
```


## Test suite

Run all the tests locally:
```
poetry run python -m unittest
```

Run only unit tests locally:
```
poetry run python -m unittest -k pv_prediction
```

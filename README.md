# Property Price API

A Web API for simple data visualizations.


## Installation

#### Prerequisites
    - Python 3.7 or higher
    - GNU Make

#### Cloning
Clone the repo to your local machine:
```sh
git clone https://github.com/halecakir/price-paid-api
```
#### Installating
Building the docker-environment is as simple running make from the directory to which you cloned the repo.
```sh
make all
```
In the above make command, `all` target does the following commands in order:

    - Creates venv virtual environment.
    - Intalls python packages listed in requirements.txt.
    - Fetches Price Paid Data from land registry site.
    - Starts docker containers using docker-compose tool.
    - Makes database migrations
    - Populates database.

#### Uninstallating
Below command removes downloaded data, shutdown docker containers, and removes database volume.
```sh
make clean
```

#### Testing
Run all the unit tests.
```sh
make test
```

## Usage
This rest API has two endpoints:

    - /api/v1/properties/avg_prices -> Average property price over time
    - /api/v1/properties/count_transactions -> Number of transactions over time

All the details are documented in OpenAPI Specification. This rest API exposes below 3 endpoints for this purpose.

    -   /api/schema/swagger-ui  -> A JSON view of your API specification 
    -   /api/schema/redoc -> A swagger-ui view of your API specification
    -   /api/schema -> A ReDoc view of your API specification

#### Simple Colab Client
I provide a simple python client to visualize the data consumed from REST API.

     https://colab.research.google.com/drive/1TZKlXp0LENZlDezAdrCWBOFHIayAnieQ?usp=sharing



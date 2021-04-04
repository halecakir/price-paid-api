# -*- coding: utf-8 -*-
#
# Copyright 2021 Huseyin Alecakir <huseyinalecakir@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SHELL = /bin/bash

#######################################################
# load all config variables as env variables
include config/.env.dev
export

# check whether the correct python version is available
ifeq (, $(shell which python3 ))
	$(error "python3 not found in $(PATH)")
endif

VENV := "venv/bin/activate"
PRICE_PAID_FILE := "price_paid.csv"

venv/bin/activate: requirements.txt
	@echo -e "\e[0;32mINFO     Creating virtual environment and installing requirements...\e[0m"
	test -d venv || python3 -m venv venv
	. $(VENV) && pip3 install -Ur requirements.txt
	@touch venv/bin/activate

data:
	@echo -e "\e[0;32mINFO     Creating data folder...\e[0m"
	@mkdir data

data/price_paid.csv: data
	@echo -e "\e[0;32mINFO     Fetching price paid data...\e[0m"
	@wget -O "./data/$(PRICE_PAID_FILE)" $(PP_DATA)
	@touch data/price_paid.csv

.PHONY: up
up:
	@echo -e "\e[0;32mINFO     Starting containers...\e[0m"
	@cd api && docker-compose down
	@cd api && docker-compose up -d --build
	@docker ps

.PHONY: down
down:
	@cd api && docker-compose down

.PHONY: create-db
create-db: up
	@echo -e "\e[0;32mINFO     Making database migrations...\e[0m"
	@cd api && docker-compose exec web python manage.py makemigrations
	@cd api && docker-compose exec web python manage.py migrate

.PHONY: populate-data
populate-data: data/price_paid.csv venv/bin/activate create-db  
	@echo -e "\e[0;32mINFO     Populating database...\e[0m"
	@. $(VENV) && python3 scripts/populate_db.py --price-paid-data="./data/$(PRICE_PAID_FILE)" \
												--db-table-name=$(DB_TABLE_NAME) \
												--db-name=$(POSTGRES_DB) \
												--db-user=$(POSTGRES_USER) \
												--db-pass=$(POSTGRES_PASSWORD) \
												--db-host=$(POSTGRES_HOST)


#TODO: test services

.PHONY: all
all:  populate-data

.PHONY: clean
clean:
	@rm -rf data venv
	@cd api && docker-compose down
	@docker volume rm api_postgres_data || true


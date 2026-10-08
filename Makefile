.DEFAULT_GOAL := check
.PHONY: check build

ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

check:
	bash "$(ROOT_DIR)util/deploy.sh" --check

build:
	bash "$(ROOT_DIR)util/deploy.sh"
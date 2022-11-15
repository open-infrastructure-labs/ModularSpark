#!/bin/bash
set -e
pushd "$(dirname "$0")" # connect to root
pushd ../

./docker-bench.py --query_text "select * from call_center WHERE cc_call_center_id > '5'" -ll INFO --explain
./docker-bench.py --query_text "select * from store_sales WHERE ss_quantity > '1'" -ll INFO --explain
./docker-bench.py --query_text "select * from inventory WHERE inv_quantity_on_hand > '1'" -ll INFO --explain

./docker-bench.py --query_text "select * from call_center WHERE cc_call_center_id > '0'" -ll INFO --explain
./docker-bench.py --query_text "select * from store_sales WHERE ss_quantity > '0'" -ll INFO --explain
./docker-bench.py --query_text "select * from inventory WHERE inv_quantity_on_hand > '0'" -ll INFO --explain
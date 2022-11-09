import pandas as pd
import numpy as np
from sdv.tabular import GaussianCopula, CTGAN, CopulaGAN
import os, sys

primary_key_dict = {
    'catalog_returns': ['cr_item_sk', 'cr_order_number'],
    'catalog_sales': ['cs_item_sk', 'cs_order_number'],
    'customer': ['c_customer_sk'],
    'customer_address': ['ca_address_sk'],
    'customer_demographics': ['cd_demo_sk'],
    'date_dim': ['d_date_sk'],
    'household_demographics': ['hd_demo_sk'],
    'inventory': ['inv_date_sk', 'inv_item_sk', 'inv_warehouse_sk'],
    'item': ['i_item_sk'],
    'store_returns': ['sr_item_sk', 'sr_ticket_number'],
    'store_sales': ['ss_item_sk', 'ss_ticket_number'],
    'time_dim': ['t_time_sk'],
    'web_returns': ['wr_order_number', 'wr_item_sk'],
    'web_sales': ['ws_item_sk', 'ws_order_number']
}


def extract_queries_from_json_robert(jfl):
    tables, queries, gt_row_nums, spark_row_nums, error_vs_estimated, error_vs_overall = \
        [], [], [], [], [], []
    with open(jfl, 'r') as f:
        data = json.load(f)
        for d in data:
            if d['table_key'] not in tables: tables.append(d['table_key'])
            queries.append(d['query'])
            gt_row_nums.append(d['actual_rows'])
            spark_row_nums.append(d['estimated_rows'])
            error_vs_estimated.append(d['error_vs_estimated'])
            error_vs_overall.append(d['error_vs_overall'])
    return (queries, gt_row_nums, spark_row_nums, error_vs_estimated, error_vs_overall)


def extract_queries_from_json(jfl, tbl):
    tables = []
    queries = []
    with open(jfl, 'r') as f:
        data = json.load(f)
        for test in data['tests']:
            for query in test['subqueries']:
                if tbl in query['tables']:
                    queries.append(query['query'])
    return queries


def extract_keywords_from_queries(queries):
    kws = []
    for q in queries:
        for s in q.split():
            if 'ss_' not in s: continue
            if ',' in s:
                kws.extend(set(s.split(',')))
            else:
                kws.append(s)
    return list(set(kws))

if len(sys.argv)<4:
    print('usage: {sys.argv[0]} table_file(.parquet) model_type(gaussian,ctgan,copulagan) model_folder')
    exit(0)
table_name, model_type, model_dir = sys.argv[1], sys.argv[2], sys.argv[3]
batch_size, epoch = 1000, 100
# parquet_file = '/home/jimmy/Databases/tpcds-parquet/' + table_name + '.parquet'
parquet_file = table_name
# model_file = os.path.join('models', table_name + '_' + model_type + '.pkl')
model_file = os.path.join(model_dir, table_name + '_' + model_type + '.pkl')
if not os.path.exists(model_file):
    if os.path.exists(parquet_file):
        data = pd.read_parquet(parquet_file, engine='pyarrow')
    if len(primary_key_dict[table_name])==2:
        data['primary_key'] = data[primary_key_dict[table_name][0]].astype(str) + '_'\
                              + data[primary_key_dict[table_name][1]].astype(str)
        primary_key = 'primary_key'
    if len(primary_key_dict[table_name]) == 1:
        primary_key = primary_key_dict[table_name][0]

    if model_type == 'gaussian':
        model = GaussianCopula(primary_key=primary_key)
    if model_type == 'ctgan':
        model = CTGAN(embedding_dim=128, generator_dim=(256, 256),
                      discriminator_dim=(256, 256), batch_size=batch_size, epochs=epoch,
                      verbose=True, cuda=True)
    if model_type == 'copulagan':
        model = CopulaGAN(batch_size=batch_size, epochs=epoch, verbose=True, cuda=True)
    model.fit(data)
    model.save(model_file)
else:
    print(f'{model_file} exists already')

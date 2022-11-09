wget https://www.cis.fordham.edu/wisdm/includes/datasets/latest/WISDM_ar_latest.tar.gz
tar zxvf WISDM_ar_latest.tar.gz
python data_gen.py
python sensor_transformer_spark_iot.py
rm -fr WISDM_ar_latest.tar.gz WISDM_ar_v1.1

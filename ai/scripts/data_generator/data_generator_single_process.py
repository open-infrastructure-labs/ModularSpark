# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.import numpy as np

# Inspired by:
# https://sdv.dev/SDV/user_guides/timeseries/par.html
# https://github.com/brangerbriz/machine-learning-docs/tree/master/data/WISDM_ar_v1.1

import numpy as np
import pandas as pd
from sdv.timeseries import PAR
import time

def read_data(file_path):
    column_names = ['user-id','activity','timestamp', 'x-axis', 'y-axis', 'z-axis']
    f = open(file_path, 'r')
    lines = f.readlines()
    data = []
    for line in lines:
        line = line.rstrip(',')
        if len(line)<6: continue
        if line.count(';')>1:
            lines_ = line.split(';')
            for line_ in lines_:
                if len(line_)<6: continue
                line_split = line_.split(',')
                if len(line_split)<6: continue
                data.append(line_split)
        else:
            line = line.rstrip().rstrip(';')
            if line.endswith(','):
                line = line.rstrip(',')
            line_split = line.split(',')
            if len(line_split)<6: continue
            data.append(line_split)
    df = pd.DataFrame(np.asarray(data), columns=column_names)
    return df


def data_generator():
    activity2focus = 'Jogging'
    num_user2generate = 10
    file = 'WISDM_ar_v1.1/WISDM_ar_v1.1_raw.txt'
    df = read_data(file)
    df.dropna(axis=0, how='any', inplace=True)
    df.drop(df[df['timestamp']=='0'].index, inplace=True)
    df.drop_duplicates(subset=['user-id', 'timestamp'], keep='first', inplace=True)
    df = df.drop(['timestamp'], axis=1)
    for ax in ['x-axis', 'y-axis', 'z-axis']: df[ax] = df[ax].astype('float64')

    entity_columns = ['user-id']
    context_columns = ['activity']
    df_activity = df[df['activity']==activity2focus]
    model_activity = PAR(entity_columns=entity_columns, context_columns=context_columns)
    model_activity.fit(df_activity)
    df_activity_generated = model_activity.sample(num_sequences=num_user2generate)
    df_activity_generated.to_csv('generated_' + activity2focus + '.csv', index=False)
    print(f'generated data saved in generated_{activity2focus}.csv')

s = time.time()
data_generator()
print(f'elapse time {time.time()-s} seconds')

import numpy as np
import pandas as pd
from scipy import stats
import time
from sliding_window import sliding_window
from sklearn.preprocessing import OneHotEncoder

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

    # data = pd.read_csv(file_path, header = None, names = column_names)
    # return data


def feature_normalize(dataset):
    mu = np.mean(dataset,axis = 0)
    sigma = np.std(dataset,axis = 0)
    return (dataset - mu)/sigma


def segment_signal(data,window_size = 90):
    segments = sliding_window(data[['x-axis', 'y-axis', 'z-axis']].to_numpy(), (window_size, 3), (window_size//2, 1), flatten=False)
    segments = np.squeeze(segments)
    ohe = OneHotEncoder()
    labels_transformed = ohe.fit_transform(data[["activity"]]).toarray()
    labels_ = sliding_window(labels_transformed, (window_size, labels_transformed.shape[1]), (window_size//2, 1), flatten=False)
    labels_ = np.squeeze(labels_)
    n = len(labels_)
    labels = np.zeros((n, labels_.shape[2]))
    for i, v in enumerate(labels_):
        labels[i] = stats.mode(v)[0][0]
    return segments, labels


file = 'WISDM_ar_v1.1/WISDM_ar_v1.1_raw.txt'
df = read_data(file)
df.dropna(axis=0, how='any', inplace=True)
df['x-axis'] = feature_normalize(pd.to_numeric(df['x-axis'], errors='coerce').fillna(0, downcast='infer'))
df['y-axis'] = feature_normalize(pd.to_numeric(df['y-axis'], errors='coerce').fillna(0, downcast='infer'))
df['z-axis'] = feature_normalize(pd.to_numeric(df['z-axis'], errors='coerce').fillna(0, downcast='infer'))

s = time.time()
segments, labels = segment_signal(df)
labels = labels.astype(np.int8)
print(f'elapse time {time.time() - s} seconds')
np.save('segments.npy', segments)
np.save('labels.npy', labels)

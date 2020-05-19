import random
from collections import Counter
import os
import pickle
from sklearn.utils import shuffle
import numpy as np
import scipy.io as sio
from keras.utils import np_utils


def convert_one_hot(labels, num_classes):
    s = labels.shape
    labels_one_hot = np.zeros((s[0], s[1], num_classes))
    for i in range(s[1]):
        labels_one_hot[:,i,:] = np_utils.to_categorical(
            np.squeeze(labels[:,i]),
            num_classes
        )
    return labels_one_hot


def load_data_sessions(data_dir, fea_dir, sessions):
    full_sess = []
    for sess in sessions:
        d = {
            'post': '%s/%s' % (data_dir, sess),
            'feature': '%s/%s' % (fea_dir, sess)
        }
        full_sess.append(d)
    return full_sess


class DataGenerator:
    def __init__(
        self,
        data_sessions,
        look_back_cam,
        forecast_windows,
        batch_size,
        do_shuffle=False,
        class_balance=False
    ):
        self.forecast_windows = forecast_windows
        self.lb_cam = look_back_cam
        self.batch_size = batch_size
        self.data_sessions = data_sessions
        self.do_shuffle = do_shuffle
        self.class_balance = class_balance
        self.terrain_dict = {
            'tile': 0,
            'grass': 1,
            'brick': 2,
            'cement': 3,
            'upstairs': 4,
            'downstairs': 5
        }
        self.load_data()


    def load_data(self):
        self.feaList = {'rpi':[], 'tobii':[]}
        self.labelList = []
        self.index = self.n_sample = 0
        for session in self.data_sessions:
            FrameDir = {
                'rpi': '%s/rpi_frames' % session['post'],
                'tobii': '%s/tobii_frames' % session['post']
            }
            FeaDir = {
                'rpi': '%s/rpi_fea' % session['feature'],
                'tobii': '%s/tobii_fea' % session['feature']
            }
            SyncedFilename = '%s/labels_fps10.mat' % session['post']
            data = sio.loadmat(SyncedFilename)
            terrains = [str(d[0][0]) for d in data['terrains']]
            FrameIds = {
                'rpi': data['rpi_FrameIds'],
                'tobii': data['tobii_FrameIds']
            }

            td = self.terrain_dict
            for i in range(self.lb_cam, len(terrains)-max(self.forecast_windows)):
                # skip the sample if the terrain is 'unlabeled' or 'undefined'
                skip = False
                for p in self.forecast_windows:
                    for k in range(i-self.lb_cam+1+p,i+1+p):
                        if terrains[k] in ['undefined', 'unlabelled']:
                            skip = True

                if not skip:
                    # get the terrain label for multiple forecast windows
                    self.labelList.append(
                        [td[terrains[i+p]] for p in self.forecast_windows]
                    )
                    for device in ['rpi', 'tobii']:
                        self.feaList[device].append(
                            ['%s/%06d.pkl' % (FeaDir[device], FrameIds[device][j])
                            for j in range(i-self.lb_cam+1, i+1)]
                        )
                        
        self.n_samples = len(self.labelList)

        # compute the label distribution for the six terrains
        self.Tcounter = Counter([t[0] for t in self.labelList])
        c = []
        for t in range(6):
            c.append(self.Tcounter[t])
        self.T_p = {}
        for t in range(6):
            self.T_p[t] = min(c) / self.Tcounter[t]
        
        # shuffle data for training
        if self.do_shuffle:
            self.feaList['rpi'], self.feaList['tobii'],\
            self.labelList = shuffle(\
                self.feaList['rpi'], self.feaList['tobii'],\
                self.labelList)


    def next(self):
        idx = []
        while len(idx) < self.batch_size:
            if self.index >= self.n_samples:
                self.index = 0
            if self.class_balance:
                # do class balance while taking out samples
                l = self.labelList[self.index][0]
                if random.random() <= self.T_p[l]:
                    idx.append(self.index)
            else:
                idx.append(self.index)
            self.index += 1

        batch_terrains = [self.labelList[x] for x in idx]
        batch_feaArray= {}

        for d in ['rpi', 'tobii']:
            batch_feaArray[d] = np.asarray([
                self._load_pkl(self.feaList[d][x]) for x in idx
            ])
        batch_terrains = np.array(batch_terrains)

        data = {
            'feaArray':batch_feaArray,
            'terrains':batch_terrains
        }

        return data


    def reset(self):
        self.load_data()


    def get_fea_shape(self):
        sample_data = self._load_pkl(self.feaList['rpi'][1][1])
        return np.shape(sample_data)


    def _load_pkl(self, filenames):
        features = []
        for f in filenames:
            with open(f, 'rb') as file:
                fea = np.squeeze(pickle.load(file))
            features.append(fea)
        features = np.array(features, dtype=np.float64)
        return features
import scipy.io as sio
import pickle
import os
import numpy as np
import tensorflow as tf
from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from keras.preprocessing import image
from keras.layers import Input
from keras.models import Model
from keras import backend as K


config = tf.ConfigProto()
config.gpu_options.allow_growth = True
K.tensorflow_backend.set_session(tf.Session(config=config))


class feature_extractor:
    def __init__(self, input_shape):
        self.input_shape = input_shape
        self.model = self.create_encoder_model()
        self.output_shape = self.model.output.shape[1:]

    def create_encoder_model(self):
        input_tensor = Input(shape=self.input_shape)
        base_model = MobileNetV2(include_top=False, pooling='avg', input_tensor=input_tensor)
        output_tensor = base_model.output
        model = Model(inputs=input_tensor, outputs=output_tensor)
        return model

    def extract_features(self, img_path):
        img = image.load_img(img_path, target_size=self.input_shape[:2])
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        return self.model.predict(x)

    def get_output_shape(self):
        return self.output_shape


def main():
    DataPath = '/path/to/dataset_folder'
    FeaPath = '/path/to/feature_folder'
    sessions = [
        # subject_001
        'subject_001/y19m09d01', 'subject_001/y19m10d10_01',
        'subject_001/y19m10d14_01',
        'subject_001/y19m10d17_01', 'subject_001/y19m10d17_02',
        'subject_001/y19m10d19_02', 'subject_001/y19m10d19_03', 
        'subject_001/y19m12d03', 

        # subject_002
        'subject_002/y19m09d01', 'subject_002/y19m11d10',
        'subject_002/y19m11d11_01', 'subject_002/y19m11d11_02', 
        'subject_002/y19m11d25_02', 
        
        # subject_003
        'subject_003/y19m09d09_01', 'subject_003/y19m09d09_02',
        'subject_003/y19m09d09_03', 
        
        # subject_004
        'subject_004/y19m09d08_01', 'subject_004/y19m09d08_02', 
        
        # subject_005
        'subject_005/y19m10d28_01', 'subject_005/y19m10d28_02',
        'subject_005/y19m10d31_01', 'subject_005/y19m10d31_02', 
        
        # subject_006
        'subject_006/y19m11d01_01', 'subject_006/y19m11d01_02',
        'subject_006/y19m11d01_03', 'subject_006/y19m11d01_04', 
        
        # subject_007
        'subject_007/y19m12d02_01', 'subject_007/y19m12d02_02',
        'subject_007/y19m12d02_03', 'subject_007/y19m12d02_04',

        # subject_008
        'subject_008/y20m01d17_01','subject_008/y20m01d17_02'
    ]

    fea_extractor = feature_extractor((224, 224, 3))
    print(fea_extractor.get_output_shape())

    for sess in sessions:
        print('extracting features for %s' % (sess))

        for device in ['rpi', 'tobii']:
            FrameDir = '%s/%s/%s_frames' % (DataPath, sess, device)
            FeaDir = '%s/%s/%s_fea' % (FeaPath, sess, device)
            if not os.path.exists(FeaDir):
                os.makedirs(FeaDir)
            SyncedFilename = '%s/%s/labels_fps10.mat' % (DataPath, sess)
            data = sio.loadmat(SyncedFilename)
            FrameIds = data['%s_FrameIds' % device]
            for i in FrameIds:
                img_filename = '%s/%06d.jpg' % (FrameDir, i)
                fea_filename = '%s/%06d.pkl' % (FeaDir, i)
                if not os.path.isfile(fea_filename):
                    feature = fea_extractor.extract_features(img_filename)
                    with open(fea_filename, 'wb') as f:
                        pickle.dump(feature, f)


if __name__ == "__main__":
    main()

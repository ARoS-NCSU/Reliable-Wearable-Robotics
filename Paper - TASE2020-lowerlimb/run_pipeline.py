from model_utils import TerrainRecognition, ProbabilityCalibration


DataDir = '/path/to/dataset_folder'
FeaDir = '/path/to/feature_folder'
ResultDir = './results'

train_sessions = [
    'subject_001/y19m09d01',
    'subject_001/y19m10d10_01',
    'subject_001/y19m10d14_01',
    'subject_001/y19m10d17_01',
    'subject_001/y19m10d19_03',
    'subject_001/y19m12d03',
    'subject_002/y19m09d01', 
    'subject_002/y19m11d10',
    'subject_002/y19m11d11_01', 
    'subject_002/y19m11d11_02', 
    'subject_002/y19m11d25_02', 
    'subject_003/y19m09d09_02',
    'subject_003/y19m09d09_03',
    'subject_004/y19m09d08_01',
]


val_sessions = ['subject_001/y19m10d19_02', 'subject_001/y19m10d17_02', 'subject_003/y19m09d09_01', 'subject_004/y19m09d08_02']

cross_val_sessions = [
    ['subject_007/y19m12d02_03', 'subject_007/y19m12d02_04', 'subject_007/y19m12d02_01', 'subject_007/y19m12d02_02'],
    ['subject_006/y19m11d01_03', 'subject_006/y19m11d01_04', 'subject_006/y19m11d01_01', 'subject_006/y19m11d01_02'],
    ['subject_005/y19m10d31_01', 'subject_005/y19m10d31_02', 'subject_005/y19m10d28_01', 'subject_005/y19m10d28_02'],
    ['subject_008/y20m01d17_01','subject_008/y20m01d17_02']
]

params = {
    'data_dir': DataDir, # where the image frames and labels_fps10.mat file are saved.  
    'fea_dir': FeaDir, # where the extracted image features (from MobileNetV2) are saved.  
    'result_dir': ResultDir, # where the intermediate and final results are saved. 
    'val_sessions': val_sessions, # validation sessions for training probability calibration network.  
    'n_MC': 20, # increasing for more stable results, decreasing for faster inference. 
    'img_fea_dim': 1280, # the output feature dimention of MobileNetV2
    'n_terrains': 6,
    'forecast_windows': [0,10,20,40], # forecasting current terrain and 1s, 2s, 4s into the future. (for 10 FPS, 40 frames indicate 4 seconds)
    'batch_size': 64,
    'shuffle_sample': True, # shuffle samples for training
    'class_balance': True, # balance the classes by increasing the chance to select less frequent samples. 
    'train_steps': 5000
}

def main():
    model_types = [
        'baye_mlp_single_cam',
        'baye_gru_single_cam',
        'baye_mlp_two_cam', 
        'baye_gru_two_cam'
    ]

    for subjectId in range(4):
        sessions_for_train, sessions_for_test = load_sessions(cross_val_sessions, subjectId)
        params['train_sessions'] = train_sessions + sessions_for_train
        params['test_sessions'] = sessions_for_test
        params['subject_version'] = str(subjectId)
        for model_type in model_types:
            print('start %s, sub: %s' % (model_type, subjectId))
            params['model_type'] = model_type
            if 'mlp' in model_type:
                params['look_back_cam'] = 1
            else:
                params['look_back_cam'] = 30
            if 'two_cam' in model_type:
                # train and evaluate models for on-glasses + lowerlimb camera with feature fusion
                params['device'] = 'both'

                # step 1: train terrain recognition network on training dataset 
                # step 2: apply the trained network on validation and testing datasets
                TR = TerrainRecognition(params)
                TR.run_train_eval()
                del TR 

                # step 1: train probability calibration network on validation dataset 
                # step 2: apply the trained network on testing datasets
                PC = ProbabilityCalibration(params)
                PC.run_train_eval()
                del PC 

            else:
                for device in ['rpi', 'tobii']:
                    # train and evaluate models for on-glasses camera, lowerlimb camera seperately
                    params['device'] = device

                    # step 1: train terrain recognition network on training dataset 
                    # step 2: apply the trained network on validation and testing datasets
                    TR = TerrainRecognition(params)
                    TR.run_train_eval()
                    del TR 

                    # step 1: train probability calibration network on validation dataset 
                    # step 2: apply the trained network on testing datasets
                    PC = ProbabilityCalibration(params)
                    PC.run_train_eval()
                    del PC 

            print('finish %s, sub: %s' % (model_type, subjectId))


def load_sessions(cross_val_sessions, i):
    sessions_for_test = cross_val_sessions[i]
    sessions_for_train = []
    for j in range(len(cross_val_sessions)):
        if i != j:
            sessions_for_train = sessions_for_train + cross_val_sessions[j]
    return sessions_for_train, sessions_for_test

if __name__ == "__main__":
    main()

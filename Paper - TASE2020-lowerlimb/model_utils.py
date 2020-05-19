import scipy.io as sio
import pickle
import os
import collections
import numpy as np
import tensorflow as tf
from tensorflow.keras.regularizers import l1, l2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, GRU, Dropout, TimeDistributed, concatenate
import tensorflow.keras.backend as K
from load_data_utils import DataGenerator, load_data_sessions, convert_one_hot


class TerrainRecognition:
    def __init__(self, params):
        self.params = params
        self.result_mat_dir = self.params['result_dir']
        if not os.path.exists(self.result_mat_dir):
            os.makedirs(self.result_mat_dir)

        self.train_sessions = \
            load_data_sessions(self.params['data_dir'], self.params['fea_dir'], self.params['train_sessions'])
        self.val_sessions = \
            load_data_sessions(self.params['data_dir'], self.params['fea_dir'], self.params['val_sessions'])
        self.test_sessions = load_data_sessions(self.params['data_dir'], self.params['fea_dir'], self.params['test_sessions'])

        self.train_generator = DataGenerator(
            data_sessions=self.train_sessions,
            look_back_cam=self.params['look_back_cam'],
            forecast_windows=self.params['forecast_windows'],
            batch_size=self.params['batch_size'],
            do_shuffle=self.params['shuffle_sample'],
            class_balance=self.params['class_balance']
        )
        print('training samples', self.train_generator.n_samples)

        self.val_generator = DataGenerator(
            data_sessions=self.val_sessions,
            look_back_cam=self.params['look_back_cam'],
            forecast_windows=self.params['forecast_windows'],
            batch_size=1,
            do_shuffle=False,
            class_balance=False
        )
        print('validation samples', self.val_generator.n_samples)

        self.test_generator = DataGenerator(
            data_sessions=self.test_sessions,
            look_back_cam=self.params['look_back_cam'],
            forecast_windows=self.params['forecast_windows'],
            batch_size=1,
            do_shuffle=False,
            class_balance=False
        )
        print('testing samples', self.test_generator.n_samples)


    def run_train_eval(self):
        # Build Model
        model_selecter = ModelSelecter(self.params)
        model_selecter.BuildModel()

        # Train Model
        print("Starting model train process.")
        train_results = []
        for step in range(self.params['train_steps']):
            # get a batch of data 
            data = self.train_generator.next()
            terrains_one_hot = convert_one_hot(data['terrains'], self.params['n_terrains'])
            if self.params['device'] != 'both':
                input_data = data['feaArray'][self.params['device']]
            else:
                input_data = np.concatenate((data['feaArray']['rpi'], data['feaArray']['tobii']), axis=-1)

            # train model on batch 
            result = model_selecter.model.train_on_batch(input_data, terrains_one_hot)

            # show train accuracy
            train_results.append(result)  
            if step % 2000 == 1000:
                train_acc = np.mean([r['accuracy'] for r in train_results])
                print('%s, %s: step: %d -> train acc: %s' % (self.params['model_type'], self.params['device'], step, train_acc))
                train_results = []

        # Evaluating Terrain Recognition on Validation and Testing data
        print("Evaluating val dataset.")
        self.evaluation(model_selecter, self.val_generator, data_type='val')

        print("Evaluating test dataset.")
        self.evaluation(model_selecter, self.test_generator, data_type='test')

        model_selecter.model._sess.close()
        tf.keras.backend.clear_session()


    def evaluation(self, model_selecter, generator, data_type):
        resultsList, terrainsList  = [], []
        for step in range(generator.n_samples):
            data = generator.next()
            if self.params['device'] != 'both':
                input_data = data['feaArray'][self.params['device']]
            else:
                input_data = np.concatenate((data['feaArray']['rpi'], data['feaArray']['tobii']), axis=-1)

            resultsList.append(model_selecter.model.predict_on_batch(input_data))
            terrainsList.append(data['terrains'])

            if step % 5000 == 2000:
                print('complete %d/%d' % (step, generator.n_samples))

        mat_path = "%s/%s_%s_%s_v%s.mat" % (self.result_mat_dir, data_type, self.params['model_type'], self.params['device'], self.params['subject_version'])

        sio.savemat(mat_path, {
            'terrains': np.concatenate(terrainsList, axis=0),
            'softmax':np.concatenate(
                [r['softmax'] for r in resultsList], axis=0),
            'data_var':np.concatenate(
                [r['data_var']  for r in resultsList], axis=0),
            'entropy_var':np.concatenate(
                [r['entropy_var']for r in resultsList], axis=0),
            'mi_var':np.concatenate(
                [r['mi_var'] for r in resultsList], axis=0)
        })


class ProbabilityCalibration:
    def __init__(self, params):
        self.params = params


    def run_train_eval(self):
        print('train and evaluate probability calibration network')

        # build model
        cali_model = CaliNet(3)

        # prepare data
        val_file_path = "%s/val_%s_%s_v%s.mat" % (self.params['result_dir'], self.params['model_type'], self.params['device'], self.params['subject_version'])
        val_uncertainties, val_is_correct, val_softmax, val_terrains = \
            self.load_cali_data(val_file_path)

        val_uncertainties = np.reshape(val_uncertainties, (-1,3))
        val_is_correct = np.reshape(val_is_correct, (-1,))

        # train model
        cali_model.fit(val_uncertainties, val_is_correct, epochs=5, batch_size=32, shuffle=True)

        # apply probability calibration on testing data
        test_file_path = "%s/test_%s_%s_v%s.mat" % (self.params['result_dir'], self.params['model_type'], self.params['device'], self.params['subject_version'])
        test_uncertainties, _, test_softmax, test_terrains= \
            self.load_cali_data(test_file_path)

        m, n = test_uncertainties.shape[0:2]
        test_caliprobs = np.zeros((m,n,1))
        for i in range(n):
            test_caliprobs[:,i,:] = cali_model.predict(test_uncertainties[:,i,:])

        # save results    
        mat_path = "%s/test_cali_%s_%s_v%s.mat" % (self.params['result_dir'], self.params['model_type'], self.params['device'], self.params['subject_version'])
        sio.savemat(mat_path, {
            'uncertainties': test_uncertainties,
            'caliprobs': test_caliprobs,
            'terrains': test_terrains,
            'softmax': test_softmax
        })

        K.clear_session()


    def load_cali_data(self, filename):
        data = sio.loadmat(filename)

        terrains = data['terrains']
        softmaxs = data['softmax']

        terrain_pred = np.argmax(softmaxs, axis=-1)
        is_correct = terrains == terrain_pred

        uncertainties = np.concatenate((data['data_var'], data['entropy_var'], data['mi_var']), axis=-1)

        return uncertainties, is_correct, softmaxs, terrains


class ModelSelecter:
    def __init__(self, params):
        self.params = params


    def BuildModel(self):
        if self.params['model_type'] == 'baye_mlp_single_cam':
            self.model = SingleCamNet(
                look_back=1,
                n_classes=self.params['n_terrains'],
                img_fea_dim=self.params['img_fea_dim'],
                base_model='MLP',
                n_MC=self.params['n_MC'],
                num_pred=len(self.params['forecast_windows'])
            )
        elif self.params['model_type'] == 'baye_gru_single_cam':
            self.model = SingleCamNet(
                look_back=self.params['look_back_cam'],
                n_classes=self.params['n_terrains'],
                img_fea_dim=self.params['img_fea_dim'],
                base_model='GRU',
                n_MC=self.params['n_MC'],
                num_pred=len(self.params['forecast_windows'])
            )
        elif self.params['model_type'] == 'baye_mlp_two_cam':
            self.model = SingleCamNet(
                look_back=1,
                n_classes=self.params['n_terrains'],
                img_fea_dim=2*self.params['img_fea_dim'],
                base_model='MLP',
                n_MC=self.params['n_MC'],
                num_pred=len(self.params['forecast_windows'])
            )
        elif self.params['model_type'] == 'baye_gru_two_cam':
            self.model = SingleCamNet(
                look_back=self.params['look_back_cam'],
                n_classes=self.params['n_terrains'],
                img_fea_dim=2*self.params['img_fea_dim'],
                base_model='GRU',
                n_MC=self.params['n_MC'],
                num_pred=len(self.params['forecast_windows'])
            )
        else:
            raise ValueError('model is not supported')


def CaliNet(fea_dim):
    inputs = Input(shape=(fea_dim,))
    x = Dense(32, kernel_regularizer=l2(1e-5),
        bias_regularizer=l2(1e-5), activation='tanh')(inputs)
    x = Dense(64, kernel_regularizer=l2(1e-5),
        bias_regularizer=l2(1e-5), activation='tanh')(x)
    predictions = Dense(1, kernel_regularizer=l2(1e-5),
        bias_regularizer=l2(1e-5), activation='sigmoid')(x)
    model = Model(inputs=inputs, outputs=predictions)
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    return model


class SingleCamNet:
    def __init__(self, n_classes, img_fea_dim, look_back=1, base_model='RNN', n_MC=50, num_pred=1):

        self.units = 512
        self.n_classes = n_classes
        self.img_fea_dim = img_fea_dim
        
        self.look_back = look_back
        self.base_model = base_model

        self.input_cam = tf.placeholder(tf.float32, [None, look_back, img_fea_dim], name="input_cam")
        self.labels = tf.placeholder(tf.int64, [None, num_pred, n_classes], name="labels")
        self.is_train = tf.placeholder(tf.bool, name="is_train")

        self.n_MC = n_MC
        self.num_pred = num_pred

        self.global_step = tf.Variable(0, trainable=False, name="global_step")
        lr_intent = tf.train.exponential_decay(1e-3, self.global_step, 1000, 0.995, staircase=True)
        self.opt_intentNet = tf.train.AdamOptimizer(lr_intent)

        if base_model == 'MLP':
            assert self.look_back == 1 # for MLP the time step equals to one
            self.build_MLP_model()
        elif base_model == 'GRU':
            self.build_RNN_model()
        else:
            raise ValueError('model is not supported')

        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self._sess = tf.Session(config=config)
        self._sess.run(tf.initializers.global_variables())


    def bayesian_loss(self, logits, labels, datavar):
        mc_results = []
        for i in range(self.n_MC):
            s = tf.random.normal(tf.shape(logits), mean=0.0, stddev=1.0)
            std_samples = tf.multiply(datavar, s)
            distorted_loss = tf.nn.softmax_cross_entropy_with_logits(logits=(logits+std_samples), labels=labels)
            mc_results.append(distorted_loss)
        mc_results = tf.stack(mc_results, axis=0)
        var_loss = tf.reduce_mean(mc_results, axis=0)
        return var_loss


    def build_RNN_model(self):

        with tf.variable_scope("intentNet", reuse=tf.AUTO_REUSE):
            cam = TimeDistributed(Dense(512, activation='relu', kernel_regularizer=l2(1e-5), \
                bias_regularizer=l2(1e-5), name='cam_fc'))(self.input_cam)

            out = GRU(
                self.units,
                dropout=0.1,
                recurrent_dropout=0.1,
                activation='relu', 
                kernel_regularizer=l2(1e-5),
                bias_regularizer=l2(1e-5),
                name='intentNet_gru')(cam, training=self.is_train)

            out = Dropout(0.1)(out, training=self.is_train)

            # record softmax and data (aleatoric) uncertainty for the output
            softmax_multi_forecast = []
            datavar_multi_forecast = [] 

            # the list of loss
            loss_list = []

            for m in range(self.num_pred):
                logits = Dense(self.n_classes, activation='linear', kernel_regularizer=l2(1e-5), \
                    bias_regularizer=l2(1e-5), name='intentNet_logits_%d' % m)(out)
                out_prob = tf.nn.softmax(logits, axis=-1)

                datavar = Dense(1, activation='softplus', kernel_regularizer=l2(1e-5), \
                    bias_regularizer=l2(1e-5), name='intentNet_var_%d' % m)(out)

                loss = self.bayesian_loss(logits=logits, labels=self.labels[:,m,:], datavar=datavar)
                loss_list.append(loss)

                datavar_multi_forecast.append(datavar)
                softmax_multi_forecast.append(out_prob)

            self.pred_datavar = tf.stack(datavar_multi_forecast, axis=1)
            self.pred_softmax = tf.stack(softmax_multi_forecast, axis=1)

        with tf.variable_scope("intentNet_train", reuse=tf.AUTO_REUSE):
            self.intent_loss = tf.stack(loss_list, axis=1)
            self.avg_loss = tf.reduce_mean(self.intent_loss)
            intent_vars = tf.trainable_variables("intentNet")
            intent_gradients = self.opt_intentNet.compute_gradients(self.avg_loss, intent_vars)
            self.train_op_intentNet = self.opt_intentNet.apply_gradients(intent_gradients, self.global_step)
        return


    def build_MLP_model(self):

        with tf.variable_scope("intentNet", reuse=tf.AUTO_REUSE):
            input_cam = tf.squeeze(self.input_cam, axis=1)

            # cam shared net
            cam = Dense(512, activation='relu', kernel_regularizer=l2(1e-5), \
                bias_regularizer=l2(1e-5), name='fc_cam_1')(input_cam)
            cam = Dropout(0.1)(cam, training=self.is_train)

            cam = Dense(512, activation='relu', kernel_regularizer=l2(1e-5), \
                bias_regularizer=l2(1e-5), name='fc_cam_2')(cam)
            cam = Dropout(0.1)(cam, training=self.is_train)

            # the list of loss, softmax and datavar to support multi forecast lengths
            loss_list = []
            softmax_multi_forecast = []
            datavar_multi_forecast = []

            for m in range(self.num_pred):
                logits = Dense(self.n_classes, activation='linear', kernel_regularizer=l2(1e-5), \
                    bias_regularizer=l2(1e-5), name='intentNet_logits_%d' % m)(cam)
                out_prob = tf.nn.softmax(logits, axis=-1)

                datavar = Dense(1, activation='softplus', kernel_regularizer=l2(1e-5), \
                    bias_regularizer=l2(1e-5), name='intentNet_var_%d' % m)(cam)

                loss = self.bayesian_loss(logits=logits, labels=self.labels[:,m,:], datavar=datavar)
                loss_list.append(loss)

                datavar_multi_forecast.append(datavar)
                softmax_multi_forecast.append(out_prob)

            self.pred_datavar = tf.stack(datavar_multi_forecast, axis=1)
            self.pred_softmax = tf.stack(softmax_multi_forecast, axis=1)

        with tf.variable_scope("intentNet_train", reuse=tf.AUTO_REUSE):
            self.intent_loss = tf.stack(loss_list, axis=1)
            self.avg_loss = tf.reduce_mean(self.intent_loss)
            intent_vars = tf.trainable_variables("intentNet")
            intent_gradients = self.opt_intentNet.compute_gradients(self.avg_loss, intent_vars)
            self.train_op_intentNet = self.opt_intentNet.apply_gradients(intent_gradients, self.global_step)


    def train_on_batch(self, batch_cam, labels):
        results = collections.defaultdict(list)
        avg_l, pred_probs, _ = self._sess.run(
                [
                    self.avg_loss,
                    self.pred_softmax,
                    self.train_op_intentNet
                ],
                feed_dict={
                    self.input_cam: batch_cam,
                    self.labels: labels,
                    self.is_train: True
                    }
        )
        pred = np.argmax(pred_probs, axis=-1)
        correct = np.argmax(pred_probs, axis=-1) == np.argmax(labels, axis=-1)
        acc = np.mean(np.mean(correct.astype(np.float32), axis=0), axis=0)
        results['avg_l'] = avg_l
        results['softmax'] = pred_probs
        results['accuracy'] = acc
        return results


    def test_on_batch(self, batch_cam, labels):
        results = self.predict_on_batch(batch_cam)
        pred_probs = results['softmax']
        pred = np.argmax(pred_probs, axis=-1)
        correct = np.argmax(pred_probs, axis=-1) == np.argmax(labels, axis=-1)
        acc = np.mean(np.mean(correct.astype(np.float32), axis=0), axis=0)
        results['accuracy'] = acc
        return results


    def predict_on_batch(self, batch_cam):
        results = collections.defaultdict(list)

        batch_size = batch_cam.shape[0]
        pred_probs_array = np.zeros((batch_size, self.num_pred, self.n_classes))
        datavar_array = np.zeros((batch_size, self.num_pred, 1))
        mi_var_array = np.zeros((batch_size, self.num_pred, 1))
        entropy_var_array = np.zeros((batch_size, self.num_pred, 1))

        for i in range(batch_size):
            mc_cam = np.concatenate([batch_cam[i:i+1,:,:] for mc in range(self.n_MC)], axis=0)
            softmax_T, datavar_T = self._sess.run([
                    self.pred_softmax,
                    self.pred_datavar
                ],
                feed_dict={
                    self.input_cam: mc_cam,
                    self.is_train: True
                    }
            )
            for m in range(self.num_pred):
                entropy_var, mi_var, datavar, softmax_mean = \
                    self.cal_bnn_vars(softmax_T[:,m,:], datavar_T[:,m])
                pred_probs_array[i,m,:] = softmax_mean
                entropy_var_array[i,m] = entropy_var
                mi_var_array[i,m,:] = mi_var
                datavar_array[i,m,:] = datavar

        results['softmax'] = pred_probs_array
        results['entropy_var'] = entropy_var_array
        results['mi_var'] = mi_var_array
        results['data_var'] = datavar_array

        return results


    def cal_bnn_vars(self, softmax_T, datavar_T):

        softmax_mean = np.mean(softmax_T, axis=0)
        datavar = np.mean(datavar_T, axis=0)

        entropy_var = -1 * np.sum(np.multiply(np.log(np.finfo(float).eps \
                            + softmax_mean), softmax_mean), axis=-1)
        sum_c_mean_T = np.mean(np.sum(np.multiply(np.log(np.finfo(float).eps \
                            + softmax_T), softmax_T), axis=-1), axis=0)
        mi_var = entropy_var + sum_c_mean_T + np.finfo(float).eps

        return np.squeeze(entropy_var), np.squeeze(mi_var), \
            np.squeeze(datavar), np.squeeze(softmax_mean)

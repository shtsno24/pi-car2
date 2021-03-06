#-*- coding:utf-8 -*-
import os
import sys
import time
import numpy as np

import chainer
import chainer.functions as F
import chainer.links as L
import chainer.training as T
import chainer.training.extensions as E
from chainer.datasets import tuple_dataset
from chainer import serializers

import net
import util

epoch_num = 5000

NPZ = "data/bin2train_data.npz"
model_folder = "model"


"""
using CPU : gpu_id = -1

using GPU : gpu_id = 0

"""
gpu_id = 0

    
try:
    #find dataset (NPZ file)
    util.find_train_data(NPZ)

    #load dataset (NPZ file)
    ortrain, ortrain_label = util.load_train_data(NPZ,"img","img_test_bin")
    

    print("epoch : " + str(epoch_num))
    input(">>")

    #sprit dataset
    threshold = np.int32(ortrain.shape[0] * 0.50)
    ortrain = ortrain.astype(np.float32)
    orlab = ortrain_label.astype(np.float32)

    train = tuple_dataset.TupleDataset(ortrain[0:threshold], orlab[0:threshold])
    test = tuple_dataset.TupleDataset(ortrain[0:threshold:],  orlab[0:threshold:])

    #load model
    model = L.Classifier(net.MLP(),lossfun=net.Loss.loss_func)
    model.compute_accuracy = False
    
    #apply optimizer
    optimizer = chainer.optimizers.Adam()
    optimizer.setup(model)

    #set iterator
    train_iter = chainer.iterators.SerialIterator(train, batch_size=50)
    test_iter = chainer.iterators.SerialIterator(test, batch_size=30, repeat=False, shuffle=False)

    #send model to gpu
    if gpu_id >= 0:
        chainer.using_config('cudnn_deterministic',True)
        model.to_gpu(gpu_id)


    updater = T.StandardUpdater(train_iter, optimizer, device = gpu_id)
    trainer = T.Trainer(updater, (epoch_num, 'epoch'), out='result')

    trainer.extend(E.Evaluator(test_iter, model, device=gpu_id))
    trainer.extend(E.LogReport())
    trainer.extend(E.ProgressBar())

    trainer.extend(E.PrintReport(['epoch', 'main/loss', 'validation/main/loss']))
    trainer.run()
    
except:
    import traceback
    traceback.print_exc()

finally:
    print('trained model is saved in "model" folder')
    util.create_folders(model_folder)
    model.to_cpu()
    serializers.save_npz(model_folder + "/trained_model.npz",model)
    input(">>")

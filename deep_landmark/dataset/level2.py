#!/usr/bin/env python2.7
# coding: utf-8
"""
    This file convert dataset from http://mmlab.ie.cuhk.edu.hk/archive/CNN_FacePoint.htm
    We convert data for LEVEL-2 training data.
    all data are formated as (patch, delta landmark), and delta landmark is ((x1, y1), (x2, y2)...)
"""

import os
from os.path import join, exists
import time
from collections import defaultdict
import cv2
import numpy as np
import h5py
from common import logger, createDir, getDataFromTxt, getPatch, processImage
from common import shuffle_in_unison_scary
from utils import randomShift, randomShiftWithArgument


types = [(0, 'LE1', 0.16),
         (0, 'LE2', 0.18),
         (1, 'RE1', 0.16),
         (1, 'RE2', 0.18),
         (2, 'N1', 0.16),
         (2, 'N2', 0.18),
         (3, 'LM1', 0.16),
         (3, 'LM2', 0.18),
         (4, 'RM1', 0.16),
         (4, 'RM2', 0.18),]
for t in types:
    d = 'train/2_%s' % t[1]
    createDir(d)

def generate(ftxt, mode, argument=False):
    """
        Generate Training Data for LEVEL-2
        mode = train or test
    """
    data = getDataFromTxt(ftxt)

    trainData = defaultdict(lambda: dict(patches=[], landmarks=[]))
    for (imgPath, bbox, landmarkGt) in data:
        img = cv2.imread(imgPath, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        assert(img is not None)
        logger("process %s" % imgPath)

        landmarkPs = randomShiftWithArgument(landmarkGt, 0.05)
        if not argument:
            landmarkPs = [landmarkPs[0]]

        for landmarkP in landmarkPs:
            for idx, name, padding in types:
                patch, patch_bbox = getPatch(img, bbox, landmarkP[idx], padding)
                patch = cv2.resize(patch, (15, 15))
                patch = patch.reshape((1, 15, 15))
                trainData[name]['patches'].append(patch)
                _ = patch_bbox.project(bbox.reproject(landmarkGt[idx]))
                trainData[name]['landmarks'].append(_)

    for idx, name, padding in types:
        logger('writing training data of %s'%name)
        patches = np.asarray(trainData[name]['patches'])
        landmarks = np.asarray(trainData[name]['landmarks'])
        patches = processImage(patches)

        shuffle_in_unison_scary(patches, landmarks)

        with h5py.File('/home/admin01/workspace/deep_landmark/dataset/train/2_%s/%s.h5'%(name, mode), 'w') as h5:
            h5['data'] = patches.astype(np.float32)
            h5['landmark'] = landmarks.astype(np.float32)
        with open('/home/admin01/workspace/deep_landmark/dataset/train/2_%s/%s.txt'%(name, mode), 'w') as fd:
            fd.write('/home/admin01/workspace/deep_landmark/dataset/train/2_%s/%s.h5'%(name, mode))


if __name__ == '__main__':
    np.random.seed(int(time.time()))
    # trainImageList.txt
    generate('/home/admin01/workspace/deep_landmark/cnn-face-data/trainImageList.txt', 'train', argument=True)
    # testImageList.txt
    generate('/home/admin01/workspace/deep_landmark/cnn-face-data/testImageList.txt', 'test')
    # Done

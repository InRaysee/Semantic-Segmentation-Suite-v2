# -*- coding: utf-8 -*-

import os
import cv2
import numpy as np

path = 'results_tiles01'

def compute(path):
    for subdir in os.listdir(path):
        if subdir != '.DS_Store':
            per_image_Rmean = []
            target = open(("scores/" + path + "_" + subdir + ".csv"), 'w')
            target.write("file,score\n")
            dirtionary = os.listdir(path + "/" + subdir)
            dirtionary.sort(key= lambda x:int(x[:-4]))
            for file in dirtionary:
                if file != '.DS_Store':
                    img = cv2.imread((path + "/" + subdir + "/" + file), 1)
                    per_Rmean = np.mean(img[:, :, 2])
                    per_image_Rmean.append(per_Rmean)
                    target.write(file[0:-4] + "," + str(per_Rmean) + "\n")
            R_mean = np.mean(per_image_Rmean)
            print(R_mean)
            target.write("average," + str(R_mean))
            target.close()
    return

if __name__ == '__main__':
    compute(path)

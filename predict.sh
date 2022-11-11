#!/bin/bash

for ((i=0;i<6;i++));
do
  for ((j=1;j<124;j++));
  do
    python3 predict.py --image demo/face$i/face$i\_$j.png --checkpoint_path checkpoints/latest_model_FC-DenseNet56_CamVid.ckpt --model FC-DenseNet56 --crop_height 512 --crop_width 512
  done
done

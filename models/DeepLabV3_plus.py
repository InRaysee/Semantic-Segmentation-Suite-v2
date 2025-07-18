# coding=utf-8

import tensorflow as tf
import tf_slim as slim
from builders import frontend_builder
import numpy as np
import os, sys

def Upsampling(inputs,feature_map_shape):
    return tf.image.resize(inputs, size=tf.cast(feature_map_shape, tf.int32), method=tf.image.ResizeMethod.BILINEAR)

def ConvUpscaleBlock(inputs, n_filters, kernel_size=[3, 3], scale=2):
    """
    Basic conv transpose block for Encoder-Decoder upsampling
    Apply successivly Transposed Convolution, BatchNormalization, ReLU nonlinearity
    """
    net = tf.nn.relu(slim.batch_norm(inputs, fused=True))
    net = slim.conv2d_transpose(net, n_filters, kernel_size=[3, 3], stride=[scale, scale], activation_fn=None)
    return net

def ConvBlock(inputs, n_filters, kernel_size=[3, 3]):
    """
    Basic conv block for Encoder-Decoder
    Apply successivly Convolution, BatchNormalization, ReLU nonlinearity
    """
    net = tf.nn.relu(slim.batch_norm(inputs, fused=True))
    net = slim.conv2d(net, n_filters, kernel_size, activation_fn=None, normalizer_fn=None)
    return net

def AtrousSpatialPyramidPoolingModule(inputs, depth=256):
    """

    ASPP consists of (a) one 1×1 convolution and three 3×3 convolutions with rates = (6, 12, 18) when output stride = 16
    (all with 256 filters and batch normalization), and (b) the image-level features as described in the paper

    """

    feature_map_size = tf.shape(input=inputs)

    # Global average pooling
    image_features = tf.reduce_mean(input_tensor=inputs, axis=[1, 2], keepdims=True)

    image_features = slim.conv2d(image_features, depth, [1, 1], activation_fn=None)
    image_features = tf.image.resize(image_features, (feature_map_size[1], feature_map_size[2]), method=tf.image.ResizeMethod.BILINEAR)

    atrous_pool_block_1 = slim.conv2d(inputs, depth, [1, 1], activation_fn=None)

    atrous_pool_block_6 = slim.conv2d(inputs, depth, [3, 3], rate=6, activation_fn=None)

    atrous_pool_block_12 = slim.conv2d(inputs, depth, [3, 3], rate=12, activation_fn=None)

    atrous_pool_block_18 = slim.conv2d(inputs, depth, [3, 3], rate=18, activation_fn=None)

    net = tf.concat((image_features, atrous_pool_block_1, atrous_pool_block_6, atrous_pool_block_12, atrous_pool_block_18), axis=3)

    return net





def build_deeplabv3_plus(inputs, num_classes, preset_model='DeepLabV3+', frontend="ResNet101", weight_decay=1e-5, is_training=True, pretrained_dir="models"):
    """
    Builds the DeepLabV3 model. 

    Arguments:
      inputs: The input tensor= 
      preset_model: Which model you want to use. Select which ResNet model to use for feature extraction 
      num_classes: Number of classes

    Returns:
      DeepLabV3 model
    """

    logits, end_points, frontend_scope, init_fn  = frontend_builder.build_frontend(inputs, frontend, pretrained_dir=pretrained_dir, is_training=is_training)


    label_size = tf.shape(input=inputs)[1:3]

    encoder_features = end_points['pool2']

    net = AtrousSpatialPyramidPoolingModule(end_points['pool4'])
    net = slim.conv2d(net, 256, [1, 1], scope="conv_1x1_output", activation_fn=None)
    decoder_features = Upsampling(net, label_size / 4)

    encoder_features = slim.conv2d(encoder_features, 48, [1, 1], activation_fn=tf.nn.relu, normalizer_fn=None)

    net = tf.concat((encoder_features, decoder_features), axis=3)

    net = slim.conv2d(net, 256, [3, 3], activation_fn=tf.nn.relu, normalizer_fn=None)
    net = slim.conv2d(net, 256, [3, 3], activation_fn=tf.nn.relu, normalizer_fn=None)

    net = Upsampling(net, label_size)
    
    net = slim.conv2d(net, num_classes, [1, 1], activation_fn=None, scope='logits')

    return net, init_fn


def mean_image_subtraction(inputs, means=[123.68, 116.78, 103.94]):
    inputs=tf.cast(inputs, dtype=tf.float32)
    num_channels = inputs.get_shape().as_list()[-1]
    if len(means) != num_channels:
      raise ValueError('len(means) must match the number of channels')
    channels = tf.split(axis=3, num_or_size_splits=num_channels, value=inputs)
    for i in range(num_channels):
        channels[i] -= means[i]
    return tf.concat(axis=3, values=channels)

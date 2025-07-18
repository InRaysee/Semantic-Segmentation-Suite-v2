import os,time,cv2, sys, math
import tensorflow as tf
import argparse
import numpy as np

from utils import utils, helpers
from builders import model_builder

parser = argparse.ArgumentParser()
parser.add_argument('--dir', type=str, default=None, required=True, help='The images you want to predict on. ')
parser.add_argument('--outdir', type=str, default=None, required=True, help='The place you want to save the images you predict on. ')
parser.add_argument('--checkpoint_path', type=str, default=None, required=True, help='The path to the latest checkpoint weights for your model.')
parser.add_argument('--crop_height', type=int, default=512, help='Height of cropped input image to network')
parser.add_argument('--crop_width', type=int, default=512, help='Width of cropped input image to network')
parser.add_argument('--model', type=str, default=None, required=True, help='The model you are using')
parser.add_argument('--dataset', type=str, default="CamVid", required=False, help='The dataset you are using')
args = parser.parse_args()

class_names_list, label_values = helpers.get_label_info(os.path.join(args.dataset, "class_dict_weight01.csv"))

num_classes = len(label_values)

print("\n***** Begin prediction *****")
print("Dataset -->", args.dataset)
print("Model -->", args.model)
print("Crop Height -->", args.crop_height)
print("Crop Width -->", args.crop_width)
print("Num Classes -->", num_classes)
print("Dir -->", args.dir)
print("Outdir -->", args.outdir)

# Initializing network
config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
sess=tf.compat.v1.Session(config=config)

tf.compat.v1.disable_eager_execution()
net_input = tf.compat.v1.placeholder(tf.float32,shape=[None,None,None,3])
net_output = tf.compat.v1.placeholder(tf.float32,shape=[None,None,None,num_classes]) 

network, _ = model_builder.build_model(args.model, net_input=net_input,
                                        num_classes=num_classes,
                                        crop_width=args.crop_width,
                                        crop_height=args.crop_height,
                                        is_training=False)

sess.run(tf.compat.v1.global_variables_initializer())

print('Loading model checkpoint weights')
saver=tf.compat.v1.train.Saver(max_to_keep=1000)
saver.restore(sess, args.checkpoint_path)

# Create directories if needed
if not os.path.isdir(args.outdir):
    os.makedirs(args.outdir)

input_images = []
output_dirs = []
for subdir in os.listdir(args.dir):
    if subdir != '.DS_Store':
        # Create directories if needed
        if not os.path.isdir(args.outdir + "/" + subdir):
            os.makedirs(args.outdir + "/" + subdir)
        for file in os.listdir(args.dir + "/" + subdir):
            if file != '.DS_Store':
                cwd = os.getcwd()
                input_images.append(cwd + "/" + args.dir + "/" + subdir + "/" + file)
                output_dirs.append(cwd + "/" + args.outdir + "/" + subdir + "/")

for ind in range(len(input_images)):

    print("Running test image %d / %d"%(ind+1, len(input_images)))

    loaded_image = utils.load_image(input_images[ind])
    resized_image =cv2.resize(loaded_image, (args.crop_width, args.crop_height))
    input_image = np.expand_dims(np.float32(resized_image[:args.crop_height, :args.crop_width]), axis=0)/255.0

    st = time.time()
    output_image = sess.run(network, feed_dict={net_input: input_image})

    run_time = time.time()-st

    output_image = np.array(output_image[0, :, :, :])
    output_image = helpers.reverse_one_hot(output_image)

    out_vis_image = helpers.colour_code_segmentation(output_image, label_values)
    file_name = output_dirs[ind] + utils.filepath_to_name(input_images[ind])[11:] + ".png"
    cv2.imwrite(file_name, cv2.cvtColor(np.uint8(out_vis_image), cv2.COLOR_RGB2BGR))

    print("")
    print("Finished!")
    print("Wrote image " + file_name)

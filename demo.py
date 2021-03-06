import numpy as np
import tensorflow as tf
from utils import decode
from net import Net
from net_att import Net_att
from net_densenet import DenseNet
from skimage.io import imsave
import random
import cv2
import re

'''
Parameters(Please follow the instruction below)
'''
# Note: The current model only supports image with size 256 * 256
# 1.Choose a model
# Select from [no_att_5w, ht3_weighted_loss_5w, end_to_end_weighted_loss]
#model = 'ht3_weighted_loss_5w'
#model = 'no_att_5w'
model = 'end_to_end_weighted_loss'


# 2.Specify the path to read the image from
# and the path to generate the generated image
# Note: Both paths must be valid
folder_path = 'data/output/'
output_path = 'output_results/'

# 3.Specify the image names
img_names = ['rsz_n02119789_3731.JPEG']



'''
Code
'''
img_num = len(img_names)
batch_size = 1
assert batch_size <= img_num


height = 256
width = 256

img_list = []

## img collection
img_col = []

for img_name in img_names:
    img = cv2.imread(folder_path+img_name)
    if img.shape[0] != 256 or img.shape[1] != 256:
        img = cv2.resize(img, (256, 256))
    #save ref
    img_col.append(img)

    # Convert image from rgb to gray
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imsave(output_path+img_name, img)

    # Preprocess the image
    img = img.reshape((1, img.shape[0], img.shape[1], 1))
    img = img.astype(dtype=np.float32) / 255.0 * 100 - 50
    img_list.append(img)

# Stack all images to get a 4d image tensor that consists of all images
all_data_l = np.vstack(img_list)

# Construct graph
training_flag = tf.placeholder(tf.bool)
if model == 'end_to_end_weighted_loss':
    autocolor = Net_att(train=training_flag)
else:
    autocolor = Net(train=training_flag)
# autocolor = DenseNet(train=training_flag)

data_l = tf.placeholder(tf.float32, (batch_size, height, width, 1))
conv8_313 = autocolor.inference(data_l)


# Load model and run the graph
saver = tf.train.Saver()

with tf.Session() as sess:
    saver.restore(sess, 'models/'+model+'/model.ckpt')
    reconstructed_img_list = []

    for start_ind in range(0, img_num, batch_size):
        end_ind = start_ind + batch_size
        if end_ind > img_num:
            end_ind = img_num

        batch_data_l = all_data_l[start_ind:end_ind]
        conv8_313_returned = sess.run(conv8_313, feed_dict={training_flag:False, data_l:batch_data_l})

        for i in range(batch_size):

            # Colorize w/ class rebalancing
            # reconstructed_img_rgb  : [height, width, 3], predicted colorized image
            reconstructed_img_rgb = decode(batch_data_l[i][None,:,:,:], conv8_313_returned[i][None,:,:,:], 0.00001)
            reconstructed_img_rgb = np.concatenate([reconstructed_img_rgb[:,:,2][:,:,np.newaxis], reconstructed_img_rgb[:,:,1][:,:,np.newaxis], reconstructed_img_rgb[:,:,0][:,:,np.newaxis]], axis=2)
            reconstructed_img_list.append(reconstructed_img_rgb.astype(np.uint8))

            imsave(output_path+model+'_'+img_names[start_ind+i], reconstructed_img_rgb)

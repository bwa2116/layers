# -*- coding: utf-8 -*-
"""Untitled6.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WxPfoSwjwudK0LQp5VQTXAui-afo4hvX
"""

# Print iterations progress
def print_progress_bar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

#This is copied from https://raw.githubusercontent.com/yandexdataschool/Practical_DL/spring2019/week03_convnets/tiny_img.py

import numpy as np
from sklearn.model_selection import train_test_split
import os, sys
if sys.version_info[0] == 2:
    from urllib import urlretrieve
    import cPickle as pickle

else:
    from urllib.request import urlretrieve
    import pickle

def unpickle(file):
    fo = open(file, 'rb')
    if sys.version_info[0] == 2:
        dict = pickle.load(fo)
    else:
        dict = pickle.load(fo,encoding='latin1')

    fo.close()
    return dict

def download_tinyImg200(path,
                     url='http://cs231n.stanford.edu/tiny-imagenet-200.zip',
                     tarname='tiny-imagenet-200.zip'):
    if not os.path.exists(path):
        os.mkdir(path)
    urlretrieve(url, os.path.join(path,tarname))
    print (os.path.join(path,tarname))
    import zipfile
    zip_ref = zipfile.ZipFile(os.path.join(path,tarname), 'r')
    zip_ref.extractall()
    zip_ref.close()

data_path = "."
full_data_path = os.path.join(data_path, "tiny-imagenet-200/")
if not os.path.exists(full_data_path):
    print ("Dataset not found. Downloading...")
    print (data_path)
    download_tinyImg200(data_path)

cd /content/tiny-imagenet-200/

from torchvision.io import read_image

import cv2 as cv
import os, pickle, torch
import pandas as pd

NUM_CLASSES = 200
IMGS_PER_CLASS = 500

"""
Suggested workflow for preparing data:
get_train_data() # construct the training set
pickle_data()    # pickle the dataset for fast reading
get_val_data()   # construct the validation set
pickle_data()    # pickle the dataset for fast reading
"""

def get_label_mapping():
    object_mapping = pd.read_csv('words.txt', sep='\t', index_col=0, names=['label'])
    labels_str = [f.name for f in os.scandir('train') if f.is_dir()]
    labels = pd.DataFrame(labels_str, columns=['id'])
    labels['label'] = [object_mapping.loc[ids].item() for ids in labels['id']]

    return labels

def get_train_data(one_hot=False):
    train_data = torch.Tensor().type(torch.ByteTensor)
    labels_str = [f.name for f in os.scandir('train') if f.is_dir()]
    labels = []
    i = 1
    for root, dirs, files in os.walk('train'):
        if root.find('images') != -1:
            one_class = torch.Tensor().type(torch.ByteTensor)
            for name in files:
                img = read_image(root + os.sep + name)
                if img.shape[0] == 1:
                    img = torch.tensor(cv.cvtColor(img.permute(1,2,0).numpy(), cv.COLOR_GRAY2RGB)).permute(2,0,1)
                one_class = torch.cat((one_class, img), 0)
                labels.append(i-1)
                first_image = False

            one_class = one_class.reshape(-1, 3, 64, 64)
            print_progress_bar(i, NUM_CLASSES, prefix = 'Progress:', suffix = 'Complete')
            i+=1
            train_data = torch.cat((train_data, one_class), 0)

    return train_data, torch.Tensor(labels)

def get_val_data(one_hot=False):
    val_data = torch.Tensor().type(torch.ByteTensor)
    labels_str = [f.name for f in os.scandir('train') if f.is_dir()]
    labels = []
    val_annotations = pd.read_csv('val/val_annotations.txt', sep='\t', names=['filename', 'label_str', 'x_min', 'y_min', 'x_max', 'y_max'])
    num_imgs = len(os.listdir('val/images'))

    i = 1
    for name in os.listdir('val/images'):
        img = read_image('val/images' + os.sep + name)
        if img.shape[0] == 1:
            img = torch.tensor(cv.cvtColor(img.permute(1,2,0).numpy(), cv.COLOR_GRAY2RGB)).permute(2,0,1)
        val_data = torch.cat((val_data, img), 0)
        class_name = val_annotations.loc[val_annotations['filename'] == name]['label_str'].item()
        labels.append(labels_str.index(class_name))
        print_progress_bar(i, num_imgs, prefix = 'Progress:', suffix = 'Complete')
        i+=1

    return val_data.reshape(-1, 3, 64, 64), torch.Tensor(labels)

def pickle_data(data, label, filename):
    outfile = open(filename, 'wb')
    pickle.dump((data, label), outfile)
    outfile.close()

if __name__ == '__main__':
    data, labels = get_train_data()
    print(data.shape, labels.shape)
    pickle_data(data, labels, 'train_dataset.pkl')
    data, labels = get_val_data()
    print(data.shape, labels.shape)
    pickle_data(data, labels, 'val_dataset.pkl')

from torch import FloatTensor, div
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode

import pickle, torch
import numpy as np

class ImageNetDataset(Dataset):
    """Dataset class for ImageNet"""
    def __init__(self, dataset, labels, transform=None, normalize=None):
        super(ImageNetDataset, self).__init__()
        assert(len(dataset) == len(labels))
        self.dataset = dataset
        self.labels = labels
        self.transform = transform
        self.normalize = normalize

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        data = self.dataset[idx]
        if self.transform:
            data = self.transform(data)

        data = div(data.type(FloatTensor), 255)
        if self.normalize:
            data = self.normalize(data)

        return data, self.labels[idx]

def load_train_data(img_size, magnitude, batch_size):
    with open('train_dataset.pkl', 'rb') as f:
        train_data, train_labels = pickle.load(f)
    transform = transforms.Compose([
        transforms.Resize(img_size, interpolation=InterpolationMode.BICUBIC),
        transforms.RandAugment(num_ops=2,magnitude=magnitude),
    ])
    train_dataset = ImageNetDataset(train_data, train_labels.type(torch.LongTensor), transform,
        normalize=transforms.Compose([
            transforms.Normalize(
                mean=(0.485, 0.456, 0.406),
                std=(0.229, 0.224, 0.225)
            )
        ]),
    )
    train_loader = DataLoader(
        train_dataset,
        shuffle=True,
        batch_size=batch_size,
        num_workers=8,
        pin_memory=True,
        drop_last=True,
    )
    f.close()
    return train_loader

def load_val_data(img_size, batch_size):
    with open('val_dataset.pkl', 'rb') as f:
        val_data, val_labels = pickle.load(f)
    transform = transforms.Compose([
        transforms.Resize(img_size, interpolation=InterpolationMode.BICUBIC),
    ])
    val_dataset = ImageNetDataset(val_data, val_labels.type(torch.LongTensor), transform,
        normalize=transforms.Compose([
            transforms.Normalize(
                mean=(0.485, 0.456, 0.406),
                std=(0.229, 0.224, 0.225)
            ),
        ])
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )
    f.close()
    return val_loader


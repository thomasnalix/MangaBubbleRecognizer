import os
import shutil
import random

train_img_dir = 'data/images/train'
val_img_dir = 'data/images/val'
train_label_dir = 'data/labels/train'
val_label_dir = 'data/labels/val'

img_train = [f for f in os.listdir(train_img_dir) if f.endswith('.png')]

img_sample = random.sample(img_train, 25)

for img in img_sample:
    shutil.copy(os.path.join(train_img_dir, img), os.path.join(val_img_dir, img))
    
    label = img.replace('.png', '.txt')
    shutil.copy(os.path.join(train_label_dir, label), os.path.join(val_label_dir, label))

print(f'Transferred {len(img_sample)} images to validation: {img_sample}')
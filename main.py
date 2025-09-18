import os

folder = 'data/images/train'
start_num = 88

for i in range(1, 101):
    old_name = os.path.join(folder, f'image_{i}')
    new_name = os.path.join(folder, str(start_num + i))
    if os.path.exists(old_name):
        os.rename(old_name, new_name)

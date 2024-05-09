import os
import zipfile
import shutil


def create_directory(dir,delete=False):
    if os.path.isdir(dir) and delete:
        shutil.rmtree(dir)
    os.makedirs(dir,exist_ok=True)

extrc_dir = f'extracted/2022'


raw_dataroot = f'zip/2022'
for file in os.scandir(raw_dataroot):
    if file.name[-4:] != '.zip':
        continue
    with zipfile.ZipFile(file.path, 'r') as zip_ref:
        zip_ref.extractall(extrc_dir)
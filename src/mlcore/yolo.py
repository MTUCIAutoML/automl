import os
import zipfile
import glob
import shutil

from typing import List
from ultralytics import YOLO
from tempfile import TemporaryDirectory

import os.path as p

from db import Session
from models.models import TrainingConfiguration
from s3.s3 import s3


async def train_yolo(conf_id: int,
                     db: Session):
    conf = db.query(TrainingConfiguration).filter_by(id=conf_id).first()
    if conf is None:
        raise
    yolo = YOLO(str(conf.model) + '.yaml')
    conf.status = 'processing'
    db.commit()

    with TemporaryDirectory(dir=os.getcwd()) as tmp:

        with open(tmp + f'/{conf.name}.zip', mode='w+b') as f:
            s3.download_file(f, conf.dataset_s3_location)

        with zipfile.ZipFile(tmp + f'/{conf.name}.zip', 'r') as f:
            f.extractall(path=tmp + '/dataset')

        with open(tmp + '/dataset/data.yaml', 'w') as f:
            classes = conf.training_conf['classes']
            names = [f'  {classes.index(name)}: {name}\n' for name in classes]
            f.writelines(['path: ' + tmp + '/dataset\n',
                          'train: train/images\n',
                          'val: val/images\n',
                          'names:\n'] + names)

        yolo.train(
            data=tmp + '/dataset/data.yaml',
            project=tmp,
            name=conf.name,
            epochs=conf.training_conf['epochs'],
            patience=conf.training_conf['patience'],
            batch=conf.training_conf['batch'],
            imgsz=conf.training_conf['imgsz'],
            optimizer=conf.training_conf['optimizer'],
            device=0
        )

        with zipfile.ZipFile(tmp + '/result.zip', 'w') as f:
            for dirname, subdirs, files in os.walk(tmp+f'/{conf.name}'):
                f.write(dirname)
                for filename in files:
                    f.write(p.join(dirname, filename))

        with open(tmp + '/result.zip', 'rb') as f:
            path = f'/user/{conf_id}/result/result.zip'
            s3.upload_file(f, path)

        conf.weight_s3_location = path

    conf.status = 'processed'
    db.commit()
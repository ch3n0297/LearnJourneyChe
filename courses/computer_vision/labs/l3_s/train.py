import os
import sys
from datetime import datetime
import numpy as np
import pandas as pd
from pandas import DataFrame
from sklearn.utils import shuffle
import matplotlib.pyplot as plt

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation
from tensorflow.keras.optimizers import Adam  # ← 改用 Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau  # ← 加上回調
from tensorflow.keras.losses import Huber
import tensorflow as tf

np.random.seed(42)
tf.random.set_seed(42)

FTRAIN = 'data/training.csv'
FTEST = 'data/test.csv'
FLOOKUP = 'data/IdLookupTable.csv'

def load(test=False, cols=None):
    """Loads data from FTEST if *test* is True, otherwise from FTRAIN.
    Pass a list of *cols* if you're only interested in a subset of the
    target columns.
    """
    fname = FTEST if test else FTRAIN
    df = pd.read_csv(fname)

    df['Image'] = df['Image'].apply(lambda im: np.fromstring(im, sep=' '))

    if cols:
        df = df[list(cols) + ['Image']]

    print(df.count())
    df = df.dropna()

    X = np.vstack(df['Image'].values) / 255.
    X = X.astype(np.float32)

    # zero-mean / unit-std normalization on top of /255
    X_mean = X.mean()
    X_std = X.std() + 1e-8
    X = (X - X_mean) / X_std

    if not test:
        y = df[df.columns[:-1]].values
        y = (y - 48) / 48
        X, y = shuffle(X, y, random_state=42)
        y = y.astype(np.float32)
    else:
        y = None

    return X, y

def load2d(test=False, cols=None):
    X, y = load(test=test, cols=cols)
    X = X.reshape(-1, 96, 96, 1)
    return X, y

def pixel_mae(y_true, y_pred):
    # convert normalized coords back to pixel space for a human-readable MAE
    y_true_px = y_true * 48.0 + 48.0
    y_pred_px = y_pred * 48.0 + 48.0
    return tf.reduce_mean(tf.abs(y_true_px - y_pred_px))

model = Sequential()
model.add(Dense(100, activation='relu', input_shape=(9216,)))
model.add(Dense(30))

# ======== 推薦的超參數 ========
# Optimizer: Adam, lr=1e-3, 並加上 clipnorm 避免不穩
adam = Adam(learning_rate=1e-3, beta_1=0.9, beta_2=0.999, epsilon=1e-7, clipnorm=1.0)

# Loss 維持 MSE（與你原設定一致）
model.compile(loss=Huber(delta=0.5), optimizer=adam, metrics=[pixel_mae])

model.summary()

X, y = load()

print("X.shape == {}; X.min == {:.3f}; X.max == {:.3f}".format(X.shape, X.min(), X.max()))
print("y.shape == {}; y.min == {:.3f}; y.max == {:.3f}".format(y.shape, y.min(), y.max()))

# ======== 訓練相關超參數 ========
batch_size = 64          # ← 256 改為 64
epochs = 300              # ← 100 改為 300（配合早停不會真的跑滿）
val_split = 0.25          # ← 0.2 改為 0.25

# ======== 回調：早停 + 自動降學習率 ========
callbacks = [
    EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience=4,
                      cooldown=1, min_lr=1e-6, verbose=1)
]

history = model.fit(
    X, y,
    batch_size=batch_size,
    epochs=epochs,
    validation_split=val_split,
    callbacks=callbacks,
    verbose=1
)

loss = history.history['loss']
val_loss = history.history['val_loss']

plt.plot(loss, linewidth=3, label='train')
plt.plot(val_loss, linewidth=3, label='valid')
plt.grid()
plt.legend()
plt.xlabel('epoch')
plt.ylabel('loss')
plt.ylim(1e-3, 1e-2)
plt.yscale('log')
plt.show()
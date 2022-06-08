"""tools.py
Some tools for you to read the input data
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt

DEFAULT_DATA_SPLITS = ['train', 'val', 'test', 'extra']
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def percent(num):
  return int(num * 10000) / 100

def todense(X):
  return X.todense()

def read_data(split = 'train', include_oos = True, include_mine = False):
  """read_data
  Read the data from the provided data files
  """
  if not split in DEFAULT_DATA_SPLITS:
    raise Exception(f'The data split must be one of {DEFAULT_DATA_SPLITS}')
  sentences, labels = [], []
  with open(os.path.join(DATA_PATH, f'is_{split}.json'), 'r') as f:
    data = json.load(f)
    for sentence, label in data:
      sentences.append(sentence)
      labels.append(label)
  if include_oos:
    with open(os.path.join(DATA_PATH, f'oos_{split}.json'), 'r') as f:
      data = json.load(f)
      for sentence, label in data:
        sentences.append(sentence)
        labels.append(label)
  if include_mine:
    with open(os.path.join(DATA_PATH, f'my_intents_{split}.json'), 'r') as f:
      data = json.load(f)
      for sentence, label in data:
        sentences.append(sentence)
        labels.append(label)
  return np.array(sentences), np.array(labels)

def labels(labels):
  return np.unique(labels)

def relabel(y, classes):
  return np.array([classes.index(y_i) for y_i in y])

def plot_learning_curve(train_sizes, train_scores, test_scores):
  """plot_learning_curve
  Plot the learning curves generated
  :param train_sizes: Array of training set sizes (n)
  :param train_scores: Raw array of training set scores (n, m)
  :param test_scores: Raw array of cross-validation set scores (n, m)
  """
  train_scores_mean = np.mean(train_scores, axis=1)
  train_scores_std = np.std(train_scores, axis=1)
  test_scores_mean = np.mean(test_scores, axis=1)
  test_scores_std = np.std(test_scores, axis=1)
  _, axes = plt.subplots(1, 1)
  axes.set_xlabel("% Training examples")
  axes.set_ylabel("Accuracy")
  axes.grid()
  # Plot the confidence intervals
  axes.fill_between(train_sizes, train_scores_mean - train_scores_std,
                         train_scores_mean + train_scores_std, alpha=0.1,
                         color="r")
  axes.fill_between(train_sizes, test_scores_mean - test_scores_std,
                         test_scores_mean + test_scores_std, alpha=0.1,
                         color="g")
  # Plot the mean acc. scores
  axes.plot(train_sizes, train_scores_mean, 'o-', color="r",
                 label="Training Acc.")
  axes.plot(train_sizes, test_scores_mean, 'o-', color="g",
                 label="Validation Acc.")
  axes.legend(loc="best")
  # Change this to the commented line to save the plot instead of showing it
  plt.show()

def accuracy(y_pred, y_test):
  return sum(1 for a, b in zip(y_pred, y_test) if a == b) / len(y_test)

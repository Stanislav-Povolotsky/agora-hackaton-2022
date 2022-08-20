import sys
import os
import re
import json
import sqlite3
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import numpy as np
import tensorflow as tf
from tensorflow import keras

try:
  from loader import *
except:
  from .loader import *

script_folder = os.path.dirname(os.path.realpath(__file__))
data_folder = os.path.join(script_folder, 'data')

# Loading network and weights and testing it
def load_model(file_base_name):
  with open(file_base_name + ".model.json", "rt") as f: model_json = f.read()
  model = tf.keras.models.model_from_json(model_json)
  model.load_weights(file_base_name + ".weights.h5")
  with open(file_base_name + ".classes.%s.json" % 'tags' , "rt") as f: all_tags_list_ = json.load(f)
  with open(file_base_name + ".classes.%s.json" % 'refs' , "rt") as f: all_refs_list_ = json.load(f)
  return model, all_tags_list_, all_refs_list_
  
model_name = "agora"
model, all_tags_list, all_refs_list = load_model(os.path.join(data_folder, model_name)) # "x.model.json", 'x.weights.h5'...
all_tags_list_map_tag_to_index = {v:i for i,v in enumerate(all_tags_list)}

def match_product__ml1(product):
  global model, all_tags_list, all_refs_list
  res = None

  tags = product.get_tags()
  x = np.zeros(len(all_tags_list))
  for tag in tags:
    if(tag in all_tags_list_map_tag_to_index):
      x[all_tags_list_map_tag_to_index[tag]] = 1

  out = model.predict(np.array([x,]))
  predicted_class = all_refs_list[np.argmax(out)]

  items_refs = get_items_refs()
  if(predicted_class in items_refs):
    res = items_refs[predicted_class]
  #print(res)

  return res

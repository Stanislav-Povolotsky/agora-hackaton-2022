import sys
import os
import re
import json
import os

print("Loading ML modules... ", end = "", flush = True)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import numpy as np
import tensorflow as tf
from tensorflow import keras
print("Done.", flush = True)

try:
  from loader import *
except:
  from .loader import *

# Вероятность, ниже которой товар считается не найденным
const_cut_propability = 0.15

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

if(True):  
  model_name = "agora"
  print("Loading model '%s'... " % model_name, end = "", flush = True)
  model, all_tags_list, all_refs_list = load_model(os.path.join(data_folder, model_name)) # "x.model.json", 'x.weights.h5'...
  all_tags_list_map_tag_to_index = {v:i for i,v in enumerate(all_tags_list)}
  print("Done.")

def match_products__ml1(products_group):
  global model, all_tags_list, all_refs_list
  res = None

  x_products = []
  n = len(products_group)
  for product in products_group:
    tags = product.get_tags()
    x = np.zeros(len(all_tags_list))
    for tag in tags:
      if(tag in all_tags_list_map_tag_to_index):
        x[all_tags_list_map_tag_to_index[tag]] = 1
    x_products.append(x)

  out = model.predict(np.array(x_products), use_multiprocessing=True, verbose=0)

  res_products = []
  items_refs = get_items_refs()
  for i in range(n):
    res = None
    idx_max = np.argmax(out[i])
    predicted_class = all_refs_list[idx_max]
    propability = out[i][idx_max]
    if(predicted_class and (predicted_class in items_refs)):
      res = items_refs[predicted_class]
      #print("Predicted class: %s with propability %.04f" % (res.pid, propability))
      res.propability = propability
      if(propability >= const_cut_propability):
        pass
      else:
        res = None
    res_products.append(res)
  #print(res)

  return res_products

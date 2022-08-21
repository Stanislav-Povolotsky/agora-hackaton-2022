try:
  from loader import *
  from ml_matcher import *
except:
  from .loader import *
  from .ml_matcher import *

from itertools import chain

def match_product__intersections(product):
  best = None
  best_matches = 0
  #pnt = product.name_tokens
  pnt = product.get_tags()

  refs = get_items_refs()
  for ref in refs.values():
    #rpnt = ref.name_tokens
    rpnt = ref.get_tags()
    i = rpnt.intersection(pnt)
    if(len(i) > best_matches):
      best = ref
      best_matches = len(i)
  res = best
  return res

def match_product__product_tags_weight(product):
  best = None
  best_weight = 0
  #pnt = product.name_tokens
  pnt = product.get_tags()

  refs = get_items_refs()
  for ref in refs.values():
    #rpnt = ref.name_tokens
    rpnt = ref.get_tags()
    its = rpnt.intersection(pnt)
    weight = 0.0
    for tag in its:
      weight += ref.tags_weight[tag]
    if(weight > best_weight):
      best = ref
      best_weight = weight
  res = best
  return res

def int_match_products(products_group):
  algo_type = 'ml'
  #algo_type = 'intersections'
  if(not products_group): return []
  if(algo_type == 'ml'):
    return match_products__ml1(products_group)
  elif(algo_type == 'intersections'):
    results = list([match_product__intersections(product) for product in products_group])
    return results
  elif(algo_type == 'product_tags_weight'):
    results = list([match_product__product_tags_weight(product) for product in products_group])
    return results
  else:
    raise Exception("Not implemented")

def match_products(products_to_match, test_mode = False):
  res = []
  chunk_size = 100
  cur_chunk = []
  #print(products_to_match)
  for citem in chain(load_items_on_demand(products_to_match), [None,]):
    if(citem):
      enrich_item(citem)
      cur_chunk.append(citem)
    if(len(cur_chunk) >= chunk_size) or (citem is None):
      cur_chunk_to_process = cur_chunk
      cur_chunk = []

      #schedule_match_product(cur_chunk)
      ritems = int_match_products(cur_chunk_to_process)
      for i in range(len(cur_chunk_to_process)):
        item = cur_chunk_to_process[i]
        ritem = ritems[i]
        r = {"id": item.pid, "reference_id": ritem.pid if ritem else None} 
        if(test_mode):
          r["reference_id_original"] = item.rid
        if(False): # Debug
          r["name"] = item.name
          if(ritem):
            r["ref-name"] = ritem.name
        res.append(r)


  return res

if __name__ == '__main__':
  with open(os.path.join(data_folder, "agora_hack_products.products.json"), "rt", encoding="utf8") as f:
    products = json.load(f)
  t_start = time.time()
  matched = match_products(products, test_mode = True)
  t_end = time.time()

  n_total = len(matched)
  n_correct = 0
  incorrect_items = []
  for item in matched:
    if item['reference_id'] == item['reference_id_original']:
      n_correct += 1
    else:
      incorrect_items.append(item)

  all_items_map = {v.pid: v for v in dbg_get_items_all()}

  with open(os.path.join(data_folder, "tmp.incorrect.detection.json"), "wt", encoding="utf8") as f:
    for ii in incorrect_items:
      if(ii['id'] in all_items_map):
        ii['name'] = all_items_map[ii['id']].name
      if(ii['reference_id'] in all_items_map):
        ii['name-incorrect'] = all_items_map[ii['reference_id']].name
      if(ii['reference_id_original'] in all_items_map):
        ii['name-correct'] = all_items_map[ii['reference_id_original']].name
    json.dump(incorrect_items, f, ensure_ascii=False, indent=4, sort_keys=True)

  print("Total:\t%u" % n_total)
  print("Correct:\t%u" % n_correct)
  print("Valid:\t%.02f%%" % (100.0 * n_correct / (n_total if n_total else 1)))
  print("Time:\t%.02f ms (%.02f ms per 100 items)" % (((t_end - t_start) * 1000.0), (t_end - t_start) * 1000.0 * 100.0 / n_total))

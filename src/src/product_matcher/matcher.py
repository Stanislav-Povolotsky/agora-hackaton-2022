if __name__ == '__main__':
  from loader import *
else:
  from .loader import *

def match_product(product):
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

def match_products(products_to_match, test_mode = False):
  res = []
  for item in load_items_on_demand(products_to_match):
    enrich_item(item)
    ritem = match_product(item)
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
  for item in matched:
    if item['reference_id'] == item['reference_id_original']:
      n_correct += 1
  print("Total:\t%u" % n_total)
  print("Correct:\t%u" % n_correct)
  print("Valid:\t%.02f%%" % (100.0 * n_correct / (n_total if n_total else 1)))
  print("Time:\t%.02f ms (%.02f ms per 100 items)" % (((t_end - t_start) * 1000.0), (t_end - t_start) * 1000.0 * 100.0 / n_total))

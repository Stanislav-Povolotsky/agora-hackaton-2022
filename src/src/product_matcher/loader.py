import json
import time
import re
import os

script_folder = os.path.dirname(os.path.realpath(__file__))
data_folder = os.path.join(script_folder, 'data')

#class CProp:
#  name = ""
#  values = set()

class CItem:
  pid = ""    # product_id
  rid = None  # reference_id
  name = ""
  props = []
  is_ref = False

  @staticmethod
  def create(obj):
    me = CItem()
    me.load(obj)
    return me

  def load(self, obj):
    self.pid    = obj['product_id'] if ('product_id' in obj) else obj['id']
    self.rid    = obj['reference_id'] if 'reference_id' in obj else None
    self.name   = obj['name'] if 'name' in obj else ""
    self.is_ref = (True if obj['is_reference'] else False) if 'reference_id' in obj else False
    self.props  = obj['props'] if 'props' in obj else []

  def save(self):
    obj = {}
    obj['id'] = self.pid
    obj['reference_id'] = self.rid
    obj['name'] = self.name
    obj['is_reference'] = self.is_ref
    obj['props'] = self.props
    return obj

  def save_ex(self):
    obj = self.save()
    if(hasattr(self, 'name_tokens')):
      obj['name_tokens'] = self.name_tokens
    if(hasattr(self, 'props_norm')):
      obj['props_norm'] = self.props_norm
    if(hasattr(self, 'tags_weight')):
      obj['tags_weight'] = self.tags_weight
    obj['tags'] = self.get_tags()
    return obj

  def get_tags(self):
    if(not hasattr(self, 'tags_cache')):
      tags = []
      if(hasattr(self, 'name_tokens')):
        tags.extend(list(self.name_tokens))
      if(hasattr(self, 'props_norm')):
        for k,vals in self.props_norm.items():
          tags.append(k)
          for v in vals:
            for vi in v.split(' '):
              tags.append("%s:%s" % (k,vi))
      tags = set(tags)
      self.tags_cache = tags
    return self.tags_cache

  def __repr__(self):
    return "%s%s (%s)" % (self.pid, "[REF]" if self.is_ref else "", self.name)

def load_items_json_full(s):
  items = json.loads(s)
  items = list([CItem.create(o) for o in items])
  return items

def load_items_json_on_demand(s):
  items = json.loads(s)
  for item in items:
    yield CItem.create(item)

def load_items_on_demand(items):
  for item in items:
    yield CItem.create(item)

def serialize_items(items, extended = False):
  items = list([(o.save() if not extended else o.save_ex()) for o in items])
  return items

class CPropsMgr:
  props = {} # name => CProp()

  def add(self, p_name, p_value = None):
    if not(p_name in self.props):
      self.props[p_name] = set()
    if(p_value):
      self.props[p_name].add(p_value)
      #print(self.props[p_name])
  def have(self, p_name):
     return p_name in self.props

class SetEncoder(json.JSONEncoder):
  def default(self, obj):
      if isinstance(obj, set):
          return list(obj)
      return json.JSONEncoder.default(self, obj)

g_props = CPropsMgr()

re_replace_space = re.compile("[ \t\r\n()\[\].\-+/,.]+")
re_list_splitter = re.compile("[^;,]+")

# lowercase, удаляем повторы символов, все пробельные символы заменяем на один пробел
# удаляем скобки и другие спец. символы
def normalize_str(s):
  s = re_replace_space.sub(' ', s)
  s = s.strip()
  s = s.lower()
  return s

def extract_eprops(sprop):
  spropn = normalize_str(sprop)
  tkn = spropn.split(' ')
  parts = 1
  p_name = tkn[0]
  p_values = set()
  while((parts + 1) < len(tkn)):
    cpart = " ".join(tkn[:parts + 1])
    if(g_props.have(cpart)):
      p_name = cpart
    parts += 1
  s = spropn[len(p_name):]
  m = re_list_splitter.findall(s)
  if(m):
    for cm in m:
      cm = normalize_str(cm)
      if(cm):
        p_values.add(cm)
  return (p_name, p_values)


def enrich_item(item):
  n = item.name
  n = normalize_str(n)
  ntokens = n.split(' ')
  #ntokens = list([t for t in ntokens if len(t) > 1])
  ntokens = set(ntokens)
  item.name_tokens = ntokens
  
  item.props_norm = {} # name => values
  for p in item.props:
    (p_name, p_values) = extract_eprops(p)
    item.props_norm[p_name] = p_values

g_items_refs = []
g_items_all = []
def get_items_refs():
  return g_items_refs

def matches_loader(generate_debug_files = False):
  with open(os.path.join(data_folder, "agora_hack_products.json"), "rt", encoding="utf8") as f:
    json_s = f.read()

  items_products = []
  items_refs = {}
  items_all = []
  for item in load_items_json_on_demand(json_s):
    if(item.is_ref):
      items_refs[item.pid] = item
    else:
      items_products.append(item)
    items_all.append(item)

  if(generate_debug_files):
    with open(os.path.join(data_folder, "agora_hack_products.refs.json"), "wt", encoding="utf8") as f:
      json.dump(serialize_items(items_refs.values()), f, ensure_ascii=False, indent=4, sort_keys=True)
    with open(os.path.join(data_folder, "agora_hack_products.products.json"), "wt", encoding="utf8") as f:
      json.dump(serialize_items(items_products), f, ensure_ascii=False, indent=4, sort_keys=True)

  # Шаг 1: обрабатываем props, находим разделённые tab'ом - будем считать то, что до tab'а - нормальным именем
  for item in items_refs.values():
    for p in item.props:
      #pos = p.index("\t") if ("\t" in p) else (p.index(":") if (":" in p) else None)
      pos = p.index("\t") if ("\t" in p) else None
      if not(pos is None):
        p_name = normalize_str(p[:pos])
        p_values = p[pos + 1:]
        m = re_list_splitter.findall(p_values)
        g_props.add(p_name)
        if(m):
          for cm in m:
            cm = normalize_str(cm)
            if(cm):
              g_props.add(p_name, cm)

  # Шаг 2: обрабатываем props остальных эталонов
  for item in items_refs.values():
    for p in item.props:
      (p_name, p_values) = extract_eprops(p)
      g_props.add(p_name)
      for pv in p_values:
        g_props.add(p_name, pv)
  
  if(generate_debug_files):
    with open(os.path.join(data_folder, "res.found-props.json"), "wt", encoding="utf8") as f:
      json.dump(g_props.props, f, ensure_ascii=False, indent=4, sort_keys=True, cls=SetEncoder)
  
  for item in items_all:
    enrich_item(item)

  # Считаем уникальность тэгов для каждого продукта
  tag_stats_all = {}           # tag => count                    (общее количество каждых тэгов)
  tag_stats_product = {}       # product => {tag => count}       (количество каждого тега для каждого продукта)
  name_tag_stats_product = {}  # product => {name_tag => count}  (количество каждого тега для каждого продукта (только для именных тэгов))
  product_count = {}           # pid => count                    (сколько продуктов каждого типа)
  tag_products = {}            # tag => set(pids)                (список продуктов для каждого тэга)

  for item in items_all:
    item_name_tags = set(item.name_tokens)
    rid = item.pid if item.is_ref else item.rid
    if not(rid in product_count): product_count[rid] = 0
    #print(item)
    item_ref = items_refs[rid]

    product_count[rid] += 1
    if not(rid in tag_stats_product): tag_stats_product[rid] = {}
    tag_stats_product_cur = tag_stats_product[rid]
    if not(rid in name_tag_stats_product): name_tag_stats_product[rid] = {}
    name_tag_stats_product_cur = name_tag_stats_product[rid]
    for tag in item.get_tags():
      if not(tag in tag_stats_product_cur): tag_stats_product_cur[tag] = 0
      tag_stats_product_cur[tag] += 1
      if(tag in item_name_tags):
        if not(tag in name_tag_stats_product_cur): name_tag_stats_product_cur[tag] = 0
        name_tag_stats_product_cur[tag] += 1
      if not(tag in tag_stats_all): tag_stats_all[tag] = 0
      tag_stats_all[tag] += 1
      if not(tag in tag_products): tag_products[tag] = set()
      tag_products[tag].add(rid)

  # Проставляем веса каждого тэго для каждого продукта
  name_tag_base_weight = 1.0
  prop_tag_base_weight = 1.0
  ref_tag_base_coef = 2.0 # дополнительный коффициент для тэгов, принадлежащий референсному товару
  for rid,p_count in product_count.items():
    item_ref = items_refs[rid]
    item_ref_tags = set(item_ref.get_tags())
    if(not hasattr(item_ref, 'tags_weight')): item_ref.tags_weight = {}
    tag_stats_product_cur = tag_stats_product[rid]
    name_tag_stats_product_cur = name_tag_stats_product[rid]

    name_tag_count = len(name_tag_stats_product_cur)
    total_tag_count = len(tag_stats_product_cur)
    prop_tag_count = total_tag_count - name_tag_count

    name_tag_cur_base_weight = name_tag_base_weight / name_tag_count
    prop_tag_cur_base_weight = prop_tag_base_weight / prop_tag_count
    for tag, t_count in tag_stats_product_cur.items():
      # Вычисляем вес тэга, как количество таких тэгов найденных ранее в продуктах этого типа / количество ссылок на продукт этого типа / количество продуктов с таким тэгом
      n_products_with_this_tag = len(tag_products[tag])
      tag_weight_product = t_count / p_count / n_products_with_this_tag
      #tag_weight_product = t_count / p_count

      # Умножаем на базовый вес конкретного тэга для продукта
      is_name_tag = tag in name_tag_stats_product_cur
      cur_tag_cur_base_weight = name_tag_cur_base_weight if is_name_tag else prop_tag_cur_base_weight

      is_ref_tag = tag in item_ref_tags
      ref_tag_coef = ref_tag_base_coef if is_ref_tag else 1.0
      #ref_tag_coef = 1.0

      tag_weight_product = tag_weight_product * cur_tag_cur_base_weight  * ref_tag_coef

      item_ref.tags_weight[tag] = tag_weight_product
      
  #print("Added props:", len(g_props.props))

  if(generate_debug_files):
    with open(os.path.join(data_folder, "agora_hack_products.products.extended.json"), "wt", encoding="utf8") as f:
      json.dump(serialize_items(items_products, extended = True), f, ensure_ascii=False, indent=4, sort_keys=True, cls=SetEncoder)
    with open(os.path.join(data_folder, "agora_hack_products.refs.extended.json"), "wt", encoding="utf8") as f:
      json.dump(serialize_items(items_refs.values(), extended = True), f, ensure_ascii=False, indent=4, sort_keys=True, cls=SetEncoder)
    with open(os.path.join(data_folder, "agora_hack_products.all.extended.json"), "wt", encoding="utf8") as f:
      json.dump(serialize_items(items_all, extended = True), f, ensure_ascii=False, indent=4, sort_keys=True, cls=SetEncoder)
  
  """
  defered_free = []
  start = time.time()
  for test in range(300):
    items = load_items_json_full(json_s)
    #for i in load_items_json_on_demand(json_s): pass
  end = time.time()
  print('Load time:', end - start)
  
  """
  global g_items_refs
  g_items_refs = items_refs

  global g_items_all
  g_items_all = items_all

matches_loader(generate_debug_files = (__name__ == '__main__'))
if __name__ == '__main__':
  pass

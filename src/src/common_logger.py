import sys
import logging
import logging.handlers
import os

script_folder = os.path.dirname(os.path.realpath(__file__))
app_folder = os.path.join(script_folder, "..")
data_folder = os.path.join(app_folder, "data")
logs_folder = os.path.join(app_folder, "logs")

log = logging.getLogger('current-app')
#logs_folder = None
logs_appname = ''

# add this task to allow script to exit using Ctrl+C
async def ctrl_c_checker():
  while(True):
    await asyncio.sleep(2.0)

def get_logs_folder():
  global logs_folder
  return logs_folder

def set_logs_folder(logs_folder_arg):
  global logs_folder
  logs_folder = logs_folder_arg

def set_logs_app_name(app_name):
  global logs_appname
  logs_appname = app_name

def get_log_file_path():
  global logs_appname
  an = '' if (logs_appname is None) else '-%s' % logs_appname
  return os.path.join(get_logs_folder(), "log%s.log" % an) if (get_logs_folder()) else None

def setup_logger(logs_folder, app_name, level = logging.DEBUG, log_to_stdout = False, log_to_file = True, log_to_stdout_if_no_file = True, log_rotate = True, log_rotate_backups = 5, log_rotate_size = 1024 * 1024 * 100, modules_to_include = [], init_default_logger = False):
  global log
  set_logs_folder(logs_folder)
  set_logs_app_name(app_name)
  all_loggers = []

  if(init_default_logger):
    all_loggers.append(None)
  all_loggers.append('current-app')
  all_loggers.extend(modules_to_include)

  #logger.setLevel(logging.INFO)
  #logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(asctime)s | %(levelname)-5s | %(message)s', 
                              '%m-%d-%Y %H:%M:%S')

  stdout_handler = logging.StreamHandler(sys.stdout)
  stdout_handler.setLevel(logging.DEBUG)
  stdout_handler.setFormatter(formatter)

  log_fpath = get_log_file_path()
  if(log_to_file and log_fpath):
    if(log_rotate):
      file_handler = logging.handlers.RotatingFileHandler(
        log_fpath, maxBytes=log_rotate_size, backupCount=log_rotate_backups)
    else:
      file_handler = logging.FileHandler(log_fpath, 'a', 'utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
  else:
    file_handler = None

  for cur_log in all_loggers:
    logger = logging.getLogger(cur_log)
    logger.setLevel(level)
  
    if(file_handler):
      logger.addHandler(file_handler)
    if log_to_stdout or (log_to_stdout_if_no_file and not(file_handler)):
      logger.addHandler(stdout_handler)

if(logs_folder):
  setup_logger(logs_folder, 'current-app')
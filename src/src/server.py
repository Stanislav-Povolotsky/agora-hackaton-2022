import time
import os
import aiohttp.web
import argparse
import sys
import traceback
import json
from common_logger import log
from product_matcher import match_products

script_folder = os.path.dirname(os.path.realpath(__file__))

async def options_handler(req_obj):
  return aiohttp.web.Response(status=204) # No content

async def index(request):
    return aiohttp.web.FileResponse(os.path.join(script_folder, 'static/index.html'))

async def on_prepare_append_allow_cors(request, response):
  response.headers['Access-Control-Allow-Origin'] = '*'
  response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
  response.headers['Access-Control-Allow-Headers'] = '*'
  response.headers['Access-Control-Expose-Headers'] = '*'
  response.headers['Cache-Control'] = 'no-cache'

async def handle_match_products(request):
  res = []
  response = None
  try:
    start_req = time.time()
    req = await request.json()

    start_match = time.time()
    res = match_products(req)
    end_match = time.time()

    response = aiohttp.web.json_response(res)
    end_req = time.time()
    log.info('Match time: %.2f ms; Full time: %.2f ms' % (((end_match - start_match) * 1000.0), ((end_req - start_req) * 1000.0)))

  except Exception as e:
    res = {"error": {"text": str(e)}}
    log.error("Error %s: %s" % (e,  traceback.print_exc()))
  return response

def main():
  sys.stdout.reconfigure(encoding='utf-8')

  parser = argparse.ArgumentParser(description="web server")
  parser.add_argument('--port', default="8100", type=int)
  args = parser.parse_args()

  app = aiohttp.web.Application(client_max_size = 1024 * 1024 * 100)
  app.add_routes([aiohttp.web.get('/', index),
                  aiohttp.web.post('/match_products', handle_match_products),])
  app.router.add_static('/', path=os.path.join(script_folder, 'static/'), name='root')
  app.router.add_static('/static/', path=os.path.join(script_folder, 'static/'), name='static')
  app.router.add_static('/dist/', path=os.path.join(script_folder, 'static/'), name='dist')
  app.on_response_prepare.append(on_prepare_append_allow_cors)
  app.router.add_options("/{tail:.*}", options_handler)
  aiohttp.web.run_app(app, port=args.port)

if __name__ == '__main__':
  main()

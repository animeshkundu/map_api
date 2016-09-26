#!/usr/bin/env python

from gevent import monkey
monkey.patch_all()

import re
import json
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import concurrent.futures

from msp_scraper_lib.base import SmartPrice

# import and define tornado-y things
from tornado.options import define
define("port", default=int(os.environ.get('PORT', 5000)), help="run on the given port", type=int)


# application settings and handle mapping info
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", PingHandler),
            (r"/ping", PingHandler),
            (r"/pricesearch", SearchPriceHandler),
            (r"/sellersearch", SearchSellerHandler),
            (r"/fetchproduct", FetchProductHandler),
            (r"/fetchseller", FetchSellerHandler),
            (r"/matchproduct", MatchProductHandler),
        ]
        settings = dict(debug=True)
        tornado.web.Application.__init__(self, handlers, **settings)


class PingHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.write("Everything's okay")

    def post(self) :
        self.get()


class FetchProductHandler(tornado.web.RequestHandler) :
    executor = concurrent.futures.ThreadPoolExecutor(max_workers = 10)

    @tornado.concurrent.run_on_executor
    def fetch(self, url) :
        response = []

        if url:
            sp = SmartPrice()
            results = sp.list(url)

            for r in results :
                response.append(r.dumptojson)

        return response

    @tornado.gen.coroutine
    def get(self) :
        url = self.get_query_argument('url', None)
        response = yield self.fetch(url)
        self.write(json.dumps(response))

    def post(self) :
        self.get()


class FetchSellerHandler(tornado.web.RequestHandler) :
    executor = concurrent.futures.ThreadPoolExecutor(max_workers = 100)

    @tornado.concurrent.run_on_executor
    def fetch(self, pid = None, url = None) :
        response = []
        results = []
        sp = SmartPrice()
        
        if pid :
            purl = sp.pidurl(pid)
            results = sp.seller(purl)
        elif url :
            results = sp.seller(url)

        for r in results :
            response.append(r.dumptojson)

        return response

    @tornado.gen.coroutine
    def get(self) :
        msp_id = self.get_query_argument('msp_id', None)
        url = self.get_query_argument('url', None)
        response = yield self.fetch(msp_id, url)
        self.write(json.dumps(response))

    def post(self) :
        self.get()


class SearchPriceHandler(tornado.web.RequestHandler) :
    executor = concurrent.futures.ThreadPoolExecutor(max_workers = 10)

    @tornado.concurrent.run_on_executor
    def search(self, name) :
        response = []

        if name :
            sp = SmartPrice()
            results = sp.search(name)

            for r in results :
                response.append(r.dumptojson)

        return response
   
    @tornado.gen.coroutine
    def get(self) :
        name = self.get_query_argument('name', None)
        response = yield self.search(name)
        self.write(json.dumps(response))

    def post(self) :
        self.get()


class SearchSellerHandler(tornado.web.RequestHandler) :
    executor = concurrent.futures.ThreadPoolExecutor(max_workers = 10)

    @tornado.concurrent.run_on_executor
    def search(self, name) :
        response = []

        if name :
            sp = SmartPrice()
            results = sp.sellers(name)

            for r in results :
                response.append(r.dumptojson)

        return response

    @tornado.gen.coroutine
    def get(self) :
        name = self.get_query_argument('name', None)
        response = yield self.search(name)
        self.write(json.dumps(response))

    def post(self) :
        self.get()


class MatchProductHandler(tornado.web.RequestHandler) :
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=100)

    @tornado.concurrent.run_on_executor
    def get_matches(self, name) :
        response = []
        results = []

        if name :
            sp = SmartPrice()
            product_url = sp.match(name)
            mspid = re.search('.*msp(\d*)$', product_url)
            if mspid :
                pid = mspid.group(1)
                url = sp.pidurl(pid)
                results = sp.seller(url)
            elif product_url :
                results = sp.seller(product_url)
                
            for r in results :
                response.append(r.dumptojson)
        return response

    @tornado.gen.coroutine
    def get(self) :
        name = self.get_query_argument('name', None)
        response = yield self.get_matches(name)
        self.write(json.dumps(response))

    def post(self):
        self.get()


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()


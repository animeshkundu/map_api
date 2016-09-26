#!/usr/bin/env python

from gevent import monkey
monkey.patch_all()

import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

import json
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
    def fetch(self, url) :
        response = []

        if url :
            sp = SmartPrice()
            results = sp.seller(url)

            for r in results :
                response.append(r.dumptojson)

        return response

    @tornado.gen.coroutine
    def get(self) :
        msp_id = self.get_query_argument('msp_id', None)
        response = []
        if msp_id :
            url = 'http://www.mysmartprice.com/mobile/ptrows_details.php?mspid=' + str(msp_id) + '&data=table'
        else :
            url = self.get_query_argument('url', None)
        response = yield self.fetch(url)
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


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()


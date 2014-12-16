import tornado.ioloop
import tornado.web
import logging
import logging.handlers

from datetime import date
import tornado.escape

 
class VersionHandler(tornado.web.RequestHandler):
    def get(self):
        response = { 'version': '3.5.1',
                     'last_build':  date.today().isoformat() }
        self.write(response)
 
class GetGameByIdHandler(tornado.web.RequestHandler):
    def get(self, id):
        response = { 'id': int(id),
                     'name': 'Crazy Game',
                     'release_date': date.today().isoformat() }
        self.write(response)
 
application = tornado.web.Application([
    (r"/getgamebyid/([0-9]+)", GetGameByIdHandler),
    (r"/version", VersionHandler)
])
 
if __name__ == "__main__":
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()
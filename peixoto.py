import sys

# import para o autobahn
from autobahn.twisted.component import Component
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.task import react
from twisted.web import server, resource
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

# import do controlador do raspi
import controlraspi as app

# cria servidor para recerber msg dos componentes remotos
class Simple(resource.Resource):
    isLeaf = True
    controller = None

    def render_GET(self, request):
        if self.controller:
            self.controller.remote_state(request.args)
        return b"OK"
    
    # def render_POST(self, request):
    #     with open(request.args['filename'][0], 'wb') as fd:
    #         fd.write(request.content.read())
    #     request.setHeader('Content-Length', os.stat(request.args['filename'][0]).st_size)
    #     with open(request.args['filename'][0], 'rb') as fd:
    #         request.write(fd.read())
    #     request.finish()
    #     return server.NOT_DONE_YET


# objeto que envia msg para os dispositivos remotos
class Requests():
    def __init__(self, reactor):
        self.agent = Agent(reactor)
        self.d = None
        
    def get_request(self, url):    
        self.d = self.agent.request(
            b'GET', url,
            Headers(),
            None)
        self.d.addCallback(self.cbRequest)
        return self.d

    def cbRequest(self, response):
        print('Response version:', response.version)
        print('Response code:', response.code)
        print('Response phrase:', response.phrase)
        self.d = readBody(response)
        self.d.addCallback(self.cbBody)
        return self.d

    def cbBody(self, body):
        print('Response body:')
        print(body)

@inlineCallbacks
def main(reactor, teste):
    wsurl = u"ws://localhost/ws"
    if acesso_remoto:
        wsurl = u"ws://201.131.170.231:8080/ws"
        # wsurl = u"ws://192.168.1.70/ws"
    print('host:', wsurl)

    # configuração do cliente WAMP
    component = Component(
        transports=[
            {
                u"url": wsurl,

                # you can set various websocket options here if you want
                u"max_retries": -1,
                u"initial_retry_delay": 5,
                u"options": {
                    u"open_handshake_timeout": 30,
                }
            },
        ],
        realm=u"realm1",
        authentication={
            u"wampcra": {
                u"authid": u"raspi",
                u"secret": "1234"
            }
        }
    )

    # cria app principal
    controller = app.Controlraspi(component, reactor, teste=teste)

    # we don't *have* to hand over control of the reactor to
    # component.run -- if we don't want to, we call .start()
    # The Deferred it returns fires when the component is "completed"
    # (or errbacks on any problems).
    comp_d = controller._wamp.start(reactor)

    # inicia servidor para escutar a rede local
    # serve para controlar outros dispositivos por wifi
    # local_server = LocalServer()
    # local_server.controller = controller
    local_server = Simple()
    local_server.controller = controller
    site = server.Site(local_server)
    reactor.listenTCP(8080, site)

    # When not using run() we also must start logging ourselves.
    import txaio
    txaio.start_logging(level='info')

    # If the Component raises an exception we want to exit. Note that
    # things like failing to connect will be swallowed by the
    # re-connection mechanisms already so won't reach here.

    def _failed(f):
        print("Component failed: {}".format(f))
        done.errback(f)
    comp_d.addErrback(_failed)

    # wait forever (unless the Component raises an error)
    done = Deferred()
    yield done

if __name__ == '__main__':
    teste = ('teste' in sys.argv)
    acesso_remoto = ('remoto' in sys.argv)

    try:
        react(main, [teste])
    except (KeyboardInterrupt, SystemExit) as e:
        app.exit(e)
    except Exception as e:
        app.exit(e)

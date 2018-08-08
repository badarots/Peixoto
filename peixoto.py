import sys

# import para o autobahn
from autobahn.twisted.component import Component
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.task import react

# import do controlador do raspi
import controlraspi as app


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

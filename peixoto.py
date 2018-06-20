import sys

# import para o autobahn
from autobahn.twisted.component import Component
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.task import react

# import para o APScheler
from apscheduler.schedulers.twisted import TwistedScheduler

# import do controlador do raspi
from controlraspi import Controlraspi


@inlineCallbacks
def main(reactor, controller, component, scheduler):

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
        # configuração do cliente WAMP
    component = Component(
        transports=[
            {
                u"url": u"ws://hackerspace.if.usp.br/crossbar/ws",
                # you can set various websocket options here if you want
                u"max_retries": -1,
                u"initial_retry_delay": 5,
                u"options": {
                    u"open_handshake_timeout": 30,
                }
            },
        ],
        realm=u"realm1",
    )

    # criação do scheduler
    scheduler = TwistedScheduler()

    try:
        arg = sys.argv[1]
    except Exception:
        arg = None

    if arg == 'raspi':
        teste = False
        print('GPIO habilitados')
    else:
        teste = True
        print('Rodando em modo de teste, GPIO desbilitados')

    # cria app principal
    controller = Controlraspi(component, scheduler, teste=teste)

    try:
        react(main, [controller, component, scheduler])
    except (KeyboardInterrupt, SystemExit):
        controller.cleanup()
        print('Desligamento: tchau!')

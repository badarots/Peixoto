import sys
import asyncio

# import para o autobahn
from autobahn.asyncio.component import Component
import txaio
import signal
from functools import partial

# import do controlador do raspi
import controlador

def main(loop, components, teste):

    txaio.start_logging(level='info')
    log = txaio.make_logger()

    async def exit():
        return loop.stop()

    def nicely_exit(signal):
        log.info("Shutting down due to {signal}", signal=signal)

        controlador.stop(signal)

        for task in asyncio.Task.all_tasks():
            task.cancel()
        asyncio.ensure_future(exit())

    loop.add_signal_handler(signal.SIGINT, partial(nicely_exit, 'SIGINT'))
    loop.add_signal_handler(signal.SIGTERM, partial(nicely_exit, 'SIGTERM'))

    controlador.start(loop, component, teste)
    # returns a future; could run_until_complete() but see below
    component.start(loop)

    try:
        print('loop run_forever')
        loop.run_forever()
        # this is probably more-correct, but then you always get
        # "Event loop stopped before Future completed":
        # loop.run_until_complete(f)
    except asyncio.CancelledError:
        pass

    loop.close()


teste = ('teste' in sys.argv)
acesso_remoto = ('remoto' in sys.argv)

wsurl = "ws://localhost/ws"
if acesso_remoto:
    wsurl = "ws://201.131.170.231:8080/ws"
    # wsurl = u"ws://192.168.1.70/ws"
print('host:', wsurl)

component = Component(
    transports=[
        {
            "url": wsurl,

            # you can set various websocket options here if you want
            "max_retries": -1,
            "initial_retry_delay": 5,
            "options": {
                "open_handshake_timeout": 30,
            }
        },
    ],
    realm="realm1",
    authentication={
        "wampcra": {
            "authid": "raspi",
            "secret": "1234"
        }
    }
)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    main(loop, component, teste)

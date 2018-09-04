import os
import json

import datetime as dt
import asyncio

# import para o APScheler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger

# import da estrutura de metodos de escrita no banco de dados
import banco_de_dados as db

# import do biblioteca mqtt
import paho.mqtt.client as mqtt

# encontra o diretorio atual, onde serão escrito os arquivos necessários
path = os.path.dirname(os.path.realpath(__file__))

# carrega arquivo de configurações
with open(path + '/controlador.json') as f:
    conf = json.load(f)

output_pins = {key: val for key, val in conf["saidas"].items() if type(val) == int}
input_pins = {key: val for key, val in conf["entradas"].items() if type(val) == int}
habilitar_pins = {'aerador': 8}

estado = {x: False for x in conf["entradas"]}
sensor_pins = conf["sensores"]

gpio = None

# criação do scheduler
scheduler = AsyncIOScheduler()
# configurações do scheduler
scheduler = scheduler
scheduler.add_jobstore('sqlalchemy', engine=db.engine)

# variáveis globais
dispositivo = None
agenda = None
wamp_comp = None
wamp_session = None
mqtt_client = None
loop = None

def start(event_loop, wamp, teste=False):
    global dispositivo, agenda, wamp_comp, wamp_session, mqtt_client, loop

    estado["controlador"] = True

    agenda = db.recupera_agenda()

    # wamp config
    wamp_session = None  # "None" while we're disconnected from WAMP router
    wamp_comp = wamp
    # associate ourselves with WAMP session lifecycle
    wamp_comp.on('join', wamp_initialize)
    wamp_comp.on('leave', wamp_uninitialize)

    loop = event_loop

    # configura pinos do raspberry
    if teste:
        modo = 'Rodando em modo de teste, GPIO desbilitados'
        dispositivo = u'teste'
    else:
        modo = 'GPIO habilitados'
        config_gpio()
        # configura interruptores
        for val in input_pins.values():
            if type(val) == int:
                gpio.add_event_detect(
                    val, gpio.BOTH, callback=input_state_thread,
                    bouncetime=300)

        dispositivo = u'raspi'
    dispositivo = u'com.' + dispositivo

    wamp_comp._transports
    db.log('app', u'inicialização', msg=modo)

    scheduler.start()

    if not teste:
        # configura cliente mqtt para se comunicar com componentes remotos pela rede
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = mqtt_initialize
        mqtt_client.on_message = mqtt_message

        mqtt_client.connect("127.0.0.1", 1883, 60)
        mqtt_client.loop_start()

    # lê sensor dht a cada meia hora: temperatura e umidade
    if not teste and "dht22" in conf["sensores"]:
        config_dht()


def stop(exception):
    db.log('app', 'desligamento', msg=str(exception), nivel='erro')
    db.log('app', 'desligamento', msg='limpando pinos')

    if wamp_session:
        wamp_session.leave()

    if mqtt_client:
        mqtt_client.disconnect()
        mqtt_client.loop_stop()

    if gpio:
        gpio.cleanup()


async def repeating_call(interval, f, *args):
    while True:
        f(*args)
        await asyncio.sleep(interval)


async def wamp_initialize(session, details):
    global wamp_session

    # print("Connected to WAMP router")
    db.log('conexao', 'conectado')
    wamp_session = session

    # reseta valores de reconexão
    # está mal implementado, se houver mais de um transport não saberei
    # reseta. tenho que encontrar o transporte em uso na conexão
    print("resetando valores de reconexão")
    wamp_comp._transports[0].reset()

    try:
        await session.register(atualizar, dispositivo + u'.atualizar')
        await session.register(update_status, dispositivo + u'.status')
        await session.register(ativar, dispositivo + u'.ativar')

        # print("procedimentos registrados")
        db.log('conexao', 'registro', msg='procedimentos registrados')
    except Exception as e:
        # print("Erro: não for possível registrar os procedimentos: {0}".format(e))
        db.log('conexao', 'registro', msg=str(e), nivel='erro')


def wamp_uninitialize(session, reason):
    global wamp_session

    # print(session, reason)
    # print("Lost WAMP connection")
    db.log('conexao', 'desconectado', msg=reason.message, nivel='alerta')

    wamp_session = None


def mqtt_initialize(client, userdata, flags, rc):
    client.subscribe("tratador")

    loop.create_task(repeating_call(300, mqtt_sendstatus))

    db.log("mqtt", "conectado", msg=str(rc))


def mqtt_message(client, userdata, msg):
    db.log("mqtt", "mensagem", msg="topico: {}, msg: {}".format(msg.topic, msg.payload))


def mqtt_sendstatus():
    while True:
        status = 'on' if (estado["controller"]) else 'off'
        mqtt_client.publish("controlador", status)


# procedimento que envia agenda atual para quem requisitou
def update_status(info):

    def dumpMsg(entrada):
        # formato de entrada {'atuador': [[param1, param2], ...], ...}
        # formato de saida {'atuador': {'0': [param1, param2], ...}, ...}
        saida = {}
        for atuador in entrada:
            agenda = entrada[atuador]
            atuador_saida = {}
            for i in range(len(agenda)):
                evento = agenda[i]
                a = atuador_saida[str(i)] = []
                for v in evento:
                    if type(v) == float:
                        a.append(str(v))
                    elif type(v) == dt.time:
                        a.append(v.strftime('%H:%M'))

            saida[atuador] = atuador_saida
        return json.dumps(saida)

    msg = None
    if info == "agenda":
        msg = dumpMsg(agenda)
    elif info == "estado":
        msg = json.dumps(estado)
    elif info == "sensores":
        msg = json.dumps(db.ultimo_dht(), cls=DateTimeEncoder)
    return msg


def send_update(info):
    msg = update_status("estado")
    if wamp_session is None:
        db.log('conexao', 'envia status', msg='desconectado', nivel='erro')
    else:
        wamp_session.publish(dispositivo + ".componentes", msg)
        db.log('conexao', 'envia status', msg='enviado {}: {}'.format(info, msg))


# lida com mudanças no estado dos pinos de entrada
def input_state_thread(channel):
    """essa função é chamada por uma thread que observa a mudança nos estados dos pinos
     ela nao pode executar diretamente funcoes do twisted, entao essa funcao envia
     a funcao input_state para ser executado no loop do reator"""

    asyncio.run_coroutine_threadsafe(input_state(channel), loop=loop)

async def input_state(channel):
    # esse tempo de espera serve para assegurar que o estado lido é o final
    # já que ele pode variar rapidamente e muitas vezes quando o contactor liga e desliga

    await asyncio.sleep(0.1)

    modulo = None
    for key, value in input_pins.items():
        if value == channel:
            modulo = key

    # atualiza o estado dos pinos na memoria
    estado[modulo] = not gpio.input(channel)
    print("input changed: {}: {}".format(modulo, estado[modulo]))
    # envia atualizacao
    send_update("estado")


# lida com mudança de estado de pinos de saida
def output_state(payload):
    for key in payload:
        estado[key] = payload[key]
    send_update("estado")


# lida com as mudancas de estado de modulos remotos (obsoleto)
def remote_state(payload):
    mudanca = False
    if b'tratador_presenca' in payload:
        mudanca = True
        print("Prensenca no tratador")
        estado['presenca_tratador'] = dt.datetime.now().isoformat()

    if b'tratador_motor' in payload:
        mudanca = True
        print('Tratador ligado: {}'.format(payload[b'tratador_motor'][0]))
        if payload[b'tratador_motor'][0] == b'true':
            estado['tratador'] = True
        else:
            estado['tratador'] = False

    # envia novo status de dispositvos para
    if mudanca and wamp_session:
        send_update("estado")
        # msg = json.dumps(estado)
        # url = dispositivo + ".componentes"
        # yield wamp_session.publish(url, msg)
        # db.log('publicacao', url, msg='enviado: ativo')


# liga e desliga os componentes a pedido do cliente
def ativar(payload):
    try:
        msg = json.loads(payload)
    except Exception:
        db.log('mensagem', 'ativacao',
               msg='Formato de msg nao suportada: ' + str(payload), nivel='alerta')
    else:
        db.log('mensagem', 'ativacao', msg=str(msg))

        if 'aerador' in msg:
            if msg['aerador']:
                ligar_aerador()
            else:
                desligar_aerador()

        if 'refletor' in msg:
            if msg['refletor']:
                ligar_refletor()
            else:
                desligar_refletor()

        if 'tratador' in msg:
            iniciar_tratador(msg['tratador'])

        if 'teste' in msg:
            digitalWrite('teste', msg['teste'])
            output_state({'teste': msg['teste']})

        if 'controlador' in msg:
            estado['controlador'] = msg['controlador']

            mqtt_sendstatus() if mqtt_client else None
            for pin in habilitar_pins.values():
                digitalWrite(pin, estado['controlador'])

            send_update('estado')


# Recebe dados, valida e os executa
def atualizar(payload):

    def load_msg(message):
        # Tenta converter a mensagem em um dict
        kw = json.loads(message)
        schedule = {}

        # recebe um json string, valida os dados e converte o string em float e
        # datetime.time
        # formato esperado kw = {'atuador1': [[param1, param2], ...], ...}
        def parseList(kw, valid_options):
            sched = []

            for value in kw.values():
                if len(value) != len(valid_options):
                    raise ValueError('há campos não preenchidos')

                alarme = []
                for i in range(len(value)):
                    if valid_options[i] == 'tempo':
                        formato = '%H'
                        if ':' in value[i]:
                            formato = '%H:%M'
                        try:
                            t = dt.datetime.strptime(value[i], formato).time()
                            alarme.append(t)
                        except Exception:
                            raise ValueError("formato inválido para hora:", value[i])

                    elif valid_options[i] == 'float':
                        try:
                            x = float(value[i].replace(',', '.'))
                            alarme.append(x)
                        except Exception:
                            raise ValueError("formato inválido para número:", value[i])

                sched.append(alarme)
            return sched

        # verifica se o tipo de msg enviada é suportada
        valid_msg = ['tratador', 'aerador', 'leds']

        for k in kw:
            if k not in valid_msg:
                raise ValueError("mensagens do tipo '{}' não são suportadas".format(k))

            # procura pelas informações contidadas em cada tipo de msg
            # e define o formato da lista final de agendamentos usando
            # o formato de valid_options
            elif k == 'aerador':
                valid_options = ['tempo', 'tempo']
                schedule['aerador'] = parseList(kw[k], valid_options)

            elif k == 'tratador':
                valid_options = ['tempo', 'float']
                schedule['tratador'] = parseList(kw[k], valid_options)

            elif k == 'leds':
                schedule['leds'] = None

        return schedule

    resposta = ''

    try:
        nova_agenda = load_msg(payload)
    except Exception as e:
        resposta += 'Alerta, mensagem: ' + str(e)
        db.log('conexao', 'mensagem', msg=str(e), nivel='alerta')

    else:
        resposta += 'Atualizado: '
        if 'tratador' in nova_agenda:
            resposta += 'Tratador '
            db.log('agenda', 'tratador atualizado', msg=stringfy_agenda(nova_agenda['tratador']))
            atl_tratador(nova_agenda['tratador'])

        if 'aerador' in nova_agenda:
            resposta += 'Aeradores'
            db.log('agenda', 'aerador atualizado', msg=stringfy_agenda(nova_agenda['aerador']))
            atl_aerador(nova_agenda['aerador'])

        # atualiza agenda na memória e no banco de dados
        for key in nova_agenda:
            agenda[key] = nova_agenda[key]

        db.salva_agenda(nova_agenda)

    return resposta


def stringfy_agenda(agenda):
    # formato de entrada list = [[param1, param2], ...]
    # formato de saída str = param1, param2/ ...
    saida = ""
    for evento in agenda:
        for i in range(len(evento)):
            item = evento[i]
            if type(item) == dt.time:
                saida += item.strftime('%H:%M')
            else:
                saida += str(item)

            if i < len(evento) - 1:
                saida += ', '
        saida += '/ '
    saida = saida[:-2]
    return saida


# agenda do Aerador tem o formato: [[inicio (datetime), fim (dt)], ...]
def atl_aerador(agenda):

    # atualiza o estado atual para nova configuração
    # se agenda está vazia: deslige
    if agenda:
        now = dt.datetime.now()
        last_on = []
        last_off = []
        for evento in agenda:
            inicio = dt.datetime.combine(date=dt.date.today(), time=evento[0])
            if inicio > now:
                inicio -= dt.timedelta(days=1)
            last_on.append(inicio)

            fim = dt.datetime.combine(date=dt.date.today(), time=evento[1])
            if fim > now:
                fim -= dt.timedelta(days=1)
            last_off.append(fim)

        last_on = max(last_on)
        last_off = max(last_off)

        if last_on > last_off:
            ligar_aerador()
        else:
            desligar_aerador()
    else:
        desligar_aerador()

    # exclui alarmes antigos
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id == 'ligar_aerador' or job.id == 'desligar_aerador':
            job.remove()

    # cria alarmes para o acionamento dos aeradores.
    # coloquei o replace() para garantir que a açao de ligar será
    # executada depois de desligar, assim se houver eventos de desligar e
    # ligar no mesmo horário 'ligar' será o último a ser executador
    lista_alarmes = [gera_CronTrigger(evento[0].replace(second=1)) for evento in agenda]
    trigger = OrTrigger(lista_alarmes)
    scheduler.add_job(ligar_aerador, trigger, id='ligar_aerador')

    # cria alarmes para o desligamento
    lista_alarmes = [gera_CronTrigger(evento[1]) for evento in agenda]
    trigger = OrTrigger(lista_alarmes)
    scheduler.add_job(desligar_aerador, trigger, id='desligar_aerador')


# agenda do Tratador tem o formato [[hora (datetime), ração (int)], ...]
def atl_tratador(agenda):

    # exclui jobs antigos
    jobs = scheduler.get_jobs()
    for job in jobs:
        if 'iniciar_tratador' in job.id:
            job.remove()

    # gera novos jobs
    for i in range(len(agenda)):
        scheduler.add_job(
            iniciar_tratador, gera_CronTrigger(agenda[i][0]),
            args=[agenda[i][1]], id='iniciar_tratador_' + str(i))


def gera_CronTrigger(time):
    return CronTrigger(hour=time.hour, minute=time.minute, second=time.second)


def ligar_aerador():
    db.log('aerador', 'ligado')
    digitalWrite(output_pins['aerador'], True)


def desligar_aerador():
    db.log('aerador', 'desligado')
    digitalWrite(output_pins['aerador'], False)


def ligar_refletor():
    db.log('refletor', 'ligado')
    digitalWrite(output_pins['refletor'], True)
    output_state({"refletor": True})


def desligar_refletor():
    db.log('refletor', 'desligado')
    digitalWrite(output_pins['refletor'], False)
    output_state({"refletor": False})


def iniciar_tratador(freq):
    try:
        freq = float(freq)
        if not 10 <= freq <= 120:
            raise ValueError("Frequencia {} fora da faixa permita: 10-120".format(freq))
    except Exception as e:
        db.log("ativar", "ativar tratador", msg=str(e), nivel="alerta")
    else:
        # converte a frequencia do motor para a da entrada de freq
        # entrada: min = 3, max = 120
        # saida: min = 500, max = 2500
        # o 0.5 serve pora arredondar
        freq = int((freq - 3) * (2500 - 500) / (120 - 3) + 500 + 0.5)
        if mqtt_client:
            mqtt_client.publish("controlador", "cycle:freq{}".format(freq))

        db.log('tratador', 'iniciado', msg='freq: {}'.format(freq))


# configurações para o raspi
def config_gpio():
    import RPi.GPIO as GPIO
    global gpio
    gpio = GPIO

    gpio.setmode(gpio.BCM)
    for pin in output_pins:
        gpio.setup(output_pins[pin], gpio.OUT, initial=gpio.HIGH)

    for pin in input_pins:
        gpio.setup(input_pins[pin], gpio.IN, pull_up_down=gpio.PUD_UP)

    for pin in estado:
        if pin in input_pins:
            estado[pin] = not gpio.input(input_pins[pin])
        elif conf["entradas"][pin] == "saida":
            estado[pin] = not gpio.input(output_pins[pin])

    for pin in habilitar_pins.values():
        gpio.setup(output_pins[pin], gpio.OUT, initial=gpio.LOW)


def config_dht():
    # import do sensor dht de temp e umidade
    import read_dht

    pin = conf["sensores"]["dht22"]
    loop.create_task(repeating_call(1800, read_dht.read_threaded, '22', pin, db))
    # LoopingCall(read_dht.read_threaded, '22', pin, db).start(1800, now=True)


# executa ações com os pinos de saida
def digitalWrite(pin, state):
    if type(pin) == str:
        pin = output_pins[pin]

    if gpio:
        # o relê liga em LOW, por isso o not na frente de state
        gpio.output(pin, not state)


# Encoder de datetime para json
class DateTimeEncoder(json.JSONEncoder):
    '''Regra que converte datetime em string nos jsons'''

    def default(self, o):
        if isinstance(o, dt.datetime):
            o = o.replace(microsecond=0)
            return o.isoformat(' ')

        return super().default(o)

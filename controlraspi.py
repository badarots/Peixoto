import json

import datetime as dt
from twisted.internet.defer import inlineCallbacks

# import para o APScheler
from apscheduler.schedulers.twisted import TwistedScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
# from apscheduler.triggers.date import DateTrigger

# importações para o banco de dados
from sqlalchemy.orm import sessionmaker, scoped_session
# arquivo com a estrutura do banco de dados
import sqlalchemy_modelo as db


pins = {"tratador": 2, "aerador": 3}
gpio = None

# configuração da banco de dados
db.Base.metadata.bind = db.engine
# cria uma sessão
DBSession = scoped_session(sessionmaker(bind=db.engine))
#db_session = DBSession()

# criação do scheduler
scheduler = TwistedScheduler()
# configurações do scheduler
scheduler = scheduler
scheduler.add_jobstore('sqlalchemy', engine=db.engine)


# salva log no banco de dados alem de imprimir
def log(origem, evento, nivel='info', msg=None):
    log = db.Log(nivel=nivel, origem=origem, evento=evento, mensagem=msg)

    # scoped_session foi adcionado pq estava recebendo um erro do sqlite:
    # SQLite objects created in a thread can only be used in that same thread
    db_session = DBSession()
    db_session.add(log)
    db_session.commit()
    db_session.flush()
    db_session.close()

    texto = "{}, {}, {}".format(nivel, origem, evento)
    if msg:
        texto += ', {}'.format(msg)
    print(texto)


# configurações para o raspi
def configGPIO():
    import RPi.GPIO as GPIO
    global gpio
    gpio = GPIO

    gpio.setmode(gpio.BCM)
    for pin in pins:
        gpio.setup(pins[pin], gpio.OUT, initial=gpio.HIGH)


# excuta ações com os pinos

def digitalWrite(pin, state):
    if gpio:
        # o led liga em LOW, por isso o not na frente de state
        gpio.output(pin, not state)

def ligar_tratador(quantidade):
    # print('Tratador: ligado', racao)
    log('tratador', 'ligado', msg='quantidade: ' + str(quantidade))
    digitalWrite(pins['tratador'], True)

    scheduler.add_job(desligar_tratador, 'date', run_date=dt.datetime.now() + dt.timedelta(seconds=2))

def desligar_tratador():
    # print('Tratador: fim do pulso')
    log('tratador', 'fim do pulso')
    digitalWrite(pins['tratador'], False)

def ligar_aerador():
    log('aerador', 'ligado')
    digitalWrite(pins['aerador'], True)

def desligar_aerador():
    log('aerador', 'desligado')
    digitalWrite(pins['aerador'], False)

def exit(exception):
    # print("Desligamento: limpando pinos")
    log('app', 'desligamento', msg=str(exception), nivel='erro')
    log('app', 'desligamento', msg='limpando pinos')
    if gpio:
        gpio.cleanup()


class Controlraspi(object):
    """
    """

    def __init__(self, wamp_comp, teste=False):
        self.agenda = {}

        # wamp config
        self.wamp_session = None  # "None" while we're disconnected from WAMP router
        self._wamp = wamp_comp
        # associate ourselves with WAMP session lifecycle
        self._wamp.on('join', self._initialize)
        self._wamp.on('leave', self._uninitialize)

        # configura pinos do raspberry
        if teste:
            modo = 'Rodando em modo de teste, GPIO desbilitados'
        else:
            modo = 'GPIO habilitados'
            configGPIO()

        log('app', 'inicialização', msg=modo)

        scheduler.start()


    @inlineCallbacks
    def _initialize(self, session, details):
        # print("Connected to WAMP router")
        log('conexao', 'conectado')
        self.wamp_session = session

        # reseta valores de reconexão
        # está mal implementado, se houver mais de um transport não saberei
        # reseta. tenho que encontrar o transporte em uso na conexão
        print("resetando valores de reconexão")
        self._wamp._transports[0].reset()

        try:
            yield session.register(self.atualizar, u'com.exec.atualizar')
            yield session.register(self.update_status, u'com.exec.status')
            # print("procedimentos registrados")
            log('conexao', 'registro', msg='procedimentos registrados')
        except Exception as e:
            # print("Erro: não for possível registrar os procedimentos: {0}".format(e))
            log('conexao', 'registro', msg=str(e), nivel='erro')

    def _uninitialize(self, session, reason):
        # print(session, reason)
        # print("Lost WAMP connection")
        log('conexao', 'desconectado', msg=reason.message, nivel='alerta')

        self.wamp_session = None

    def update_status(self):
        msg = 'Tá faltando isso aqui'
        if self.wamp_session is None:
            return "No WAMP session"
        self.wamp_session.publish(u"com.myapp.status", msg)
        return "Published to 'com.myapp.status'" + msg

    # Recebe dados, valida e os executa
    def atualizar(self, payload):
        resposta = ''

        try:
            agenda = self.loadMsg(payload)
        except Exception as e:
            resposta += 'Alerta, mensagem: ' + str(e)
            log('conexao', 'mensagem', msg=str(e), nivel='alerta')

        else:
            resposta += 'Atualizado: '
            if 'leds' in agenda:
                resposta += 'Leds '
                log('leds', 'atualizado', msg=str(agenda['leds']))
                self.attLeds(agenda['leds'])

            if 'tratador' in agenda:
                resposta += 'Tratador '
                log('tratador', 'atualizado', msg=str(agenda['tratador']))
                self.attTratador(agenda['tratador'])

            if 'aerador' in agenda:
                resposta += 'Aeradores'
                log('aerador', 'atualizado', msg=str(agenda['aerador']))
                self.attAerador(agenda['aerador'])

            # atualiza agenda na memória
            self.agenda = agenda

        return resposta

    # função que processa lista de agendamento
    def loadMsg(self, message):
        # Tenta converter a mensagem em um dict
        kw = json.loads(message)
        schedule = {}

        # recebe um json string, valida os dados e converte o string em int
        # datetimes
        def parseList(kw, valid_opions):
            sched = []
            visited = []

            for k in kw:

                # encontra os pares de info da lista de agendamento
                if k not in visited:
                    try:
                        key = k.split('_')
                        find = (valid_options.index(key[0]) + 1) % 2
                        opt = valid_opions[find] + '_' + key[1]

                        sched.append([kw[valid_options[0] + '_' + key[1]], kw[valid_options[1] + '_' + key[1]]])
                        visited.append(opt)
                    except Exception:
                        raise ValueError('há campos não preenchidos')

            # valida e converte as informações contidas nos pares
            for a in sched:
                for i in range(len(a)):
                    if valid_opions[i] == 'racao':
                        if a[i].isdigit():
                            a[i] = int(a[i])
                        else:
                            raise ValueError("quantidade de ração inválida:", a[i])

                    elif valid_options[i] in ['hora', 'inicio', 'fim']:
                        formato = '%H'
                        if ':' in a[i]:
                            formato = '%H:%M'

                        try:
                            t = dt.datetime.strptime(a[i], formato).time()
                            a[i] = t
                        except Exception:
                            raise ValueError("formato de hora inválido:", a[i])

            return sched

        # verifica se o tipo de msg enviada é suportada
        valid_msg = ['tratador', 'aerador', 'leds']

        for k in kw:
            if k not in valid_msg:
                raise ValueError("mensagens do tipo '{}' não são suportadas".format(k))

            # procura pelas informações contidadas em casa tipo de msg
            # e define o formato da lista final de agendamentos usando
            # o formato de valid_options
            elif k == 'aerador':
                valid_options = ['inicio', 'fim']
                schedule['aerador'] = parseList(kw[k], valid_options)

            elif k == 'tratador':
                valid_options = ['hora', 'racao']
                schedule['tratador'] = parseList(kw[k], valid_options)

            elif k == 'leds':
                schedule['leds'] = None

        return schedule

    # agenda do Aerador tem o formato: [[inicio (datetime), fim (dt)], ...]
    def attAerador(self, agenda):

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
            if job.id == 'ligar_aerador' or job.id =='desligar_aerador':
                job.remove()

        # cria alarmes para o acionamento dos aeradores
        lista_alarmes = [self.geraCronTrigger(evento[0]) for evento in agenda]
        trigger = OrTrigger(lista_alarmes)
        scheduler.add_job(ligar_aerador, trigger, id='ligar_aerador')

        # cria alarmes para o desligamento
        lista_alarmes = [self.geraCronTrigger(evento[1]) for evento in agenda]
        trigger = OrTrigger(lista_alarmes)
        scheduler.add_job(desligar_aerador, trigger, id='desligar_aerador')

    # agenda do Tratador tem o format [[hora (datetime), ração (int)], ...]
    def attTratador(self, agenda):

        # exclui jobs antigos
        jobs = scheduler.get_jobs()
        for job in jobs:
            if 'ligar_tratador' in job.id:
                job.remove()

        # gera novos jobs
        for i in range(len(agenda)):
            scheduler.add_job(ligar_tratador, self.geraCronTrigger(agenda[i][0]), args=[agenda[i][1]], id='ligar_tratador_' + str(i))

    def attLeds(self, agenda):
        pass

    def geraCronTrigger(self, time):
        return CronTrigger(hour=time.hour, minute=time.minute)

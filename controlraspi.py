import json

import datetime as dt
from twisted.internet.defer import inlineCallbacks

from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
# from apscheduler.triggers.date import DateTrigger


class Controlraspi(object):
    """
    A simple Web application that publishes an event every time the
    url "/" is visited.
    """

    def __init__(self, wamp_comp, scheduler, teste=False):
        self.pins = {"tratador": 2, "aerador": 3}
        self.agenda = {}

        # configurações para o raspi
        self.teste = teste
        if not teste:
            import RPi.GPIO as gpio
            self.gpio = gpio

            self.gpio.setmode(gpio.BCM)
            for pin in self.pins:
                self.gpio.setup(self.pins[pin], self.gpio.OUT, initial=self.gpio.HIGH)

        # wamp config
        self._session = None  # "None" while we're disconnected from WAMP router
        self._wamp = wamp_comp
        # associate ourselves with WAMP session lifecycle
        self._wamp.on('join', self._initialize)
        self._wamp.on('leave', self._uninitialize)

        # configurações do scheduler
        self.scheduler = scheduler
        # scheduler.add_job(self.tick, 'interval', seconds=3)
        self.scheduler.start()

    @inlineCallbacks
    def _initialize(self, session, details):
        print("Connected to WAMP router")
        self._session = session

        # reseta valores de reconexão
        # está mal implementado, se houver mais de um transport não saberei
        # reseta. tenho que encontrar o transporte em uso na conexão
        print("resetando valores de reconexão")
        self._wamp._transports[0].reset()

        try:
            yield session.register(self.atualizar, u'com.exec.atualizar')
            yield session.register(self.update_status, u'com.exec.status')
            print("procedimentos registrados")
        except Exception as e:
            print("Erro: não for possível registrar os procedimentos: {0}".format(e))

    def _uninitialize(self, session, reason):
        print(session, reason)
        print("Lost WAMP connection")
        self._session = None

    def update_status(self):
        msg = 'Tá faltando isso aqui'
        if self._session is None:
            return "No WAMP session"
        self._session.publish(u"com.myapp.status", msg)
        return "Published to 'com.myapp.status'" + msg

    # Recebe dados, valida e os executa
    def atualizar(self, payload):
        resposta = ''

        try:
            agenda = self.loadMsg(payload)
        except Exception as e:
            print(e)
            resposta += 'Alerta, mensagem: ' + str(e)

        else:
            resposta += 'Atualizado: '
            if 'leds' in agenda:
                resposta += 'Leds '
                self.attLeds(agenda['leds'])
            if 'tratador' in agenda:
                resposta += 'Tratador '
                self.attTratador(agenda['tratador'])
            if 'aerador' in agenda:
                resposta += 'Aeradores'
                self.attAerador(agenda['aerador'])

            # atualiza agenda na memória
            self.agenda = agenda



        print(resposta)
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

        def ligar():
            print('Aerador: ligado')
            self.digitalWrite(self.pins['aerador'], True)

        def desligar():
            print('Aerador: desligado')
            self.digitalWrite(self.pins['aerador'], False)

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
                ligar()
            else:
                desligar()
        else:
            desligar()

        # define nome dos jobs
        jobIds = ['ligar_aerador', 'desligar_aerador']
        # gera as listas de triggers
        trigger_list = []
        trigger_list.append([self.geraCronTrigger(evento[0]) for evento in agenda])

        lista_desligar = []
        for inicio, fim in agenda:
            hoje = dt.date.today()
            date = dt.datetime.combine(date=hoje, time=fim)
            if inicio > fim:
                date += dt.timedelta(days=1)
            lista_desligar.append(self.geraCronTrigger(date))
        trigger_list.append(lista_desligar)

        # cria agendadoes para ligar e desligar aerador
        for i in range(len(trigger_list)):
            acao = desligar
            if i == 0:
                acao = ligar

            trigger = OrTrigger(trigger_list[i])
            job = self.scheduler.get_job(jobIds[i])
            if job:
                job.reschedule(trigger)
            else:
                self.scheduler.add_job(acao, trigger, id=jobIds[i])

    # agenda do Tratador tem o format [[hora (datetime), ração (int)], ...]
    def attTratador(self, agenda):

        def ligar(racao):
            print('Tratador: ligado', racao)

            self.digitalWrite(self.pins['tratador'], True)

            self.scheduler.add_job(desligar, 'date', run_date=dt.datetime.now() + dt.timedelta(seconds=2))

        def desligar():
            print('Tratador: fim do pulso')
            self.digitalWrite(self.pins['tratador'], False)

        # exclui jobs antigos
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if 'ligar_tratador' in job.id:
                job.remove()

        # gera novos jobs
        for i in range(len(agenda)):
            self.scheduler.add_job(ligar, args=[agenda[i][1]], trigger=self.geraCronTrigger(agenda[i][0]), id='ligar_tratador_' + str(i))

    def attLeds(self, agenda):
        pass

    def geraCronTrigger(self, time):
        return CronTrigger(hour=time.hour, minute=time.minute)

    def digitalWrite(self, pin, state):
        if not self.teste:
            # o led liga em LOW, por isso o not na frente de state
            self.gpio.output(pin, not state)

    def cleanup(self):
        print("Desligamento: limpando pinos")
        if not self.teste:
            self.gpio.cleanup()

    def tick(self):
        self.i += 1
        print("Já rodei {} vezes".format(self.i))

    def ledToggle(self, *args):
        self.ledState[args[0]] = not self.ledState[args[0]]
        print(args[0], self.ledState[args[0]])

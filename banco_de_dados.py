import os

from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, DateTime, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, scoped_session


# cria pasta 'dados' se ela ainda não existe
if not os.path.isdir('dados'):
    os.mkdir('dados')

Base = declarative_base()

class Log(Base):
    __tablename__ = 'log'

    id = Column(Integer, primary_key=True)
    horario = Column(DateTime, default=datetime.now)
    nivel = Column(String(10), default='info') # nivel de importancia: info, alerta, erro...
    origem = Column(String(20), nullable=False) # aerador, tratador, conexao
    evento = Column(String(20), nullable=False) # evento ocorrido na origem
    mensagem = Column(String(300)) # mensagem adcional que acompanha o evento ex: nova agenda

# agenda atual do aerador
class Aerador(Base):
    __tablename__ = 'agenda_aerador'

    id = Column(Integer, primary_key=True)
    inicio = Column(Time, nullable=False)
    fim = Column(Time, nullable=False)

# agenda atual do tratador
class Tratador(Base):
    __tablename__ = 'agenda_tratador'
    id = Column(Integer, primary_key=True)
    inicio = Column(Time, nullable=False)
    quantidade = Column(Float, nullable=False)

# funções para gravação no banco de dados

# salva log no banco de dados alem de imprimir
def log(origem, evento, nivel='info', msg=None):
    entrada = Log(nivel=nivel, origem=origem, evento=evento, mensagem=msg)
    session = Session()
    session.add(entrada)
    session.commit()
    session.flush()
    session.close()

    texto = "{}, {}, {}".format(nivel, origem, evento)
    if msg:
        texto += ', {}'.format(msg)
    print(texto)

# salva a agenda dos atuadores
def salva_agenda(agenda):
    # formato da agenda {'tratador':[...], 'aerador':[...]}
    # percorre os atuadores da agenda
    session = Session()
    for atuador in agenda:
        for alarme in agenda[atuador]:
            if atuador == 'tratador':
                entrada = Tratador(inicio=alarme[0], quantidade=alarme[1])
            elif atuador == 'aerador':
                entrada = Aerador(inicio=alarme[0], fim=alarme[1])
            else:
                raise ValueError("atuador {} não está configurado no banco de dados".format(atuador))
            session.add(entrada)

    session.commit()
    session.flush()
    session.close()

url = 'sqlite:///dados/arquivo.db'

engine = create_engine(url, poolclass=NullPool)

Base.metadata.create_all(engine)

# configuração da banco de dados
Base.metadata.bind = engine

# cria uma sessão
# scoped_session foi adcionado pq estava recebendo um erro do sqlite:
# SQLite objects created in a thread can only be used in that same thread
Session = scoped_session(sessionmaker(bind=engine))
#db_session = DBSession()

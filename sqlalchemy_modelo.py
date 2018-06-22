import os

from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, DateTime, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

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

url = 'sqlite:///dados/arquivo.db'

engine = create_engine(url, poolclass=NullPool)

Base.metadata.create_all(engine)

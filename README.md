#

## Afazeres

Controle

- [x] Agendamento
- [x] Inicialização com systemd
- [x] Log
- [x] Banco de dados
- [x] Informar status aos clientes
- [x] Controle de velocidade do tratador
- [ ] Desabilitar temporizador externo
- [ ] Refazer agenda do tratador
- [ ] Reformular configurações

WAMP

- [x] Estabelecer comunicação
- [x] Definir rota de conexão
- [x] Processamento de mensagens
- [x] Autenticação
- [ ] Criptografia

MQTT

- [ ] Autenticação e autorizações
- [ ] Criptografia
- [ ] QoS

## Configuração do Raspiberry

### Atualização e instalação de pacotes necessários

    sudo apt update && sudo apt upgrade
    sudo apt install git mosquitto

Pacotes úteis:

    sudo apt install wiringpi sqlite3 nmap

### Instalando interpretador python dedicado (3.6)

Pacotes necessários

    sudo apt-get -y install build-essential libssl-dev libffi-dev libreadline-dev libbz2-dev libsqlite3-dev libncurses5-dev

Instalação

    cd $HOME
    wget https://www.python.org/ftp/python/3.6.6/Python-3.6.6.tar.xz
    tar xvf Python-3.6.6.tar.xz
    cd Python-3.6.6 && ./configure --prefix=$HOME/python366
    make && make install
    sudo ln -s ~/python366/bin/python3 /usr/local/bin/pythond
    sudo ln -s ~/python366/bin/pip /usr/local/bin/pipd

Instalando e atualizando pip

    pythond -m ensurepip
    pythond -m pip install -U pip

### Instalando pypy (não está funcionando)

Pacotes necessários:

    sudo apt install libssl-dev libffi-dev

Instalação:

    wget https://bitbucket.org/pypy/pypy/downloads/pypy3-v6.0.0-linux-armhf-raspbian.tar.bz2
    sudo mkdir /opt/pypy
    sudo tar xvf pypy3-v6.0.0-linux-armhf-raspbian.tar.bz2 --directory /opt/pypy/ --strip-components=1
    sudo ln -s /opt/pypy/bin/pypy3 /usr/local/bin/pypy

Intalando pip

    pypy -m ensurepip
    pypy -m pip install -U pip

[referencia](https://github.com/Nikolay-Kha/PyCNC/issues/20)

### PlatformIO no raspberry

Requisito: python 2.7

Adcione o usuario ao grupo 'dialout'

    sudo usermod -a -G dialout pi

Habilite a comunicação serial

    raspi-config

Interfacing -> Serial

Configure o arquivo 99-platformio-udev.rules

    curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/develop/scripts/99-platformio-udev.rules | sudo tee /etc/udev/rules.d/99-platformio-udev.rules
    sudo service udev restart

Script de instalaçao do platformio (também instala pip)

    sudo python -c "$(curl -fsSL https://raw.githubusercontent.com/platformio/platformio/develop/scripts/get-platformio.py)"

## Instalação

Clone o repositório na pasta home

    cd $HOME
    git clone https://github.com/badarot/Peixoto

Dentro da pasta criada instale as dependências

    cd Peixoto
    pipd install -r requeriments-server.txt

Se pretente usar um broker WAMP remoto basta instalar as dependências de ``requiriments.txt``.

### Inicialização manual

Inicialize o ``crossbar`` e rode o script ``peixoto.py`` com o interpretador python dedicado

    cd Peixoto
    crossbar start &
    pythond peixoto.py

### Opções

Para rodar em mode de teste (sem o controle dos GPIOs) use o argumento ``teste``

    pythond peixoto.py teste

Para se conectar em um WAMP broker remoto use o argumento ``remoto``

    pythond peixoto.py remoto

### Inicialização atomática

Para habilitar a inicialização automática do crossbar e do peixoto copie os arquivos ``crossbar.service`` e ``peixoto.service`` dentro da pasta ``services`` para:

> /etc/systemd/system/

E execute:

    sudo systemctl enable crossbar
    sudo systemctl enable peixoto

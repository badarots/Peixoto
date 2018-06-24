## Afazeres

WAMP
- [x] Estabelecer comunicação
- [x] Definir rota de conexão
- [x] Processamento de mensagens
- [x] Autenticação
- [ ] Criptografia (opcional?)

App
- [x] Agendamento
- [x] Inicialização com systemd
- [x] Log
- [x] Banco de dados
- [x] Informar status aos clientes
- [ ] Controle de velocidade do tratador

Site
- [x] Formulários
- [x] Formulário de autenticação
- [ ] Otimização para celular
- [ ] Painel para ligar e desligar atuadores
- [ ] Painel de informações

## Inicialização atomática
Para habilitar a inicialização automática do crossbar e do peixoto copie os arquivos ``crossbar.service`` e ``peixoto.service`` dentro da pasta ``services`` para:

> /etc/systemd/system/

E execute:

    # systemctl enable crossbar
    # systemctl enable peixoto

A saída do programa será salva no arquivo ``/home/badaro/dados/peixoto.log``

### Desatualizado

Para salvar a saída do peixoto no arquivo ``/var/log/peixoto.log`` copie o arquivo ``peixoto.conf`` dentro da pasta ``services`` para:

> /etc/rsyslog.d/

Referência: [stackoverflow](https://stackoverflow.com/questions/37585758/how-to-redirect-output-of-systemd-service-to-a-file)

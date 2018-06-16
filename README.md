## Inicialização atomática
Para habilitar a inicialização automática do crossbar e do peixoto copie os arquivos ``crossbar.service`` e ``peixoto.service`` dentro da pasta ``services`` para:

> /etc/systemd/system/

E execute:

    # systemctl enable crossbar.service
    # systemctl enable peixoto.service

Para salvar a saída do peixoto no arquivo ``/var/log/peixoto.log`` copie o arquivo ``peixoto.conf`` dentro da pasta ``services`` para:

> /etc/rsyslog.d/


Referência: [stackoverflow](https://stackoverflow.com/questions/37585758/how-to-redirect-output-of-systemd-service-to-a-file)
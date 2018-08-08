import sys
from time import sleep
import threading
# import Adafruit_DHT

sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }

def read(sensor, pin, logger=None):
    if sensor not in sensor_args:
        print("Sensor {} não suportado".format(sensor))
        return

    for i in range(5):
        humidity, temperature = Adafruit_DHT.read_retry(sensor_args[sensor], pin)

        valid_humidity = humidity is not None and 10 <= humidity <= 100
        valid_temperature = temperature is not None and -5 <= temperature <= 50

        if valid_humidity and valid_temperature:
            break
        else:
            humidity = temperature = None

        sleep(5)
    if logger is None:
        print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(humidity, temperature))
    else:
        print('Log -- Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(humidity, temperature))

def read_threaded(sensor, pin, logger=None):
    t = threading.Thread(target=read, args=(sensor, pin, logger))
    t.start()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] in sensor_args:
        sensor = sensor_args[sys.argv[1]]
        pin = sys.argv[2]
        read(sensor, pin)
    else:
        print('Uso: python read_dht [11|22|2302] <número do pino>')
        print('Exemple: python read_dht 22 10 - Lê um DHT22 conectado no pino #10')

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ESP8266HTTPClient.h>

#define N_PARAMETROS 3

ESP8266WiFiMulti wifiMulti;
WiFiServer server(80);

String senha = "tratador";
const unsigned long connection_timeout = 1000;


void setup()
{
 
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // configuracao do wifi
  WiFi.mode(WIFI_STA);
  wifiMulti.addAP("PEIXECAIDO", "informatica");
  wifiMulti.addAP("Badaro1", "informatica");
  wifiMulti.addAP("eita", "informatica");
  wifiMulti.run();

  // configuracao do servidor
  server.begin();
  Serial.printf("Web server started, open %s in a web browser\n", WiFi.localIP().toString().c_str());

  //configuracao do OTA
// Port defaults to 8266
  // ArduinoOTA.setPort(8266);

  // Hostname defaults to esp8266-[ChipID]
  ArduinoOTA.setHostname("esp_sensores");

  // No authentication by default
  ArduinoOTA.setPassword("admin");

  // Password can be set with it's md5 value as well
  // MD5(admin) = 21232f297a57a5a743894a0e4a801fc3
  // ArduinoOTA.setPasswordHash("21232f297a57a5a743894a0e4a801fc3");

  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else { // U_SPIFFS
      type = "filesystem";
    }

    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Serial.println("Start updating " + type);
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("End Failed");
    }
  });
  ArduinoOTA.begin();
  Serial.println("Ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop()
{
  // reconecta ao wifi
  wifiMulti.run();

  // lida com OTA
  ArduinoOTA.handle();

  //---------------------------------------------//
  //      lida com pedidos ao servidor
  //---------------------------------------------//
  WiFiClient client = server.available();
  if (!client) return;

  // Wait until the client sends some data
  Serial.println("new client");
  unsigned long temp = millis();
  while (!client.available()) {
    delay(1);
    // impede do loop travar se o cliente nao terminar o pedido (?)
    if ((millis() - temp) > connection_timeout) {
      Serial.println("conexao fechada: excedido tempo limite");
      client.stop();
      return;
    }
  }

  // Read the first line of the request
  String req = client.readStringUntil('\r');
  Serial.println(req);
  client.flush();

  // formata pedido
  // formato esperado: /senha/funcao/opcoes
  String pedido[N_PARAMETROS];
  int i = req.indexOf('/');

  for (int k = 0; k < N_PARAMETROS && i != -1; k++) {
    int f = req.indexOf('/', i + 1);
    int f2 = req.indexOf(' ', i + 1);
    if (f2 > -1 && f2 < f) f = f2;
    pedido[k] = req.substring(i + 1, f);
    i = f;
  }
  //for (int k = 0; k < N_PARAMETROS && 1; k++) Serial.println(pedido[k]);

  // processa pedido
  String resp;
  if (pedido[0] == senha) {

    if (pedido[1] == "adc") {
      resp = String(analogRead(A0));
    } 
  } else resp = "Senha incorreta";

  if (resp == "") resp = "Pedido invalido";
  Serial.println(resp);
  if (resp == "Senha incorreta") {
    client.stop();
    return;
  }

  client.flush();

  // Prepare the response
  String s = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<!DOCTYPE HTML>\r\n<html>\r\n";
  s += resp;
  s += "</html>\n";

  // Send the response to the client
  client.print(s);
  delay(1);
  Serial.println("Client disconnected");


  // The client will actually be disconnected
  // when the function returns and 'client' object is detroyed
}

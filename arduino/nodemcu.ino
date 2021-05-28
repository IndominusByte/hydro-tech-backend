#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ESPAsyncWebServer.h>
#include <EEPROM.h>

WebSocketsClient webSocket;
// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

// variable eeprom
String esid, epass, ewebsocket, ewsport, ewsurl;
String token;

// variable nodemcu
bool ws_connected = false;

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.printf("[WSc] Disconnected!\n");

      ws_connected = false;
      break;
    case WStype_CONNECTED: {
      Serial.printf("[WSc] Connected to url: %s\n", payload);

      ws_connected = true;
    }
      break;
    case WStype_TEXT:
    
      ws_connected = false;
      getData(payload);
      // send message to server
      // webSocket.sendTXT("message here");
      break;
    case WStype_BIN:
      Serial.printf("[WSc] get binary length: %u\n", length);
      hexdump(payload, length);

      // send data to server
      // webSocket.sendBIN(payload, length);
      break;
        case WStype_PING:
            // pong will be send automatically
            Serial.printf("[WSc] get ping\n");
            break;
        case WStype_PONG:
            // answer to a ping we send
            Serial.printf("[WSc] get pong\n");
            break;
    }
}

void setup() {
  Serial.begin(9600);
  while(!Serial) continue;

  Serial.println(F("Disconnecting previously connected WiFi"));
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  EEPROM.begin(512); //Initializing EEPROM
  delay(10);

  readEEPROM(); // read eeprom

  if(esid != NULL && epass != NULL)
    WiFi.begin(esid.c_str(), epass.c_str());

  (testWifi()) ? Serial.println(F("Succesfully Connected!!!")) : Serial.println(F("Cannot Connect Wifi"));

  setupAP();// Setup HotSpot

  if((WiFi.status() == WL_CONNECTED)){
    // server address, port and URL
    webSocket.begin(ewebsocket, ewsport.toInt(), ewsurl + "?token=" + token);
    // event handler
    webSocket.onEvent(webSocketEvent);
    // try ever 5000 again if connection has failed
    webSocket.setReconnectInterval(5000);
  }
}

void writeStr(int add, String data) {
  int len = data.length();
  for(int i = 0; i < len; i++)
    EEPROM.write(add + i, data[i]);
  
  EEPROM.write(add + len,'\0');   // Add termination null character for String Data
  EEPROM.commit();
}

void flushStr(int start, int offset){
  for (int i = start; i < offset; ++i)
    EEPROM.write(i, 0);

  EEPROM.commit();
}

String readStr(int add) {
  unsigned char k;
  int len = 0, len_eeprom = EEPROM.length();
  char data[len_eeprom]; // Max depend eeprom length

  k = EEPROM.read(add);
  while(k != '\0' && len < len_eeprom)   //Read until null character
  {    
    k = EEPROM.read(add + len);
    data[len] = k;
    len++;
  }
  data[len] = '\0';
  return String(data);
}

void readEEPROM(void){
  // Read eeprom
  esid = readStr(0);
  epass = readStr(32);
  ewebsocket = readStr(64);
  ewsport = readStr(96);
  ewsurl = readStr(128);
  token = readStr(160);

  Serial.println(F("============= READ EEPROM ============="));
  Serial.println("SSID : " + esid);
  Serial.println("Password : " + epass);
  Serial.println("Websocket : " + ewebsocket);
  Serial.println("Websocket Port : " + ewsport);
  Serial.println("Websocket Url : " + ewsurl);
  Serial.println("Token : " + token);
  Serial.println(F("============= READ EEPROM ============="));
}

void resetEEPROM(void){
  for (int i = 0 ; i < EEPROM.length() ; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
}

void writeEEPROM(
  String qsid = "", String qpass = "",
  String qwebsocket = "", String qwsport = "",
  String qwsurl = "", String qtoken = ""
)
{
  if(qsid.length() > 0) {
    flushStr(0,32);
    writeStr(0,qsid);
  }
  if(qpass.length() > 0){
    flushStr(32,64);
    writeStr(32,qpass);
  }
  if(qwebsocket.length() > 0){
    flushStr(64,96);
    writeStr(64,qwebsocket);
  }
  if(qwsport.length() > 0){
    flushStr(96,128);
    writeStr(96,qwsport);
  }
  if(qwsurl.length() > 0){
    flushStr(128,160);
    writeStr(128,qwsurl);
  }
  if(qtoken.length() > 0){
    flushStr(160,512);
    writeStr(160,qtoken);
  }
}

bool testWifi(void) {
  int c = 0;
  Serial.println(F("Waiting for Wifi to connect"));
  while ( c < 20 ) {
    if (WiFi.status() == WL_CONNECTED)
    {
      return true;
    }
    delay(500);
    Serial.print("*");
    c++;
  }
  Serial.println(F(""));
  Serial.println(F("Connect timed out, opening AP"));
  return false;
}

void launchWeb()
{
  Serial.println(F(""));
  Serial.println(F("WiFi connected"));
  Serial.print(F("Local IP: "));
  Serial.println(WiFi.localIP());
  Serial.print(F("SoftAP IP: "));
  Serial.println(WiFi.softAPIP());
  createWebServer();
  // Start the server
  server.begin();
  Serial.println(F("Server started"));
}

void setupAP(void){
  delay(100);
  WiFi.softAP("Hydro-wifi", "");
  Serial.println(F("Initializing_Wifi_accesspoint"));
  launchWeb();
}

void createWebServer(){
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    String json = "[";
    int n = WiFi.scanComplete();
    if(n == -2){
      WiFi.scanNetworks(true);
    } else if(n){
      for (int i = 0; i < n; ++i){
        if(i) json += ",";
        json += "{";
        json += "\"rssi\":"+String(WiFi.RSSI(i));
        json += ",\"ssid\":\""+WiFi.SSID(i)+"\"";
        json += ",\"bssid\":\""+WiFi.BSSIDstr(i)+"\"";
        json += ",\"channel\":"+String(WiFi.channel(i));
        json += ",\"secure\":"+String(WiFi.encryptionType(i));
        json += "}";
      }
      WiFi.scanDelete();
      if(WiFi.scanComplete() == -2){
        WiFi.scanNetworks(true);
      }
    }
    json += "]";
    request->send(200, "application/json", json);
    json = String();
  });

  server.on("/setting", HTTP_POST, [](AsyncWebServerRequest *request){
    String qsid = request->arg("ssid");
    String qpass = request->arg("pass");
    String qwebsocket = request->arg("websocket");
    String qwsport = request->arg("wsport");
    String qwsurl = request->arg("wsurl");
    String qtoken = request->arg("token");

    String json;
    if(
      qsid.length() > 0 || qpass.length() > 0 ||
      qwebsocket.length() > 0 || qwsport.length() > 0 ||
      qwsurl.length() > 0 || qtoken.length() > 0
    ) {
        writeEEPROM(qsid,qpass,qwebsocket,qwsport,qwsurl,qtoken);
        json = "{\"Success\":\"saved to eeprom... reset to boot into new wifi\"}";
        request->send(200, "application/json", json);
        delay(1000);
        ESP.restart();
      } else {
        json = "{\"Error\":\"Ups please fill one of an input field\"}";
        request->send(422, "application/json", json);
      }

    json = String();
  });

  server.on("/reset", HTTP_GET, [](AsyncWebServerRequest *request){
    resetEEPROM();
    String json = "{\"Success\":\"successfully reset eeprom\"}";
    request->send(200, "application/json", json);
    delay(1000);
    ESP.restart();
    json = String();
  });

  server.on("/restart", HTTP_GET, [](AsyncWebServerRequest *request){
    String json = "{\"Success\":\"successfully restart servo\"}";
    request->send(200, "application/json", json);
    delay(1000);
    ESP.restart();
    json = String();
  });

}

void getDataSerial(){
  String received = Serial.readStringUntil('\n');
  if(received.indexOf("Hydro") != -1){
    webSocket.sendTXT(received);
  }
  delay(1000);
}

void getData(uint8_t * payload){ 
  String dataweb = (char*)payload;
  bool looping = true;

  while(looping){
    Serial.println("stop_hydro");
    delay(1000);
    String received = Serial.readStringUntil('\n');
    if(received.indexOf("Hydro") == -1){
      looping = false;
    }
  }

  looping = true;

  while(looping){
    Serial.println(dataweb);
    delay(1000);
    String received = Serial.readStringUntil('\n');
    if(received.indexOf("set_hydro_true") != -1){
      looping = false;
    }
  }
  
  ws_connected = true;
}

void loop() {
  if((WiFi.status() == WL_CONNECTED)){
    webSocket.loop();  

    if(ws_connected == true) getDataSerial();
  }
}

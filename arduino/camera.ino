#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ESPAsyncWebServer.h>
#include <Preferences.h>
#include "soc/soc.h" //disable brownout problems
#include "soc/rtc_cntl_reg.h"  //disable brownout problems
#include "esp_camera.h"

WiFiClient client;
WebSocketsClient webSocket;
// Create AsyncWebServer object on port 80
AsyncWebServer server(80);
// similar like EEPROM
Preferences preferences;

bool live_cam = false;
// variable eeprom
String esid, epass, ewebsocket, ewsport, ewsurl;
String pathUpload, token;

#define CAMERA_MODEL_AI_THINKER
//#define CAMERA_MODEL_M5STACK_PSRAM
//#define CAMERA_MODEL_M5STACK_WITHOUT_PSRAM
//#define CAMERA_MODEL_M5STACK_PSRAM_B
//#define CAMERA_MODEL_WROVER_KIT

#if defined(CAMERA_MODEL_WROVER_KIT)
  #define PWDN_GPIO_NUM    -1
  #define RESET_GPIO_NUM   -1
  #define XCLK_GPIO_NUM    21
  #define SIOD_GPIO_NUM    26
  #define SIOC_GPIO_NUM    27
  
  #define Y9_GPIO_NUM      35
  #define Y8_GPIO_NUM      34
  #define Y7_GPIO_NUM      39
  #define Y6_GPIO_NUM      36
  #define Y5_GPIO_NUM      19
  #define Y4_GPIO_NUM      18
  #define Y3_GPIO_NUM       5
  #define Y2_GPIO_NUM       4
  #define VSYNC_GPIO_NUM   25
  #define HREF_GPIO_NUM    23
  #define PCLK_GPIO_NUM    22

#elif defined(CAMERA_MODEL_M5STACK_PSRAM)
  #define PWDN_GPIO_NUM     -1
  #define RESET_GPIO_NUM    15
  #define XCLK_GPIO_NUM     27
  #define SIOD_GPIO_NUM     25
  #define SIOC_GPIO_NUM     23
  
  #define Y9_GPIO_NUM       19
  #define Y8_GPIO_NUM       36
  #define Y7_GPIO_NUM       18
  #define Y6_GPIO_NUM       39
  #define Y5_GPIO_NUM        5
  #define Y4_GPIO_NUM       34
  #define Y3_GPIO_NUM       35
  #define Y2_GPIO_NUM       32
  #define VSYNC_GPIO_NUM    22
  #define HREF_GPIO_NUM     26
  #define PCLK_GPIO_NUM     21

#elif defined(CAMERA_MODEL_M5STACK_WITHOUT_PSRAM)
  #define PWDN_GPIO_NUM     -1
  #define RESET_GPIO_NUM    15
  #define XCLK_GPIO_NUM     27
  #define SIOD_GPIO_NUM     25
  #define SIOC_GPIO_NUM     23
  
  #define Y9_GPIO_NUM       19
  #define Y8_GPIO_NUM       36
  #define Y7_GPIO_NUM       18
  #define Y6_GPIO_NUM       39
  #define Y5_GPIO_NUM        5
  #define Y4_GPIO_NUM       34
  #define Y3_GPIO_NUM       35
  #define Y2_GPIO_NUM       17
  #define VSYNC_GPIO_NUM    22
  #define HREF_GPIO_NUM     26
  #define PCLK_GPIO_NUM     21

#elif defined(CAMERA_MODEL_AI_THINKER)
  #define PWDN_GPIO_NUM     32
  #define RESET_GPIO_NUM    -1
  #define XCLK_GPIO_NUM      0
  #define SIOD_GPIO_NUM     26
  #define SIOC_GPIO_NUM     27
  
  #define Y9_GPIO_NUM       35
  #define Y8_GPIO_NUM       34
  #define Y7_GPIO_NUM       39
  #define Y6_GPIO_NUM       36
  #define Y5_GPIO_NUM       21
  #define Y4_GPIO_NUM       19
  #define Y3_GPIO_NUM       18
  #define Y2_GPIO_NUM        5
  #define VSYNC_GPIO_NUM    25
  #define HREF_GPIO_NUM     23
  #define PCLK_GPIO_NUM     22

#elif defined(CAMERA_MODEL_M5STACK_PSRAM_B)
  #define PWDN_GPIO_NUM     -1
  #define RESET_GPIO_NUM    15
  #define XCLK_GPIO_NUM     27
  #define SIOD_GPIO_NUM     22
  #define SIOC_GPIO_NUM     23
  
  #define Y9_GPIO_NUM       19
  #define Y8_GPIO_NUM       36
  #define Y7_GPIO_NUM       18
  #define Y6_GPIO_NUM       39
  #define Y5_GPIO_NUM        5
  #define Y4_GPIO_NUM       34
  #define Y3_GPIO_NUM       35
  #define Y2_GPIO_NUM       32
  #define VSYNC_GPIO_NUM    25
  #define HREF_GPIO_NUM     26
  #define PCLK_GPIO_NUM     21

#else
  #error "Camera model not selected"
#endif

void configCamera(){
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG; //YUV422,GRAYSCALE,RGB565,JPEG

  // Select lower framesize if the camera doesn't support PSRAM
  // FRAMESIZE_ + QVGA|CIF|VGA|SVGA|XGA|SXGA|UXGA
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;  //10-63 lower number means higher quality
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;  //10-63 lower number means higher quality
    config.fb_count = 1;
  }
  
  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    delay(1000);
    ESP.restart();
  }

  sensor_t * s = esp_camera_sensor_get();
  s->set_brightness(s, 0);     // -2 to 2
  s->set_contrast(s, 0);       // -2 to 2
  s->set_saturation(s, 0);     // -2 to 2
  s->set_special_effect(s, 0); // 0 to 6 (0 - No Effect, 1 - Negative, 2 - Grayscale, 3 - Red Tint, 4 - Green Tint, 5 - Blue Tint, 6 - Sepia)
  s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
  s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
  s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
  s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
  s->set_aec2(s, 0);           // 0 = disable , 1 = enable
  s->set_ae_level(s, 0);       // -2 to 2
  s->set_aec_value(s, 300);    // 0 to 1200
  s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
  s->set_agc_gain(s, 0);       // 0 to 30
  s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
  s->set_bpc(s, 0);            // 0 = disable , 1 = enable
  s->set_wpc(s, 1);            // 0 = disable , 1 = enable
  s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
  s->set_lenc(s, 1);           // 0 = disable , 1 = enable
  s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
  s->set_vflip(s, 0);          // 0 = disable , 1 = enable
  s->set_dcw(s, 1);            // 0 = disable , 1 = enable
  s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
}

void hexdump(const void *mem, uint32_t len, uint8_t cols = 16) {
  const uint8_t* src = (const uint8_t*) mem;
  Serial.printf("\n[HEXDUMP] Address: 0x%08X len: 0x%X (%d)", (ptrdiff_t)src, len, len);
  for(uint32_t i = 0; i < len; i++) {
    if(i % cols == 0) {
      Serial.printf("\n[0x%08X] 0x%08X: ", (ptrdiff_t)src, i);
    }
    Serial.printf("%02X ", *src);
    src++;
  }
  Serial.printf("\n");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.printf("[WSc] Disconnected!\n");
      break;
    case WStype_CONNECTED:
      Serial.printf("[WSc] Connected to url: %s\n", payload);

      // send message to server when Connected
      webSocket.sendTXT("kind:Camera");
      break;
    case WStype_TEXT:
      Serial.printf("[WSc] get text: %s\n", payload);

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
    case WStype_ERROR:      
    case WStype_FRAGMENT_TEXT_START:
    case WStype_FRAGMENT_BIN_START:
    case WStype_FRAGMENT:
    case WStype_FRAGMENT_FIN:
      break;
  }
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); //disable brownout detector

  Serial.begin(115200);
  Serial.println("Disconnecting previously connected WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(10);

  readEEPROM(); // read eeprom

  if(esid != NULL && epass != NULL)
    WiFi.begin(esid.c_str(), epass.c_str());

  (testWifi()) ? Serial.println("Succesfully Connected!!!") : Serial.println("Cannot Connect Wifi");

  setupAP();// Setup HotSpot

  if((WiFi.status() == WL_CONNECTED)){
    configCamera();
    // server address, port and URL
    webSocket.begin(ewebsocket, ewsport.toInt(), ewsurl + "?token=" + token);
    // event handler
    webSocket.onEvent(webSocketEvent);
    // try ever 5000 again if connection has failed
    webSocket.setReconnectInterval(5000);
  }
}

void getData(uint8_t * payload){ 
  for(char *p = strtok((char*) payload, ","); p != NULL; p = strtok(NULL, ",")){
    int l = 0;
    String tmp[2];
    char *token, *str, *tofree;
    tofree = str = strdup(p);
    while((token = strsep(&str,":"))){
      tmp[l] = token;
      l++;
    }
    if(tmp[0] == "kind" && tmp[1] == "capture_image") sendPhoto();
    if(tmp[0] == "kind" && tmp[1] == "live_cam_true") live_cam = true;
    if(tmp[0] == "kind" && tmp[1] == "live_cam_false") live_cam = false;
    free(tofree);
  }
}

void readEEPROM(void){
  // Read eeprom
  preferences.begin("my-app",false);

  esid = preferences.getString("esid");
  epass = preferences.getString("epass");
  ewebsocket = preferences.getString("ewebsocket");
  ewsport = preferences.getString("ewsport");
  ewsurl = preferences.getString("ewsurl");
  pathUpload = preferences.getString("pathUpload");
  token = preferences.getString("token");

  preferences.end();

  Serial.println("============= READ EEPROM =============");
  Serial.println("SSID : " + esid);
  Serial.println("Password : " + epass);
  Serial.println("Websocket : " + ewebsocket);
  Serial.println("Websocket Port : " + ewsport);
  Serial.println("Websocket Url : " + ewsurl);
  Serial.println("Path Upload : " + pathUpload);
  Serial.println("Token : " + token);
  Serial.println("============= READ EEPROM =============");
}

void resetEEPROM(void){
  preferences.begin("my-app",false);
  preferences.clear();
  preferences.end();
}

void writeEEPROM(
  String qsid = "", String qpass = "",
  String qwebsocket = "", String qwsport = "",
  String qwsurl = "", String qpathUpload = "",
  String qtoken = ""
)
{
  preferences.begin("my-app",false);

  if(qsid.length() > 0)
    preferences.putString("esid", qsid);

  if(qpass.length() > 0)
    preferences.putString("epass", qpass);

  if(qwebsocket.length() > 0)
    preferences.putString("ewebsocket", qwebsocket);

  if(qwsport.length() > 0)
    preferences.putString("ewsport", qwsport);

  if(qwsurl.length() > 0)
    preferences.putString("ewsurl", qwsurl);

  if(qpathUpload.length() > 0)
    preferences.putString("pathUpload", qpathUpload);

  if(qtoken.length() > 0)
    preferences.putString("token", qtoken);
 
   preferences.end();
}

bool testWifi(void) {
  int c = 0;
  Serial.println("Waiting for Wifi to connect");
  while ( c < 20 ) {
    if (WiFi.status() == WL_CONNECTED)
    {
      return true;
    }
    delay(500);
    Serial.print("*");
    c++;
  }
  Serial.println("");
  Serial.println("Connect timed out, opening AP");
  return false;
}

void launchWeb()
{
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("Local IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("SoftAP IP: ");
  Serial.println(WiFi.softAPIP());
  createWebServer();
  // Start the server
  server.begin();
  Serial.println("Server started");
}

void setupAP(void){
  delay(100);
  WiFi.softAP("ESP32-CAM", "");
  Serial.println("Initializing_Wifi_accesspoint");
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
    String qpathUpload = request->arg("pathUpload");
    String qtoken = request->arg("token");

    String json;
    if(
      qsid.length() > 0 || qpass.length() > 0 ||
      qwebsocket.length() > 0 || qwsport.length() > 0 ||
      qwsurl.length() > 0 || qpathUpload.length() > 0 ||
      qtoken.length() > 0
    ) {
        writeEEPROM(qsid,qpass,qwebsocket,qwsport,qwsurl,qpathUpload,qtoken);
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
    String json = "{\"Success\":\"successfully restart camera\"}";
    request->send(200, "application/json", json);
    delay(1000);
    ESP.restart();
    json = String();
  });

}

String sendPhoto() {
  String getAll, getBody;

  camera_fb_t * fb = esp_camera_fb_get();

  if(!fb) {
    Serial.println("Camera capture failed");
    delay(1000);
    ESP.restart();
  }
 
  Serial.println("Connecting to server: " + ewebsocket);

  if (client.connect(ewebsocket.c_str(), ewsport.toInt())) {
    Serial.println("Connection successful!");    
    String head = "--WebKitFormBoundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"esp32-cam.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
    String tail = "\r\n--WebKitFormBoundary--\r\n";

    uint32_t imageLen = fb->len;
    uint32_t extraLen = head.length() + tail.length();
    uint32_t totalLen = imageLen + extraLen;
  
    client.println("POST " + pathUpload + " HTTP/1.1");
    client.println("Host: " + ewebsocket);
    client.println("User-Agent: arduino-Web-Client");
    client.println("Authorization: Bearer " + token);
    client.println("Content-Type: multipart/form-data; boundary=WebKitFormBoundary");
    client.println("Content-Length: " + String(totalLen));
    client.println();
    client.print(head);
  
    uint8_t *fbBuf = fb->buf;
    size_t fbLen = fb->len;
    for (size_t n=0; n<fbLen; n=n+1024) {
      if (n+1024 < fbLen) {
        client.write(fbBuf, 1024);
        fbBuf += 1024;
      }
      else if (fbLen%1024>0) {
        size_t remainder = fbLen%1024;
        client.write(fbBuf, remainder);
      }
    }   
    client.print(tail);
    
    esp_camera_fb_return(fb);
    
    int timoutTimer = 10000;
    long startTimer = millis();
    boolean state = false;
    
    while ((startTimer + timoutTimer) > millis()) {
      Serial.print(".");
      delay(100);      
      while (client.available()) {
        char c = client.read();
        if (c == '\n') {
          if (getAll.length()==0) { state=true; }
          getAll = "";
        }
        else if (c != '\r') { getAll += String(c); }
        if (state==true) { getBody += String(c); }
        startTimer = millis();
      }
      if (getBody.length()>0) { break; }
    }
    Serial.println();
    client.stop();
    Serial.println(getBody);
  }
  else {
    getBody = "Connection to " + ewebsocket +  " failed.";
    Serial.println(getBody);
  }
  return getBody;
}

void liveCam(void){
  camera_fb_t * fb = esp_camera_fb_get();

  if(!fb) {
    Serial.println("Camera capture failed");
    esp_camera_fb_return(fb);
    return;
  }

  webSocket.sendBIN(fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void loop() {
  if((WiFi.status() == WL_CONNECTED)){
    webSocket.loop();  
    if(live_cam == true) liveCam();
  }
}

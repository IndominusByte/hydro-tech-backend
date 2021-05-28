/*
 - PH (dfrobot) [✅]
 - TDS (dfrobot) // ppm [✅]
 - LDR cahaya >= 200 DARK else BRIGHT [✅]
 - Ultrasonic // ketinggian air [✅]
 - Suhu (ds18b20) [✅]
 
 - Relay phup [✅], phdown [✅], ppm [✅], solenoid [✅]
 - Relay lampu [✅]
*/
#include <stdio.h>
#include <string.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>
#include <LiquidCrystal_I2C.h>

// set lcd 20x4
LiquidCrystal_I2C lcd(0x27,20,4);

/* SENSOR TEMP SETTING */
#define ONE_WIRE_BUS 2 // Data wire is plugged into digital pin 2 on the Arduino
OneWire oneWire(ONE_WIRE_BUS); // Setup a oneWire instance to communicate with any OneWire device
DallasTemperature sensors(&oneWire); // Pass oneWire reference to DallasTemperature library
/* SENSOR PH SETTING */
#define pHAnalog A0 // pH meter Analog output to Arduino Analog Input 0
#define pHArrayLength 5 // times of collection
/* SENSOR TDS SETTING */
#define tdsAnalog A1
#define VREF 5.0 // analog reference voltage(Volt) of the ADC
#define SCOUNT 5 // sum of sample point
/* SENSOR LDR SETTING */
#define ldrAnalog A3
/* SENSOR ULTRASONIC SETTING */
#define trigPin 9
#define echoPin 10
/* RELAY SETTING */
#define tdsRelay 6
#define phupRelay 7
#define phdownRelay 5
#define solenoidRelay 4
#define lampRelay 11

// incoming data serial variable
bool send_data = true;
char payload[300];

/* STATUS RELAY */
String lampStatus, pHUpStatus, pHDownStatus;
String nutritionStatus, solenoidStatus;
/* STATUS BUTTON IN USER */
/* 1 its mean on 0 its mean off */
int lampStatusUser, pHUpStatusUser, pHDownStatusUser;
int nutritionStatusUser, solenoidStatusUser;

/* CONTROL SETTING & SENSOR CALIBRATION */
float pHCal, tdsCal;
float pHMax, pHMin, tdsMin;
/* TANK IN CM */
int tankHeight, tankMin;

/* SENSOR ULTRASONIC VAR */
long duration;
int distance, tankPercent;
/* SENSOR LDR VAR */
int ldrValue;
String ldrStatus;
/* SENSOR TDS VAR */
int analogBuffer[SCOUNT]; // store the analog value in the array, read from ADC
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0, copyIndex = 0;
float averageVoltage = 0, tdsValue = 0;
/* SENSOR PH VAR */
float phValue;
int pHArray[pHArrayLength];
int pHArrayIndex = 0;
/* SENSOR TEMP VAR */
float temp;

// declare reset fuction at address 0
void(* resetFunc) (void) = 0;

void setup() {
  // Temp sensor begin
  sensors.begin();
  // Tds sensor begin
  pinMode(tdsAnalog,INPUT);

  // Ultrasonic sensor begin
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Relay begin
  pinMode(tdsRelay,OUTPUT);
  digitalWrite(tdsRelay,HIGH);

  pinMode(phupRelay,OUTPUT);
  digitalWrite(phupRelay,HIGH);

  pinMode(phdownRelay,OUTPUT);
  digitalWrite(phdownRelay,HIGH);

  pinMode(solenoidRelay,OUTPUT);
  digitalWrite(solenoidRelay,HIGH);

  pinMode(lampRelay,OUTPUT);
  digitalWrite(lampRelay,HIGH);

  // lcd begin
  lcd.init();
  // turn on backlight and print message
  lcd.backlight();

  Serial.begin(9600);
  while(!Serial) continue;

  delay(10);
  readEEPROM();
}

void loop() { 
  setTemp();
  setpH();
  setTds();
  setLdr();
  setUltrasonic();
  relayController();

  getDataSerial();
  displayLcd();
  // displayDebug();
  delay(1000);
}

template <class T> int EEPROM_writeAnything(int ee, const T& value)
{
    const byte* p = (const byte*)(const void*)&value;
    int i;
    for (i = 0; i < sizeof(value); i++)
        EEPROM.write(ee++, *p++);
    return i;
}

template <class T> int EEPROM_readAnything(int ee, T& value)
{
    byte* p = (byte*)(void*)&value;
    int i;
    for (i = 0; i < sizeof(value); i++)
        *p++ = EEPROM.read(ee++);
    return i;
}

void readEEPROM(){
  // Read eeprom
  EEPROM_readAnything(15,pHCal);
  EEPROM_readAnything(25,tdsCal);
  EEPROM_readAnything(35,pHMax);
  EEPROM_readAnything(45,pHMin);
  EEPROM_readAnything(55,tdsMin);
  EEPROM_readAnything(65,tankHeight);
  EEPROM_readAnything(75,tankMin);
  EEPROM_readAnything(85,lampStatusUser);
  EEPROM_readAnything(95,pHUpStatusUser);
  EEPROM_readAnything(105,pHDownStatusUser);
  EEPROM_readAnything(115,nutritionStatusUser);
  EEPROM_readAnything(125,solenoidStatusUser);

  Serial.println(F("============= READ EEPROM ============="));
  Serial.println("phcal : " + String(pHCal));
  Serial.println("tdscal : " + String(tdsCal));
  Serial.println("phmax : " + String(pHMax));
  Serial.println("phmin : " + String(pHMin));
  Serial.println("tdsmin : " + String(tdsMin));
  Serial.println("tankheight : " + String(tankHeight));
  Serial.println("tankmin : " + String(tankMin));
  Serial.println("lamp : " + String(lampStatusUser));
  Serial.println("phup : " + String(pHUpStatusUser));
  Serial.println("phdown : " + String(pHDownStatusUser));
  Serial.println("nutrition : " + String(nutritionStatusUser));
  Serial.println("solenoid : " + String(solenoidStatusUser));
  Serial.println(F("============= READ EEPROM ============="));
}

void displayDebug() {
  Serial.println(F("=============== DEBUG ============="));
  Serial.println("Temperature: " + String(temp));
  Serial.println("pH: " + String(phValue));
  Serial.println("Tds: " + String(tdsValue));
  Serial.println("Ldr: " + String(ldrValue));
  Serial.println("Ldr Status: " + String(ldrStatus));
  Serial.println("Distance : " + String(distance) + " cm");
  Serial.println("Tank Remaining : " + String(tankPercent) + " %");
  Serial.println(F("========== CONTROL STATUS =========="));
  Serial.println("Lamp: " + lampStatus);
  Serial.println("pH Up: " + pHUpStatus);
  Serial.println("pH Down: " + pHDownStatus);
  Serial.println("Nutrition: " + nutritionStatus);
  Serial.println("Solenoid: " + solenoidStatus);
  Serial.println(F("==================================="));
}

void displayLcd(){
  lcd.clear();
  lcd.setCursor(3,0);
  lcd.print("PH   : ");
  lcd.print(String(phValue));
  lcd.setCursor(3,1);
  lcd.print("TDS  : ");
  lcd.print(String(tdsValue));
  lcd.setCursor(3,2);
  lcd.print("TEMP : ");
  lcd.print(String(temp));
  lcd.print((char)223);
  lcd.print("C");
  lcd.setCursor(3,3);
  lcd.print("TANK : ");
  lcd.print(String(tankPercent));
  lcd.print("%");
  delay(100);
}

void getDataSerial(){
  String received = Serial.readStringUntil('\n');

  if(received.indexOf("stop_hydro") != -1){
    send_data = false;
  }

  if(received.indexOf("set_hydro") != -1){
    Serial.println("received -> " + received);
    received.toCharArray(payload,300);
    
    for(char *p = strtok(payload, ","); p != NULL; p = strtok(NULL, ",")){
      int l = 0;
      String tmp[2];
      char *token, *str, *tofree;
      tofree = str = strdup(p);
      while((token = strsep(&str,":"))){
        tmp[l] = token;
        l++;
      }

      if(tmp[0] == "phmax"){
        pHMax = tmp[1].toFloat();
        EEPROM_writeAnything(35,pHMax);
      }
      if(tmp[0] == "phmin"){
        pHMin = tmp[1].toFloat();
        EEPROM_writeAnything(45,pHMin);
      }
      if(tmp[0] == "tdsmin"){
        tdsMin = tmp[1].toFloat();
        EEPROM_writeAnything(55,tdsMin);
      }
      if(tmp[0] == "phcal"){
        pHCal = tmp[1].toFloat();
        EEPROM_writeAnything(15,pHCal);
      }
      if(tmp[0] == "tdscal"){
        tdsCal = tmp[1].toFloat();
        EEPROM_writeAnything(25,tdsCal);
      }
      if(tmp[0] == "tankheight"){
        tankHeight = tmp[1].toInt();
        EEPROM_writeAnything(65,tankHeight);
      }
      if(tmp[0] == "tankmin"){
        tankMin = tmp[1].toInt();
        EEPROM_writeAnything(75,tankMin);
      }
      
      if(tmp[0] == "lamp"){
        lampStatusUser = (tmp[1] == "on") ? 1 : 0;
        EEPROM_writeAnything(85,lampStatusUser);
      }
      if(tmp[0] == "phup") {
        pHUpStatusUser = (tmp[1] == "on") ? 1 : 0;
        EEPROM_writeAnything(95,pHUpStatusUser);
      }
      if(tmp[0] == "phdown") {
        pHDownStatusUser = (tmp[1] == "on") ? 1 : 0;
        EEPROM_writeAnything(105,pHDownStatusUser);
      }
      if(tmp[0] == "nutrition") {
        nutritionStatusUser = (tmp[1] == "on") ? 1 : 0;
        EEPROM_writeAnything(115,nutritionStatusUser);
      }
      if(tmp[0] == "solenoid") {
        solenoidStatusUser = (tmp[1] == "on") ? 1 : 0;
        EEPROM_writeAnything(125,solenoidStatusUser);
      }

      free(tofree);
    }
    memset(payload, 0, sizeof(payload));

    Serial.println("delay 3 second");
    delay(3000);
    Serial.println("set_hydro_true");
    delay(1000);
    resetFunc();
  }

  if(send_data == true){
    sendDataSerial();
  }
}

void sendDataSerial(){
  String data = "kind:Hydro,ph:" + String(phValue) + "," +
    "temp:" + String(temp) + "," + 
    "tank:" + String(tankPercent) + "," + 
    "tds:" + String(tdsValue) + "," + 
    "ldr:" + String(ldrStatus) + "," +
    "lamp:" + String(lampStatus) + "," +
    "phup:" + String(pHUpStatus) + "," +
    "phdown:" + String(pHDownStatus) + "," +
    "nutrition:" + String(nutritionStatus) + "," +
    "solenoid:" + String(solenoidStatus);
    
  Serial.println(data);
}

void setLdr(){
 ldrValue = analogRead(ldrAnalog);
 if(ldrValue >= 200) ldrStatus = "dark";
 else ldrStatus = "bright";
}

void setTemp() {
  sensors.requestTemperatures(); // Send the command to get temperatures
  temp = sensors.getTempCByIndex(0); // Set temperature in Celsius
}

void setpH() {
  static float voltage;

  pHArray[pHArrayIndex++] = analogRead(pHAnalog);
  if(pHArrayIndex == pHArrayLength) pHArrayIndex = 0;
  voltage = avgpHValue(pHArray, pHArrayLength) * 5.0 / 1024;
  phValue = 3.5 * voltage + pHCal;
}

void setTds() {
  static unsigned long analogSampleTimepoint = millis();
  // every 40 milliseconds,read the analog value from the ADC
  if(millis() - analogSampleTimepoint > 40U){
     analogSampleTimepoint = millis();
     analogBuffer[analogBufferIndex] = analogRead(tdsAnalog); // read the analog value and store into the buffer
     analogBufferIndex++;
     if(analogBufferIndex == SCOUNT) 
      analogBufferIndex = 0;
   }   

   static unsigned long printTimepoint = millis();
   if(millis() - printTimepoint > 800U){
      printTimepoint = millis();
      for(copyIndex = 0; copyIndex < SCOUNT; copyIndex++)
        analogBufferTemp[copyIndex] = analogBuffer[copyIndex];

      // read the analog value more stable by the median filtering algorithm, and convert to voltage value
      averageVoltage = getMedianNum(analogBufferTemp,SCOUNT) * (float)VREF / 1024.0;
      //temperature compensation formula: fFinalResult(25^C) = fFinalResult(current)/(1.0+0.02*(fTP-25.0));
      float compensationCoefficient=1.0 + 0.02 * (temp - 25.0);
      //temperature compensation
      float compensationVolatge = averageVoltage / compensationCoefficient;
      //convert voltage value to tds value
      tdsValue = (
        133.42 * compensationVolatge * compensationVolatge * compensationVolatge - 255.86 *
        compensationVolatge * compensationVolatge + 857.39 * compensationVolatge
      ) * 0.5;

      tdsValue = (tdsValue == 0.0) ? tdsValue : tdsValue + tdsCal;
    }
}

void setUltrasonic() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = (duration * 0.034) / 2;
  tankPercent = 100.0 - (((float)distance / (float)tankHeight) * 100.0);
  tankPercent = (tankPercent < 0.0) ? 0.0 : tankPercent;
 }

int getMedianNum(int bArray[], int iFilterLen) {
  int bTab[iFilterLen];
  int i, j, bTemp;

  for(byte i = 0; i < iFilterLen; i++)
    bTab[i] = bArray[i];

  for(j = 0; j < iFilterLen - 1; j++) {
    for(i = 0; i < iFilterLen - j - 1; i++) {
      if(bTab[i] > bTab[i + 1]) {
        bTemp = bTab[i];
        bTab[i] = bTab[i + 1];
        bTab[i + 1] = bTemp;
      }
    }
  }

  if((iFilterLen & 1) > 0) bTemp = bTab[(iFilterLen - 1) / 2];
  else bTemp = (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;

  return bTemp;
}

double avgpHValue(int* arr, int number){
  double avg;
  long amount = 0;
  int i, max, min;

  if(number <= 0){
    Serial.println(F("Error number for the array to avraging!/n"));
    return 0;
  }

  // less than 5, calculated directly statistics
  if(number < 5){
    for(i = 0;i < number; i++){
      amount += arr[i];
    }
    avg = amount / number;
    return avg;
  }else{
    if(arr[0] < arr[1]){
      min = arr[0];
      max = arr[1];
    }
    else{
      min = arr[1];
      max = arr[0];
    }

    for(i = 2; i < number; i++){
      if(arr[i] < min){
        amount += min;
        min = arr[i];
      }else {
        if(arr[i] > max){
          amount += max;
          max = arr[i];
        }else{
          amount+=arr[i];
        }
      }
    }
    avg = (double)amount / (number - 2);
  }
  return avg;
}

void relayController(){
  // ldr >= 200 DARK and turn on lamp
  if(ldrValue >= 200 || lampStatusUser == 1){
    lampStatus = "on";
    digitalWrite(lampRelay,LOW);
  }
  else {
    lampStatus = "off";
    digitalWrite(lampRelay,HIGH); 
  }

  if(tankMin < distance || solenoidStatusUser == 1){
    solenoidStatus = "on";
    digitalWrite(solenoidRelay,LOW);
    delay(500);
    digitalWrite(solenoidRelay,HIGH);
  }else solenoidStatus = "off";

  if(phValue < pHMin || pHUpStatusUser == 1){
      pHUpStatus = "on";
      digitalWrite(phupRelay,LOW);
      delay(250);
      digitalWrite(phupRelay,HIGH);
  } else pHUpStatus = "off";
      
  if(phValue > pHMax || pHDownStatusUser == 1){
      pHDownStatus = "on";
      digitalWrite(phdownRelay,LOW);
      delay(250);
      digitalWrite(phdownRelay,HIGH);
  } else pHDownStatus = "off";
      
  if((tdsValue < tdsMin && tdsValue != 0.0) || nutritionStatusUser == 1){
      nutritionStatus = "on";
      digitalWrite(tdsRelay,LOW);
      delay(250);
      digitalWrite(tdsRelay,HIGH);
  } else nutritionStatus = "off";
}

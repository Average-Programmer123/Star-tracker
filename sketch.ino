#include <AccelStepper.h>
#include <ArduinoJson.h>
AccelStepper tracker(AccelStepper::FULL4WIRE, 8, 10, 9, 11);
StaticJsonDocument<64> doc;
int isTracking=0;
void setup() {
  Serial.begin(9600);   
  tracker.setMaxSpeed(500); 
}
void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    doc.clear();
    DeserializationError error = deserializeJson(doc, input);

    if (!error) {
      isTracking = doc["s"];
      if (isTracking==1) {
        float newSpeed = 0.5;
        tracker.setSpeed(newSpeed);
      } else {
        tracker.setSpeed(0);
  digitalWrite(8, LOW);
  digitalWrite(10, LOW);
  digitalWrite(9, LOW);
  digitalWrite(11, LOW);
      }
    }
  }

  if (isTracking==1) {
    tracker.runSpeed();
  }
}

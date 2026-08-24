#include <Servo.h>
#include <SoftwareSerial.h>

Servo myservo;  // Creating servo object

SoftwareSerial BT(10, 9); // The pins need to be defined in reverse (RX to TX and vice versa)

char command = 'S';
char mode = 'M'; //Defualt is manual mode (prevents the robot moving until the user is ready)

//Defining the pins
const int LM_control = 11;
const int LM_in1 = 13;
const int LM_in2 = 12;
const int RM_control = 6;
const int RM_in1 = 8;
const int RM_in2 = 7;

const int ultrasonic_trig = 4;
const int ultrasonic_echo = 2;

const int servoPin = 3;

//Defining variables
long duration; 
float distance;

float rightDistance;
float leftDistance;

// Defining constants
const float safeDistance = 20; // cm

float ultrasonicSensor() {
  // Clears the trig pin
  digitalWrite(ultrasonic_trig, LOW);
  delayMicroseconds(2);

  // Sets the trig pin on HIGH state for 10 micro seconds
  digitalWrite(ultrasonic_trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(ultrasonic_trig, LOW);

  // Reads the echoPin, returns the sound wave travel time in microseconds - 30 ms timeout
  duration = pulseIn(ultrasonic_echo, HIGH, 30000);

  // Handle timeout
  if (duration == 0) {
    distance = 999;  // no object detected
  } else {
    distance = duration * 0.034 / 2;
  }

  // Outputting distance to serial
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  return distance;

}

void stopMotors() {

  //Both motors stopped
  digitalWrite(LM_in1, LOW);
  digitalWrite(LM_in2, LOW);
  analogWrite(LM_control, 0);

  digitalWrite(RM_in1, LOW);
  digitalWrite(RM_in2, LOW);
  analogWrite(RM_control, 0);
}

void moveForward() {

  //Left motor forwards
  digitalWrite(LM_in1, LOW);
  digitalWrite(LM_in2, HIGH);
  analogWrite(LM_control, 190);

  //Right motor forwards
  digitalWrite(RM_in1, LOW);
  digitalWrite(RM_in2, HIGH);
  analogWrite(RM_control, 190);
}

// Manual movement functions

void turnRight() {

  //Left motor forwards
  digitalWrite(LM_in1, LOW);
  digitalWrite(LM_in2, HIGH);
  analogWrite(LM_control, 200);

  //Right motor backwards
  digitalWrite(RM_in1, HIGH);
  digitalWrite(RM_in2, LOW);
  analogWrite(RM_control, 200);
}

void turnLeft() {

   //Left motor backwards
  digitalWrite(LM_in1, HIGH);
  digitalWrite(LM_in2, LOW);
  analogWrite(LM_control, 200);

  //Right motor forwards
  digitalWrite(RM_in1, LOW);
  digitalWrite(RM_in2, HIGH);
  analogWrite(RM_control, 200);
}

void reverse() {
  digitalWrite(LM_in1, HIGH);
  digitalWrite(LM_in2, LOW);
  analogWrite(LM_control, 180);

  digitalWrite(RM_in1, HIGH);
  digitalWrite(RM_in2, LOW);
  analogWrite(RM_control, 180);

}

// Autonomous movement functions
void checkSides () {

  // Checking the left side
  myservo.write(20);
  delay(700);

  leftDistance = ultrasonicSensor();

  // Checking the right side
  myservo.write(160);
  delay(700);
  
  rightDistance = ultrasonicSensor();

  myservo.write(90);

  if (rightDistance >= 20 && rightDistance >= leftDistance) {
    autoTurnRight();
  }

  else if (leftDistance >= 20 && leftDistance >= rightDistance) {
    autoTurnLeft();
  }

  else {
    autoReverse();
  }
}

void autoTurnLeft () {

  //Left motor stopped
  digitalWrite(LM_in1, LOW);
  digitalWrite(LM_in2, LOW);
  analogWrite(LM_control, 0);

  //Right motor forwards
  digitalWrite(RM_in1, LOW);
  digitalWrite(RM_in2, HIGH);
  analogWrite(RM_control, 200);

  delay(1000);

  moveForward();
}

void autoTurnRight () {

  //Left motor forwards
  digitalWrite(LM_in1, LOW);
  digitalWrite(LM_in2, HIGH);
  analogWrite(LM_control, 200);

  //Right motor stopped
  digitalWrite(RM_in1, LOW);
  digitalWrite(RM_in2, LOW);
  analogWrite(RM_control, 0);
  
  delay(1000);

  moveForward();
}

void autoReverse() {

  //Left motor backwards
  digitalWrite(LM_in1, HIGH);
  digitalWrite(LM_in2, LOW);
  analogWrite(LM_control, 180);

  //Right motor backwards
  digitalWrite(RM_in1, HIGH);
  digitalWrite(RM_in2, LOW);
  analogWrite(RM_control, 180);

  delay(800);

  stopMotors();
}

void setup() {

  Serial.begin(9600); // Starts the serial communication
  BT.begin(9600); // Starts HM-10 communication

  // Defining the pins
  pinMode(LM_control, OUTPUT);
  pinMode(LM_in1, OUTPUT);
  pinMode(LM_in2, OUTPUT);
  pinMode(RM_control, OUTPUT);
  pinMode(RM_in1, OUTPUT);
  pinMode(RM_in2, OUTPUT);

  pinMode(ultrasonic_trig, OUTPUT);
  pinMode(ultrasonic_echo, INPUT);

  pinMode(servoPin, OUTPUT);
  myservo.attach(servoPin,600,2300);

  // Putting the robot into its starting state
  myservo.write(90);
  stopMotors();

}

void loop() {

  if (BT.available()) {
    command = BT.read();

    Serial.print("Command received: "); // For testing
    Serial.println(command);
  }

  // Stop command works in manual or autonomous mode
  if (command == 'S') {
    stopMotors();
    return;
  }

  // Mode control
  if (command == 'A') {
    mode = 'A';
    myservo.write(90);
  }

  if (command == 'P') {
    mode = 'P';
    myservo.write(90);
    stopMotors();
  }

  if (command == 'M') {
    mode = 'M';
    myservo.write(90);
    stopMotors();
  }

  // Autonomous mode
  if (mode == 'A'){

    distance = ultrasonicSensor(); // Measuring the distance

    // If path is clear, move forward
    if (distance > 25) {
      moveForward();
    }

    // If obstacle is detected at a medium distance, stop and check sides
    else if (distance <= 25 && distance >= 10) {
      stopMotors();

      checkSides();
    }

    // If obstacle is detected at close distance, reverse
    else if (distance < 10) {
      stopMotors();

      delay(200);

      autoReverse();
    }
  }

  // Assisted mode
  if (mode == 'P') {

    distance = ultrasonicSensor(); // Continously measuring the distance

    if (command == 'F') {

      // It will only move forward if the path is clear
      if (distance > safeDistance) {
        moveForward();
      }

      else {
        stopMotors();
      }
    }

    // Other controls still behave manually
    if (command == 'B') reverse();

    if (command == 'L') turnLeft();

    if (command == 'R') turnRight();

  }

  // Manual mode
  if (mode == 'M') {

    if (command == 'F') moveForward();

    if (command == 'B') reverse();

    if (command == 'L') turnLeft();

    if (command == 'R') turnRight();

  }

}

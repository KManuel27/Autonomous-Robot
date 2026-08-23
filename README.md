# Autonomous Mobile Robot

An Arduino-based mobile robot developed to explore autonomous navigation,
embedded control and Bluetooth Low Energy communication.

The robot supports three operating modes:

- **Manual** – direct user control from a desktop interface.
- **Assisted** – manual control with ultrasonic obstacle protection.
- **Autonomous** – reactive obstacle avoidance using an ultrasonic sensor
  mounted on a servo.

The final control interface was developed in Python using Tkinter and Bleak
and communicates wirelessly with the Arduino through an HM-10 BLE module.

## Features

- Autonomous obstacle detection and avoidance
- Servo-mounted ultrasonic environmental scanning
- Manual remote driving
- Assisted driving with forward collision prevention
- Bluetooth Low Energy communication
- Python desktop control interface
- Connection status and error handling
- Adjustable motor speed and obstacle detection thresholds

## Hardware

- Arduino Uno R3
- L298N dual H-bridge motor driver
- 4 × 6 V TT DC geared motors
- HC-SR04 ultrasonic distance sensor
- SG90 micro servo motor
- HM-10 Bluetooth Low Energy (BLE) module
- 3D-printed PLA chassis
- 6 × AA battery holder
- 9 V battery
- Power switch

## System Overview

The system consists of an Arduino-based mobile platform controlled either by
its onboard autonomous navigation algorithm or through a Python desktop
controller.

The Python application uses:

- **Tkinter** for the graphical user interface
- **Bleak** for Bluetooth Low Energy communication
- **asyncio** for asynchronous BLE operations
- **threading** to separate Bluetooth communication from the GUI

Movement and mode commands are transmitted to an HM-10 BLE module, which
forwards them to the Arduino over serial.

## Operating Modes

### Manual

The user directly controls forward, reverse, left and right movement from the
Python interface. Releasing a movement button sends a stop command to the
Arduino.

### Assisted

Assisted mode retains direct user control while continuously monitoring the
ultrasonic sensor. Forward movement is prevented when an obstacle is detected
within the defined safety distance.

### Autonomous

The robot continuously measures the distance ahead.

When an obstacle is detected, the robot stops and rotates the ultrasonic sensor
using a servo to measure the available space on either side. It then turns
towards the clearer path or reverses if neither side provides sufficient
clearance.

## Software Architecture

```text
Python Controller
Tkinter + Bleak
       |
       | Bluetooth Low Energy
       v
     HM-10
       |
       | Serial
       v
     Arduino
     /     \
    /       \
Motors    Sensors
           |
     Ultrasonic + Servo

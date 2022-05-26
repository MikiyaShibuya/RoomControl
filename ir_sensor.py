#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import threading

class IR_Sensor:
  def __init__(self):
    self.ir_pin = 4
    self.thread = None
    self.mutex = threading.Lock()
    self.human = False

    self.terminate = True

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.ir_pin, GPIO.IN)

  def _loop(self):
    while True:
      det = GPIO.input(self.ir_pin)

      self.mutex.acquire()
      terminate = self.terminate
      self.human = det > 0
      self.mutex.release()

      if terminate:
        break

      time.sleep(0.5)

  def start(self):
    self.mutex.acquire()
    if not self.terminate:
        return
    self.terminate = False
    self.mutex.release()

    thread = threading.Thread(target=self._loop)
    thread.start()

  def stop(self):
    self.mutex.acquire()
    self.terminate = True
    self.mutex.release()

  def get(self):
    self.mutex.acquire()
    human = self.human
    self.human = False
    self.mutex.release()

    return human
    

if __name__ == '__main__':

  ir_det = IR_Sensor()
  ir_det.start()

  while True:

    det = ir_det.get()

    print(det)

    time.sleep(1)

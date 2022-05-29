#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import threading

class IR_Sensor:
  def __init__(self, interval=0.5):
    self._ir_pin = 4
    self._mutex = threading.Lock()
    self._human = False

    self._terminate = True
    self._interval = interval

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self._ir_pin, GPIO.IN)

  def _loop(self):
    while True:
      # Inverted by level conversion
      det = GPIO.input(self._ir_pin) == 0

      self._mutex.acquire()
      terminate = self._terminate
      self._human = self._human or det
      self._mutex.release()

      if terminate:
        break

      time.sleep(self._interval)

  def start(self):
    self._mutex.acquire()
    if not self._terminate:
        return
    self._terminate = False
    self._mutex.release()

    thread = threading.Thread(target=self._loop)
    thread.start()

  def stop(self):
    self._mutex.acquire()
    self._terminate = True
    self._mutex.release()

  def get(self):
    self._mutex.acquire()
    human = self._human
    self._human = False
    self._mutex.release()

    return human


if __name__ == '__main__':

  ir_det = IR_Sensor()
  ir_det.start()

  while True:

    det = ir_det.get()

    print(det)

    time.sleep(1)


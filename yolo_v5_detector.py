#!/usr/bin/env python3

# reference : https://learnopencv.com/object-detection-using-yolov5-and-opencv-dnn-in-c-and-python/

import cv2
import numpy as np
import time
import threading

INPUT_WIDTH = 640
INPUT_HEIGHT = 640
CONFIDENCE_THRESHOLD = 0.45
SCORE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.45
FONT_SCALE = 0.7
FONT_FACE = cv2.FONT_HERSHEY_SIMPLEX

class YOLO_V5:
  def __init__(self, classFile, modelWeights):
    with open(classFile, 'rt') as f:
        self.classes = f.read().rstrip('\n').split('\n')

    self.net = cv2.dnn.readNet(modelWeights)

  def infer(self, input_image):
    blob = cv2.dnn.blobFromImage(input_image, 1/255, (INPUT_WIDTH, INPUT_HEIGHT), [0, 0, 0], 1, crop=False)
    self.net.setInput(blob)
    outputs = self.net.forward(self.net.getUnconnectedOutLayersNames())

    return self._post_process(input_image, outputs)

  def _post_process(self, input_image, outputs):
    # Lists to hold respective values while unwrapping.
    cand_class_ids = []
    cand_confidences = []
    cand_boxes = []
    # Rows.
    rows = outputs[0].shape[1]
    image_height, image_width = input_image.shape[:2]
    # Resizing factor.
    x_factor = image_width / INPUT_WIDTH
    y_factor =  image_height / INPUT_HEIGHT
    # Iterate through detections.
    for r in range(rows):
      row = outputs[0][0][r]
      confidence = row[4]
      # Discard bad detections and continue.
      if confidence < CONFIDENCE_THRESHOLD:
        continue

      classes_scores = row[5:]
      # Get the index of max class score.
      class_id = np.argmax(classes_scores)
      #  Continue if the class score is above threshold.
      if classes_scores[class_id] < SCORE_THRESHOLD:
        continue

      cand_confidences.append(confidence)
      cand_class_ids.append(class_id)
      cx, cy, w, h = row[0], row[1], row[2], row[3]
      left = int((cx - w/2) * x_factor)
      top = int((cy - h/2) * y_factor)
      width = int(w * x_factor)
      height = int(h * y_factor)
      box = np.array([left, top, width, height])
      cand_boxes.append(box)

    indices = cv2.dnn.NMSBoxes(cand_boxes, cand_confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)

    # Gather filtered items
    class_ids = []
    confidences = []
    boxes = []

    for i in indices:
      class_ids.append(cand_class_ids[i])
      confidences.append(cand_confidences[i])
      boxes.append(cand_boxes[i])

    return class_ids, confidences, boxes

  def _draw_label(self, im, label, x, y):
    """Draw text onto image at location."""
    # Get text size.
    text_size = cv2.getTextSize(label, FONT_FACE, FONT_SCALE, 1)
    dim, baseline = text_size[0], text_size[1]
    # Use text size to create a BLACK rectangle.
    cv2.rectangle(im, (x,y), (x + dim[0], y + dim[1] + baseline), (0,0,0), cv2.FILLED);
    # Display text inside the rectangle.
    cv2.putText(im, label, (x, y + dim[1]), FONT_FACE, FONT_SCALE, (0, 255, 255), 1, cv2.LINE_AA)

  def draw_bboxes(self, image, outputs):
    class_ids, confidences, boxes = outputs

    for i in range(len(class_ids)):
      box = boxes[i]
      left = box[0]
      top = box[1]
      width = box[2]
      height = box[3]
      # Draw bounding box.
      cv2.rectangle(image, (left, top), (left + width, top + height), (255, 0, 0), 3)
      # Class label.
      label = "{}:{:.2f}".format(self.classes[class_ids[i]], confidences[i])
      # Draw label.
      self._draw_label(image, label, left, top)

    return image


if __name__ == '__main__':
  classFile = 'coco.names'
  modelWeights = 'yolov5n.onnx'
  yolo = YOLO_V5(classFile, modelWeights)
  cam = cv2.VideoCapture(0)

  while True:
    ret, frame = cam.read()
    if not ret:
      continue

    cv2.imshow('prev', frame)
    key = cv2.waitKey(20)

    if key != 114:
      continue

    outputs = yolo.infer(frame)
    img = yolo.draw_bboxes(frame.copy(), outputs)

    cv2.imshow('infer', img)
    cv2.waitKey(1)


import os
import sys
sys.path.append('/content/gdrive/MyDrive/yolov7')


import argparse
import time
from pathlib import Path
import cv2
import torch
import numpy as np
import torch.backends.cudnn as cudnn
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel
import time
import moviepy.editor as mp

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
    # Resize and pad image while meeting stride-multiple constraints
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better test mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return img, ratio, (dw, dh)


#classes_to_filter = ['Coverall']  #You can give list of classes to filter by name, Be happy you don't have to put class number. ['train','person' ]
all_class_names = ['Safety Helmet', 'No Safety Helmet', 'Coverall', 'No Coverall', 'Safety Gloves', 'No Safety Gloves', 'Safety Shoes', 'No Safety Shoes', 'Drilling Area', 'Safety Glasses', 'No Safety Glasses', 'Person', 'Harness']
classes_to_filter = ['No Safety Helmet','No Coverall','No Safety Gloves','No Safety Shoes','No Safety Glasses']
zone_detection_class_filter = ['Person','Drilling Area']
specific_class_indices = [all_class_names.index(class_name) for class_name in classes_to_filter]
zone_detect_class_indices = [all_class_names.index(class_name) for class_name in zone_detection_class_filter]
current_dir = os.path.dirname(os.path.abspath(__file__))
opt = {

    "weights": os.path.join(current_dir, "best.pt"),  # Path to weights file default weights are for nano model
    "yaml": os.path.join(current_dir, "data/SafeVision_Detect.yaml"),
    "img-size": 640,  # default image size
    "conf-thres": 0.35,  # confidence threshold for inference.
    "iou-thres": 0.45,  # NMS IoU threshold for inference.
    "device": 'cpu',  # device to run our model i.e. 0 or 0,1,2,3 or cpu
    "classes": ['Coverall','Safety Helmet','Safety Gloves','Safety Shoes','Safety Glasses','Harness']  # list of classes to filter or None

}

def video_detection(path_x='' ,conf_=0.25):
  import time
  start_time = time.time()
  # total_detections = 0

  video_path = path_x

  video = cv2.VideoCapture(video_path)


  #Video information
  fps = video.get(cv2.CAP_PROP_FPS)
  w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
  h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
  nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

  # Initialzing object for writing video output
  # output = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'DIVX'),fps , (w,h))
  torch.cuda.empty_cache()
  # Initializing model and setting it for inference
  with torch.no_grad():
    weights, imgsz = opt['weights'], opt['img-size']
    set_logging()
    device = select_device(opt['device'])
    half = device.type != 'cpu'
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size
    if half:
      model.half()

    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
    if device.type != 'cpu':
      model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))

    classes = None
    if opt['classes']:
      classes = []
      for class_name in opt['classes']:
        classes.append(opt['classes'].index(class_name))

    coverall_count = 0
    helmet_count = 0

    for j in range(nframes):
        

        ret, img0 = video.read()
        if ret:
          img = letterbox(img0, imgsz, stride=stride)[0]
          img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
          img = np.ascontiguousarray(img)
          img = torch.from_numpy(img).to(device)
          img = img.half() if half else img.float()  # uint8 to fp16/32
          img /= 255.0  # 0 - 255 to 0.0 - 1.0
          if img.ndimension() == 3:
            img = img.unsqueeze(0)

          # Inference
          t1 = time_synchronized()
          pred = model(img, augment= False)[0]

          # conf = 0.5
          total_detections = 0
          #pred = non_max_suppression(pred, conf_, opt['iou-thres'], classes= classes, agnostic= False)
          pred = non_max_suppression(pred, conf_, opt['iou-thres'], classes=specific_class_indices, agnostic=False)
          t2 = time_synchronized()

          for i, det in enumerate(pred):
            s = ''
            s += '%gx%g ' % img.shape[2:]  # print string
            gn = torch.tensor(img0.shape)[[1, 0, 1, 0]]
            no_coverall_count = 0
            no_helmet_count = 0
            no_gloves_count = 0
            no_glasses_count = 0
            total_safety_violations = 0
            # Initialize an empty dictionary to store class counts
            class_counts = {}

            if len(det):
              det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()

              for c in det[:, -1].unique():
                n = (det[:, -1] == c).sum()  # detections per class
                total_detections += int(n)
                s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                if names[int(c)] == 'No Coverall':
                    no_coverall_count += int(n)
                if names[int(c)] == 'No Safety Helmet':
                    no_helmet_count += int(n)
                if names[int(c)] == 'No Safety Gloves':
                    no_gloves_count += int(n)
                if names[int(c)] == 'No Safety Glasses':
                    no_glasses_count += int(n)
                if names[int(c)] == 'No Coverall' or names[int(c)] == 'No Safety Helmet' or names[int(c) == 'No Safety Gloves'] or names[int(c) == 'No Safety Glasses']:
                    total_safety_violations = no_coverall_count + no_helmet_count + no_gloves_count + no_glasses_count

              for *xyxy, conf, cls in reversed(det):

                label = f'{names[int(cls)]} {conf:.2f}'
                plot_one_box(xyxy, img0, label=label, color=colors[int(cls)], line_thickness=3)

                # Update the class counts dictionary
                class_counts[int(cls)] = class_counts.get(int(cls), 0) + 1

          fps_x = int((j+1)/(time.time() - start_time))
          print("No Coverall Count in Frame {}: {}".format(j, no_coverall_count))
          print("Total Number of Safety Violations: ", total_safety_violations)
          # yield img0, fps_x, img0.shape, total_detections
          yield img0, fps_x, img0.shape, no_coverall_count, no_helmet_count, no_gloves_count, total_safety_violations, class_counts, no_glasses_count

        else:
          break

  video.release()

def zone_detection(path_x='',conf_=0.25 ,warning_threshold=50):
    import time
    start_time = time.time()

    video_path = path_x

    video = cv2.VideoCapture(video_path)

    # Video information
    fps = video.get(cv2.CAP_PROP_FPS)
    w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    torch.cuda.empty_cache()

    with torch.no_grad():
        weights, imgsz = opt['weights'], opt['img-size']
        set_logging()
        device = select_device(opt['device'])
        half = device.type != 'cpu'
        model = attempt_load(weights, map_location=device)  # load FP32 model
        stride = int(model.stride.max())  # model stride
        imgsz = check_img_size(imgsz, s=stride)  # check img_size
        if half:
            model.half()

        names = model.module.names if hasattr(model, 'module') else model.names
        colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
        if device.type != 'cpu':
            model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))

        classes = None
        if opt['classes']:
            classes = []
            for class_name in opt['classes']:
                classes.append(opt['classes'].index(class_name))

        for j in range(nframes):

            ret, img0 = video.read()
            if ret:
                img = letterbox(img0, imgsz, stride=stride)[0]
                img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
                img = np.ascontiguousarray(img)
                img = torch.from_numpy(img).to(device)
                img = img.half() if half else img.float()  # uint8 to fp16/32
                img /= 255.0  # 0 - 255 to 0.0 - 1.0
                if img.ndimension() == 3:
                    img = img.unsqueeze(0)

                # Inference
                t1 = time_synchronized()
                pred = model(img, augment=False)[0]

                # conf = 0.5
                total_detections = 0
                # pred = non_max_suppression(pred, conf_, opt['iou-thres'], classes= classes, agnostic= False)
                pred = non_max_suppression(pred, conf_, opt['iou-thres'], classes=zone_detect_class_indices,
                                           agnostic=False)
                t2 = time_synchronized()

                drilling_box = None
                for i, det in enumerate(pred):
                    s = ''
                    s += '%gx%g ' % img.shape[2:]  # print string
                    gn = torch.tensor(img0.shape)[[1, 0, 1, 0]]
                    total_violations = 0
                    warning_count = 0
                    class_counts = {}

                    if len(det):
                        det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()

                        for c in det[:, -1].unique():
                            n = (det[:, -1] == c).sum()  # detections per class
                            total_detections += int(n)
                            s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                            print (s)
                            if names[int(c)] == 'Drilling Area':
                                drilling_box = det[:, :4][det[:, -1] == c][0]  # Get drilling box coordinates
                                print("Drilling Area Coordinates: ", drilling_box)
                            if names[int(c)] == 'Person':
                                person_box = det[:, :4][det[:, -1] == c][0]  # Get person box coordinates
                                person_x_center = (person_box[0] + person_box[2]) / 2
                                person_y_center = (person_box[1] + person_box[3]) / 2

                                if drilling_box is not None:
                                    drilling_x_center = (drilling_box[0] + drilling_box[2]) / 2
                                    drilling_y_center = (drilling_box[1] + drilling_box[3]) / 2

                                    distance = np.sqrt((person_x_center - drilling_x_center) ** 2 + (
                                            person_y_center - drilling_y_center) ** 2)
                                    print ("Distance in Pixels: ", distance)
                                    if distance < warning_threshold:  # Adjust the threshold value as needed
                                        print("Warning: Person is near the drilling area!")
                                        warning_count += int(n)
                                        print("Warning Count: ", warning_count)
                                        total_violations = warning_count


                        for *xyxy, conf, cls in reversed(det):
                            label = f'{names[int(cls)]} {conf:.2f}'
                            #plot_one_box(xyxy, img0, label=label, color=colors[int(cls)], line_thickness=3)
                            #plot_one_box(drilling_box, img0, label="Drilling Area", color=(0, 255, 0), line_thickness=3)

                            # Update the class counts dictionary
                            class_counts[int(cls)] = class_counts.get(int(cls), 0) + 1

                fps_x = int((j + 1) / (time.time() - start_time))

                yield img0, fps_x, img0.shape, warning_count, total_violations

            else:
                break
    video.release()
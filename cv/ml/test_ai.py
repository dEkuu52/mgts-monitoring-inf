import cv2
from ultralytics import YOLO

# работа с камерой и видео

model = YOLO('yolo-v/best.pt') # основная тренируемая моделька будет

# ===================   photo  ===================
results = model.predict(
    source='35453688.jpg',
    # target_size=(416, 416),
    imgsz=900 ,
    conf=0.4 ,
    iou=0.1 ,
    save=True
)

annotated_frame = results[0].plot()
cv2.imshow('Result', annotated_frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
# ===================   photo  ===================



# ===================   video  ===================
# cap = cv2.VideoCapture(0)
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# video_writer = cv2.VideoWriter('hulumul.mp4', fourcc, 60.0, (640,480) )
#
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# while True:
#     ret, frame = cap.read()
#
#     frame = cv2.flip(frame, 1)
#
#     results = model.predict(frame, imgsz=352 ,conf=0.25 ,verbose=False)
#
#     annotated_frame = results[0].plot()
#
#     video_writer.write(annotated_frame)
#
#     cv2.imshow('Annoted_frame', annotated_frame)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# cap.release()
# video_writer.release()
# cv2.destroyAllWindows()
# ===================   video  ===================
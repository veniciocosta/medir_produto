import cv2
import numpy as np

# Create point matrix get coordinates of mouse click on image
point_matrix = [0, 0]

counter = 0


def mousePoints(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        point_matrix[0] = x
        point_matrix[1] = y


# Read image
captura = cv2.VideoCapture(0)

while True:
    check, frame = captura.read()

    x = point_matrix[0]
    y = point_matrix[1]

    cv2.rectangle(frame, (20, 50), (70, 80), (0, 0, 255), -1)
    cv2.rectangle(frame, (90, 50), (140, 80), (255, 0, 0), -1)

    if 20 < x < 70 and 50 < y < 80:
        cv2.putText(frame, 'x: ' + str(x) + ', y: ' +
                    str(y), (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 128), 1)

    if 90 < x < 140 and 50 < y < 80:
        cv2.putText(frame, 'x: ' + str(x) + ', y: ' +
                    str(y), (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (128, 0, 0), 1)

    cv2.imshow("Original Image ", frame)

    cv2.setMouseCallback("Original Image ", mousePoints)

    print(point_matrix)

    cv2.waitKey(1)

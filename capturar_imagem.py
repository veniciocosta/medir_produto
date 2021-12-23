import cv2
from cracker_measurement import captura


def registrar_img(captura):
    file = "foto.jpg"
    check, img = captura.read()
    cv2.imwrite(file, img)
    #cv2.destroyAllWindows()
    #camera.release()

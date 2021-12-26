import cv2


def registrar_img(captura):
    file = "foto.jpg"
    check, img = captura.read()
    cv2.imwrite(file, img)
    #cv2.destroyAllWindows()
    #camera.release()

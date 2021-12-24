import cv2
import os
import capturar_imagem
import utlis
from datetime import datetime
import registrar_info

usuario = os.getlogin()  # usuário logado
webcam = False  # False para ler foto.jpg, True para ler webcam

arquivo_img = "foto.jpg"
escala = 2

larguraPapel = 210 * escala
alturaPapel = 297 * escala

largura = 100
altura = 100

# Informações para registro das medições
arquivo_dados = "dados_cracker.csv"
pasta = os.environ['USERPROFILE']
pasta_arq = os.path.join(pasta, "Desktop", arquivo_dados)
cabecalho = ['Data e hora', 'User', 'Lado', 'Largura', 'Altura', 'Cor']
data_hora = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
user = os.getlogin()
cor = "OK"
lado = ""

# fim

# cria matriz para x,y do mouse
point_matrix = [0, 0]
#funcão para identificar x, y do mouse
def mousePoints(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        point_matrix[0] = x
        point_matrix[1] = y

captura = cv2.VideoCapture(0, cv2.CAP_DSHOW)


verdadeiro = True
while verdadeiro:

    x = point_matrix[0]
    y = point_matrix[1]

    # se a webcam = verdadeiro, o frame será da webcam, caso contrário será da imagem salva
    if webcam:
        check, frame = captura.read()
    else:
        frame = cv2.imread(arquivo_img)

    frame, contornos = utlis.pegarContornos(frame, minArea=50000, filtro=4, desenhar=False)

    if len(contornos) != 0:
        o_maior = contornos[0][2]
        # print(o_maior)
        imagemWarp = utlis.warpImagem(frame, o_maior, larguraPapel, alturaPapel)
        frame2, contornos2 = utlis.pegarContornos(imagemWarp, minArea=2000, filtro=4, cThr=[50, 50], desenhar=False)

        if len(contornos) != 0:
            for obj in contornos2:
                cv2.polylines(frame2, [obj[2]], True, (0, 255, 0), 2)
                nPoints = utlis.reordenar(obj[2])
                minhaLargura = round((utlis.encontrarDistancia(nPoints[0][0] // escala, nPoints[1][0] // escala) / 10),
                                     1)
                minhaAltura = round((utlis.encontrarDistancia(nPoints[0][0] // escala, nPoints[2][0] // escala) / 10),
                                    1)

                # início incluir linhas com seta
                cv2.arrowedLine(frame2, (nPoints[0][0][0], nPoints[0][0][1]), (nPoints[1][0][0], nPoints[1][0][1]),
                                (255, 0, 255), 3, 8, 0, 0.05)
                cv2.arrowedLine(frame2, (nPoints[0][0][0], nPoints[0][0][1]), (nPoints[2][0][0], nPoints[2][0][1]),
                                (255, 0, 255), 3, 8, 0, 0.05)
                xl, yl, w, h = obj[3]
                # incluir texto
                cv2.putText(frame2, '{}cm'.format(minhaLargura), (xl + 30, yl - 10), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            0.7,
                            (255, 0, 255), 2)
                largura = minhaLargura

                cv2.putText(frame2, '{}cm'.format(minhaAltura), (xl - 50, yl + h // 2), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            0.7, (255, 0, 255), 2)
                altura = minhaAltura
                # fim

                # botão lado esquerdo
                cv2.rectangle(frame2, (20, 515), (190, 550), (112, 25, 25), -1)
                esquerda1 = str(" Registrar lado")
                esquerda2 = str("  esquerdo")
                cv2.putText(frame2, esquerda1, (30, alturaPapel - 60), cv2.FONT_HERSHEY_PLAIN,
                            1, (255, 255, 255), 1)
                cv2.putText(frame2, esquerda2, (30, alturaPapel - 45), cv2.FONT_HERSHEY_PLAIN,
                            1, (255, 255, 255), 1)

                # botão lado direito
                cv2.rectangle(frame2, (200, 515), (370, 550),
                              (79, 79, 47), -1)
                direita1 = str(" Registrar lado")
                direita2 = str("  direito")
                cv2.putText(frame2, direita1, (larguraPapel // 2, alturaPapel - 60), cv2.FONT_HERSHEY_PLAIN,
                            1, (255, 255, 255), 1)
                cv2.putText(frame2, direita2, (larguraPapel // 2, alturaPapel - 45), cv2.FONT_HERSHEY_PLAIN,
                            1, (255, 255, 255), 1)
                # print(x,y) exibir coordenadas do mouse
                if 20 < x < 190 and 515 < y < 550:
                    lado = "Esquerdo"
                    cv2.putText(frame2, 'Lado: ' + lado, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 0, 128), 1)

                elif 200 < x < 370 and 515 < y < 550:
                    lado = "Direito"
                    cv2.putText(frame2, 'Lado: ' + lado, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (128, 0, 0), 1)

        cv2.imshow("A4", frame2)
        cv2.setMouseCallback("A4", mousePoints)

    # cv2.imshow("Original", frame)
    # cv2.waitKey(1)

    tecla = cv2.waitKey(1)
    # mandar ele parar se o usuário clicar em "Esc"
    if tecla == 27:
        cv2.destroyAllWindows()
        captura.release()
        verdadeiro = False
        quit()
        break

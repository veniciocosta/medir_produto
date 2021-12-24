import cv2
import numpy as np


def pegarContornos(frame, cThr=[100, 100], showBordas=False, minArea=1000, filtro=0, desenhar=False):
    imagemCinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    imagemDesfocada = cv2.GaussianBlur(imagemCinza, (5, 5), 1)
    imagemBordas = cv2.Canny(imagemDesfocada, cThr[0], cThr[1])  # limiar 100, limiar 100
    kernel = np.ones((5, 5))
    imagemDilatada = cv2.dilate(imagemBordas, kernel, iterations=3)  # linha10
    imagemThre = cv2.erode(imagemDilatada, kernel, iterations=2)  # linha11

    # caso a marcação já seja bem detalahada, você não precisará "dilatar as bordas"
    # portanto poderá substituir imagemThre abaixo por imagemBordas e comentar as linhas 10 e 11

    if showBordas:
        cv2.imshow("Bordas", imagemThre)  # aqui

    contornos, hierarquia = cv2.findContours(imagemThre, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # aqui também

    contornos_finais = []

    for i in contornos:
        area = cv2.contourArea(i)
        if area > minArea:
            perimetro = cv2.arcLength(i, True)
            contorno_aprox = cv2.approxPolyDP(i, 0.02 * perimetro, True)  # original 0.02
            retangulo_delimitador = cv2.boundingRect(contorno_aprox)
            if filtro > 0:
                if len(contorno_aprox) == filtro:
                    contornos_finais.append([len(contorno_aprox), area, contorno_aprox, retangulo_delimitador, i])
            else:
                contornos_finais.append([len(contorno_aprox), area, contorno_aprox, retangulo_delimitador, i])
    contornos_finais = sorted(contornos_finais, key=lambda x: x[1], reverse=True)
    if desenhar:
        for contorno in contornos_finais:
            cv2.drawContours(frame, contorno[4], -1, (0, 0, 255), 3)
    return frame, contornos_finais


def reordenar(meus_pontos):
    # print(meus_pontos.shape)
    meus_novos_pontos = np.zeros_like(meus_pontos)
    meus_pontos = meus_pontos.reshape((4, 2))
    adicionar = meus_pontos.sum(1)
    meus_novos_pontos[0] = meus_pontos[np.argmin(adicionar)]
    meus_novos_pontos[3] = meus_pontos[np.argmax(adicionar)]
    diferenca = np.diff(meus_pontos, axis=1)
    meus_novos_pontos[1] = meus_pontos[np.argmin(diferenca)]
    meus_novos_pontos[2] = meus_pontos[np.argmax(diferenca)]
    return meus_novos_pontos


def warpImagem(frame, pontos, largura, altura, pad=20):
    # print(pontos)
    pontos = reordenar(pontos)

    pontos1 = np.float32(pontos)
    pontos2 = np.float32([[0, 0], [largura, 0], [0, altura], [largura, altura]])
    matriz = cv2.getPerspectiveTransform(pontos1, pontos2)

    imagemWarp = cv2.warpPerspective(frame, matriz, (largura, altura))
    imagemWarp = imagemWarp[pad:imagemWarp.shape[0] - pad, pad:imagemWarp.shape[1] - pad]

    return imagemWarp


def encontrarDistancia(pts1, pts2):
    return ((pts2[0] - pts1[0]) ** 2 + (pts2[1] - pts1[1]) ** 2) ** 0.5

import cv2
import os
from datetime import datetime
import numpy as np
import csv


# funcão para identificar x, y do mouse
def mousePoints(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        point_matrix[0] = x
        point_matrix[1] = y


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


def gravar_medicoes(pasta_arq, cabecalho, data_hora, user, cod_prod, desc_prod, lado, largura, altura, cor):
    if os.path.isfile(pasta_arq):
        dados = []
        with open(pasta_arq, 'r', encoding='utf-8') as arq_csv:
            leitor = csv.reader(arq_csv, delimiter=",")
            next(leitor)  # pula o cabeçalho
            for linha in leitor:
                dados.append(linha)  # cria uma lista com todas as linhas do txt
    else:
        dados = []  # se o arquivo não existe, não tem dados, portanto, cria-se uma lista de dados vazia

    with open(pasta_arq, 'w', encoding='utf-8', newline="") as arquivo_cadastro:
        escritor = csv.writer(arquivo_cadastro)
        escritor.writerow(cabecalho)
        dados.append([data_hora, user, cod_prod, desc_prod, lado, largura, altura, cor])
        escritor.writerows(dados)


# Criar um dicionário de produtos
dict_produtos = {
    '48019': "ESTRELA CREAM CRACKER 20X400",
    '8952': "PREDILLETO BISCOITO CRACKER 20X400",
    '89019': "PREDILLETO CREAM CRACKER 20X400",
    '48219': "PELAGGIO CREAM CRACKER 20X400",
    '348219': "PELAGGIO CREAM CRACKER 20X400 - EXPORTAÇÃO",
    '48018': "ESTRELA CREAM CRACKER AGUA E SAL 20X400",
    '48215': "PELAGGIO CREAM CRACKER AMANTEIGADO 20X400",
    '348213': "PELAGGIO SAUDAVEL CREAM CRACKER INTEGRAL 20X400 - EXPORTAÇÃO",
    '48213': "PELAGGIO SAUDAVEL CREAM CRACKER INTEGRAL 20X400",
    '80146': "BIRIBA CREAM CRACKER20X400G",
    '89205': "BONSABOR CREAM CRACKER 20X400",
    '32119': "FORTALEZA CREAM CRACKER 20X400G ",
    '89426': "CARVALHO CREAM CRACKER 20X400G",
    '389205': "BONSABOR CREAM CRACKER 20X400 – EXPORTAÇÃO",
    '348215': "PELAGGIO CREAM CRACKER AMANTEIGADO 20X400 - EXPORTAÇÃO",
    '348019': "ESTRELA CREAM CRACKER 20X400 - EXPORTAÇÃO",
    '348018': "ESTRELA CREAM CRACKER AGUA E SAL 20X400 - EXPORTAÇÃO",
    '75032': "PILAR CRACKER TRADICION 20X400",
    '75027': "VIT CREAM CRACKER 20X400",
    '48622': "PELAGGIO BISCOITO CREAM CRACKER TRADICIONAL 20X400",
    '30105': "RICHESTER SUPERIORE CREAM CRACKER 20X400",
    '330105': "RICHESTER SUPERIORE CREAM CRACKER 20X400 - EXPORTACAO"
}

while True:
    # print(dict_produtos.keys())
    print("\nBem vindo ao medidor de produtos\n")

    continuar = input("Digite 1 para CONTINUAR \nou qualquer tecla para para SAIR\n")
    if continuar != '1':
        break

    cod_produto = input("Qual o código do produto?\n")
    if cod_produto not in dict_produtos.keys():
        print('\nCódigo não existente, tente novamente\n')
    else:
        print("\nO produto escolhido foi: ", dict_produtos[cod_produto], '\n')
        continuar = input("Digite 1 pra CONFIRMAR, ou qualquer tecla para retornar\n")
        if continuar == '1':
            descricao_prod = dict_produtos[cod_produto]
            break

webcam = False  # False para ler foto.jpg, True para ler webcam

arquivo_img = "foto.jpg"
escala = 2

larguraPapel = 210 * escala
alturaPapel = 297 * escala

largura = 100
altura = 100

# Informações para registro das medições
arquivo_dados = "dados_produto_" + cod_produto + ".csv"
pasta = os.environ['USERPROFILE']
pasta_arq = os.path.join(pasta, "Desktop", arquivo_dados)
cabecalho = ['Data e hora', 'User', 'Cod_prod', 'Desc_prod', 'Lado', 'Largura', 'Altura', 'Cor']
data_hora = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
user = os.getlogin()
cor = "OK"
lado = ""
registro_esquerdo = False
registro_direito = False
# código e descrição já foram coletados no início
# fim

# cria matriz para x,y do mouse
point_matrix = [0, 0]

# cod_produto = input("Qual o código do produto?\n")
# print(cod_produto)

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

    frame, contornos = pegarContornos(frame, minArea=50000, filtro=4, desenhar=False)

    if len(contornos) != 0:
        o_maior = contornos[0][2]
        # print(o_maior)
        imagemWarp = warpImagem(frame, o_maior, larguraPapel, alturaPapel)
        frame2, contornos2 = pegarContornos(imagemWarp, minArea=2000, filtro=4, cThr=[50, 50], desenhar=False)

        if len(contornos) != 0:
            for obj in contornos2:
                cv2.polylines(frame2, [obj[2]], True, (0, 255, 0), 2)
                nPoints = reordenar(obj[2])
                minhaLargura = round((encontrarDistancia(nPoints[0][0] // escala, nPoints[1][0] // escala) / 10),
                                     1)
                minhaAltura = round((encontrarDistancia(nPoints[0][0] // escala, nPoints[2][0] // escala) / 10),
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
                # print(x, y)  # exibir coordenadas do mouse

                if 20 < x < 190 and 515 < y < 550:
                    lado = "Esquerdo"
                    # escrever texto com lado nas coordenadas encontradas do mouse
                    # cv2.putText(frame2, 'Lado: ' + lado, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 128), 1)
                    # chamar função para gravar dados
                    gravar_medicoes(pasta_arq, cabecalho, data_hora, user, cod_produto, descricao_prod, lado, largura, altura, cor)
                    point_matrix[0] = 0
                    point_matrix[1] = 0
                    registro_esquerdo = True

                if 200 < x < 370 and 515 < y < 550:
                    lado = "Direito"
                    # escrever texto com lado nas coordenadas encontradas do mouse
                    # cv2.putText(frame2, 'Lado: ' + lado, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 0, 0), 1)
                    # chamar função para gravar dados
                    gravar_medicoes(pasta_arq, cabecalho, data_hora, user, cod_produto, descricao_prod, lado, largura, altura, cor)
                    point_matrix[0] = 0
                    point_matrix[1] = 0
                    registro_direito = True

        if registro_esquerdo:
            cv2.putText(frame2, 'Lado esquerdo registrado', (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        if registro_direito:
            cv2.putText(frame2, 'Lado direito registrado', (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

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

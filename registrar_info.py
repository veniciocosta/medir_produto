import csv
import os


def gravar_medicoes(pasta_arq, cabecalho, data_hora, user, lado, largura, altura, cor):
  if os.path.isfile(pasta_arq):
    dados = []
    with open(pasta_arq, 'r', encoding='utf-8') as arq_csv:
        leitor = csv.reader(arq_csv, delimiter=",")
        next(leitor) # pula o cabeçalho
        for linha in leitor:
            dados.append(linha) # cria uma lista com todas as linhas do txt
  else:
    dados = [] # se o arquivo não existe, não tem dados, portanto, cria-se uma lista de dados vazia


  with open(pasta_arq, 'w', encoding='utf-8', newline="") as arquivo_cadastro:
      escritor = csv.writer(arquivo_cadastro)
      escritor.writerow(cabecalho)
      dados.append([data_hora, user, lado, largura, altura, cor])
      escritor.writerows(dados)
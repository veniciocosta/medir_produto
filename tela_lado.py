from tkinter import Button, Label, Tk
from PIL import ImageTk, Image

import registrar_info


def escolha_lado(lado):
    lado_escolhido = lado
    print(lado_escolhido)
    return lado_escolhido


janela = Tk()
janela.title("Dimensões do Cracker")

imagem = Image.open('logo.png')
imagem = imagem.resize((150, 60), Image.ANTIALIAS)
my_img = ImageTk.PhotoImage(imagem)
label_img = Label(janela, image=my_img)
label_img.grid(row=0, padx=10, pady=10)

texto = Label(janela, text="Escolha o lado")
texto.grid(row=0, column=1, padx=10, pady=10)

btn_lado_esquerdo = Button(janela, text="Esquerdo", width=30, height=10, command=lambda: escolha_lado("Esquerdo"))
btn_lado_esquerdo.grid(column=0, row=1, padx=10, pady=00)

btn_lado_direito = Button(janela, text="Direito", width=30, height=10, command=lambda: escolha_lado("Direito"))
btn_lado_direito.grid(column=1, row=1, padx=10, pady=0)

btn_salvar_registro = Button(janela, text="Lançar Informações", width=60, height=10,
                             command=lambda: registrar_info.gravar_medicoes(
                                 pasta_arq, cabecalho, data_hora, user, lado, largura, altura, cor))
btn_salvar_registro.grid(column=0, row=2, padx=10, pady=10)

janela.mainloop()

from tkinter import Button, Label, PhotoImage, Tk
from PIL import ImageTk, Image


janela = Tk()
janela.title("Dimensões do Cracker")

imagem = Image.open('logo.png')
imagem = imagem.resize((150, 60), Image.ANTIALIAS)
my_img = ImageTk.PhotoImage(imagem)
label_img = Label(janela, image=my_img)
label_img.grid(row=0, padx=10, pady=10)

texto = Label(janela, text="Escolha o lado")
texto.grid(row=0, column=1, padx=10, pady=10)

btn_lado_esquerdo = Button(janela, text="Esquerdo", width=30, height=10) # command=pegar_cotacoes
btn_lado_esquerdo.grid(column=0, row=1, padx=10, pady=10)

btn_lado_direito = Button(janela, text="Direito", width=30, height=10) # command=pegar_cotacoes
btn_lado_direito.grid(column=1, row=1, padx=10, pady=10)

janela.mainloop()
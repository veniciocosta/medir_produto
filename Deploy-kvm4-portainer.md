Com certeza! Ter um "Playbook de Sobrevivência" é o que separa os projetos amadores dos ambientes de produção profissionais. Se daqui a seis meses você precisar mexer no sistema e não se lembrar de nada, este arquivo guiará você com segurança absoluta.

Aqui está o conteúdo completo do seu manual. Recomendo criar um arquivo chamado **`DEPLOYMENT_PLAYBOOK.md`** na raiz do seu projeto local e colar este texto lá.

---

# 📘 Manual de Operação e Implantação B2B SaaS (Metrologia Óptica)

Este documento centraliza a arquitetura, o fluxo de desenvolvimento local e o processo de deploy em produção utilizando **Docker Swarm + Portainer** na VPS `OrionDesign`.

---

## 🏗️ 1. Arquitetura do Sistema

* **Back-end:** Django 5.x executado via Gunicorn (3 Workers).
* **Visão Computacional:** OpenCV Headless (otimizado para servidores sem interface gráfica).
* **Arquivos Estáticos (CSS/JS):** Coletados, compactados e servidos diretamente pelo Gunicorn usando **WhiteNoise**.
* **Armazenamento de Mídias (Imagens de Inspeção):** Salvamento direto na nuvem usando **Cloudflare R2** (Bucket: `visao-media`).
* **Banco de Dados:** SQLite persistido localmente no host da VPS em um diretório isolado (`data/`).

---

## 💻 2. Fluxo de Desenvolvimento Local (PC)

Para evitar erros de permissão ou caminhos de banco de dados no seu computador local, a pasta `data/` deve existir na raiz do projeto.

### Inicializando o Servidor Local:

```powershell
# 1. Certifique-se de que a pasta do banco existe (executar na raiz se não existir)
mkdir data

# 2. Rode as migrações locais
python manage.py migrate

# 3. Inicie o ambiente de desenvolvimento
python manage.py runserver

```

---

## 🚀 3. Processo de Atualização e Deploy na VPS

Sempre que você criar uma nova funcionalidade no seu computador local e quiser levá-la para a produção, siga rigorosamente estes **3 passos**:

### Passo 3.1: Commit e Push do Código Local

No seu computador, envie as alterações para o GitHub:

```bash
git add .
git commit -m "Feat: Descrição da sua nova funcionalidade"
git push origin main

```

### Passo 3.2: Recompilar a Imagem no Terminal da VPS

Como o Docker Swarm não monta imagens a partir de Dockerfiles em tempo de execução, você precisa gerar a imagem estável direto no terminal da VPS. Acesse a VPS via SSH e rode:

```bash
# 1. Acesse o diretório do clone real
cd /opt/medidor_produto

# 2. Puxe o código atualizado do GitHub
git pull

# 3. Recompile a imagem local do Docker
docker build -t medidor-saas:latest .

```

### Passo 3.3: Forçar a Atualização no Portainer

O Docker Swarm precisa ser avisado para descartar o cache e ler a nova imagem gerada no passo anterior.

1. Acesse o seu **Portainer** $\rightarrow$ Vá em **Services**.
2. Clique em **`metrologia-saas_web`**.
3. Clique no botão **Update** (no menu superior).
4. Ative a caixinha **"Force redeployment"**.
5. Clique em **Apply changes**.

---

## 🐳 4. O Manifesto de Produção (YAML do Portainer)

Se você precisar recriar a Stack do zero no Portainer via **Web Editor**, utilize exatamente este modelo:

```yaml
version: '3.8'

services:
  web:
    image: medidor-saas:latest
    ports:
      - "8023:8000"
    volumes:
      - /opt/medidor_produto/data:/app/data
      - /opt/medidor_produto/media:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=medidor_project.settings
      - DEBUG=False
      - SECRET_KEY
      - ALLOWED_HOSTS
      - CSRF_TRUSTED_ORIGINS
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - AWS_S3_BUCKET_NAME
      - AWS_ENDPOINT_URL
    deploy:
      restart_policy:
        condition: on-failure

```

> ⚠️ **Segurança:** Nunca digite senhas diretamente neste arquivo. Adicione as credenciais do Cloudflare R2 e as chaves do Django clicando no botão **"+ Add environment variable"** na interface gráfica do Portainer.

---

## 🛠️ 5. Resolução de Erros Clássicos (Troubleshooting)

### Erro: `OperationalError: no such table` ao acessar o site

* **O que significa:** O contêiner subiu, mas o banco de dados SQLite está em branco, sem as tabelas criadas.
* **Como resolver:** Vá na aba *Containers* do Portainer $\rightarrow$ clique no ícone **`>_` (Console)** do contêiner ativo $\rightarrow$ clique em *Connect* $\rightarrow$ execute o comando:
```bash
python manage.py migrate

```



### Erro: `Cannot use ImageField because Pillow is not installed`

* **O que significa:** O Swarm iniciou uma versão antiga da imagem que estava presa no cache do servidor.
* **Como resolver:** Force a atualização da imagem executando o passo **3.3** deste manual (Force redeployment). Se precisar destravar o banco com urgência, abra o console do contêiner e rode `pip install Pillow && python manage.py migrate`.

### Erro: `Package libgl1-mesa-glx is not available` no Dockerfile

* **O que significa:** As bases modernas do Python Slim usam o Debian Trixie (2026), onde as bibliotecas gráficas antigas do OpenCV foram descontinuadas.
* **Como resolver:** Garanta que o seu `Dockerfile` chame apenas o pacote **`libgl1`** e que o seu `requirements.txt` utilize a biblioteca **`opencv-python-headless`**.

---

Com este arquivo guardado no seu repositório, você tem total autonomia para clonar, modificar e manter o seu SaaS escalando com segurança!
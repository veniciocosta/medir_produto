# Production Deployment Manual

This guide provides step-by-step instructions for deploying the B2B SaaS platform on a fresh Ubuntu VPS (KVM environment) using Docker.

## 1. Initial VPS Setup
Update your system and install Docker and Docker Compose.

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 2. Clone Repository
Clone the clean repository to your VPS.

```bash
git clone <your-repository-url> /opt/medidor_produto
cd /opt/medidor_produto
```

## 3. Prepare Persistent Storage
Create the media and data directories to avoid Docker creating them as root-owned directories when bind-mounting.

```bash
mkdir -p media
mkdir -p data
```

## 4. Build and Run the Docker Containers
Build the production-optimized image and start the web service in the background.

```bash
sudo docker compose up -d --build
```

## 5. Post-Deployment Commands
Run database migrations and collect static files inside the running container.

```bash
sudo docker compose exec web python manage.py migrate
sudo docker compose exec web python manage.py collectstatic --noinput
```

The application should now be accessible on your VPS's IP address on port 80.

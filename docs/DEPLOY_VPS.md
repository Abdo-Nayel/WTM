# نشر WorkTaskMe على VPS (Namecheap)

## المتطلبات على السيرفر
- Ubuntu 22.04 أو 24.04
- Docker + Docker Compose
- منفذ 8000 مفتوح (أو 80/443 مع Nginx لاحقًا)

## أوامر سريعة (بعد ما توصل SSH)

```bash
sudo apt update && sudo apt install -y git curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# اعمل logout/login بعد كده

cd /opt
sudo git clone https://github.com/Abdo-Nayel/WTM.git worktaskme
cd worktaskme
# لو ملفات الـ deploy لسه مش على GitHub، ارفعها من جهازك بـ scp أو ادفع للـ repo أولاً

cp .env.prod.example .env.prod
nano .env.prod   # غيّر SECRET_KEY و DB_PASSWORD و FRONTEND_URL لـ IP السيرفر

sudo docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
sudo docker compose -f docker-compose.prod.yml ps
curl http://127.0.0.1:8000/api/health/
```

افتح من المتصفح: `http://YOUR_VPS_IP:8000/`

Demo login:
- Email: `demo@worktaskme.com`
- Password: `Demo1234!`

## جدار ناري (UFW)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 8000/tcp
sudo ufw enable
```

## لاحقًا (دومين + HTTPS)
Nginx reverse proxy على المنفذ 80/443 + Certbot.

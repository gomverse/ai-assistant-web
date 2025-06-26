# 배포 가이드

AI 개인비서 웹앱을 다양한 환경에 배포하는 방법을 안내합니다.

## 목차

1. [로컬 개발 환경](#로컬-개발-환경)
2. [프로덕션 환경 (Linux)](#프로덕션-환경-linux)
3. [Docker 배포](#docker-배포)
4. [클라우드 배포](#클라우드-배포)
5. [환경 변수 관리](#환경-변수-관리)
6. [성능 최적화](#성능-최적화)
7. [모니터링 및 로깅](#모니터링-및-로깅)

## 로컬 개발 환경

### 1. 기본 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd ai-assistant-web

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 Windows에서:
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성:
```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Naver TTS API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Flask 개발 설정
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. 개발 서버 실행

```bash
python app.py
```

## 프로덕션 환경 (Linux)

### 1. 시스템 준비

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx

# CentOS/RHEL
sudo yum install -y python3 python3-pip nginx
```

### 2. 애플리케이션 설정

```bash
# 애플리케이션 디렉토리 생성
sudo mkdir -p /opt/ai-assistant
sudo chown $USER:$USER /opt/ai-assistant
cd /opt/ai-assistant

# 코드 배포
git clone <repository-url> .

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
pip install gunicorn
```

### 3. 환경 변수 설정

```bash
# /opt/ai-assistant/.env
cat > .env << EOF
OPENAI_API_KEY=your_production_api_key
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
FLASK_ENV=production
FLASK_DEBUG=False
EOF

# 보안을 위해 권한 설정
chmod 600 .env
```

### 4. Systemd 서비스 생성

```bash
sudo cat > /etc/systemd/system/ai-assistant.service << EOF
[Unit]
Description=AI Assistant Web App
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/ai-assistant
Environment=PATH=/opt/ai-assistant/venv/bin
ExecStart=/opt/ai-assistant/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant
```

### 5. Nginx 설정

```bash
sudo cat > /etc/nginx/sites-available/ai-assistant << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias /opt/ai-assistant/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 업로드 파일 크기 제한
    client_max_body_size 10M;
}
EOF

# 사이트 활성화
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Docker 배포

### 1. Dockerfile 생성

```dockerfile
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 데이터 디렉토리 생성
RUN mkdir -p data/conversations data/sessions data/exports data/logs

# 포트 노출
EXPOSE 5000

# 애플리케이션 실행
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]
```

### 2. Docker Compose 설정

```yaml
# docker-compose.yml
version: '3.8'

services:
  ai-assistant:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - NAVER_CLIENT_ID=${NAVER_CLIENT_ID}
      - NAVER_CLIENT_SECRET=${NAVER_CLIENT_SECRET}
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ai-assistant
    restart: unless-stopped
```

### 3. Docker 실행

```bash
# 이미지 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f ai-assistant

# 컨테이너 상태 확인
docker-compose ps
```

## 클라우드 배포

### AWS EC2

```bash
# EC2 인스턴스 생성 후
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 애플리케이션 배포
git clone <repository-url>
cd ai-assistant-web
docker-compose up -d
```

### Google Cloud Platform

```bash
# gcloud CLI 설치 후
gcloud app deploy app.yaml

# app.yaml 예시
runtime: python39
service: ai-assistant

env_variables:
  OPENAI_API_KEY: "your_api_key"
  NAVER_CLIENT_ID: "your_client_id"
  NAVER_CLIENT_SECRET: "your_client_secret"

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

### Heroku

```bash
# Heroku CLI 설치 후
heroku create ai-assistant-app
heroku config:set OPENAI_API_KEY=your_api_key
heroku config:set NAVER_CLIENT_ID=your_client_id
heroku config:set NAVER_CLIENT_SECRET=your_client_secret

# Procfile 생성
echo "web: gunicorn app:app" > Procfile

# 배포
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

## 환경 변수 관리

### 보안 가이드라인

1. **API 키 보안**
   ```bash
   # 파일 권한 설정
   chmod 600 .env
   
   # Git에서 제외
   echo ".env" >> .gitignore
   ```

2. **환경별 설정**
   ```bash
   # development.env
   FLASK_ENV=development
   FLASK_DEBUG=True
   
   # production.env
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```

3. **비밀 관리 서비스 사용**
   ```python
   # AWS Secrets Manager 예시
   import boto3
   
   def get_secret(secret_name):
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId=secret_name)
       return response['SecretString']
   ```

## 성능 최적화

### 1. Gunicorn 설정

```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
```

### 2. 캐싱 설정

```python
# app.py에 추가
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)
def cached_ai_response(message):
    # AI 응답 캐싱
    pass
```

### 3. 정적 파일 최적화

```nginx
# nginx.conf
location /static/ {
    alias /opt/ai-assistant/app/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    gzip on;
    gzip_types text/css application/javascript;
}
```

## 모니터링 및 로깅

### 1. 로그 설정

```python
# config.py에 추가
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        handler = RotatingFileHandler(
            'data/logs/app.log', 
            maxBytes=10240, 
            backupCount=10
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
```

### 2. 헬스 체크

```python
# app.py에 추가
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### 3. 모니터링 도구

```yaml
# docker-compose.yml에 추가
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## SSL/TLS 설정

### Let's Encrypt 사용

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 설정
sudo crontab -e
# 다음 라인 추가:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 백업 및 복구

### 데이터 백업

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"

# 데이터 백업
tar -czf "$BACKUP_DIR/ai-assistant-data-$DATE.tar.gz" /opt/ai-assistant/data/

# 오래된 백업 삭제 (30일 이상)
find "$BACKUP_DIR" -name "ai-assistant-data-*.tar.gz" -mtime +30 -delete
```

### 복구 절차

```bash
# 서비스 중지
sudo systemctl stop ai-assistant

# 데이터 복구
tar -xzf /opt/backups/ai-assistant-data-20231120.tar.gz -C /

# 권한 복구
sudo chown -R www-data:www-data /opt/ai-assistant/data

# 서비스 재시작
sudo systemctl start ai-assistant
```

## 문제 해결

### 일반적인 문제들

1. **메모리 부족**
   ```bash
   # 스왑 파일 생성
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

2. **디스크 공간 부족**
   ```bash
   # 오래된 로그 파일 정리
   find /opt/ai-assistant/data/logs -name "*.log.*" -mtime +7 -delete
   
   # 오래된 오디오 파일 정리
   find /opt/ai-assistant/app/static/audio -name "*.mp3" -mtime +1 -delete
   ```

3. **포트 충돌**
   ```bash
   # 사용 중인 포트 확인
   sudo netstat -tlpn | grep :5000
   
   # 프로세스 종료
   sudo kill -9 <PID>
   ```

이 배포 가이드를 통해 다양한 환경에서 AI 개인비서 웹앱을 안정적으로 운영할 수 있습니다.

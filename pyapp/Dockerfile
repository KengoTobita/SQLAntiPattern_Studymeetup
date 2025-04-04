# Pythonベースイメージ（必要に応じてバージョン調整）
FROM python:3.13

# 必要なパッケージインストール
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ・スクリプトをコピー
COPY . .


# ENTRYPOINT と CMD は docker-compose 側で指定

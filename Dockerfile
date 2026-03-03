FROM python:3.9-slim

LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="Nextcloud Server Info Exporter for Prometheus"

RUN apt-get update && apt-get install curl -y

# Создаем непривилегированного пользователя
RUN addgroup --system --gid 1000 nextcloud-exporter && \
    adduser --system --uid 1000 --ingroup nextcloud-exporter nextcloud-exporter

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с приложением
COPY app.py .

# Устанавливаем зависимости
RUN pip install --no-cache-dir requests && \
    # Проверяем, что файл существует и имеет правильные права
    chown -R nextcloud-exporter:nextcloud-exporter /app && \
    chmod +x app.py

# Переключаемся на непривилегированного пользователя
USER nextcloud-exporter

# Открываем порт для метрик
EXPOSE 9205

# Запускаем приложение
ENTRYPOINT ["python", "/app/app.py"]
CMD ["--host", "0.0.0.0", "--port", "9205"]

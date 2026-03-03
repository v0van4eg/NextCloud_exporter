# Nextcloud Prometheus Exporter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/nextcloud-exporter)](https://hub.docker.com/r/yourusername/nextcloud-exporter)
[![GitHub release](https://img.shields.io/github/v/release/yourusername/nextcloud-exporter)](https://github.com/yourusername/nextcloud-exporter/releases)

Prometheus exporter для сбора метрик с Nextcloud сервера через официальное приложение serverinfo.

## 📋 Описание

Данный экспортёр собирает метрики с Nextcloud сервера и предоставляет их в формате, понятном для Prometheus. Метрики включают информацию о системе, хранилище, пользователях, доступах, PHP и базе данных.

### ✨ Возможности

- 📊 Сбор системных метрик (CPU, память, диск)
- 👥 Статистика пользователей (всего, активные за разные периоды)
- 📁 Информация о файлах и хранилище
- 🔗 Статистика доступов (shares) по типам
- 🐘 Метрики PHP (OPcache, memory_limit и др.)
- 🗄️ Информация о базе данных
- 🏷️ Версионная информация Nextcloud
- 🔒 Аутентификация через NC-Token
- 🐳 Готовый Docker образ

## 🚀 Быстрый старт

### Предварительные требования

- Nextcloud сервер с установленным приложением `serverinfo`
- Токен доступа (генерируется в Nextcloud)

### Установка приложения serverinfo

```bash
# Установка и включение приложения serverinfo
sudo -u www-data php /var/www/nextcloud/occ app:install serverinfo
sudo -u www-data php /var/www/nextcloud/occ app:enable serverinfo

# Генерация токена (замените yourtoken на желаемый токен)
sudo -u www-data php /var/www/nextcloud/occ config:app:set serverinfo token --value yourtoken
```
## 📊 Метрики
### Основные метрики
Метрика	Тип	Описание
- nextcloud_up	Gauge	1 если сбор метрик успешен, 0 если нет
### Системные метрики
Метрика	Тип	Описание
### Метрики хранилища
Метрика	Тип	Описание
### Метрики доступов (Shares)
Метрика	Тип	Описание
### Активные пользователи
Метрика	Тип	Описание
### PHP метрики
Метрика	Тип	Описание
### Метрики базы данных
Метрика	Тип	Описание
Метрики веб-сервера
Метрика	Тип	Описание

## 📈 Интеграция с Prometheus
Добавьте в ваш prometheus.yml:

yaml
scrape_configs:
  - job_name: 'nextcloud'
    static_configs:
      - targets: ['localhost:9205']
    metrics_path: /metrics
    scrape_interval: 30s

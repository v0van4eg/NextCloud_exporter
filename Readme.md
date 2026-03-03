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
nextcloud_info	Gauge	Информация о версии Nextcloud (метки: version, major, minor, patch)
### Системные метрики
Метрика	Тип	Описание
nextcloud_system_load1	Gauge	Средняя нагрузка за 1 минуту
nextcloud_system_load5	Gauge	Средняя нагрузка за 5 минут
nextcloud_system_load15	Gauge	Средняя нагрузка за 15 минут
nextcloud_system_cpu_count	Gauge	Количество ядер CPU
nextcloud_system_memory_total_bytes	Gauge	Всего оперативной памяти (байт)
nextcloud_system_memory_free_bytes	Gauge	Свободной оперативной памяти (байт)
nextcloud_system_swap_total_bytes	Gauge	Всего swap (байт)
nextcloud_system_swap_free_bytes	Gauge	Свободного swap (байт)
nextcloud_system_free_space_bytes	Gauge	Свободное место на диске (байт)
nextcloud_system_enable_avatars	Gauge	Включены ли аватары (1/0)
nextcloud_system_enable_previews	Gauge	Включены ли превью (1/0)
nextcloud_system_filelocking_enabled	Gauge	Включена ли блокировка файлов (1/0)
nextcloud_system_debug	Gauge	Режим отладки (1/0)
nextcloud_system_backgroundjobs_mode	Gauge	Режим фоновых задач (метка: mode)
### Метрики хранилища
Метрика	Тип	Описание
nextcloud_storage_num_users	Gauge	Количество пользователей
nextcloud_storage_num_files	Gauge	Количество файлов
nextcloud_storage_num_storages	Gauge	Всего хранилищ
nextcloud_storage_num_storages_local	Gauge	Локальных хранилищ
nextcloud_storage_num_storages_home	Gauge	Домашних хранилищ
nextcloud_storage_num_storages_other	Gauge	Других хранилищ
### Метрики доступов (Shares)
Метрика	Тип	Описание
nextcloud_shares_num_shares	Gauge	Всего доступов
nextcloud_shares_num_shares_user	Gauge	Пользовательских доступов
nextcloud_shares_num_shares_groups	Gauge	Групповых доступов
nextcloud_shares_num_shares_link	Gauge	Доступов по ссылке
nextcloud_shares_num_shares_mail	Gauge	Доступов по email
nextcloud_shares_num_shares_room	Gauge	Доступов в комнатах
nextcloud_shares_num_shares_link_no_password	Gauge	Ссылок без пароля
nextcloud_shares_num_fed_shares_sent	Gauge	Отправленных федеративных доступов
nextcloud_shares_num_fed_shares_received	Gauge	Полученных федеративных доступов
### Активные пользователи
Метрика	Тип	Описание
nextcloud_active_users_last5minutes	Gauge	Активных за 5 минут
nextcloud_active_users_last1hour	Gauge	Активных за час
nextcloud_active_users_last24hours	Gauge	Активных за 24 часа
nextcloud_active_users_last7days	Gauge	Активных за 7 дней
nextcloud_active_users_last1month	Gauge	Активных за месяц
nextcloud_active_users_last3months	Gauge	Активных за 3 месяца
nextcloud_active_users_last6months	Gauge	Активных за 6 месяцев
nextcloud_active_users_lastyear	Gauge	Активных за год
### PHP метрики
Метрика	Тип	Описание
nextcloud_php_info	Gauge	Информация о версии PHP (метка: version)
nextcloud_php_memory_limit_bytes	Gauge	Лимит памяти PHP (байт)
nextcloud_php_max_execution_time_seconds	Gauge	Максимальное время выполнения (сек)
nextcloud_php_upload_max_filesize_bytes	Gauge	Максимальный размер загрузки (байт)
nextcloud_php_opcache_enabled	Gauge	Включен ли OPcache (1/0)
nextcloud_php_opcache_memory_used_bytes	Gauge	Использовано памяти OPcache (байт)
nextcloud_php_opcache_memory_free_bytes	Gauge	Свободно памяти OPcache (байт)
nextcloud_php_opcache_memory_wasted_bytes	Gauge	Потеряно памяти OPcache (байт)
nextcloud_php_opcache_hits_total	Counter	Всего попаданий в кэш OPcache
nextcloud_php_opcache_misses_total	Counter	Всего промахов OPcache
nextcloud_php_opcache_hit_rate_percent	Gauge	Процент попаданий OPcache
nextcloud_php_opcache_cached_scripts_count	Gauge	Количество скриптов в кэше
### Метрики базы данных
Метрика	Тип	Описание
nextcloud_database_info	Gauge	Информация о БД (метки: type, version)
nextcloud_database_size_bytes	Gauge	Размер базы данных (байт)
Метрики веб-сервера
Метрика	Тип	Описание
nextcloud_webserver_info	Gauge	Информация о веб-сервере (метка: version)

## 📈 Интеграция с Prometheus
Добавьте в ваш prometheus.yml:

yaml
scrape_configs:
  - job_name: 'nextcloud'
    static_configs:
      - targets: ['localhost:9205']
    metrics_path: /metrics
    scrape_interval: 30s

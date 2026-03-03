#!/usr/bin/env python3
"""
Nextcloud Server Info Exporter for Prometheus

This script fetches server info metrics from a Nextcloud instance and exposes them
on port 9205 without authentication.
"""

import os
import re
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
NEXTCLOUD_URL = os.environ.get('NEXTCLOUD_URL', '').rstrip('/')
NEXTCLOUD_AUTH_TOKEN = os.environ.get('NEXTCLOUD_AUTH_TOKEN','')

if not NEXTCLOUD_URL:
    logger.error("NEXTCLOUD_URL environment variable is not set")
    sys.exit(1)

if not NEXTCLOUD_AUTH_TOKEN:
    logger.error("NEXTCLOUD_AUTH_TOKEN environment variable is not set")
    sys.exit(1)


class NextcloudMetricsCollector:
    """Collects metrics from Nextcloud server info API."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()

        # Используем специальный заголовок NC-Token как требует Nextcloud
        logger.info("Using NC-Token authentication header")
        self.session.headers.update({
            "NC-Token": token,
            "OCS-APIRequest": "true",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Nextcloud-Prometheus-Exporter/1.0"
        })

    def fetch_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch metrics from Nextcloud API."""
        try:
            # Используем правильный endpoint из документации
            params = {'format': 'json'}
            endpoint = f"{self.base_url}/ocs/v2.php/apps/serverinfo/api/v1/info"
            url = f"{endpoint}?{urlencode(params)}"

            logger.debug(f"Fetching metrics from: {url}")
            logger.debug(f"Using headers: {dict(self.session.headers)}")

            response = self.session.get(url, timeout=30)

            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            if response.status_code != 200:
                logger.error(f"API returned status code {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                except:
                    logger.error(f"Error response text: {response.text[:200]}")
                return None

            # Парсим JSON ответ
            try:
                data = response.json()
                logger.debug(f"Response structure: {list(data.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response content: {response.text[:500]}")
                return None

            # Проверяем структуру ответа OCS
            if not isinstance(data, dict) or 'ocs' not in data:
                logger.error("Invalid response format: missing 'ocs' field")
                return None

            ocs_data = data['ocs']

            # Проверяем meta статус
            if 'meta' in ocs_data:
                meta = ocs_data['meta']
                status = meta.get('status')
                statuscode = meta.get('statuscode')

                logger.debug(f"Meta status: {status}, code: {statuscode}")

                if status != 'ok' and statuscode != 200:
                    message = meta.get('message', 'Unknown error')
                    logger.error(f"API returned error: {message} (code: {statuscode})")
                    return None

            # Извлекаем данные
            if 'data' not in ocs_data:
                logger.error("Missing 'data' field in response")
                return None

            logger.info("Successfully fetched metrics from Nextcloud")
            return ocs_data['data']

        except requests.RequestException as e:
            logger.error(f"Error fetching metrics: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {dict(e.response.headers)}")
                if e.response.text:
                    logger.error(f"Response body: {e.response.text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None


class PrometheusFormatter:
    """Formats metrics in Prometheus exposition format."""

    def __init__(self, prefix: str = "nextcloud"):
        self.metrics = []
        self.prefix = prefix

    def add_metric(self, name: str, value: Any, labels: Optional[Dict[str, str]] = None,
                   metric_type: str = "gauge", help_text: Optional[str] = None):
        """Add a metric to the formatter."""
        if labels is None:
            labels = {}

        # Add prefix to metric name
        prefixed_name = f"{self.prefix}_{name}"

        # Sanitize metric name
        sanitized_name = self._sanitize_metric_name(prefixed_name)

        # Add help text if provided
        if help_text:
            self.metrics.append(f"# HELP {sanitized_name} {help_text}")

        # Add type info
        self.metrics.append(f"# TYPE {sanitized_name} {metric_type}")

        # Format labels
        label_str = ""
        if labels:
            label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
            label_str = "{" + ",".join(label_pairs) + "}"

        # Handle different value types
        if isinstance(value, bool):
            numeric_value = 1 if value else 0
        elif isinstance(value, (int, float)):
            numeric_value = value
        else:
            # For non-numeric values, create a gauge with value as label
            if labels:
                labels['value'] = str(value)
            else:
                labels = {'value': str(value)}
            label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
            label_str = "{" + ",".join(label_pairs) + "}"
            numeric_value = 1

        self.metrics.append(f"{sanitized_name}{label_str} {numeric_value}")

    def _sanitize_metric_name(self, name: str) -> str:
        """Sanitize metric name according to Prometheus naming conventions."""
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_:]', '_', name)
        # Ensure it starts with a letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized

    def get_formatted_metrics(self) -> str:
        """Get all metrics formatted for Prometheus."""
        result = "\n".join(self.metrics) + "\n"
        self.metrics = []  # Reset for next collection
        return result


class NextcloudExporter:
    """Main exporter class."""

    def __init__(self, base_url: str, token: str):
        self.collector = NextcloudMetricsCollector(base_url, token)
        self.formatter = PrometheusFormatter(prefix="nextcloud")

    def collect(self) -> str:
        """Collect metrics and return Prometheus-formatted string."""
        try:
            data = self.collector.fetch_metrics()
            if not data:
                logger.warning("Failed to collect metrics")
                self.formatter.add_metric(
                    'up',
                    0,
                    {},
                    'gauge',
                    'Whether the last scrape was successful'
                )
                return self.formatter.get_formatted_metrics()

            # Add success metric
            self.formatter.add_metric(
                'up',
                1,
                {},
                'gauge',
                'Whether the last scrape was successful'
            )

            self._process_metrics(data)
            return self.formatter.get_formatted_metrics()
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            self.formatter.add_metric(
                'up',
                0,
                {},
                'gauge',
                'Whether the last scrape was successful'
            )
            return self.formatter.get_formatted_metrics()

    def _process_metrics(self, data: Dict[str, Any]):
        """Process the metrics data."""
        # Nextcloud system metrics
        if 'nextcloud' in data and 'system' in data['nextcloud']:
            system = data['nextcloud']['system']
            self._process_system_metrics(system)

        # Storage metrics
        if 'nextcloud' in data and 'storage' in data['nextcloud']:
            storage = data['nextcloud']['storage']
            self._process_storage_metrics(storage)

        # Shares metrics
        if 'nextcloud' in data and 'shares' in data['nextcloud']:
            shares = data['nextcloud']['shares']
            self._process_shares_metrics(shares)

        # Server metrics
        if 'server' in data:
            server = data['server']
            self._process_server_metrics(server)

        # Active users metrics
        if 'activeUsers' in data:
            active_users = data['activeUsers']
            self._process_active_users_metrics(active_users)

    def _process_system_metrics(self, system: Dict[str, Any]):
        """Process system metrics."""
        # Version info
        if 'version' in system:
            version = system['version']
            parts = version.split('.')
            self.formatter.add_metric(
                'info',
                1,
                {
                    'version': version,
                    'major': parts[0] if len(parts) > 0 else '',
                    'minor': parts[1] if len(parts) > 1 else '',
                    'patch': parts[2] if len(parts) > 2 else '',
                    'build': parts[3] if len(parts) > 3 else ''
                },
                'gauge',
                'Nextcloud version information'
            )

        # CPU load
        if 'cpuload' in system and isinstance(system['cpuload'], list) and len(system['cpuload']) >= 3:
            self.formatter.add_metric('system_load1', float(system['cpuload'][0]), {}, 'gauge',
                                      'System load average (1min)')
            self.formatter.add_metric('system_load5', float(system['cpuload'][1]), {}, 'gauge',
                                      'System load average (5min)')
            self.formatter.add_metric('system_load15', float(system['cpuload'][2]), {}, 'gauge',
                                      'System load average (15min)')

        if 'cpunum' in system:
            self.formatter.add_metric('system_cpu_count', int(system['cpunum']), {}, 'gauge', 'Number of CPU cores')

        # Memory metrics (convert from MB to bytes)
        if 'mem_total' in system:
            self.formatter.add_metric('system_memory_total_bytes', int(system['mem_total']) * 1024 * 1024, {}, 'gauge',
                                      'Total memory in bytes')
        if 'mem_free' in system:
            self.formatter.add_metric('system_memory_free_bytes', int(system['mem_free']) * 1024 * 1024, {}, 'gauge',
                                      'Free memory in bytes')
        if 'swap_total' in system:
            self.formatter.add_metric('system_swap_total_bytes', int(system['swap_total']) * 1024 * 1024, {}, 'gauge',
                                      'Total swap in bytes')
        if 'swap_free' in system:
            self.formatter.add_metric('system_swap_free_bytes', int(system['swap_free']) * 1024 * 1024, {}, 'gauge',
                                      'Free swap in bytes')

        # Free space
        if 'freespace' in system:
            self.formatter.add_metric('system_free_space_bytes', int(system['freespace']), {}, 'gauge',
                                      'Free disk space in bytes')

        # Feature flags
        feature_flags = [
            ('enable_avatars', 'Avatars enabled'),
            ('enable_previews', 'Previews enabled'),
            ('filelocking_enabled', 'File locking enabled'),
            ('debug', 'Debug mode')
        ]

        for flag, description in feature_flags:
            if flag in system:
                value = 1 if system[flag] in ['yes', 'true', True] else 0
                self.formatter.add_metric(f'system_{flag}', value, {}, 'gauge', description)

    def _process_storage_metrics(self, storage: Dict[str, Any]):
        """Process storage metrics."""
        storage_metrics = [
            ('num_users', 'Number of users'),
            ('num_files', 'Number of files'),
            ('num_storages', 'Total number of storages'),
            ('num_storages_local', 'Number of local storages'),
            ('num_storages_home', 'Number of home storages'),
            ('num_storages_other', 'Number of other storages')
        ]

        for metric, description in storage_metrics:
            if metric in storage:
                try:
                    self.formatter.add_metric(f'storage_{metric}', int(storage[metric]), {}, 'gauge', description)
                except (ValueError, TypeError):
                    pass

    def _process_shares_metrics(self, shares: Dict[str, Any]):
        """Process shares metrics."""
        shares_metrics = [
            ('num_shares', 'Total number of shares'),
            ('num_shares_user', 'Number of user shares'),
            ('num_shares_groups', 'Number of group shares'),
            ('num_shares_link', 'Number of link shares'),
            ('num_shares_mail', 'Number of mail shares'),
            ('num_shares_room', 'Number of room shares'),
            ('num_shares_link_no_password', 'Number of link shares without password'),
            ('num_fed_shares_sent', 'Number of sent federated shares'),
            ('num_fed_shares_received', 'Number of received federated shares')
        ]

        for metric, description in shares_metrics:
            if metric in shares:
                try:
                    self.formatter.add_metric(f'shares_{metric}', int(shares[metric]), {}, 'gauge', description)
                except (ValueError, TypeError):
                    pass

    def _process_server_metrics(self, server: Dict[str, Any]):
        """Process server metrics."""
        # Web server info
        if 'webserver' in server:
            self.formatter.add_metric(
                'webserver_info',
                1,
                {'version': server['webserver']},
                'gauge',
                'Web server information'
            )

        # PHP metrics
        if 'php' in server:
            php = server['php']

            if 'version' in php:
                self.formatter.add_metric('php_info', 1, {'version': php['version']}, 'gauge',
                                          'PHP version information')

            if 'memory_limit' in php:
                try:
                    self.formatter.add_metric('php_memory_limit_bytes', int(php['memory_limit']), {}, 'gauge',
                                              'PHP memory limit in bytes')
                except (ValueError, TypeError):
                    pass

            if 'max_execution_time' in php:
                try:
                    self.formatter.add_metric('php_max_execution_time_seconds', int(php['max_execution_time']), {},
                                              'gauge', 'PHP max execution time in seconds')
                except (ValueError, TypeError):
                    pass

            if 'upload_max_filesize' in php:
                try:
                    self.formatter.add_metric('php_upload_max_filesize_bytes', int(php['upload_max_filesize']), {},
                                              'gauge', 'PHP upload max filesize in bytes')
                except (ValueError, TypeError):
                    pass

            # OPcache metrics
            if 'opcache' in php and php['opcache']:
                opcache = php['opcache']

                if 'opcache_enabled' in opcache:
                    self.formatter.add_metric('php_opcache_enabled', 1 if opcache['opcache_enabled'] else 0, {},
                                              'gauge', 'OPcache enabled')

                if 'memory_usage' in opcache:
                    memory = opcache['memory_usage']
                    if 'used_memory' in memory:
                        self.formatter.add_metric('php_opcache_memory_used_bytes', int(memory['used_memory']), {},
                                                  'gauge', 'OPcache used memory in bytes')
                    if 'free_memory' in memory:
                        self.formatter.add_metric('php_opcache_memory_free_bytes', int(memory['free_memory']), {},
                                                  'gauge', 'OPcache free memory in bytes')
                    if 'wasted_memory' in memory:
                        self.formatter.add_metric('php_opcache_memory_wasted_bytes', int(memory['wasted_memory']), {},
                                                  'gauge', 'OPcache wasted memory in bytes')

                if 'opcache_statistics' in opcache:
                    stats = opcache['opcache_statistics']
                    if 'hits' in stats:
                        self.formatter.add_metric('php_opcache_hits_total', int(stats['hits']), {}, 'counter',
                                                  'OPcache hits total')
                    if 'misses' in stats:
                        self.formatter.add_metric('php_opcache_misses_total', int(stats['misses']), {}, 'counter',
                                                  'OPcache misses total')
                    if 'opcache_hit_rate' in stats:
                        self.formatter.add_metric('php_opcache_hit_rate_percent', float(stats['opcache_hit_rate']), {},
                                                  'gauge', 'OPcache hit rate percentage')
                    if 'num_cached_scripts' in stats:
                        self.formatter.add_metric('php_opcache_cached_scripts_count', int(stats['num_cached_scripts']),
                                                  {}, 'gauge', 'OPcache cached scripts count')

        # Database metrics
        if 'database' in server:
            db = server['database']

            if 'type' in db or 'version' in db:
                self.formatter.add_metric(
                    'database_info',
                    1,
                    {
                        'type': db.get('type', 'unknown'),
                        'version': db.get('version', 'unknown')
                    },
                    'gauge',
                    'Database information'
                )

            if 'size' in db:
                try:
                    self.formatter.add_metric('database_size_bytes', int(db['size']), {}, 'gauge',
                                              'Database size in bytes')
                except (ValueError, TypeError):
                    pass

    def _process_active_users_metrics(self, active_users: Dict[str, Any]):
        """Process active users metrics."""
        active_metrics = [
            ('last5minutes', 'Active users in last 5 minutes'),
            ('last1hour', 'Active users in last hour'),
            ('last24hours', 'Active users in last 24 hours'),
            ('last7days', 'Active users in last 7 days'),
            ('last1month', 'Active users in last month'),
            ('last3months', 'Active users in last 3 months'),
            ('last6months', 'Active users in last 6 months'),
            ('lastyear', 'Active users in last year')
        ]

        for metric, description in active_metrics:
            if metric in active_users:
                try:
                    self.formatter.add_metric(f'active_users_{metric}', int(active_users[metric]), {}, 'gauge',
                                              description)
                except (ValueError, TypeError):
                    pass


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the metrics endpoint."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/metrics':
            self.handle_metrics_request()
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''<html>
<head><title>Nextcloud Exporter</title></head>
<body>
<h1>Nextcloud Exporter</h1>
<p><a href="/metrics">Metrics</a></p>
<p><a href="/health">Health</a></p>
</body>
</html>''')
        else:
            self.send_error(404, "Not found")

    def handle_metrics_request(self):
        """Handle metrics request."""
        try:
            exporter = NextcloudExporter(
                NEXTCLOUD_URL,
                NEXTCLOUD_AUTH_TOKEN
            )
            metrics = exporter.collect()

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(metrics.encode('utf-8'))

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            self.send_error(500, f"Internal server error: {e}")

    def log_message(self, format, *args):
        """Log messages to stderr."""
        logger.info(f"Request: {format % args}")


def main():
    """Main function to run the exporter."""
    import argparse

    parser = argparse.ArgumentParser(description='Nextcloud Server Info Exporter for Prometheus')
    parser.add_argument('--port', type=int, default=9205, help='Port to listen on (default: 9205)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to listen on (default: 0.0.0.0)')
    parser.add_argument('--scrape-once', action='store_true', help='Scrape once and exit')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.scrape_once:
        exporter = NextcloudExporter(
            NEXTCLOUD_URL,
            NEXTCLOUD_AUTH_TOKEN
        )
        metrics = exporter.collect()
        print(metrics)
        return

    server = HTTPServer((args.host, args.port), MetricsHandler)
    logger.info(f"Starting Nextcloud Exporter on {args.host}:{args.port}")
    logger.info(f"Metrics endpoint: http://{args.host}:{args.port}/metrics")
    logger.info(f"Nextcloud URL: {NEXTCLOUD_URL}")
    logger.info("Authentication: NC-Token header")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()


if __name__ == '__main__':
    main()
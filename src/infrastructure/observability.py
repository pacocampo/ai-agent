"""Configuración centralizada para AWS Lambda Powertools."""

import os

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit


SERVICE_NAME = os.getenv("POWERTOOLS_SERVICE_NAME", "kavak-agent")
METRICS_NAMESPACE = os.getenv("POWERTOOLS_METRICS_NAMESPACE", SERVICE_NAME)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger = Logger(service=SERVICE_NAME, level=LOG_LEVEL)
tracer = Tracer(service=SERVICE_NAME)
metrics = Metrics(namespace=METRICS_NAMESPACE, service=SERVICE_NAME)

DEFAULT_METRIC_UNIT = MetricUnit.Count


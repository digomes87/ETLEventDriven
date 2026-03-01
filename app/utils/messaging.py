import asyncio
import json
import logging
from typing import Any

import pika
import redis

from app.config import get_settings
from app.interfaces.events import MessageQueueClient


logger = logging.getLogger(__name__)


class RabbitMQClient(MessageQueueClient):
    def __init__(self) -> None:
        settings = get_settings()
        credentials = pika.PlainCredentials(
            settings.rabbitmq_user, settings.rabbitmq_password
        )
        self._parameters = pika.ConnectionParameters(
            host=settings.redis_host,
            port=settings.redis_port,
            credentials=credentials,
        )
        self._exchange = "etlpay.events"

    async def publish(self, routing_key: str, message: dict[str, Any]) -> None:
        payload = json.dumps(message)
        try:
            await asyncio.to_thread(self._publish_blocking, routing_key, payload)
        except redis.ConnectionError:
            logger.exception("Failed to publish message")

    def _publish_blocking(self, routing_key: str, payload: str) -> None:
        connection = pika.BlockingConnection(self._parameters)
        channel = connection.channel()
        channel.exchange_declare(
            exchange=self._exchange, exchange_type="topic", durable=True
        )
        channel.basic_publish(
            exchange=self._exchange,
            routing_key=routing_key,
            body=payload,
        )
        connection.close()

    async def _pull_batch_blocking(
        self, queue: str, max_messages: int
    ) -> list[dict[str, Any]]:
        connection = pika.BlockingConnection(self._parameters)
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        messages: list[dict[str, Any]] = []
        for _ in range(max_messages):
            method, properties, body = channel.basic_get(queue=queue, auto_ack=True)
            if not method:
                break
            try:
                decoded = json.loads(body.decode("utf-8"))
            except json.decoder.JSONDecodeError:
                continue
            if isinstance(decoded, dict):
                messages.append(decoded)
        connection.close()
        return messages

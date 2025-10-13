import asyncio
from typing import Callable, Any, List
from loguru import logger

from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.adapters.base import MessagePlatformAdapter


class StreamProcessor:
    def __init__(self, adapter: MessagePlatformAdapter, subscription: str, processors: List[Callable[[UniversalMessage], Any]] = None):
        self.adapter = adapter
        self.subscription = subscription
        self.processors = processors if processors is not None else []
        self._running = False

    async def start(self):
        logger.info(f"Starting StreamProcessor for subscription: {self.subscription}")
        self._running = True
        try:
            async for message in self.adapter.consume(self.subscription):
                if not self._running:
                    break
                logger.debug(f"Received message: {message.metadata.get('id')}")
                for processor in self.processors:
                    try:
                        await processor(message)
                    except Exception as e:
                        logger.error(f"Error processing message {message.metadata.get('id')} with processor {processor.__name__ if hasattr(processor, '__name__') else processor}: {e}")
        except asyncio.CancelledError:
            logger.info(f"StreamProcessor for {self.subscription} cancelled.")
        except Exception as e:
            logger.error(f"StreamProcessor encountered an error for {self.subscription}: {e}")
        finally:
            logger.info(f"StreamProcessor for {self.subscription} stopped.")

    def stop(self):
        logger.info(f"Stopping StreamProcessor for subscription: {self.subscription}")
        self._running = False

# Example of a simple processor function
async def log_message_processor(message: UniversalMessage):
    logger.info(f"Log Processor: Message ID: {message.metadata.get('id')}, Type: {message.metadata.get('type')}")

# Example of a processor that could interact with an AnomalyDetector
async def anomaly_detection_processor(message: UniversalMessage, detector_instance: Any): # detector_instance would be an AnomalyDetector
    # Assuming payload contains data relevant for anomaly detection
    data_point = message.payload.get("value")
    if data_point is not None:
        is_anomaly = detector_instance.detect(data_point)
        if is_anomaly:
            logger.warning(f"Anomaly Detected by Processor: Message ID: {message.metadata.get('id')}, Data: {data_point}")
        else:
            logger.info(f"No Anomaly: Message ID: {message.metadata.get('id')}, Data: {data_point}")
    else:
        logger.warning(f"Anomaly Detection Processor: No 'value' in payload for message {message.metadata.get('id')}")
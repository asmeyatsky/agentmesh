from loguru import logger
from typing import Any, Dict, List
import numpy as np


class AnomalyDetector:
    def __init__(self, window_size: int = 30, std_dev_threshold: float = 3.0):
        self.window_size = window_size
        self.std_dev_threshold = std_dev_threshold
        self.data_window: List[float] = []
        logger.info(
            "AnomalyDetector initialized with window_size={} and std_dev_threshold={}",
            window_size,
            std_dev_threshold,
        )

    def detect(self, data_point: float) -> bool:
        """
        Detects anomalies in the given data point using a statistical approach.
        """
        is_anomaly = False
        if len(self.data_window) >= self.window_size:
            mean = np.mean(self.data_window)
            std_dev = np.std(self.data_window)
            if abs(data_point - mean) > self.std_dev_threshold * std_dev:
                is_anomaly = True
                logger.warning(
                    "Anomaly detected! Data point {} is outside the threshold.", data_point
                )

        self.data_window.append(data_point)
        if len(self.data_window) > self.window_size:
            self.data_window.pop(0)

        return is_anomaly

    def train_model(self, training_data: List[float]):
        """
        Trains the anomaly detection model by pre-populating the window.
        """
        self.data_window.extend(training_data)
        if len(self.data_window) > self.window_size:
            self.data_window = self.data_window[-self.window_size :]
        logger.info("Anomaly detection model trained with {} data points.", len(training_data))

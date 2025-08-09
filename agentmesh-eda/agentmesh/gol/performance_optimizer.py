from loguru import logger
from typing import Dict, Any, List


class PerformanceOptimizer:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.thresholds = self.config.get(
            "thresholds",
            {
                "p99_latency_ms": 200,
                "error_rate_percent": 5,
                "throughput_per_second": 1000,
            },
        )
        logger.info("PerformanceOptimizer initialized with config: {}", self.config)

    def recommend_optimizations(self, metrics_data: Dict[str, Any]) -> List[str]:
        """
        Recommends performance optimizations based on metrics data.
        This is a rule-based implementation.
        """
        recommendations = []
        p99_latency = metrics_data.get("p99_latency_ms", 0)
        error_rate = metrics_data.get("error_rate_percent", 0)
        throughput = metrics_data.get("throughput_per_second", 0)

        if p99_latency > self.thresholds["p99_latency_ms"]:
            recommendations.append(
                f"High P99 latency detected ({p99_latency}ms). Consider optimizing message processing logic or scaling up consumers."
            )

        if error_rate > self.thresholds["error_rate_percent"]:
            recommendations.append(
                f"High error rate detected ({error_rate}%). Check agent logs for errors and consider implementing more robust error handling."
            )

        if throughput < self.thresholds["throughput_per_second"]:
            recommendations.append(
                f"Low throughput detected ({throughput}/sec). Consider increasing the number of producers or batching messages."
            )

        if not recommendations:
            recommendations.append("No immediate performance optimizations recommended.")

        logger.info("Generated recommendations: {}", recommendations)
        return recommendations

    def analyze_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes performance data and returns a summary.
        """
        analysis = {
            "summary": "Performance analysis complete.",
            "details": performance_data,
        }
        logger.info("Performance analysis result: {}", analysis)
        return analysis

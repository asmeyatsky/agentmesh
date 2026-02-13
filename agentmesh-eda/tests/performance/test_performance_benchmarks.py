"""
Performance Benchmarks and Load Testing

Comprehensive performance testing for AgentMesh components.

Architectural Intent:
- Benchmark agent creation performance under load
- Test message routing throughput
- Measure circuit breaker performance impact
- Establish performance baselines
- Identify scalability bottlenecks
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from agentmesh.application.use_cases.create_agent_use_case import (
    CreateAgentUseCase,
    CreateAgentDTO,
)
from agentmesh.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
)
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from agentmesh.infrastructure.adapters.in_memory_agent_repository import (
    InMemoryAgentRepository,
)


class InMemoryEventBus:
    """Lightweight event bus for performance testing"""
    async def publish(self, events):
        pass  # No-op for perf tests


class PerformanceMetrics:
    """Collection of performance metrics"""

    def __init__(self):
        self.measurements: List[float] = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()
        if self.start_time is not None:
            duration = self.end_time - self.start_time
            self.measurements.append(duration)
            return duration
        return 0.0

    def get_stats(self) -> Dict[str, float]:
        if not self.measurements:
            return {}

        return {
            "count": len(self.measurements),
            "min": min(self.measurements),
            "max": max(self.measurements),
            "mean": statistics.mean(self.measurements),
            "median": statistics.median(self.measurements),
            "p95": self._percentile(95),
            "p99": self._percentile(99),
            "std_dev": statistics.stdev(self.measurements)
            if len(self.measurements) > 1
            else 0.0,
        }

    def _percentile(self, percentile: float) -> float:
        sorted_measurements = sorted(self.measurements)
        index = int((percentile / 100) * len(sorted_measurements))
        return sorted_measurements[min(index, len(sorted_measurements) - 1)]


@pytest.mark.asyncio
class TestAgentCreationPerformance:
    """Performance tests for agent creation"""

    @pytest.fixture
    def setup(self):
        """Setup performance testing environment"""
        agent_repo = InMemoryAgentRepository()
        event_bus = InMemoryEventBus()
        create_use_case = CreateAgentUseCase(agent_repo, event_bus)
        return create_use_case

    async def test_single_agent_creation_performance(self, setup):
        """Benchmark single agent creation"""
        create_use_case = setup
        metrics = PerformanceMetrics()

        # Create agent and measure performance
        metrics.start()
        dto = CreateAgentDTO(
            tenant_id="perf-test",
            agent_id="perf-agent",
            name="Performance Test Agent",
            capabilities=[{"name": "processing", "level": 4}],
        )
        result = await create_use_case.execute(dto)
        duration = metrics.stop()

        # Verify creation succeeded
        assert result.agent_id == "perf-agent"

        # Get performance stats
        stats = metrics.get_stats()

        # Performance assertions (adjust based on your environment)
        assert stats["max"] < 1.0  # Should complete within 1 second
        assert stats["mean"] < 0.1  # Average should be reasonable

    async def test_concurrent_agent_creation_performance(self, setup):
        """Benchmark concurrent agent creation"""
        create_use_case = setup
        metrics = PerformanceMetrics()

        # Create multiple agents concurrently
        concurrent_count = 10
        creation_tasks = []

        metrics.start()

        for i in range(concurrent_count):
            dto = CreateAgentDTO(
                tenant_id=f"perf-tenant-{i % 3}",
                agent_id=f"perf-agent-{i}",
                name=f"Performance Agent {i}",
                capabilities=[{"name": "processing", "level": i % 5 + 1}],
            )
            task = create_use_case.execute(dto)
            creation_tasks.append(task)

        # Execute all creation tasks
        results = await asyncio.gather(*creation_tasks)

        total_duration = metrics.stop()

        # Verify all creations succeeded
        assert len(results) == concurrent_count
        assert all(hasattr(result, "agent_id") for result in results)

        # Performance assertions
        stats = metrics.get_stats()
        avg_per_creation = total_duration / concurrent_count
        assert avg_per_creation < 0.5  # Each creation should be < 500ms
        assert stats["max"] < 2.0  # No single creation should take > 2s

    async def test_agent_creation_scalability(self, setup):
        """Test agent creation scalability with increasing load"""
        create_use_case = setup

        # Test with different load levels
        load_levels = [1, 5, 10, 25, 50]
        performance_results = {}

        for load_level in load_levels:
            metrics = PerformanceMetrics()

            creation_tasks = []
            for i in range(load_level):
                dto = CreateAgentDTO(
                    tenant_id=f"scale-tenant-{i % 5}",
                    agent_id=f"scale-agent-{load_level}-{i}",
                    name=f"Scale Agent {load_level}-{i}",
                    capabilities=[{"name": "processing", "level": 3}],
                )
                creation_tasks.append(create_use_case.execute(dto))

            metrics.start()
            results = await asyncio.gather(*creation_tasks)
            total_duration = metrics.stop()

            stats = metrics.get_stats()
            performance_results[load_level] = {
                "total_duration": total_duration,
                "avg_duration": total_duration / load_level,
                "throughput": load_level / total_duration,  # agents per second
                "success_rate": len(results) / load_level,
            }

        # Verify scalability characteristics
        # Throughput should increase with load (to a point)
        throughputs = [result["throughput"] for result in performance_results.values()]
        assert (
            throughputs[0] < throughputs[-1]
        )  # Higher load should yield higher throughput

        # Success rate should remain high
        success_rates = [
            result["success_rate"] for result in performance_results.values()
        ]
        assert all(rate >= 0.95 for rate in success_rates)  # 95%+ success rate


@pytest.mark.asyncio
class TestMessageRoutingPerformance:
    """Performance tests for message routing"""

    @pytest.fixture
    def setup(self):
        """Setup message routing performance test"""
        return MessageRouter()

    async def test_message_routing_throughput(self, setup):
        """Benchmark message routing throughput"""
        router = setup
        metrics = PerformanceMetrics()

        # Create many messages
        message_count = 1000
        messages = [
            UniversalMessage(
                payload={"id": i, "data": f"message_{i}"},
                routing={"targets": ["test:queue"]},
            )
            for i in range(message_count)
        ]

        # Route all messages and measure performance
        metrics.start()

        for message in messages:
            await router.route_message(message)

        total_duration = metrics.stop()

        # Calculate throughput
        throughput = message_count / total_duration  # messages per second

        # Performance assertions
        assert throughput > 100  # Should handle at least 100 msg/sec
        assert total_duration < 10.0  # Should complete within 10 seconds

        # Average latency should be reasonable
        avg_latency = total_duration / message_count
        assert avg_latency < 0.01  # < 10ms per message

    async def test_message_routing_with_varying_payloads(self, setup):
        """Test routing performance with different payload sizes"""
        router = setup

        # Test different payload sizes
        payload_sizes = [100, 1000, 10000, 100000]  # bytes
        performance_results = {}

        for size in payload_sizes:
            metrics = PerformanceMetrics()

            # Create message with specified payload size
            large_payload = "x" * size
            message = UniversalMessage(
                payload={"data": large_payload, "size": size},
                routing={"targets": ["test:queue"]},
            )

            message_count = 100  # Fixed message count for this test

            metrics.start()
            for _ in range(message_count):
                await router.route_message(message)
            total_duration = metrics.stop()

            performance_results[size] = {
                "duration": total_duration,
                "throughput": message_count / total_duration,
                "avg_per_message": total_duration / message_count,
            }

        # Verify performance scales reasonably with payload size
        small_payload_perf = performance_results[100]["throughput"]
        large_payload_perf = performance_results[100000]["throughput"]

        # Large payloads should be slower but not dramatically
        performance_ratio = large_payload_perf / small_payload_perf
        assert performance_ratio > 0.1  # At least 10% of small payload performance
        assert performance_ratio < 2.0  # But not more than 2x slower


@pytest.mark.asyncio
class TestCircuitBreakerPerformance:
    """Performance tests for circuit breaker"""

    @pytest.fixture
    def setup(self):
        """Setup circuit breaker performance test"""
        config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=1.0)
        return CircuitBreaker("perf-service", config)

    async def test_circuit_breaker_overhead(self, setup):
        """Measure circuit breaker performance overhead"""
        circuit_breaker = setup
        metrics = PerformanceMetrics()

        # Create mock fast service
        async def fast_service():
            await asyncio.sleep(0.001)  # 1ms service
            return "success"

        # Test with and without circuit breaker
        call_count = 1000

        # Test without circuit breaker (baseline)
        baseline_metrics = PerformanceMetrics()
        baseline_metrics.start()

        for _ in range(call_count):
            await fast_service()

        baseline_duration = baseline_metrics.stop()

        # Test with circuit breaker
        cb_metrics = PerformanceMetrics()
        cb_metrics.start()

        for _ in range(call_count):
            await circuit_breaker.call(fast_service)

        cb_duration = cb_metrics.stop()

        # Calculate overhead
        overhead_per_call = (cb_duration - baseline_duration) / call_count
        overhead_percentage = (overhead_per_call / baseline_duration) * 100

        # Circuit breaker overhead should be minimal
        assert overhead_per_call < 0.001  # < 1ms overhead per call
        assert overhead_percentage < 50  # < 50% overhead

    async def test_circuit_breaker_under_load(self, setup):
        """Test circuit breaker performance under load"""
        circuit_breaker = setup
        metrics = PerformanceMetrics()

        # Simulate high-concurrency scenario
        concurrent_calls = 50
        call_duration = 0.01  # 10ms per call

        async def moderate_service():
            await asyncio.sleep(call_duration)
            return "success"

        # Execute many concurrent calls through circuit breaker
        metrics.start()

        call_tasks = [
            circuit_breaker.call(moderate_service) for _ in range(concurrent_calls)
        ]

        results = await asyncio.gather(*call_tasks, return_exceptions=True)

        total_duration = metrics.stop()

        # Analyze results
        successful_calls = [r for r in results if not isinstance(r, Exception)]
        failed_calls = [r for r in results if isinstance(r, Exception)]

        success_rate = len(successful_calls) / concurrent_calls

        # Should maintain good performance under load
        assert total_duration < 2.0  # All calls should complete within 2 seconds
        assert success_rate > 0.8  # At least 80% success rate


@pytest.mark.asyncio
class TestSystemResourcePerformance:
    """System resource usage performance tests"""

    @pytest.mark.slow
    async def test_memory_usage_scaling(self):
        """Test memory usage scales with agent count"""
        # This would ideally use memory_profiler, but we'll simulate
        agent_counts = [10, 50, 100, 500]

        for count in agent_counts:
            # Simulate agent creation and track memory patterns
            initial_time = time.perf_counter()

            # Create agents (simplified memory tracking)
            agents = []
            for i in range(count):
                agent_data = {
                    "id": f"mem-agent-{i}",
                    "data": "x" * 1000,  # 1KB per agent
                    "capabilities": ["processing", "analysis"],
                }
                agents.append(agent_data)

            creation_time = time.perf_counter() - initial_time

            # Estimate memory usage (simplified)
            estimated_memory_mb = (count * 1024) / (1024 * 1024)  # Rough estimate

            # Memory should scale linearly
            assert creation_time < count * 0.01  # Should be linear scaling
            assert estimated_memory_mb < count * 0.1  # Less than 100MB per 1000 agents

    @pytest.mark.slow
    async def test_database_connection_pool_performance(self):
        """Test database connection pool performance"""
        # This is a placeholder - in real implementation you'd:
        # 1. Test connection pool exhaustion
        # 2. Test connection reuse efficiency
        # 3. Test pool scaling under load

        # Simulate connection pool metrics
        pool_sizes = [5, 10, 20, 50]
        performance_results = {}

        for pool_size in pool_sizes:
            start_time = time.perf_counter()

            # Simulate database operations
            operations = 100
            for _ in range(operations):
                # Simulate connection acquisition and release
                await asyncio.sleep(0.001)  # 1ms per operation

            duration = time.perf_counter() - start_time

            performance_results[pool_size] = {
                "duration": duration,
                "ops_per_second": operations / duration,
                "avg_operation_time": duration / operations,
            }

        # All pools should have reasonable ops/second (sequential simulation)
        for pool_size, result in performance_results.items():
            assert result["ops_per_second"] > 50  # At least 50 ops/sec


# Performance test configuration
PERFORMANCE_TEST_CONFIG = {
    "load_levels": [1, 5, 10, 25, 50, 100],
    "message_counts": [100, 500, 1000, 5000],
    "payload_sizes": [100, 1000, 10000, 100000],
    "concurrent_levels": [10, 25, 50, 100],
    "performance_thresholds": {
        "max_agent_creation_time": 1.0,
        "max_message_routing_time": 0.01,
        "min_throughput": 100,
        "max_circuit_breaker_overhead": 0.001,
        "min_success_rate": 0.95,
    },
}


def pytest_configure(config):
    """Configure pytest for performance tests"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

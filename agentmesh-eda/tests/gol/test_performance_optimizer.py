from agentmesh.gol.performance_optimizer import PerformanceOptimizer


def test_performance_optimizer_init():
    optimizer = PerformanceOptimizer()
    assert optimizer.config == {}
    assert optimizer.thresholds["p99_latency_ms"] == 200


def test_recommend_optimizations_high_latency():
    optimizer = PerformanceOptimizer()
    metrics = {"p99_latency_ms": 300, "error_rate_percent": 1, "throughput_per_second": 1200}
    recs = optimizer.recommend_optimizations(metrics)
    assert len(recs) == 1
    assert "High P99 latency" in recs[0]


def test_recommend_optimizations_high_error_rate():
    optimizer = PerformanceOptimizer()
    metrics = {"p99_latency_ms": 100, "error_rate_percent": 10, "throughput_per_second": 1200}
    recs = optimizer.recommend_optimizations(metrics)
    assert len(recs) == 1
    assert "High error rate" in recs[0]


def test_recommend_optimizations_low_throughput():
    optimizer = PerformanceOptimizer()
    metrics = {"p99_latency_ms": 100, "error_rate_percent": 1, "throughput_per_second": 500}
    recs = optimizer.recommend_optimizations(metrics)
    assert len(recs) == 1
    assert "Low throughput" in recs[0]


def test_recommend_optimizations_no_issues():
    optimizer = PerformanceOptimizer()
    metrics = {"p99_latency_ms": 100, "error_rate_percent": 1, "throughput_per_second": 1200}
    recs = optimizer.recommend_optimizations(metrics)
    assert len(recs) == 1
    assert "No immediate performance optimizations recommended" in recs[0]


def test_analyze_performance():
    optimizer = PerformanceOptimizer()
    data = {"latency": 120, "throughput": 1100}
    analysis = optimizer.analyze_performance(data)
    assert analysis["summary"] == "Performance analysis complete."
    assert analysis["details"] == data

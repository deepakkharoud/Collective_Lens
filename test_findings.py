
from src.findings import generate_findings


def test_empty_report():
    findings = generate_findings({
        "kernel_count": 0,
        "unique_kernel_names": 0,
        "slowest_kernels": [],
        "kernel_name_summary": [],
    })
    assert findings[0]["id"] == "F001"
    assert findings[0]["title"] == "No GPU kernel events found"


def test_single_gpu_report_does_not_claim_distributed_diagnosis():
    findings = generate_findings({
        "kernel_count": 2,
        "unique_kernel_names": 1,
        "slowest_kernels": [{
            "name": "example_kernel",
            "duration_us": 10.0,
            "device_id": 0,
            "stream_id": 7,
        }],
        "kernel_name_summary": [{
            "name": "example_kernel",
            "count": 2,
            "total_duration_us": 15.0,
        }],
    })
    assert any(
        f["title"] == "Distributed bottleneck not assessed"
        for f in findings
    )


def test_longest_kernel_is_evidence_linked():
    findings = generate_findings({
        "kernel_count": 1,
        "unique_kernel_names": 1,
        "slowest_kernels": [{
            "name": "test_kernel",
            "duration_us": 12.5,
            "device_id": 0,
            "stream_id": 3,
        }],
        "kernel_name_summary": [],
    })
    finding = next(f for f in findings if f["id"] == "F002")
    assert "12.50 µs" in finding["evidence"][1]

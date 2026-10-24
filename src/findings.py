
def generate_findings(report: dict) -> list[dict]:
    """Generate conservative, evidence-linked findings from kernel metrics."""
    findings = []

    count = report.get("kernel_count", 0)
    unique = report.get("unique_kernel_names", 0)
    slowest = report.get("slowest_kernels", [])
    grouped = report.get("kernel_name_summary", [])

    if count == 0:
        return [{
            "id": "F001",
            "severity": "unknown",
            "title": "No GPU kernel events found",
            "evidence": [],
            "recommendation": (
                "Verify that the profiler captured CUDA kernel activity."
            ),
        }]

    findings.append({
        "id": "F001",
        "severity": "info",
        "title": "GPU kernel activity captured",
        "evidence": [
            f"{count} kernel events were recorded.",
            f"{unique} unique kernel names were observed.",
        ],
        "recommendation": (
            "Compare equivalent workloads across repeated runs "
            "before attributing performance differences."
        ),
    })

    if slowest:
        top = slowest[0]
        findings.append({
            "id": "F002",
            "severity": "info",
            "title": "Longest individual kernel identified",
            "evidence": [
                f"Kernel: {top['name']}",
                f"Duration: {top['duration_us']:.2f} µs",
                f"GPU device: {top['device_id']}",
                f"Stream: {top['stream_id']}",
            ],
            "recommendation": (
                "Inspect this kernel in the GPU timeline and compare "
                "its duration across equivalent workload runs. "
                "Duration alone does not establish a bottleneck."
            ),
        })

    if grouped:
        dominant = grouped[0]
        findings.append({
            "id": "F003",
            "severity": "info",
            "title": "Kernel with greatest cumulative duration",
            "evidence": [
                f"Kernel: {dominant['name']}",
                f"Occurrences: {dominant['count']}",
                (
                    "Summed duration: "
                    f"{dominant['total_duration_us']:.2f} µs"
                ),
            ],
            "recommendation": (
                "Check whether this kernel is expected for the workload "
                "and whether it dominates comparable runs. Summed "
                "duration can include overlapping executions."
            ),
        })

    findings.append({
        "id": "F004",
        "severity": "unknown",
        "title": "Distributed bottleneck not assessed",
        "evidence": [
            "This report contains a single-GPU workload.",
            "No cross-rank timing comparison is available.",
        ],
        "recommendation": (
            "Capture traces from multiple ranks and compare iteration "
            "times, collective activity, and rank arrival timing before "
            "assessing communication or load-imbalance hypotheses."
        ),
    })

    return findings

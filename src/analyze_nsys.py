
import argparse
import json
import sqlite3
from pathlib import Path


def analyze_nsys(db_path: str | Path) -> dict:
    """Analyze GPU kernel activity from an Nsight Systems SQLite export."""

    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(str(db_path)) as con:
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        required = {
            "CUPTI_ACTIVITY_KIND_KERNEL",
            "StringIds",
        }
        missing = required - tables
        if missing:
            raise ValueError(f"Missing required tables: {sorted(missing)}")

        # Resolve the kernel-name IDs through Nsight's StringIds table.
        columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info(CUPTI_ACTIVITY_KIND_KERNEL)"
            )
        }
        if not {"start", "end", "deviceId", "streamId",
                "demangledName", "shortName"}.issubset(columns):
            raise ValueError("Unexpected kernel table schema")

        rows = con.execute("""
            SELECT
                k.start,
                k.end,
                k.deviceId,
                k.streamId,
                k.correlationId,
                COALESCE(d.value, s.value, 'unknown') AS kernel_name
            FROM CUPTI_ACTIVITY_KIND_KERNEL AS k
            LEFT JOIN StringIds AS d ON d.id = k.demangledName
            LEFT JOIN StringIds AS s ON s.id = k.shortName
            WHERE k.end >= k.start
            ORDER BY k.start
        """).fetchall()

        memcpy_count = 0
        if "CUPTI_ACTIVITY_KIND_MEMCPY" in tables:
            memcpy_count = con.execute(
                "SELECT COUNT(*) FROM CUPTI_ACTIVITY_KIND_MEMCPY"
            ).fetchone()[0]

    kernels = []
    for start, end, device, stream, correlation, name in rows:
        duration_ns = end - start
        kernels.append({
            "name": name,
            "start_ns": start,
            "end_ns": end,
            "duration_us": duration_ns / 1000.0,
            "device_id": device,
            "stream_id": stream,
            "correlation_id": correlation,
        })

    total_duration_ns = sum(
        kernel["end_ns"] - kernel["start_ns"]
        for kernel in kernels
    )

    by_name = {}
    for kernel in kernels:
        entry = by_name.setdefault(kernel["name"], {
            "count": 0,
            "total_duration_us": 0.0,
        })
        entry["count"] += 1
        entry["total_duration_us"] += kernel["duration_us"]

    slowest = sorted(
        kernels,
        key=lambda kernel: kernel["duration_us"],
        reverse=True,
    )[:15]

    busiest_names = sorted(
        [
            {"name": name, **stats}
            for name, stats in by_name.items()
        ],
        key=lambda entry: entry["total_duration_us"],
        reverse=True,
    )[:15]

    return {
        "source": str(db_path),
        "kernel_count": len(kernels),
        "memcpy_event_count": memcpy_count,
        "sum_kernel_duration_us": total_duration_ns / 1000.0,
        "unique_kernel_names": len(by_name),
        "slowest_kernels": slowest,
        "kernel_name_summary": busiest_names,
        "interpretation_note": (
            "Kernel durations may overlap across streams. Their sum is "
            "not GPU wall-clock time or utilization. This single-GPU "
            "report alone cannot establish a distributed-training "
            "communication bottleneck."
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze GPU kernel events in an Nsight SQLite export."
    )
    parser.add_argument(
        "--db",
        default="samples/collective_lens_capture.sqlite",
        help="Path to the Nsight Systems SQLite database",
    )
    parser.add_argument(
        "--out",
        default="samples/kernel_analysis.json",
        help="Path for the JSON analysis report",
    )
    args = parser.parse_args()

    report = analyze_nsys(args.db)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"GPU kernel events: {report['kernel_count']}")
    print(f"Unique kernel names: {report['unique_kernel_names']}")
    print(f"Memory-copy events: {report['memcpy_event_count']}")
    print(
        "Sum of kernel durations (not wall-clock time): "
        f"{report['sum_kernel_duration_us']:.2f} µs"
    )

    print("\nTop 10 kernels by individual duration:")
    for kernel in report["slowest_kernels"][:10]:
        print(
            f"{kernel['duration_us']:12.2f} µs | "
            f"GPU {kernel['device_id']} | "
            f"{kernel['name']}"
        )

    print(f"\nJSON report saved to: {output}")


if __name__ == "__main__":
    main()

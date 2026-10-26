
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.findings import generate_findings

st.set_page_config(
    page_title="CollectiveLens",
    page_icon="🔬",
    layout="wide",
)

st.title("CollectiveLens")
st.caption("Evidence-driven GPU profiling and bottleneck investigation")

report_path = Path("samples/kernel_analysis.json")

uploaded_file = st.file_uploader(
    "Upload a kernel analysis JSON report",
    type=["json"],
)

try:
    if uploaded_file is not None:
        report = json.load(uploaded_file)
        report_source = uploaded_file.name
    elif report_path.exists():
        with report_path.open("r", encoding="utf-8") as file:
            report = json.load(file)
        report_source = str(report_path)
    else:
        st.info("Upload a kernel analysis JSON report to begin.")
        st.stop()
except (json.JSONDecodeError, UnicodeDecodeError) as exc:
    st.error(f"Invalid JSON report: {exc}")
    st.stop()

required_keys = {
    "kernel_count",
    "unique_kernel_names",
    "slowest_kernels",
}

missing = required_keys - report.keys()
if missing:
    st.error(f"Missing required fields: {', '.join(sorted(missing))}")
    st.stop()

st.caption(f"Report: {report_source}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("GPU kernel events", report["kernel_count"])
col2.metric("Unique kernel names", report["unique_kernel_names"])
col3.metric("Memory-copy events", report.get("memcpy_event_count", 0))
col4.metric(
    "Summed kernel duration",
    f"{report.get('sum_kernel_duration_us', 0):,.2f} µs",
)

st.warning(
    "Summed kernel durations are not wall-clock runtime. "
    "This report alone cannot establish a distributed bottleneck."
)

st.subheader("Longest individual kernel events")

slowest = report.get("slowest_kernels", [])
if slowest:
    kernel_df = pd.DataFrame(slowest)

    if "duration_us" in kernel_df.columns:
        kernel_df = kernel_df.sort_values(
            "duration_us", ascending=False
        )

    st.dataframe(
        kernel_df,
        use_container_width=True,
        hide_index=True,
    )

    if "duration_us" in kernel_df.columns and "name" in kernel_df.columns:
        chart_df = kernel_df.head(10).copy()
        chart_df["name"] = chart_df["name"].str.slice(0, 65)
        st.subheader("Top kernel durations")
        st.bar_chart(chart_df.set_index("name")["duration_us"])
else:
    st.info("No individual kernel events are available.")

st.subheader("Automated findings")

findings = generate_findings(report)

for finding in findings:
    with st.expander(
        f"{finding['id']} · {finding['title']}",
        expanded=True,
    ):
        st.caption(f"Severity: {finding['severity']}")

        st.markdown("**Evidence**")
        for evidence in finding["evidence"]:
            st.write(f"- {evidence}")

        st.markdown("**Recommended next step**")
        st.write(finding["recommendation"])

st.caption(
    "CollectiveLens provides evidence and investigation suggestions. "
    "Findings are not proof of causality."
)

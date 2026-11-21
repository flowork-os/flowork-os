# eBPF Kernel Memory Pressure Stall Sentinel
When PSI memory stalls or page-fault spikes exceed critical threshold:
1. Identify high memory consumers without killing PIDs.
2. Recommend cgroup quota throttling or cache dropping.
3. Keep system quiescent if memory pressure normalizes.

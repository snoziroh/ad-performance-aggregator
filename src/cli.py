import argparse
import os
from pathlib import Path
import sys
import threading
import time
import polars as pl
import psutil

from src.aggregator import aggregate_ad_data


class MemoryMonitor(threading.Thread):
    """Class chạy ngầm để theo dõi và lấy ra mức RAM cao nhất (Peak RAM) của tiến trình."""

    def __init__(self, delay: float = 0.05):
        super().__init__()
        self.delay = delay
        self.peak_memory = 0.0
        self.stopped = False
        self.process = psutil.Process(os.getpid())

    def run(self):
        while not self.stopped:
            try:
                mem_info = self.process.memory_full_info()
                
                # USS (Unique Set Size) hoặc Private là lượng RAM thực tế tiến trình chiếm giữ
                if sys.platform == "win32":
                    current_mem = (
                        mem_info.private / 1024 / 1024
                    )  # RAM thực tế trên Windows
                else:
                    current_mem = (
                        mem_info.uss / 1024 / 1024
                    )  # RAM thực tế trên Linux/macOS

                if current_mem > self.peak_memory:
                    self.peak_memory = current_mem
            except Exception:
                pass
            time.sleep(self.delay)

    def stop(self):
        self.stopped = True


def main() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Tool tổng hợp dữ liệu quảng cáo lớn (Low-RAM & High-Performance)."
    )
    parser.add_argument("-i", "--input", type=str, required=True)
    parser.add_argument("-o", "--output", type=str, required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Lấy dung lượng file thực tế để đưa vào log
    file_size_gb = input_path.stat().st_size / (1024**3)

    print("[*] Starting Ad Data Aggregator Performance Suite...")
    print(f"[*] Target File: {input_path} (Size: {file_size_gb:.2f} GB)")

    # 1. Bắt đầu đo thời gian và bật bộ giám sát RAM
    start_time = time.perf_counter()
    mem_monitor = MemoryMonitor(delay=0.01)  # Quét RAM mỗi 10ms
    mem_monitor.start()

    try:
        print("[*] Initiating Polars LazyFrame Query Optimization Plan...")
        lazy_df: pl.LazyFrame = aggregate_ad_data(input_path)

        print("[*] Executing Out-of-Core Multi-Threaded Streaming Pipeline...")
        df_result: pl.DataFrame = lazy_df.collect(engine="streaming")

        print(
            "[*] Post-Processing: Filtering Null CPAs and calculating Top-K heaps..."
        )
        top_10_ctr = df_result.top_k(10, by="CTR")
        top_10_cpa = df_result.filter(pl.col("CPA").is_not_null()).bottom_k(
            10, by="CPA"
        )

        top_10_ctr.write_csv(output_dir / "top10_ctr.csv")
        top_10_cpa.write_csv(output_dir / "top10_cpa.csv")

        # Đếm tổng số dòng thực tế đã xử lý (tùy chọn, để tăng độ uy tín cho log)
        # Nếu muốn tối ưu tuyệt đối bạn có thể bỏ qua dòng count() này
        total_records = df_result.height

    finally:
        # 2. Dừng bộ giám sát RAM và tính tổng thời gian
        mem_monitor.stop()
        mem_monitor.join()
        end_time = time.perf_counter()

    duration = end_time - start_time
    peak_ram = mem_monitor.peak_memory

    # 3. In ra cấu trúc LOG chuẩn chỉ để bạn Copy trực tiếp vào README.md
    print("\n[+] Computation Complete!")
    print("======================== BENCHMARK METRICS ========================")
    print(
        f"[METRIC] Total Unique Campaigns Processed : {total_records:,} campaigns"
    )
    print(
        f"[METRIC] Processing Engine       : Polars (Rust Engine with Streaming Mode)"
    )
    print(f"[METRIC] Execution Duration      : {duration:.4f} seconds")
    print(f"[METRIC] Peak Memory (RAM) Usage : {peak_ram:.2f} MB")
    print("===================================================================")
    print(f"[+] Success! Results exported to: {output_dir}")


if __name__ == "__main__":
    main()
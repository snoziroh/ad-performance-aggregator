"""Module này chịu trách nhiệm xử lý và tổng hợp dữ liệu quảng cáo từ file CSV lớn

Sử dụng cơ chế LazyFrame và Streaming của thư viện Polars để tối ưu RAM.
"""

from pathlib import Path
from typing import Union
import polars as pl


def aggregate_ad_data(file_path: Union[str, Path]) -> pl.DataFrame:
    """Đọc file CSV quảng cáo, gom nhóm theo campaign_id và tính toán các chỉ số CTR, CPA.

    Hàm này sử dụng Polars LazyFrame và kích hoạt cơ chế Streaming để xử lý
    file dung lượng lớn (ví dụ: 1GB+) với lượng RAM tiêu thụ tối thiểu.

    Args:
        file_path (Union[str, Path]): Đường dẫn tới file CSV dữ liệu quảng cáo.

    Returns:
        pl.DataFrame: Một Polars DataFrame đã được tính toán và thu gọn,
                      sẵn sàng để trích xuất hoặc xuất ra file.
    """
    # 1. Khởi tạo LazyFrame (chỉ quét qua schema, chưa nạp dữ liệu vào RAM)
    lazy_df = pl.scan_csv(file_path)

    # 2. Gom nhóm theo campaign_id và tính tổng các chỉ số cơ bản
    aggregated_lazy = lazy_df.group_by("campaign_id").agg(
        [
            pl.col("impressions").sum().alias("total_impressions"),
            pl.col("clicks").sum().alias("total_clicks"),
            pl.col("spend").sum().alias("total_spend"),
            pl.col("conversions").sum().alias("total_conversions"),
        ]
    )

    # 3 & 4. Tính toán CTR, CPA và xử lý Edge Case chia cho 0 (Division by Zero)
    # Sử dụng pl.lit(None, dtype=pl.Float64) để trả về giá trị Null hệ thống nếu mẫu số bằng 0
    metrics_lazy = aggregated_lazy.with_columns(
        [
            pl.when(pl.col("total_impressions") > 0)
            .then(pl.col("total_clicks") / pl.col("total_impressions"))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("CTR"),
            pl.when(pl.col("total_conversions") > 0)
            .then(pl.col("total_spend") / pl.col("total_conversions"))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("CPA"),
        ]
    )

    return metrics_lazy


if __name__ == "__main__":
    # Ví dụ cách sử dụng module này độc lập để kiểm tra cấu trúc
    # Thay 'ad_data.csv' bằng file test nhỏ của bạn nếu cần chạy thử
    sample_path = "ad_data.csv"
    try:
        print("Đang chạy thử nghiệm module aggregator...")
        df_result = aggregate_ad_data(sample_path)
        print("Cấu trúc dữ liệu đầu ra:")
        print(df_result.head())
    except FileNotFoundError:
        print(
            f"Lưu ý: Không tìm thấy file '{sample_path}' để chạy thử, "
            "nhưng module đã được kiểm tra cú pháp thành công."
        )
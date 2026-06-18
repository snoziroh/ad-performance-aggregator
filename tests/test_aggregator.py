"""Module chứa các bộ kiểm thử (Unit Tests) cho logic tổng hợp dữ liệu quảng cáo."""

from pathlib import Path
import polars as pl
import pytest

from src.aggregator import aggregate_ad_data


@pytest.fixture
def mock_csv_basic(tmp_path: Path) -> Path:
    """Fixture tạo file CSV giả lập để kiểm tra gom nhóm và tính toán cơ bản."""
    csv_content = (
        "campaign_id,impressions,clicks,spend,conversions\n"
        "camp_A,1000,10,100,5\n"  # CTR = 0.01, CPA = 20.0
        "camp_A,1000,10,100,5\n"  # Tổng Camp A: imp=2000, clk=20, spd=200, conv=10
        "camp_B,2000,40,300,15\n"  # CTR = 0.02, CPA = 20.0
    )
    file_path = tmp_path / "mock_ad_data_basic.csv"
    file_path.write_text(csv_content)
    return file_path


@pytest.fixture
def mock_csv_edge_cases(tmp_path: Path) -> Path:
    """Fixture tạo file CSV chứa các trường hợp đặc biệt (bằng 0)."""
    csv_content = (
        "campaign_id,impressions,clicks,spend,conversions\n"
        "camp_zero_imp,0,0,50,2\n"  # impressions = 0 -> CTR phải là Null
        "camp_zero_conv,1000,10,50,0\n"  # conversions = 0 -> CPA phải là Null
    )
    file_path = tmp_path / "mock_ad_data_edge.csv"
    file_path.write_text(csv_content)
    return file_path


@pytest.fixture
def mock_csv_top10(tmp_path: Path) -> Path:
    """Fixture tạo 12 campaign để kiểm tra logic lọc Top 10."""
    lines = ["campaign_id,impressions,clicks,spend,conversions"]

    # Tạo 12 chiến dịch có chỉ số tăng dần
    # camp_1 sẽ có CTR thấp nhất, camp_12 có CTR cao nhất và CPA thấp nhất
    for i in range(1, 13):
        lines.append(f"camp_{i},1000,{i},{1200},{i}")

    # Thêm 1 chiến dịch lỗi để đảm bảo bị loại khỏi bộ lọc CPA
    lines.append("camp_edge,500,5,50,0")

    file_path = tmp_path / "mock_ad_data_top10.csv"
    file_path.write_text("\n".join(lines))
    return file_path


def test_aggregation_and_calculations(mock_csv_basic: Path) -> None:
    """Kiểm tra hàm aggregator gom nhóm chính xác và tính đúng chỉ số."""
    # Thực thi hàm và collect dữ liệu từ LazyFrame
    result_df = aggregate_ad_data(mock_csv_basic).collect()

    # Xác nhận số lượng campaign sau khi group_by
    assert result_df.height == 2

    # Kiểm tra tính toán của camp_A (dữ liệu đã được cộng dồn)
    camp_a = result_df.filter(pl.col("campaign_id") == "camp_A")
    assert camp_a.item(0, "total_impressions") == 2000
    assert camp_a.item(0, "total_clicks") == 20
    assert camp_a.item(0, "total_spend") == 200
    assert camp_a.item(0, "total_conversions") == 10
    assert camp_a.item(0, "CTR") == 0.01
    assert camp_a.item(0, "CPA") == 20.0


def test_edge_cases_division_by_zero(mock_csv_edge_cases: Path) -> None:
    """Kiểm tra xử lý an toàn khi mẫu số bằng 0 (impressions=0 hoặc conversions=0)."""
    result_df = aggregate_ad_data(mock_csv_edge_cases).collect()

    # Kiểm tra trường hợp impressions = 0
    camp_zero_imp = result_df.filter(
        pl.col("campaign_id") == "camp_zero_imp"
    )
    assert camp_zero_imp.item(0, "CTR") is None  # Phải nhận giá trị Null/None
    assert camp_zero_imp.item(0, "CPA") == 25.0

    # Kiểm tra trường hợp conversions = 0
    camp_zero_conv = result_df.filter(
        pl.col("campaign_id") == "camp_zero_conv"
    )
    assert camp_zero_conv.item(0, "CTR") == 0.01
    assert camp_zero_conv.item(0, "CPA") is None  # Phải nhận giá trị Null/None


def test_top_10_ctr_and_cpa_logic(mock_csv_top10: Path) -> None:
    """Kiểm tra logic trích xuất Top 10 CTR cao nhất và Top 10 CPA thấp nhất."""
    df_result = aggregate_ad_data(mock_csv_top10).collect()

    # 1. Kiểm tra Top 10 CTR cao nhất
    top_10_ctr = df_result.top_k(10, by="CTR")
    assert top_10_ctr.height == 10
    # Chiến dịch có CTR cao nhất phải là camp_12
    assert top_10_ctr.item(0, "campaign_id") == "camp_12"

    # 2. Kiểm tra Top 10 CPA thấp nhất (áp dụng filter loại bỏ Null)
    top_10_cpa = df_result.filter(pl.col("CPA").is_not_null()).bottom_k(
        10, by="CPA"
    )
    assert top_10_cpa.height == 10
    # Đảm bảo camp_edge (conversions=0 -> CPA=Null) không lọt vào top thấp nhất
    assert "camp_edge" not in top_10_cpa["campaign_id"].to_list()
    # Chiến dịch có CPA thấp nhất (1200 / 12 = 100) phải đứng đầu danh sách bottom_k
    assert top_10_cpa.item(0, "campaign_id") == "camp_12"
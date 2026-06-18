- Promt 1: "Tôi đang cần xử lý một file dữ liệu quảng cáo CSV nặng khoảng 1GB (ad_data.csv). Yêu cầu cốt lõi là phải gom nhóm dữ liệu theo campaign_id, tính toán các chỉ số (CTR, CPA), lọc ra Top 10 CTR cao nhất và Top 10 CPA thấp nhất, xuất ra file CSV.

Vì dung lượng file lớn (1GB), tiêu chí hàng đầu là tối ưu hiệu năng và bộ nhớ RAM (Memory-efficient). Tôi muốn dùng ngôn ngữ Python. Hãy phân tích bài toán này và đề xuất cho tôi các giải pháp đọc/ghi dữ liệu để RAM tiêu tốn là thấp nhất (ví dụ: dùng thư viện standard csv với cơ chế streaming, hoặc dùng Polars với LazyFrame). Hãy so sánh ưu/nhược điểm và chọn ra giải pháp tốt nhất."

- Promt 2: "Dựa trên giải pháp Polars LazyFrame, hãy viết cho tôi module core logic (src/aggregator.py).
    Module này cần chứa một hàm xử lý chính nhận vào đường dẫn file input và trả về một Polars DataFrame đã tính toán. Yêu cầu chi tiết:
    1. Sử dụng pl.scan_csv(file_path) để khởi tạo LazyFrame.
    2. Sử dụng .group_by("campaign_id") và .agg() để tính tổng: impressions, clicks, spend, conversions.
    3. Sử dụng .with_columns() để tính toán 2 chỉ số mới:
        - CTR = clicks / impressions
        - CPA = spend / conversions
    4. Xử lý Edge Case: Sử dụng pl.when().then().otherwise() của Polars để nếu conversions == 0 thì CPA sẽ nhận giá trị None (hoặc Null) nhằm tránh lỗi chia cho 0 (expr-division-by-zero). Nếu impressions == 0, CTR cũng nên trả về None hoặc 0.
Hãy viết code clean, tuân thủ PEP 8, có Type Hinting đầy đủ."

- Promt 3: "Bây giờ, hãy viết file src/cli.py sử dụng thư viện argparse để nhận tham số dòng lệnh --input và --output.
    Trong file này, hãy gọi hàm xử lý từ src/aggregator.py thu được ở bước trước (đang là một LazyFrame). Sau đó thực hiện tiếp:
    1. Kích hoạt tính toán bằng cách gọi .collect(streaming=True) để đảm bảo Polars xử lý file 1GB theo dạng stream cụm dữ liệu nhằm tiết kiệm RAM.
    2. Từ DataFrame kết quả thu được, hãy lọc ra:
        - Top 10 CTR cao nhất: Sử dụng hàm .top_k(10, by="CTR") của Polars để tối ưu hiệu năng.
        - Top 10 CPA thấp nhất: Cần filter loại bỏ các dòng có CPA là Null hoặc conversions == 0 trước, sau đó dùng .bottom_k(10, by="CPA") (hoặc top_k với giá trị âm/đảo ngược) để lấy 10 campaign có CPA thấp nhất.
    3. Xuất kết quả của 2 danh sách này ra file top10_ctr.csv và top10_cpa.csv vào thư mục --output bằng hàm .write_csv(). Tự động tạo thư mục output nếu chưa có."

- Promt 4: "Tôi cần viết Unit Test cho hệ sinh thái Polars này bằng pytest. Hãy tạo file tests/test_aggregator.py.
    Hãy viết các test case sử dụng dữ liệu giả lập (mock data) dạng chuỗi CSV hoặc Polars DataFrame nhỏ để kiểm tra:
    1. Hàm aggregator gom nhóm và tính tổng chính xác.
    2. Phép tính CTR và CPA hoạt động đúng, đặc biệt là khi dữ liệu có dòng conversions = 0 hoặc impressions = 0.
    3. Logic lọc Top 10 CTR và CPA trả về đúng số lượng và đúng thứ tự mong muốn.
Hãy hướng dẫn tôi câu lệnh chạy test."

- Promt 5: "Trong file ad_data.csv có chứa cột date (định dạng YYYY-MM-DD). Dù cột này không tham gia vào các phép tính toán tổng (Aggregation) hay tính CTR/CPA, chúng ta vẫn cần đảm bảo hệ thống nhận diện đúng Schema của file đầu vào và phần Mock Data trong Unit Test phải khớp 100% với thực tế.
    Hãy giúp tôi cập nhật lại:
    1. src/aggregator.py: Khi sử dụng pl.scan_csv(), hãy khai báo tường minh schema đầu vào (hoặc đảm bảo Polars bỏ qua/xử lý cột date một cách tối ưu thông qua Projection Pushdown - tức là tự động loại bỏ cột không dùng tới trước khi tính toán để tiết kiệm RAM).
    2. tests/test_aggregator.py: Cập nhật lại chuỗi Mock Data (hoặc DataFrame giả lập) để bổ sung thêm cột date với dữ liệu mẫu dạng 2025-01-01, 2025-01-02 chuẩn schema.
Hãy xuất lại cho tôi đoạn code hoàn chỉnh sau khi sửa của cả 2 file này."

- Promt 6: "Hãy giúp tôi tạo 2 file sau:
    1. File Dockerfile: Sử dụng python:3.11-slim và tối ưu dung lượng image.
    2. File README.md (tiếng Anh) chứa các mục sau: Setup instructions, How to run the program, Libraries used, Processing time for the 1GB file, Peak memory usage, Benchmark logs"
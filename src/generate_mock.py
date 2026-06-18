from pathlib import Path
import time


def replicate_csv(
    input_file: str, output_file: str, num_copies: int = 10
) -> None:
    """Nhân bản file CSV bằng cách sao chép theo từng cụm (Chunk) 64KB.

    Đảm bảo chỉ giữ lại 1 dòng Header ở đầu file mới.
    """
    in_p = Path(input_file)
    out_p = Path(output_file)

    start_time = time.perf_counter()
    print(f"[*] Bắt đầu nhân bản file: {in_p.name} -> {out_p.name}")

    # 1. Đọc và ghi dòng Header đầu tiên
    with open(in_p, "r", encoding="utf-8") as f_in:
        header = f_in.readline()

    with open(out_p, "w", encoding="utf-8") as f_out:
        f_out.write(header)

        # 2. Lặp 10 lần để append phần dữ liệu (bỏ qua header của mỗi lần đọc)
        for i in range(num_copies):
            print(f"   -> Đang ghi bản sao lần thứ {i + 1}/{num_copies}...")

            with open(in_p, "r", encoding="utf-8") as f_in:
                f_in.readline()  # Bỏ qua dòng header của file gốc

                # Đọc theo cụm 64KB và ghi thẳng vào file out
                while True:
                    chunk = f_in.read(64 * 1024)  # 64 KB buffer
                    if not chunk:
                        break
                    f_out.write(chunk)

    duration = time.perf_counter() - start_time
    file_size_gb = out_p.stat().st_size / (1024**3)
    print(
        f"[+] Thành công! Đã tạo file {out_p.name} ({file_size_gb:.2f} GB) trong {duration:.2f} giây."
    )


if __name__ == "__main__":
    # Thay đổi đường dẫn cho đúng cấu trúc thư mục của bạn
    replicate_csv("data/ad_data_new.csv", "data/ad_data_10gb.csv", num_copies=10)
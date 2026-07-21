# CV AI cho Odoo 17

`cv_ai` đọc CV dạng PDF có text hoặc DOCX, gửi phần văn bản đã trích xuất
đến Ollama và trả về một Python dictionary chứa thông tin ứng viên đã được
kiểm tra, chuẩn hóa.

Module không tạo batch, document hoặc candidate. Việc lưu và duyệt ứng viên
thuộc trách nhiệm của module `cv_repository`.

## 1. Thành phần cần có

- Odoo 17.
- Python đang được dùng để chạy Odoo.
- Ollama chạy trên máy host, máy khác hoặc Docker.
- Model mặc định: `qwen3:1.7b`.
- Thư viện Python: `requests`, `PyMuPDF`, `python-docx`.

Module hỗ trợ:

- PDF có lớp text.
- DOCX, gồm paragraph và nội dung trong table.

Module chưa hỗ trợ PDF scan, ảnh và OCR.

## 2. Cài thư viện Python

Phải cài thư viện vào đúng Python interpreter đang chạy Odoo. Nếu dự án dùng
virtual environment `.venv` trên Windows, chạy tại thư mục chứa `odoo-bin`:

```powershell
.\.venv\Scripts\python.exe -m pip install requests PyMuPDF python-docx
```

Nếu Odoo dùng Python hệ thống:

```powershell
python -m pip install requests PyMuPDF python-docx
```

Kiểm tra import:

```powershell
python -c "import requests, fitz, docx; print('Python dependencies OK')"
```

Tên package và tên import khác nhau ở hai thư viện:

| Package cài bằng pip | Tên import |
|---|---|
| `PyMuPDF` | `fitz` |
| `python-docx` | `docx` |
| `requests` | `requests` |

## 3. Cài Ollama trực tiếp trên Windows

Tải bộ cài Windows từ tài liệu chính thức:

- <https://docs.ollama.com/windows>

Sau khi cài, mở PowerShell mới và kiểm tra:

```powershell
ollama --version
```

Ollama trên Windows thường tự chạy nền. Nếu cần chạy thủ công:

```powershell
ollama serve
```

Không chạy hai tiến trình `ollama serve` cùng chiếm cổng `11434`.

### Pull model

```powershell
ollama pull qwen3:1.7b
```

Kiểm tra model đã tải:

```powershell
ollama list
```

Có thể chạy thử trực tiếp:

```powershell
ollama run qwen3:1.7b
```

Trang model chính thức:

- <https://ollama.com/library/qwen3:1.7b>

## 4. Chạy Ollama bằng Docker

### CPU

```powershell
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
```

Volume `ollama` giữ model sau khi container được tạo lại.

Pull model vào đúng container:

```powershell
docker exec -it ollama ollama pull qwen3:1.7b
```

Kiểm tra:

```powershell
docker ps
docker exec -it ollama ollama list
docker logs ollama
```

Khởi động lại container đã có:

```powershell
docker start ollama
```

Tài liệu Docker chính thức:

- <https://docs.ollama.com/docker>

### NVIDIA GPU

Chỉ dùng khi Docker đã được cấu hình NVIDIA Container Toolkit:

```powershell
docker run -d --gpus=all --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
```

Không thêm `--gpus=all` nếu máy hoặc Docker chưa hỗ trợ GPU passthrough.

## 5. Chọn đúng Ollama URL

URL phụ thuộc nơi Odoo và Ollama đang chạy:

| Odoo | Ollama | URL cấu hình |
|---|---|---|
| Windows host | Windows host | `http://localhost:11434` |
| Windows host | Docker có `-p 11434:11434` | `http://localhost:11434` |
| Docker | Windows host | `http://host.docker.internal:11434` |
| Docker | Container cùng Docker network | `http://ollama:11434` |
| Máy khác | Ollama server trong LAN | `http://IP_MAY_CHU:11434` |

`localhost` bên trong container Odoo là chính container Odoo, không phải máy
Windows và cũng không phải container Ollama.

Nếu Ollama chạy trên máy khác, cần cấu hình Ollama lắng nghe trên interface phù
hợp và chỉ mở firewall cho mạng tin cậy. Không nên công khai cổng `11434` trực
tiếp ra Internet.

## 6. Kiểm tra Ollama API trước khi cài module

Kiểm tra server và danh sách model bằng PowerShell:

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:11434/api/tags"
```

Kiểm tra `/api/chat`:

```powershell
$body = @{
    model = "qwen3:1.7b"
    stream = $false
    think = $false
    messages = @(
        @{
            role = "user"
            content = "Chỉ trả lời: OK"
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:11434/api/chat" `
    -ContentType "application/json" `
    -Body $body
```

Nếu Odoo chạy trong Docker, nên kiểm tra URL từ chính container Odoo thay vì
chỉ kiểm tra từ Windows host.

## 7. Cài module Odoo

Đảm bảo `custom_addons` có trong `addons_path`, sau đó chạy tại thư mục chứa
`odoo-bin`:

```powershell
python odoo-bin -c odoo.conf -d school_management -i cv_ai --stop-after-init
```

Nếu cài đồng thời kho CV:

```powershell
python odoo-bin -c odoo.conf -d school_management -i cv_ai,cv_repository --stop-after-init
```

Update sau khi thay đổi source code:

```powershell
python odoo-bin -c odoo.conf -d school_management -u cv_ai,cv_repository --stop-after-init
```

Khởi động lại tiến trình Odoo đang phục vụ web sau khi cài hoặc update nếu môi
trường hiện tại không tự reload registry.

## 8. Cấu hình trong Odoo

Đăng nhập bằng tài khoản có quyền Settings và mở phần cấu hình **CV AI**. Nếu
đã cài `cv_repository`, có thể đi từ:

```text
CV Repository → Configuration
```

Cấu hình khuyến nghị cho Ollama chạy CPU:

| Cấu hình | Giá trị khuyến nghị |
|---|---|
| Ollama URL | Theo bảng URL ở trên |
| Model | `qwen3:1.7b` |
| Request timeout | `300` giây |
| Maximum CV text length | `50000` ký tự |

Các config parameter tương ứng:

```text
cv_ai.ollama_base_url
cv_ai.ollama_model
cv_ai.request_timeout
cv_ai.max_text_length
```

Model trong Odoo phải trùng chính xác với tên hiển thị bởi `ollama list`.

## 9. Public service contract

Module khác gọi service bằng một record `ir.attachment`:

```python
result = self.env["cv.ai.service"].parse_attachment(attachment)
```

Kết quả là Python dictionary, không phải chuỗi JSON:

```python
{
    "full_name": "Nguyễn Văn A",
    "email": "example@gmail.com",
    "phone": "0912345678",
    "current_position": "IT Helpdesk",
    "location": "Hà Nội",
    "summary": "Thông tin tóm tắt",
    "skills": ["Windows", "Networking"],
    "education": [],
    "experiences": [],
    "certifications": [],
    "languages": [],
    "links": {
        "linkedin": None,
        "github": None,
        "portfolio": None,
    },
    "warnings": [],
    "raw_text": "Nội dung đã extract từ CV",
    "provider": "ollama",
    "model": "qwen3:1.7b",
}
```

Service thực hiện theo thứ tự:

```text
Validate attachment
→ extract PDF/DOCX
→ giới hạn text
→ POST /api/chat
→ parse JSON từ message.content
→ validate và chuẩn hóa
→ bổ sung raw_text, provider, model
→ trả dictionary
```

## 10. Payload gửi đến Ollama

Provider gọi:

```text
POST {Ollama URL}/api/chat
```

Các thiết lập chính:

```python
{
    "model": "qwen3:1.7b",
    "stream": False,
    "think": False,
    "keep_alive": "30m",
    "format": "candidate JSON schema",
    "options": {
        "temperature": 0,
        "num_predict": 2048,
    },
}
```

Module gửi text đã trích xuất, không gửi trực tiếp file PDF/DOCX. Nội dung CV có
thể chứa dữ liệu cá nhân, vì vậy chỉ nên dùng Ollama server do tổ chức kiểm soát.
Module không log toàn bộ CV hoặc toàn bộ AI response.

## 11. Xử lý lỗi thường gặp

### `Could not connect to the configured Ollama server`

1. Chạy `Invoke-RestMethod .../api/tags` với đúng URL.
2. Kiểm tra `ollama serve`, `docker ps` hoặc `docker logs ollama`.
3. Kiểm tra port mapping `11434:11434`.
4. Nếu Odoo chạy trong Docker, đổi `localhost` thành
   `host.docker.internal` hoặc tên service Docker.
5. Kiểm tra firewall và network.

### Ollama báo không tìm thấy model

Pull model trên đúng instance Ollama mà Odoo đang gọi:

```powershell
ollama pull qwen3:1.7b
```

Hoặc với Docker:

```powershell
docker exec -it ollama ollama pull qwen3:1.7b
```

### Request timeout

Ollama chạy CPU có thể cần vài phút cho một CV. Tăng `Request timeout` lên
`300` hoặc cao hơn và dùng model nhỏ phù hợp phần cứng. `cv_repository` xử lý
CV bằng cron nên request giao diện không phải chờ Ollama.

### PDF không có text

Đây thường là PDF scan hoặc ảnh. Phiên bản hiện tại không hỗ trợ OCR; cần dùng
PDF có text hoặc chuyển nội dung sang DOCX.

### Ollama trả JSON không hợp lệ

Kiểm tra model đúng là `qwen3:1.7b`, cập nhật Ollama, thử lại document và xem
Processing Logs. Candidate chỉ được tạo khi kết quả vượt qua validator.

## 12. Kiểm tra source module

```powershell
python -m compileall custom_addons/cv_ai
```

Module không yêu cầu API token, không tạo candidate, không quản lý batch và
không thực hiện OCR.

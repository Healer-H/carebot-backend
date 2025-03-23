# CareBot Chatbot Service

CareBot Chatbot Service là thành phần chính trong hệ thống CareBot, cung cấp chức năng trò chuyện y tế thông minh với khả năng truy xuất thông tin từ nguồn đáng tin cậy.

## Tính năng

- Xử lý câu hỏi y tế bằng công nghệ RAG (Retrieval Augmented Generation)
- Truy xuất thông tin từ cơ sở dữ liệu vector chứa kiến thức y tế
- Tạo phản hồi thông minh với trích dẫn nguồn
- Đảm bảo thông tin an toàn và đáng tin cậy
- Hỗ trợ quản lý lịch sử trò chuyện
- Phát hiện và xử lý tình huống y tế khẩn cấp

## Cài đặt

### Yêu cầu

- Python 3.9+
- MongoDB
- ChromaDB
- OpenAI API key

### Cài đặt dependencies

```bash
pip install -r requirements.txt
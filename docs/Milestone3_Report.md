flowchart TD
    %% Định nghĩa màu sắc cho các cụm (Styling)
    classDef frontend fill:#e1bee7,stroke:#8e24aa,stroke-width:2px;
    classDef backend fill:#bbdefb,stroke:#1e88e5,stroke-width:2px;
    classDef ai fill:#c8e6c9,stroke:#43a047,stroke-width:2px;
    classDef db fill:#ffe0b2,stroke:#fb8c00,stroke-width:2px;

    %% 1. Khởi đầu từ User
    Start([👤 Người dùng nhập từ khóa]):::frontend --> API[⚡ Cổng API: GET /api/search]:::backend

    %% 2. Tách luồng chạy song song (Async)
    API -->|Phân nhánh| Split((Chạy song song))
    
    %% Luồng 1: Truyền thống (Lexical)
    Split --> BM25_Prep[Tiền xử lý văn bản \n (Tách từ, xóa stopwords)]
    BM25_Prep --> BM25_Search[(Inverted Index .pkl)]
    BM25_Search --> BM25_Top[Trả về Top N Doc IDs \n (Khớp chính xác chữ)]

    %% Luồng 2: Trí tuệ nhân tạo (Semantic)
    Split --> Vector_Embed[🤖 Model AI \n Biến câu query thành mảng số Vector]:::ai
    Vector_Embed --> Vector_Search[(FAISS Vector Database)]:::ai
    Vector_Search --> Vector_Top[Trả về Top N Doc IDs \n (Khớp theo ý nghĩa)]:::ai

    %% 3. Hợp nhất (Hybrid)
    BM25_Top --> Hybrid_Merge{Gộp 2 tập kết quả \n (Hybrid Re-ranking)}:::backend
    Vector_Top --> Hybrid_Merge
    
    %% 4. Xử lý sau hợp nhất
    Hybrid_Merge --> RRF[Chấm điểm lại bằng trọng số \n Loại bỏ ID trùng lặp]
    RRF --> Top20[Chốt danh sách Top 20 Doc IDs xuất sắc nhất]
    
    %% 5. Kết nối Database
    Top20 --> DB_Query[Gửi danh sách 20 ID lên Supabase]:::db
    DB_Query --> DB[(Supabase PostgreSQL)]:::db
    DB -->|Trả về Tên, Giá, Ảnh| Formatter[Format dữ liệu & Sắp xếp theo ID]:::backend
    
    %% 6. Trả kết quả
    Formatter --> Response[📦 Trả về file JSON]:::backend
    Response --> End([💻 Hiển thị lên Website]):::frontend

    %% Ghi log ngầm
    Response -.->|Background Task| LogDB[(Bảng search_logs \n trên Supabase)]:::db

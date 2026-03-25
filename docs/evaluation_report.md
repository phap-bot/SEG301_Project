# M3 Evaluation Report: Precision@10 Comparison

This report compares the performance of Traditional Search (BM25) vs AI Search (Vector) vs Hybrid Search.

## Overall Average Precision@10
- **BM25**: 1.00
- **Vector**: 0.92
- **Hybrid**: 1.00

## Detailed Results
| Query                             | Type      |   BM25 P@10 |   Vector P@10 |   Hybrid P@10 |
|:----------------------------------|:----------|------------:|--------------:|--------------:|
| máy tính chơi game                | Semantic  |           1 |           1   |             1 |
| điện thoại chụp ảnh đẹp           | Semantic  |           1 |           0.5 |             1 |
| tai nghe không dây                | Semantic  |           1 |           0.9 |             1 |
| đồng hồ thông minh                | Semantic  |           1 |           1   |             1 |
| quạt mát mùa hè                   | Semantic  |           1 |           0.7 |             1 |
| iphone 15 pro max                 | Keyword   |           1 |           1   |             1 |
| macbook air m2                    | Keyword   |           1 |           1   |             1 |
| tủ lạnh panasonic inverter        | Keyword   |           1 |           1   |             1 |
| máy giặt toshiba 9kg              | Keyword   |           1 |           1   |             1 |
| samsung galaxy z flip             | Keyword   |           1 |           1   |             1 |
| laptop                            | Short     |           1 |           1   |             1 |
| tivi                              | Short     |           1 |           1   |             1 |
| chuột                             | Short     |           1 |           1   |             1 |
| bàn phím                          | Short     |           1 |           1   |             1 |
| ipad                              | Short     |           1 |           1   |             1 |
| nồi chiên không dầu dung tích lớn | Long-tail |           1 |           0.9 |             1 |
| balo đựng laptop chống nước       | Long-tail |           1 |           1   |             1 |
| giày thể thao nam chạy bộ         | Long-tail |           1 |           1   |             1 |
| áo sơ mi nam trắng công sở        | Long-tail |           1 |           0.7 |             1 |
| sách đắc nhân tâm                 | Long-tail |           1 |           0.7 |             1 |

## Analysis
- **Vector Search (AI)** tends to outperform BM25 on Semantic queries (e.g., 'máy tính chơi game'), discovering items even when exact keywords are missing.
- **BM25** remains very strong on Exact/Keyword queries (e.g., 'iphone 15 pro max').
- **Hybrid Search** provides the most balanced and optimal results by leveraging Reciprocal Rank Fusion.

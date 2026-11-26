# Hướng dẫn truy vết số liệu — Báo cáo quản trị DOAU

Tài liệu này giải thích report lấy số từ workbook nào, sheet/cell nào, biến đổi ra sao và quy tắc nào được áp dụng trước khi số xuất hiện trên HTML/PDF. Không ghi lại giá trị tài chính thực tế ở đây để tránh tạo thêm bản sao của dữ liệu khách hàng, SKU và tài chính.

## 1. Luồng tạo số và file đầu ra

```text
inputs/workbooks/*.xlsm
        │
        ├─ src/report/extract_data.py
        │      đọc cell / dò nhãn → kiểm tra đối chiếu → data/generated/extracted_data.json
        │
        ├─ src/report/report_metrics.py
        │      tính các KPI dẫn xuất
        │
        ├─ src/report/chart_rendering.py + generate_report.py
        │      tạo SVG, bảng, lời bình → reports/generated/*.html
        │
        └─ Chrome Headless → reports/generated/*.pdf
```

Workbook chính là `inputs/workbooks/FS DOAU Oct 26_adjust.xlsm`; báo cáo lưu chuyển tiền tệ gián tiếp nằm trong `inputs/workbooks/FS_DOAU_Oct_26_CF_Indirect_Fixed_v2.xlsm`. Hai workbook đều có sheet tên `CF` nhưng phục vụ hai phần khác nhau: sheet `CF` của workbook chính là lịch EBITDA điều chỉnh; sheet `CF` của workbook lưu chuyển tiền tệ riêng là cash flow.

Chạy tại thư mục gốc repo:

```powershell
python .\src\report\extract_data.py
python -m unittest discover -s .\src\report -p "test_*.py" -v
python .\src\report\generate_report.py
```

`generate_report.py` đọc snapshot `data/generated/extracted_data.json`; trình duyệt không đọc workbook hoặc JSON trực tiếp. Khi thay workbook, phải chạy extraction trước khi sinh lại HTML/PDF. PDF cần Google Chrome; có thể đặt `CHROME_PATH` nếu Chrome không nằm ở vị trí mặc định.

## 2. Quy ước đọc và trình bày

- Python đọc workbook bằng `openpyxl` với `data_only=True`: report lấy **giá trị đã được Excel lưu/cached**, không tự tính lại công thức Excel. Nếu workbook chưa được Excel tính/lưu lại, giá trị cached có thể cũ hoặc trống.
- Trong các cell được chuyển bằng biểu thức `float(cell.value or 0)`, ô trống/`None` được xem là `0`. Những dòng cần thiết hoặc ô cash flow không số sẽ gây lỗi rõ ràng thay vì tự bỏ qua.
- Ký hiệu ô như `K45` nghĩa là cột K, hàng 45. `B:C` chỉ hai cột current/prior, không phải công thức Excel. Tất cả số tiền theo USD như workbook nguồn.
- `fmt(...)`: USD, làm tròn về số nguyên khi hiển thị; số âm đặt trong ngoặc, ví dụ định dạng `( $... )` không dùng dấu trừ.
- `fmt_k(...)`: chia 1.000, hiển thị một chữ số thập phân và hậu tố `k`; số âm trong ngoặc.
- `compact_money(...)` cho nhãn chart: trị tuyệt đối từ 1.000.000 trở lên hiển thị `$M` một chữ số thập phân; thấp hơn hiển thị `$k` làm tròn đến nghìn; số âm trong ngoặc.
- `pct(...)`: nhân tỷ lệ với 100, hiển thị một chữ số thập phân; số âm trong ngoặc. `N/A` nghĩa là tỷ lệ không xác định vì thiếu mẫu số hoặc mẫu số bằng 0.
- `percent_change(current, prior) = (current - prior) / abs(prior)`. Mẫu số bằng 0/không có thì trả `None`, thường hiển thị `N/A`. Dùng trị tuyệt đối của kỳ trước nên phần trăm vẫn có mẫu số dương kể cả khi số kỳ trước âm.
- `safe_divide(a, b) = a / b`; nếu `a`/`b` thiếu hoặc `b = 0`, kết quả là `None`. Riêng gross margin tháng trong `monthly_trend` được extractor gán `0` khi doanh thu bằng 0; đó là một ngoại lệ khác với KPI dùng `safe_divide`.
- Màu xanh/đỏ chủ yếu biểu thị dấu của giá trị hoặc chênh lệch; không tự nó khẳng định kết quả là tốt/xấu. Một số dòng variance trong markup đặt class màu cố định, vì vậy hãy đọc số và công thức, không suy luận từ màu đơn lẻ.

## 3. Quy tắc trích xuất theo sheet

### Workbook chính — `FS DOAU Oct 26_adjust.xlsm`

| Sheet | Nguồn và phạm vi đọc | Xử lý |
|---|---|---|
| `007-DOAU data` | Tháng ở `G3:P3`; các hàng chỉ tiêu: revenue `106`, COGS `159`, gross profit `160`, admin expense `207`, sales expense `219`, total OpEx `221`, net operating income `234`, interest `229`, depreciation `129`, EBITDA `246`. | Tên tháng được tạo từ date header; cột tháng được chọn theo header. Các tháng hiện có trải từ G đến P. Sep/Oct so sánh dùng trực tiếp cột O/P. Gross margin tháng trong JSON = `gross profit / revenue`, nếu revenue 0 thì gán 0. |
| `PL YTD Aug 26` | Cột B = YTD hiện tại, C = YTD năm trước; D/E là revenue variance/variance % được workbook cung cấp. Các hàng: custom processing `9`, sales `12`, discounts `10`, revenue `14`, direct labor `23`, COGS `52`, gross profit `53`, factory overhead `51`, admin expenses `96`, sales expenses `106`, total OpEx `107`, ordinary income `108`, interest `115`, net income `118`. | B/C được đọc thành số liệu current/prior. D14/E14 cũng được giữ riêng. Nhiều variance khác được Python tính từ B−C thay vì đọc variance trong workbook. Tên sheet có chữ “Aug” nhưng kỳ trong báo cáo phải được hiểu theo header và số liệu thực của workbook; mã hiện dùng so sánh YTD 2026 với YTD 2025. |
| `PL` | Cột L (“After”, tháng report): custom processing `9`, direct labor taxes `19`, direct labor base `21`, direct labor `22`, production payroll `35`, factory overhead `43`, COGS `44`, gross profit `45`, payroll fee `69`, admin payroll `72`, admin expense `77`, sales expense `87`, total OpEx `88`, ordinary income `89`, interest `95`, other income `97`, net income `98`, sales `12`, revenue `14`. | Các số P&L tháng được lấy trực tiếp từ L. Một số hàng payroll là component riêng cho trang HR. Các tỷ lệ `% Revenue` trên trang 5 được Python tính bằng từng line item chia cho `PL!L14`. |
| `CF` (lịch điều chỉnh EBITDA trong workbook chính) | YTD tại cột C; tháng report tại cột M. Hàng: depreciation `10`, interest `12`, baseline EBITDA `14`, consulting `17`, bonus `18`, loyalty `19`, rent `20`, total addbacks `21`, adjusted EBITDA `23`. | Các giá trị schedule được đọc trực tiếp, không tính lại bridge từ từng addback. Ở tháng report, `consulting_fee` và `bonus_vinh` được gán cứng bằng 0 trong Python; không đọc M17/M18. Operational EBITDA là số từ `007-DOAU data!P246` cho tháng và tổng `G246:P246` cho YTD, được trình bày riêng với baseline EBITDA của sheet CF. |
| `BS` | Cột K (“After”), snapshot cuối tháng report. Current assets: cash `10`, allowance `13`, gross AR `14`, net AR `15`, inventory `22`, undeposited `24`, prepaid `25`, current assets total `26`. Fixed assets: accumulated depreciation components `28:30`, auto `31`, automation `32`, building improvements components `33:34`, office/computer components `35` và `38`, CIP `36`, furniture/equipment `37`, production equipment `39`, fixed assets total `40`, total assets `45`. Liabilities/equity: AP `51`, credit cards `57`, accrued `59`, loan `64`, payroll liability `67`, current liabilities `69`, long-term loans `71:76`, total long-term liabilities `77`, total liabilities `78`, capital `80`, members' equity `81`, retained earnings `82`, net income `83`, total equity `84`, liabilities + equity `85`. | Các line items lấy trực tiếp; nhóm hiển thị có thể là tổng của nhiều cell: prepaid + undeposited = `K25+K24`; building improvements = `K34+K33`; office/computer = `K35+K38`; accumulated depreciation = `K30+K28+K29`. Các nhóm trên trang 6 cũng cộng những khoản liên quan để trình bày cùng một dòng. |
| `AR` | Chi tiết hàng `2:59`: tên `A`, buckets current `B`, 1–30 `C`, 31–60 `D`, 61–90 `E`, >90 `G`, tổng `H`, phân loại `N`. Tổng sheet: hàng `60` cho bucket và total; phân loại intercompany/third-party ở `H62:H63`. | Bỏ dòng thiếu tên và dòng tên có chữ `total` (không phân biệt hoa/thường). Chỉ đưa chi tiết vào JSON nếu tổng, current hoặc >90 khác 0. Tên được trim; nếu thiếu classification thì suy ra Interco nếu tên chứa `DOF` hoặc `Dan`, còn lại là third party. Chi tiết được sắp theo total giảm dần; report hiện hiển thị tổng theo bucket, không liệt kê toàn bộ khách hàng. |
| `AP` | Chi tiết hàng `2:88`: tên `A`, current `B`, 1–30 `D`, 31–60 `F`, 61–90 `H`, >90 `J`, tổng `L`, loại `M`. Tổng sheet: hàng `89` cho bucket/total; phân loại ở `L93:L95`. | Bỏ dòng thiếu tên và dòng tên có chữ `total`; chỉ giữ chi tiết nếu total hoặc current khác 0. Tên được trim, dòng sắp theo total giảm dần. Với dòng tổng âm, dùng `M` nếu có, nếu không ghi “Advance to supplier”; với tổng không âm thì gán “3rd Party”. Report trang 6 dùng các tổng bucket, không hiển thị danh sách chi tiết từng nhà cung cấp. |
| `Sales by cust` | Hàng `2` đến `max_row`: tên khách hàng `A`, sales `K`, cost `M`, gross profit `N`. | Bỏ dòng không có tên. Các dòng trùng tên sau trim được cộng sales/cost/GP. Gross margin khách hàng = tổng GP / tổng sales; nếu sales bằng 0 thì margin 0. Sắp khách hàng theo sales giảm dần. |
| `GP` | Hàng `2` đến `max_row`: item `E`, account `F`, debit `H`, credit `I`. | Bỏ dòng không có item. Chỉ account khớp chính xác `Sales` hoặc `Cost of Goods Sold` được cộng. Sales = credit − debit; COGS = debit − credit; GP = sales − COGS; GM = GP / sales (sales 0 thì 0). Sắp sản phẩm theo sales giảm dần. |
| `INV` | Hàng `2` đến `max_row`: SKU/tên `E`, asset value `I`; các subtotal chính tại `I378`, `I425`, `I462`, `I473`, `I506`, `I535`, `I536`, `I538`. Packaging cộng các hàng `I64`, `I99`, `I210`, `I217`, `I274`, `I303`, `I339`, `I353`, `I362`. | SKU detail chỉ giữ tên khớp regex `^[A-Za-z0-9_-]+\s*\(`. Giá trị phải là số, nếu không extraction báo lỗi. Tổng SKU detail phải khớp `I538` trong sai số 0,05 USD. Report không phân bổ chênh lệch giữa tổng SKU và `BS!K22` về từng SKU. |

### Workbook cash flow riêng — `FS_DOAU_Oct_26_CF_Indirect_Fixed_v2.xlsm`, sheet `CF`

Extractor dò tên dòng đã chuẩn hóa trong cột A (trim khoảng trắng, chuẩn hóa dash, không phân biệt hoa/thường), thay vì dựa vào số hàng cố định. Giá trị YTD đọc từ cột C. Tháng đọc từ các header kiểu ngày ở hàng 4, từ cột D trở đi, rồi đối chiếu với danh sách tháng lấy từ `007-DOAU data`.

| Trường JSON | Nhãn cần tìm ở cột A |
|---|---|
| Operating income/loss | `Net Operating Income (Loss)` |
| Depreciation | `Add: Depreciation & Amortisation` |
| Provision | `Add: Provision for Doubtful Debts` |
| Interest reclassified | `Add: Interest Expense (reclassified to CFF)` |
| Operating working capital | AR, Inventory, Prepaid Expenses, Undeposited Funds, Employee Advances, Accounts Payable, Credit Cards Payable, Accrued Expenses, Payroll Liabilities; theo các nhãn tăng/giảm trong sheet |
| CFO | `Net Cash from Operating Activities (CFO)` |
| Investing | CAPEX, Security Deposits và `Net Cash from Investing Activities (CFI)` |
| Financing | Interest Paid, Net Proceeds / (Repayment) of Borrowings, Capital / Equity Contributions và `Net Cash from Financing Activities (CFF)` |
| Cash reconciliation | Net increase/decrease in cash, opening balance, closing balance, và `Reconciliation Check (Closing – Opening – Net Change)` |

CFO = tổng các component vận hành trong extractor; CFI = CAPEX + biến động security deposits; CFF = interest paid + borrowings net + equity proceeds. Net cash change phải bằng CFO + CFI + CFF; closing cash phải bằng opening cash + net change. Các quan hệ này được kiểm tra cho YTD và từng tháng với tolerance 0,05 USD. Các dòng bắt buộc thiếu, header tháng thiếu hoặc giá trị không phải số đều làm extraction dừng.

## 4. Công thức dùng chung trong report

| Chỉ số hiển thị | Quy tắc |
|---|---|
| Chênh lệch tiền | Current − prior, trừ nơi ghi rõ variance được đọc sẵn từ workbook. |
| Phần trăm thay đổi | `(current − prior) / abs(prior)`; denominator 0/thiếu → `N/A`. |
| Biên lợi nhuận gộp | Gross profit / Revenue; YTD lấy gross profit và revenue tương ứng từ `PL YTD Aug 26`; tháng lấy từ `PL`. |
| Current ratio | Total current assets / Total current liabilities. |
| Debt / Equity | Total liabilities / Total equity. |
| Net working capital | Total current assets − Total current liabilities; chưa loại intercompany. |
| Tỷ trọng AR/AP bucket | Giá trị bucket / tổng AR hoặc AP tương ứng. |
| Tỷ trọng category/SKU/fixed asset | Giá trị category / mẫu số được ghi tại phần trang tương ứng. |
| Tỷ lệ payroll / revenue | Core payroll / revenue; core payroll loại processing fees. |
| Top customer share | Tổng positive sales của top N / tổng positive sales của tất cả khách hàng; số âm không làm giảm mẫu số. |
| Chênh lệch inventory | `BS!K22 − tổng SKU detail`; chỉ báo cáo chênh lệch, không phân bổ xuống SKU. |

## 5. Từng trang report: số nào xuất hiện và được tạo thế nào

### Trang 1 — Executive Summary

- **YTD revenue**: `PL YTD Aug 26!B14`; YoY trên KPI card dùng `E14`. Narrative chênh lệch tiền dùng Python `B14−C14`; phần trăm narrative dùng `percent_change(B14, C14)`. Đây là hai nguồn tính riêng, nên nếu E14 khác phép tính Python, card và narrative có thể khác.
- **YTD gross profit / margin**: `B53` và `B53/B14`; prior margin là `C53/C14`.
- **Revenue và gross profit của tháng report**: `PL!L14` và `PL!L45`; month gross margin = `L45/L14`.
- **MoM revenue %**: lấy hai tháng gần nhất từ `007-DOAU data` hàng 106, không lấy từ sheet `PL`; = thay đổi mới nhất / trị tuyệt đối revenue tháng trước.
- **Balance Sheet snapshot**: `BS!K45` total assets, `K10` cash, `K15` net AR, `K22` inventory, `K78` liabilities, `K84` equity.
- **Current ratio** = `K26/K69`; **Debt/Equity** = `K78/K84`; mẫu số 0 thì hiển thị `N/A`.
- **Operational EBITDA**: tháng từ `007-DOAU data!P246`; YTD là tổng `G246:P246`. **Adjusted EBITDA**: trực tiếp từ main workbook `CF!M23` (tháng) và `CF!C23` (YTD), không đồng nhất với operational EBITDA.
- **Monthly Sales Trend chart**: revenue từ hàng 106 cho các tháng G:P. Mỗi điểm ghi `$M` hai chữ số thập phân; phần MoM trong chart dùng `(current−prior)/prior`, nhưng prior bằng 0 thì chart ghi `0.0%` (khác bảng dùng `N/A`). Trục dọc chia theo 25%, 50%, 75%, 100% của `max(monthly revenue) × 1.15`.
- Các số `Page 1`…`Page 8` và “1 of 8” là nhãn trang tĩnh trong HTML, không lấy từ workbook.

### Trang 2 — Sales Report

- **YTD 2026/prior sales**: `PL YTD Aug 26!B12/C12`. Sales variance = B12−C12; % variance dùng `percent_change(B12,C12)`.
- **Custom Processing**: B9/C9; **Discounts Given**: B10/C10. Đây là số source workbook; trang không tự suy diễn nguyên nhân biến động.
- **10-Month Sales Trajectory**: doanh thu tháng lấy từ `007-DOAU data` hàng 106, G:P. MoM % dùng `percent_change`; tháng đầu tiên để dấu gạch ngang vì không có tháng trước.
- **YTD revenue narrative**: revenue B14/C14; chênh lệch và % do Python tính, không dùng D14/E14 ở câu narrative. Product sales change = B12−C12; custom processing change = B9−C9.
- **Top 3 customer concentration** và **Top 5 share**: từ `Sales by cust`, aggregate customer sales trước, sắp giảm dần. Tử số cộng sales dương của top 3/5; mẫu số cộng sales dương của toàn bộ khách hàng. Số âm/bằng 0 bị loại khỏi phép chia.
- **Customer Sales Share — Top 5 + Other**: 5 khách hàng có sales dương cao nhất là slice riêng; `Other` = tổng positive customer sales − tổng top 5. Pie percent dựa trên tổng các slice; chỉ slice ≥6% có nhãn phần trăm bên trong, mọi slice có phần trăm/giá trị trong legend.
- **YTD CFO trong review table**: YTD `net_cfo` từ workbook cash flow riêng, cột C của dòng CFO.
- Các mục “YTD Revenue”, “Customer Mix”, “Product Margin”, “Inventory” và “Cash Conversion” là lặp lại các chỉ số trên; các câu hỏi quản trị là lời bình rule-based, không phải chỉ tiêu mới.

### Trang 3 — Financial Performance (Sep/Oct và YTD)

- **MoM Sep/Oct**: các giá trị Sep/Oct đọc từ `007-DOAU data` cột O/P; rows 106 revenue, 159 COGS, 160 gross profit, 207 admin, 219 sales expenses, 221 total OpEx, 234 operating income, 246 EBITDA. Tiền chênh lệch luôn `Oct−Sep`.
- **Gross margin Sep/Oct**: row160 / row106 mỗi tháng. Cột chênh lệch hiển thị margin Oct − margin Sep theo **điểm phần trăm** (dù ký hiệu `%` được dùng trong HTML).
- Bảng **YTD P&L** dùng các row ở `PL YTD Aug 26`, cột B hiện tại và C prior. Variance cho từng dòng (sales, custom processing, discounts, labor, factory overhead, COGS, GP, admin, sales expenses, OpEx, ordinary income, interest, net income) là B−C; % thay đổi dùng công thức chung.
- **Ngoại lệ doanh thu**: dòng `TOTAL REVENUE` trong bảng YTD hiển thị trực tiếp D14/E14 từ workbook; narrative và trang 1 lại tính B14−C14 và percent-change bằng Python.
- **Gross margin YTD/prior**: B53/B14 và C53/C14. Ô variance là chênh lệch của hai tỷ lệ, đơn vị điểm phần trăm; phần % change của hàng gross margin được để dấu gạch ngang.
- **Net ordinary income** và **Net income**: variance tiền vẫn tính B−C; cột phần trăm trên template để dấu gạch ngang, không tính %.
- **Lời bình đối chiếu gross profit**: tổng gross profit tháng từ row160, cột G:P trừ YTD gross profit `PL YTD Aug 26!B53`. Hai nguồn được giữ nguyên; chênh lệch không bị ép về 0.

### Trang 4 — Commercial Analysis

- **Top Customer Analysis**: tối đa 10 khách hàng đã aggregate từ `Sales by cust` (sales K, GP N) và sắp sales giảm dần. GM = aggregate GP / aggregate sales; sales 0 thì GM 0. “Top 10 Total” cộng sales/GP của 10 dòng; tổng margin = tổng GP / tổng sales, không phải trung bình cộng margin từng khách hàng.
- **Highest customer sales**: khách hàng đầu tiên của danh sách đã sắp xếp; nếu danh sách trống thì thay bằng câu “No customer sales rows were available.”
- **Product Sales / Gross Profit charts**: lấy cùng 10 sản phẩm đầu trong danh sách `GP`, đã sắp sales giảm dần. Sales/COGS tính từ debit-credit theo account; GP = sales−COGS. Tên dài bị rút gọn trong chart. Chart GP dùng trục diverging quanh 0 để giữ dấu lãi/lỗ; chart Sales chỉ vẽ độ dài dương (âm bị chặn về zero).
- **Highest Gross Profit**: item có GP cao nhất trong các item có sales dương. **Lowest Recorded Margin**: GM thấp nhất trong cùng tập item sales dương. Nếu không có item phù hợp thì không in chỉ số.
- Tiền trong bảng khách hàng hiển thị số USD nguyên; giá trị chart dùng compact `$k`/`$M`, làm tròn theo quy tắc chung. Margin hiển thị 1 chữ số thập phân.

### Trang 5 — Inventory, P&L và Adjusted EBITDA

- **Inventory category**:
  - Raw Nuts = `INV!I462`; Raw Ingredients = `I425`; Raw Dried Fruits = `I378`.
  - Packaging = tổng các subtotal `I64`, `I99`, `I210`, `I217`, `I274`, `I303`, `I339`, `I353`, `I362`.
  - Total Raw & Packaging = `I473`; Finished Bulk = `I506`; Finished Pack = `I535`; Total Finished Assembly = `I536`; INV total = `I538`; BS inventory = `BS!K22`.
  - Mỗi `% Total` = số dòng / `INV!I538`; total được ghi tĩnh 100.0%; BS inventory không có tỷ trọng (dấu gạch ngang).
- **Inventory Share by SKU chart**: lấy SKU có asset value >0, xếp giảm dần, lấy top 5; “Other” gồm toàn bộ positive SKU còn lại. Số âm không vào pie; note báo số lượng SKU âm. Chênh lệch trong note = `BS!K22 − INV SKU detail total`. Nếu `Other` không dương thì không tạo slice Other.
- **Monthly P&L**: tháng report từ `PL!L`. Sales L12; custom processing L9; revenue L14; total COGS L44; labor L22; factory overhead L43; GP L45; admin L77; sales expense L87; operating income L89; interest L95; net income L98.
  - “Material & Production COGS” = total COGS − direct labor − factory overhead.
  - Mỗi `% Rev` = line amount / revenue L14; total revenue hiển thị 100%.
- **EBITDA Bridge**: operational EBITDA từ `007-DOAU data!P246` / tổng G246:P246; baseline và adjustment totals đọc từ main `CF!M/C`. Các adjustment line `CF!M/C` 19–20 và totals 21, adjusted EBITDA 23 là số workbook. Tháng report hiển thị consulting/bonus bằng dấu gạch ngang vì extractor gán hai giá trị bằng 0; YTD lấy hàng 17/18 trực tiếp. Không cộng lại bridge trong HTML để thay số adjusted EBITDA của workbook.

### Trang 6 — Balance Sheet và AR/AP aging

- **Balance Sheet**: toàn bộ snapshot lấy từ cột K sheet `BS`, chi tiết nguồn ở bảng sheet phía trên. Các dòng tổng nhóm trên report được tạo như sau:
  - Prepaid + undeposited = K25+K24.
  - Production & automation = K39+K32; building improvements & auto = K34+K33+K31.
  - Accumulated depreciation = K30+K28+K29; total fixed assets và total assets đọc trực tiếp K40/K45.
  - Accrued expenses & credit cards = K59+K57.
  - East West loans = K71+K72; Horseshoe & DDP = K76+K75; các nhóm long-term khác lấy cell tương ứng; tổng long-term liabilities/total liabilities đọc K77/K78.
  - Capital stock & members equity = K80+K81; retained earnings K82; net income K83; total equity K84; total liabilities & equity K85.
- **AR Aging**: current, 1–30, 31–60, 61–90, >90 và total lấy từ `AR!B60:E60`, `G60:H60`; mỗi bucket % = bucket / H60. Intercompany/third party lấy H62/H63, không có % trong report. Total AR phải reconcile về net AR `BS!K15`.
- **AP Aging**: bucket current/1–30/31–60/61–90/>90 và total lấy từ `AP!B89`, `D89`, `F89`, `H89`, `J89`, `L89`; phần trăm = bucket / L89. Advance supplier/intercompany/third-party lấy L93:L95; không có % trong report. Total AP phải reconcile với `BS!K51`. Số âm/advance không bị chuyển thành số dương.
- **Working capital** = `BS!K26 − BS!K69`; không loại intercompany.

### Trang 7 — CapEx và Cash Flow

- **Fixed asset values** lấy từ sheet `BS`, cột K. Production equipment K39; CIP K36; building improvements K34+K33; automation K32; auto K31; furniture/equipment K37; office/computer K35+K38.
- Mẫu số cột `% Gross` trong code là `BS!K40 − accumulated_depreciation`, trong đó accumulated depreciation = K30+K28+K29. “Total Gross Fixed Assets” dùng chính mẫu số này; “Accumulated Depreciation %” = accumulated depreciation / mẫu số; “NET PPE %” = K40 / mẫu số. Giữ nguyên đúng phép tính trong mã, không thay bằng một định nghĩa kế toán khác.
- **CapEx purchase** là dòng CAPEX được dò theo nhãn trong CF workbook riêng, không suy ra từ biến động số dư fixed asset trên BS.
- **Cash flow table** dùng giá trị YTD cột C theo label trong CF workbook riêng. Dòng tiền giữ nguyên dấu:
  - CFO details: operating income/loss, depreciation, interest reclassified, AR, inventory, AP và “Other Working Capital Movements”. Dòng “Other” = prepaid + undeposited + employee advances + credit cards + accrued expenses + payroll liabilities. Provision for doubtful debts được trích và dùng khi kiểm tra CFO nhưng không có dòng riêng trong bảng hiển thị.
  - CFO total lấy trực tiếp dòng net CFO trong workbook.
  - CFI hiển thị CAPEX, security deposits và CFI total.
  - CFF hiển thị borrowings, interest paid, equity proceeds và CFF total.
  - Net change, opening cash, closing cash và reconciliation check lấy theo label. Tính kiểm tra: CFO+CFI+CFF = net change; opening + net change = closing.
- **Cash-flow chart** dùng YTD CFO, CFI, CFF, net cash change; trục zero ở giữa, số âm vẽ trái/đỏ, số dương vẽ phải/xanh. Độ dài bar chuẩn hóa theo giá trị tuyệt đối lớn nhất; nhãn giá trị USD làm tròn nguyên và số âm đặt ngoặc.

### Trang 8 — Payroll Cost Analysis

- **Payroll tháng** từ `PL` cột L: direct labor L22, production payroll L35, admin payroll L72, processing fees L69. Direct labor base L21 và taxes L19 được trích nhưng không cộng riêng vào dòng “Direct Labor” vì L22 đã được dùng trực tiếp.
- **Payroll YTD/current và prior** từ `PL YTD Aug 26`: direct labor row23, production payroll row41, admin payroll row87, processing fee row83; B=current, C=prior.
- **Core Payroll** = direct labor + production payroll + admin payroll; không gồm payroll processing fees. Tháng = L22+L35+L72; YTD/prior = tương ứng B/C các row 23+41+87.
- **YoY Core Payroll Change** = current core − prior core; % = `percent_change(current, prior)`.
- **Core Payroll as % of Revenue**: tháng core payroll / `PL!L14`; current YTD / `PL YTD Aug 26!B14`; prior YTD / C14.
- **Payroll Composition chart** bao gồm cả processing fees, khác core payroll. Segment width = `max(0, category amount)` / tổng các `max(0, category amount)` của bốn nhóm direct labor, production, admin, processing fees. Giá trị âm không tạo segment, nhưng legend vẫn in giá trị gốc và `category amount / positive total`, nên phần trăm legend có thể âm. Nhãn trong bar chỉ hiện khi segment đủ rộng; nếu tổng các giá trị dương bằng 0, render chart báo lỗi.
- Workbook không có headcount, turnover, tenure, labor hours, output hoặc HR project status; report không ước lượng các số này. Tỷ lệ payroll/revenue không phải năng suất lao động.

## 6. Kiểm tra dữ liệu, giới hạn và chỗ cần đối chiếu thủ công

- Mỗi cash flow subtotal/reconciliation được kiểm tra cho YTD và từng tháng, tolerance 0,05 USD. Nếu thiếu row label, tháng hoặc số hợp lệ thì extraction dừng.
- Tổng doanh thu tháng từ `007-DOAU data` phải khớp revenue YTD `PL YTD Aug 26`; YTD gross profit phải bằng revenue trừ COGS; total assets phải bằng liabilities & equity; AR aging phải khớp BS net AR; AP aging phải khớp BS AP.
- INV SKU total phải khớp `INV!I538`. Sai khác giữa `I538` và `BS!K22` chỉ được tiết lộ, không chia bổ sung cho SKU.
- Monthly gross profit sum và YTD gross profit được lấy từ hai nguồn khác nhau; report nêu sai khác thay vì tự chỉnh.
- Có một khác biệt chủ ý/đáng lưu ý giữa report và source: trang 3 dùng `PL YTD Aug 26!D14/E14` cho revenue variance, trong khi trang 1, trang 2 và narrative dùng phép tính từ B14/C14. Kiểm tra hai cách nếu workbook cập nhật.
- Bảng CFO không hiển thị provision for doubtful debts thành một dòng riêng, dù extractor đọc dòng này và dùng nó khi reconcile CFO. Đối chiếu chi tiết với CF workbook khi cần cộng lại các thành phần hiển thị.
- Các số là management accounts chưa kiểm toán; kết quả và bình luận rule-based cần management review. Không dùng các kết luận này để tự suy diễn nguyên nhân.
- Gemini demo chỉ dùng fixture tổng hợp cố định. Không gửi workbook thật, JSON, tên khách hàng/SKU hay số report thật lên API bên ngoài.

## 7. Files liên quan

- [extract_data.py](./extract_data.py) — đọc workbook, tạo JSON và kiểm tra reconciliation.
- [report_metrics.py](./report_metrics.py) — công thức KPI dùng chung.
- [chart_rendering.py](./chart_rendering.py) — SVG chart và quy tắc label/format.
- [generate_report.py](./generate_report.py) — bảng, narrative và 8 trang HTML.
- [README.md](../../README.md) — sơ đồ repo và lệnh chạy nhanh.

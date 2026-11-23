Option Explicit

' =====================================================================
' Creates a "Summary" sheet that pulls Balance Sheet (BS) and
' Profit & Loss (PL) figures into one fixed report.
'
' Matching: SUMIFS theo (Level + Cleaned Name) cho BS
'           SUMIFS theo Cleaned SourceName cho PL
'
' Moi item co the co them phan tu thu 4 = SumSpec.
'   - SumSpec = ""    -> dung SUMIFS tu source
'   - SumSpec = "5-8" -> SUM cac item con (item number trong array)
'   - SumSpec = "8,12,21" -> SUM cac item roi rac
' Phan tu thu 5 (neu co) = SourceName override cho PL.
' =====================================================================
Sub CreateSummaryDOAU()
    Dim wb As Workbook
    Dim wsNew As Worksheet, wsBS As Worksheet, wsPL As Worksheet
    Dim i As Long
    Dim accountName As String, srcName As String
    Dim bsItems As Variant, plItems As Variant
    Dim lastRowBS As Long, lastRowPL As Long
    Dim inputMonth As String
    Dim colAfterBS As String, colAfterPL As String
    Dim helperLevelBS As Long, helperNameBS As Long
    Dim helperLevelPL As Long, helperNamePL As Long
    Dim outRow As Long
    Dim lvl As Long
    Dim hasVal As Boolean
    Dim sumSpec As String
    Dim srcOverride As String

    Set wb = ThisWorkbook

    inputMonth = InputBox("Enter the month this file covers (e.g. Jul 2026):", "Month Selection", "Jul 2026")
    If inputMonth = "" Then Exit Sub

    On Error Resume Next
    Set wsBS = wb.Sheets("BS")
    Set wsPL = wb.Sheets("PL")
    On Error GoTo 0
    If wsBS Is Nothing Then MsgBox "Sheet 'BS' not found.", vbCritical: Exit Sub
    If wsPL Is Nothing Then MsgBox "Sheet 'PL' not found.", vbCritical: Exit Sub

    colAfterBS = FindColumnByHeader(wsBS, 1, "After")
    colAfterPL = FindColumnByHeader(wsPL, 1, "After")
    If colAfterBS = "" Then MsgBox "Could not find the 'After' column in BS row 1.", vbCritical: Exit Sub
    If colAfterPL = "" Then MsgBox "Could not find the 'After' column in PL row 1.", vbCritical: Exit Sub

    lastRowBS = wsBS.Cells(wsBS.Rows.Count, "A").End(xlUp).Row
    lastRowPL = wsPL.Cells(wsPL.Rows.Count, "A").End(xlUp).Row
    Dim tmpLast As Long
    For i = 2 To 7
        tmpLast = wsBS.Cells(wsBS.Rows.Count, i).End(xlUp).Row
        If tmpLast > lastRowBS Then lastRowBS = tmpLast
    Next i
    For i = 2 To 7
        tmpLast = wsPL.Cells(wsPL.Rows.Count, i).End(xlUp).Row
        If tmpLast > lastRowPL Then lastRowPL = tmpLast
    Next i

    helperLevelBS = AddHelperColumns(wsBS, lastRowBS)
    helperLevelPL = AddHelperColumns(wsPL, lastRowPL)
    helperNameBS = helperLevelBS + 1
    helperNamePL = helperLevelPL + 1

    Dim colLevelBS As String, colNameBS As String
    Dim colLevelPL As String, colNamePL As String
    colLevelBS = Split(wsBS.Cells(1, helperLevelBS).Address, "$")(1)
    colNameBS = Split(wsBS.Cells(1, helperNameBS).Address, "$")(1)
    colLevelPL = Split(wsPL.Cells(1, helperLevelPL).Address, "$")(1)
    colNamePL = Split(wsPL.Cells(1, helperNamePL).Address, "$")(1)

    On Error Resume Next
    Application.DisplayAlerts = False
    wb.Sheets("Summary").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0

    Set wsNew = wb.Sheets.Add(After:=wb.Sheets(wb.Sheets.Count))
    wsNew.Name = "Summary"

    With wsNew
        .Range("A1").Value = "FINANCIAL STATEMENT SUMMARY"
        .Range("A2").Value = "Month:"
        .Range("B2").Value = inputMonth
        .Range("A1:B2").Font.Bold = True
        .Range("A4").Value = "BALANCE SHEET"
        .Range("A4").Font.Bold = True
    End With

    ' ===================================================================
    ' BALANCE SHEET template - 88 items
    ' Format: Array(Level, Name, HasValue, [SumSpec])
    '   SumSpec rong/khong co -> SUMIFS tu source
    ' ===================================================================
    ReDim bsItems(1 To 88)
    bsItems(1) = Array(1, "ASSETS", False)
    bsItems(2) = Array(2, "Current Assets", False)
    bsItems(3) = Array(3, "Checking/Savings", False)
    bsItems(4) = Array(4, "East West Bank -8078001859", True)
    bsItems(5) = Array(4, "EWB Payroll 2725", True)
    bsItems(6) = Array(4, "Fresno First Bank - 3743", True)
    bsItems(7) = Array(4, "Petty Cash", True)
    bsItems(8) = Array(3, "Total Checking/Savings", True, "4-7")
    bsItems(9) = Array(3, "Accounts Receivable", False)
    bsItems(10) = Array(4, "Accounts Receivable", True)
    bsItems(11) = Array(4, "Allowance for Doubtful Accounts", True)
    bsItems(12) = Array(3, "Total Accounts Receivable", True)          ' SUMIFS
    bsItems(13) = Array(3, "Other Current Assets", False)
    bsItems(14) = Array(4, "Inventory Asset", False)
    bsItems(15) = Array(5, "Inventory Clearing", True)
    bsItems(16) = Array(5, "Work-in-Process", True)
    bsItems(17) = Array(5, "Inventory Asset", True)
    bsItems(18) = Array(4, "Total Inventory Asset", True)              ' SUMIFS
    bsItems(19) = Array(4, "Undeposited Funds", True)
    bsItems(20) = Array(4, "Pre-paid", True)
    bsItems(21) = Array(3, "Total Other Current Assets", True, "18-20")
    bsItems(22) = Array(2, "Total Current Assets", True, "8,12,21")
    bsItems(23) = Array(2, "Fixed Assets", False)
    bsItems(24) = Array(3, "Accum. Depreciation - Equipment", True)
    bsItems(25) = Array(3, "Accum. Depreciation - Furniture", True)
    bsItems(26) = Array(3, "Accum. Depreciations", True)
    bsItems(27) = Array(3, "Auto", True)
    bsItems(28) = Array(3, "Automation", True)
    bsItems(29) = Array(3, "Building Improvements - 12368", True)
    bsItems(30) = Array(3, "Building Improvements - 2628", True)
    bsItems(31) = Array(3, "Computer", True)
    bsItems(32) = Array(3, "Construction in Progress", True)
    bsItems(33) = Array(3, "Furniture and Equipment", True)
    bsItems(34) = Array(3, "Office Equipment", True)
    bsItems(35) = Array(3, "Production Equipment", True)
    bsItems(36) = Array(2, "Total Fixed Assets", True, "24-35")
    bsItems(37) = Array(2, "Other Assets", False)
    bsItems(38) = Array(3, "Deposit", True)
    bsItems(39) = Array(3, "Employee Advance", True)
    bsItems(40) = Array(2, "Total Other Assets", True, "38-39")
    bsItems(41) = Array(1, "TOTAL ASSETS", True, "22,36,40")
    bsItems(42) = Array(1, "LIABILITIES & EQUITY", False)
    bsItems(43) = Array(2, "Liabilities", False)
    bsItems(44) = Array(3, "Current Liabilities", False)
    bsItems(45) = Array(4, "Accounts Payable", True)
    bsItems(46) = Array(4, "Credit Cards", False)
    bsItems(47) = Array(5, "Home Depot", True)
    bsItems(48) = Array(5, "Macy's", True)
    bsItems(49) = Array(5, "Visa - 6188", True)
    bsItems(50) = Array(5, "VISA - 3240", True)
    bsItems(51) = Array(4, "Total Credit Cards", True, "47-50")
    bsItems(52) = Array(4, "Other Current Liabilities", False)
    bsItems(53) = Array(5, "Accrued Expenses", True)
    bsItems(54) = Array(5, "Installment Loan", False)
    bsItems(55) = Array(6, "Electric Forklift 7FBEU20", True)
    bsItems(56) = Array(6, "Loan East West Bank -8078001859", True)
    bsItems(57) = Array(6, "Toyota", True)
    bsItems(58) = Array(5, "Total Installment Loan", True, "55-57")
    bsItems(59) = Array(5, "Payroll Liabilities", False)
    bsItems(60) = Array(6, "Payroll Liabilities - Other", True)
    bsItems(61) = Array(6, "Payroll Accrual", True)
    bsItems(62) = Array(5, "Total Payroll Liabilities", True, "60-61")
    bsItems(63) = Array(4, "Total Other Current Liabilities", True, "53,58,62")
    bsItems(64) = Array(3, "Total Current Liabilities", True, "45,51,63")
    bsItems(65) = Array(3, "Long Term Liabilities", False)
    bsItems(66) = Array(4, "Advance from Danway Holdings Lt", True)
    bsItems(67) = Array(4, "East West Loan # 332001332", True)
    bsItems(68) = Array(4, "East West Loan # 355001220", True)
    bsItems(69) = Array(4, "Loan from Shareholders", True)
    bsItems(70) = Array(4, "Loan Payable - Alex Do", True)
    bsItems(71) = Array(4, "Loan Payable - DDFH", True)
    bsItems(72) = Array(4, "Loan Payable - Danways", True)
    bsItems(73) = Array(4, "Loan Payable - DDF Hongkong", True)
    bsItems(74) = Array(4, "Loan Payable - DDP, LLC", True)
    bsItems(75) = Array(4, "Loan Payable - Horseshoe", True)
    bsItems(76) = Array(4, "Loan Payable- Dan D Pistachio", True)
    bsItems(77) = Array(4, "Loan Payable - Dan-D-Foods- Ltd", True)
    bsItems(78) = Array(4, "Loan Payable - Danway", True)
    bsItems(79) = Array(4, "Loan Payable- Dan D Pistachio", True)
    bsItems(80) = Array(3, "Total Long Term Liabilities", True, "66-79")
    bsItems(81) = Array(2, "Total Liabilities", True, "64,80")
    bsItems(82) = Array(2, "Equity", False)
    bsItems(83) = Array(3, "Capital Stock", True)
    bsItems(84) = Array(3, "Members Equity", True)
    bsItems(85) = Array(3, "Retained Earnings", True)
    bsItems(86) = Array(3, "Net Income", True)
    bsItems(87) = Array(2, "Total Equity", True, "83-86")
    bsItems(88) = Array(1, "TOTAL LIABILITIES & EQUITY", True, "81,87")

    ' ===================================================================
    ' PROFIT & LOSS template - 146 items
    ' Format: Array(Level, DisplayName, HasValue, [SumSpec], [SourceName])
    ' ===================================================================
    ReDim plItems(1 To 146)

    plItems(1) = Array(1, "PROFIT AND LOSS", False)
    plItems(2) = Array(1, "Income", False)
    plItems(3) = Array(2, "REVENUE", False)
    plItems(4) = Array(3, "Custom Processing", False)
    plItems(5) = Array(4, "Mixing fee", True)
    plItems(6) = Array(4, "Packing Fees", True)
    plItems(7) = Array(4, "Roasting Fees", True)
    plItems(8) = Array(4, "Custom Processing - Other", True)
    plItems(9) = Array(3, "Total Custom Processing", True, "5-8")
    plItems(10) = Array(3, "Discounts Allowed", True)
    plItems(11) = Array(3, "Other Revenue", True)
    plItems(12) = Array(3, "Returns and Allowances", True)
    plItems(13) = Array(3, "Sales", True)
    plItems(14) = Array(3, "Store Sales", True)
    plItems(15) = Array(2, "Total REVENUE", True, "9-14")
    plItems(16) = Array(1, "Total Income", True, "15")

    plItems(17) = Array(1, "Cost of Goods Sold", False)
    plItems(18) = Array(2, "Cost of Goods Sold", False)
    plItems(19) = Array(3, "Discounts on Purchases", True)
    plItems(20) = Array(3, "Inventory Write Off", True)
    plItems(21) = Array(3, "Physical Inventory Variance", True)
    plItems(22) = Array(3, "Cost of Goods Sold - Other", True)
    plItems(23) = Array(2, "Total Cost of Goods Sold", True, "19-22")
    plItems(24) = Array(2, "Direct Labor", False)
    plItems(25) = Array(3, "Applied DL", True)
    plItems(26) = Array(3, "Bonus", True)
    plItems(27) = Array(3, "Payroll Taxes", True)
    plItems(28) = Array(3, "Temporary Labor", True)
    plItems(29) = Array(3, "Direct Labor ", True)
    plItems(30) = Array(2, "Total Direct Labor", True)                  ' SUMIFS (source)

    plItems(31) = Array(2, "FACTORY OVERHEAD", False)
    plItems(32) = Array(3, "Applied OH", True)
    plItems(33) = Array(3, "Bonus", True)
    plItems(34) = Array(3, "Building Repairs", True)
    plItems(35) = Array(3, "Calibration & Certification", True)
    plItems(36) = Array(3, "Cleaning Services", True)
    plItems(37) = Array(3, "Consulting", True)
    plItems(38) = Array(3, "Depreciation Expense", True)
    plItems(39) = Array(3, "Equipment Rental", True)
    plItems(40) = Array(3, "Equipment Repairs", True)
    plItems(41) = Array(3, "Fire Protection", True)
    plItems(42) = Array(3, "Fumigation", True)
    plItems(43) = Array(3, "Janitorial Supplies", True)
    plItems(44) = Array(3, "Lab Fees", True)
    plItems(45) = Array(3, "Lease Payment", True)
    plItems(46) = Array(3, "Licenses & Permits", True)
    plItems(47) = Array(3, "Pallets", True)
    plItems(48) = Array(3, "Payroll Expense", False)
    plItems(49) = Array(4, "Payroll Taxes Production", True)
    plItems(50) = Array(4, "Payroll Expense - Other", True)
    plItems(51) = Array(4, "Salaries", True)
    plItems(52) = Array(3, "Total Payroll Expense", True, "49-51")
    plItems(53) = Array(3, "Pest Control", True)
    plItems(54) = Array(3, "Plate Charge", True)
    plItems(55) = Array(3, "Production Supplies", True)
    plItems(56) = Array(3, "Rent Expense", True)
    plItems(57) = Array(3, "Repairs and Maintenance", True)
    plItems(58) = Array(3, "Sales Tax/Use Tax", True)
    plItems(59) = Array(3, "Tools & Instruments", True)
    plItems(60) = Array(3, "Training and Seminars", True)
    plItems(61) = Array(3, "Uniforms", True)
    plItems(62) = Array(3, "Utilities", True)
    plItems(63) = Array(3, "Validation Expenses", True)
    plItems(64) = Array(3, "Workers Comp", True)
    plItems(65) = Array(3, "FACTORY OVERHEAD - Other", True)
    plItems(66) = Array(3, "Freight and Shipping Costs", True)
    plItems(67) = Array(2, "Total FACTORY OVERHEAD", True)              ' SUMIFS (source)

    plItems(68) = Array(1, "Total COGS", True)                          ' SUMIFS (source)
    plItems(69) = Array(1, "Gross Profit", True)                        ' SUMIFS (source)

    plItems(70) = Array(1, "Expense", False)
    plItems(71) = Array(2, "ADMINISTRATION EXPENSES", False)
    plItems(72) = Array(3, "Accounting Fees", True)

    plItems(73) = Array(3, "Automobile Expense", False)
    plItems(74) = Array(4, "Auto Repairs", True)
    plItems(75) = Array(4, "Gasoline, parking & mileage", True)
    plItems(76) = Array(4, "Registration", True)
    plItems(77) = Array(4, "Automobile Expense - Other", True)
    plItems(78) = Array(3, "Total Automobile Expense", True, "74-77")

    plItems(79) = Array(3, "Bad Debts Expense", True)
    plItems(80) = Array(3, "Bank Service Charges", True)
    plItems(81) = Array(3, "Bank Document Fees", True)
    plItems(82) = Array(3, "Business Tax", True)
    plItems(83) = Array(3, "Computer and Internet Expenses", True)
    plItems(84) = Array(3, "Credit Card Service Charge", True)
    plItems(85) = Array(3, "Donation", True)
    plItems(86) = Array(3, "Dues and Subscriptions", True)

    plItems(87) = Array(3, "Insurance Expense", False)
    plItems(88) = Array(4, "General Liability", True)
    plItems(89) = Array(4, "Property", True)
    plItems(90) = Array(4, "Insurance Expense - Other", True)
    plItems(91) = Array(4, "Vehicle Insurance", True)
    plItems(92) = Array(3, "Total Insurance Expense", True, "88-91")

    plItems(93) = Array(3, "Legal", True)
    plItems(94) = Array(3, "Licenses & Permits", True)
    plItems(95) = Array(3, "Loan Processing Fees", True)
    plItems(96) = Array(3, "Meals and Entertainment", True)
    plItems(97) = Array(3, "Office Expenses", True)

    plItems(98) = Array(3, "Payroll Expenses", False)
    plItems(99) = Array(4, "Bonus", True)
    plItems(100) = Array(4, "Payroll Processing Fees", True)
    plItems(101) = Array(4, "Payroll Taxes - Admin", True)
    plItems(102) = Array(4, "Salaries - Admin", True)
    plItems(103) = Array(4, "Medical Expenses", True)
    plItems(104) = Array(4, "Employee Benefits", True)
    plItems(105) = Array(4, "Payroll Expenses - Other", True)
    plItems(106) = Array(3, "Total Payroll Expenses", True, "99-105")

    plItems(107) = Array(3, "Penalty & fine", True)
    plItems(108) = Array(3, "Property Taxes Paid", True)
    plItems(109) = Array(3, "Printing & Reproduction", True)
    plItems(110) = Array(3, "Security and Alarm System", True)
    plItems(111) = Array(3, "Suspense", True)
    plItems(112) = Array(3, "Storage Expense", True)
    plItems(113) = Array(3, "State Tax", True)
    plItems(114) = Array(3, "ADMINISTRATION EXPENSES - Other", True)
    plItems(115) = Array(3, "Telephone Expense", True)
    ' Total ADMIN = leaves + sub-totals (khong double-count cac con cua subtotal)
    plItems(116) = Array(2, "Total ADMINISTRATION EXPENSES", True, _
        "72,78,79,80,81,82,83,84,85,86,92,93,94,95,96,97,106,107,108,109,110,111,112,113,114,115")

    plItems(117) = Array(2, "SALES EXPENSES", False)
    plItems(118) = Array(3, "Commissions", True)
    plItems(119) = Array(3, "Domestic Shipping & Handling", True)
    plItems(120) = Array(3, "EDI Fees", True)
    plItems(121) = Array(3, "Export Shipping & Handling", True)
    plItems(122) = Array(3, "Postage and Delivery Expense", True)
    plItems(123) = Array(3, "Service Fee", True)
    plItems(124) = Array(3, "Shipping Supplies", True)
    plItems(125) = Array(3, "Trade Show/Promotion", True)
    plItems(126) = Array(3, "SALES EXPENSES - Other", True)
    plItems(127) = Array(3, "Travel Expense", True)
    plItems(128) = Array(2, "Total SALES EXPENSES", True, "118-127")

    plItems(129) = Array(2, "Taxes", True)
    plItems(130) = Array(1, "Total Expense", True, "116,128,129")
    plItems(131) = Array(1, "Net Ordinary Income", True)                ' SUMIFS (source)

    plItems(132) = Array(1, "Other Income/Expense", False)
    plItems(133) = Array(2, "Other Income", False)
    plItems(134) = Array(3, "Foreign Currency Gain/Loss", True)
    plItems(135) = Array(3, "Other Income", True)
    plItems(136) = Array(2, "Total Other Income", True, "134-135")

    plItems(137) = Array(2, "Other Expense", False)
    plItems(138) = Array(3, "Interest Expense", True)
    plItems(139) = Array(3, "Loss(Gain) on disposal of Asset", True)
    plItems(140) = Array(3, "Other Expense (adjustment)", True)
    plItems(141) = Array(2, "Total Other Expense", True, "138-140")

    plItems(142) = Array(1, "Net Other Income", True)                   ' SUMIFS (source)
    plItems(143) = Array(1, "Net operating Income", True)               ' SUMIFS (source)
    plItems(144) = Array(1, "", False)
    plItems(145) = Array(1, "Commission/Service Fee - Vietnam", True)   ' SUMIFS (source)
    plItems(146) = Array(1, "Adjusted Net Income", True)                ' SUMIFS (source)

    ' ===================================================================
    ' Write Balance Sheet section
    ' ===================================================================
    Dim bsRows() As Long
    ReDim bsRows(1 To UBound(bsItems))

    outRow = 5
    For i = LBound(bsItems) To UBound(bsItems)
        lvl = bsItems(i)(0)
        accountName = bsItems(i)(1)
        hasVal = bsItems(i)(2)
        sumSpec = ""
        If UBound(bsItems(i)) >= 3 Then sumSpec = CStr(bsItems(i)(3))

        wsNew.Cells(outRow, "B").Value = accountName
        wsNew.Cells(outRow, "B").IndentLevel = lvl - 1
        If lvl <= 2 Then wsNew.Cells(outRow, "B").Font.Bold = True

        bsRows(i) = outRow

        If hasVal Then
            If Len(sumSpec) > 0 Then
                wsNew.Cells(outRow, "D").Formula = "=" & BuildSumFormula(sumSpec, bsRows, "D")
            Else
                wsNew.Cells(outRow, "D").Formula = _
                    "=SUMIFS(BS!$" & colAfterBS & "$3:$" & colAfterBS & "$" & lastRowBS & "," & _
                    "BS!$" & colLevelBS & "$3:$" & colLevelBS & "$" & lastRowBS & "," & lvl & "," & _
                    "BS!$" & colNameBS & "$3:$" & colNameBS & "$" & lastRowBS & "," & _
                    Chr(34) & CleanName(accountName) & Chr(34) & ")"
            End If
        End If
        outRow = outRow + 1
    Next i

    outRow = outRow + 1
    wsNew.Cells(outRow, "A").Value = "PROFIT AND LOSS"
    wsNew.Cells(outRow, "A").Font.Bold = True
    outRow = outRow + 1

    ' ===================================================================
    ' Write Profit & Loss section
    ' ===================================================================
    Dim plRows() As Long
    ReDim plRows(1 To UBound(plItems))

    For i = LBound(plItems) To UBound(plItems)
        lvl = plItems(i)(0)
        accountName = plItems(i)(1)
        hasVal = plItems(i)(2)
        sumSpec = ""
        srcOverride = ""
        If UBound(plItems(i)) >= 3 Then sumSpec = CStr(plItems(i)(3))
        If UBound(plItems(i)) >= 4 Then srcOverride = CStr(plItems(i)(4))
        If Len(srcOverride) = 0 Then srcOverride = accountName

        wsNew.Cells(outRow, "B").Value = accountName
        wsNew.Cells(outRow, "B").IndentLevel = lvl - 1
        If lvl <= 2 Then wsNew.Cells(outRow, "B").Font.Bold = True

        plRows(i) = outRow

        If hasVal Then
            If Len(sumSpec) > 0 Then
                wsNew.Cells(outRow, "D").Formula = "=" & BuildSumFormula(sumSpec, plRows, "D")
            Else
                wsNew.Cells(outRow, "D").Formula = _
                    "=SUMIFS(PL!$" & colAfterPL & "$3:$" & colAfterPL & "$" & lastRowPL & "," & _
                    "PL!$" & colNamePL & "$3:$" & colNamePL & "$" & lastRowPL & "," & _
                    Chr(34) & CleanName(srcOverride) & Chr(34) & ")"
            End If
        End If
        outRow = outRow + 1
    Next i

    ' --- Formatting ---
    With wsNew
        .Columns("A:D").AutoFit
        .Columns("D").NumberFormat = "#,##0.00;(#,##0.00)"
    End With

    MsgBox "Sheet 'Summary' created successfully for " & inputMonth & "!" & vbCrLf & _
           "Helper columns (Level / Name Cleaned) were added to BS and PL.", vbInformation
End Sub

' =====================================================================
' Helper: build SUM formula from a SumSpec string like "5-8" or "8,12,21".
' itemRows() is 1-based array mapping item index -> output row on sheet.
' colLetter is "D".
' =====================================================================
Private Function BuildSumFormula(spec As String, ByRef itemRows() As Long, _
                                 colLetter As String) As String
    Dim parts() As String, p As Variant, s As String
    Dim lo As Long, hi As Long, n As Long
    Dim sb As String

    parts = Split(spec, ",")
    sb = "SUM("
    For Each p In parts
        s = Trim(CStr(p))
        If Len(s) = 0 Then GoTo NextPart
        If InStr(s, "-") > 0 Then
            lo = CLng(Split(s, "-")(0))
            hi = CLng(Split(s, "-")(1))
            sb = sb & colLetter & itemRows(lo) & ":" & colLetter & itemRows(hi) & ","
        Else
            n = CLng(s)
            sb = sb & colLetter & itemRows(n) & ","
        End If
NextPart:
    Next p
    If Right(sb, 1) = "," Then sb = Left(sb, Len(sb) - 1)
    sb = sb & ")"
    BuildSumFormula = sb
End Function

' =====================================================================
' Helper: finds the column letter in a given row whose value contains
' the given header text (case-insensitive). Returns "" if not found.
' =====================================================================
Function FindColumnByHeader(ws As Worksheet, headerRow As Long, headerText As String) As String
    Dim c As Range
    Dim lastCol As Long
    lastCol = ws.Cells(headerRow, ws.Columns.Count).End(xlToLeft).Column
    If lastCol < 20 Then lastCol = 20
    For Each c In ws.Range(ws.Cells(headerRow, 1), ws.Cells(headerRow, lastCol))
        If InStr(1, CStr(c.Value), headerText, vbTextCompare) > 0 Then
            FindColumnByHeader = Split(c.Address, "$")(1)
            Exit Function
        End If
    Next c
    FindColumnByHeader = ""
End Function

' =====================================================================
' Helper: adds "Level" and "Name Cleaned" helper columns to a QuickBooks
' -style indented sheet. Returns the column number of "Level".
' =====================================================================
Function AddHelperColumns(ws As Worksheet, lastRow As Long) As Long
    Dim colLevel As Long, colName As Long
    Dim r As Long
    Dim q As String
    q = Chr(34) & Chr(34)

    If ws.Cells(1, "P").Value = "Level" And ws.Cells(1, "Q").Value = "Name Cleaned" Then
        AddHelperColumns = ws.Range("P1").Column
        Exit Function
    End If

    colLevel = 16
    colName = 17

    ws.Cells(1, colLevel).Value = "Level"
    ws.Cells(1, colName).Value = "Name Cleaned"
    ws.Range(ws.Cells(1, colLevel), ws.Cells(1, colName)).Font.Bold = True

    Dim formulaLevel As String, formulaName As String
    For r = 3 To lastRow
        formulaLevel = "=IF(LEN(A" & r & ")>0,1,IF(LEN(B" & r & ")>0,2,IF(LEN(C" & r & ")>0,3," & _
                       "IF(LEN(D" & r & ")>0,4,IF(LEN(E" & r & ")>0,5,IF(LEN(F" & r & ")>0,6," & _
                       "IF(LEN(G" & r & ")>0,7," & q & ")))))))"
        ws.Cells(r, colLevel).Formula = formulaLevel

        formulaName = "=TRIM(PROPER(CLEAN(IF(LEN(A" & r & ")>0,A" & r & ",IF(LEN(B" & r & ")>0,B" & r & _
                      ",IF(LEN(C" & r & ")>0,C" & r & ",IF(LEN(D" & r & ")>0,D" & r & _
                      ",IF(LEN(E" & r & ")>0,E" & r & ",IF(LEN(F" & r & ")>0,F" & r & ",G" & r & ")))))))))"
        ws.Cells(r, colName).Formula = formulaName
    Next r

    AddHelperColumns = colLevel
End Function

' =====================================================================
' Helper: replicate Excel's TRIM(PROPER(CLEAN(x))) in VBA
' =====================================================================
Function CleanName(s As String) As String
    Dim result As String
    result = Application.WorksheetFunction.Clean(s)
    result = Application.WorksheetFunction.Proper(result)
    result = Application.WorksheetFunction.Trim(result)
    result = Replace(result, Chr(34), Chr(34) & Chr(34))
    CleanName = result
End Function
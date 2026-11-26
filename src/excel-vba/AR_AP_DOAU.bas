' Note DOAU phải xóa cột đầu set lại là Name 
Sub DOAU_merge()
    Dim wsAR As Worksheet, wsAP As Worksheet, wsResult As Worksheet
    Dim lastRowAR As Long, lastRowAP As Long
    Dim i As Long, destRow As Long

    ' ====== CẤU TRÚC DỮ LIỆU SHEET DOAU ======
    ' Sheet AR và AP đều có cùng cấu trúc:
    '   Cột A (1) = Name
    '   Cột B (2) = Ending Balance
    ' Header nằm ở dòng 1
    ' ==========================================
    Const HEADER_ROW As Long = 1
    Const COL_NAME As Long = 1       ' Cột A = Name
    Const COL_BALANCE As Long = 2    ' Cột B = Ending Balance

    On Error Resume Next
    Set wsAR = ThisWorkbook.Sheets("AR")
    Set wsAP = ThisWorkbook.Sheets("AP")
    On Error GoTo 0

    If wsAR Is Nothing Then
        MsgBox "Không tìm thấy sheet 'AR'. Vui lòng kiểm tra lại tên."
        Exit Sub
    End If
    If wsAP Is Nothing Then
        MsgBox "Không tìm thấy sheet 'AP'. Vui lòng kiểm tra lại tên."
        Exit Sub
    End If

    ' --- Xóa sheet Merged_AR_AP nếu đã tồn tại ---
    On Error Resume Next
    Application.DisplayAlerts = False
    ThisWorkbook.Sheets("Merged_AR_AP").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0

    ' --- Tạo sheet kết quả ---
    Set wsResult = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
    wsResult.Name = "Merged_AR_AP"

    ' --- Ghi tiêu đề ---
    With wsResult
        .Cells(1, 1).Value = "Kind"
        .Cells(1, 2).Value = "Entity"
        .Cells(1, 3).Value = "Name"
        .Cells(1, 4).Value = "Ending Balance"
        .Range("A1:D1").Font.Bold = True
    End With

    destRow = 2

    ' --- Lấy dữ liệu từ sheet AR ---
    lastRowAR = wsAR.Cells(wsAR.Rows.Count, COL_NAME).End(xlUp).Row
    For i = HEADER_ROW + 1 To lastRowAR
        If Trim(wsAR.Cells(i, COL_NAME).Value) <> "" Then
            wsResult.Cells(destRow, 1).Value = "AR"                         ' Kind
            wsResult.Cells(destRow, 2).Value = "DOAU"                       ' Entity
            wsResult.Cells(destRow, 3).Value = wsAR.Cells(i, COL_NAME).Value    ' Name
            wsResult.Cells(destRow, 4).Value = wsAR.Cells(i, COL_BALANCE).Value ' Ending Balance
            destRow = destRow + 1
        End If
    Next i

    ' --- Lấy dữ liệu từ sheet AP ---
    lastRowAP = wsAP.Cells(wsAP.Rows.Count, COL_NAME).End(xlUp).Row
    For i = HEADER_ROW + 1 To lastRowAP
        If Trim(wsAP.Cells(i, COL_NAME).Value) <> "" Then
            wsResult.Cells(destRow, 1).Value = "AP"                         ' Kind
            wsResult.Cells(destRow, 2).Value = "DOAU"                       ' Entity
            wsResult.Cells(destRow, 3).Value = wsAP.Cells(i, COL_NAME).Value    ' Name
            wsResult.Cells(destRow, 4).Value = wsAP.Cells(i, COL_BALANCE).Value ' Ending Balance
            destRow = destRow + 1
        End If
    Next i

    ' --- Tự động co giãn cột ---
    wsResult.Columns("A:D").AutoFit

    MsgBox "Đã gộp xong! Kết quả nằm trong sheet '" & wsResult.Name & "'."
End Sub
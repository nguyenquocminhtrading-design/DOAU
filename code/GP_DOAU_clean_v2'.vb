' nhớ xóa cột đầu cho cột name là cột A'

Sub Clean_GP_DOAU()
    Dim ws As Worksheet
    Dim oldCalc As XlCalculation, oldEvents As Boolean, oldScreen As Boolean
    Dim lastRow As Long, lastCol As Long
    Dim i As Long, j As Long
    Dim customerName As String
    Dim cellVal As Variant
    Dim val As String
    Dim data As Variant, tempData As Variant, finalData As Variant
    Dim keepRow() As Boolean, keepCol() As Boolean, hasHeader() As Boolean
    Dim isTotalRow As Boolean, isBlankRow As Boolean, colIsBlank As Boolean
    Dim blankCount As Long
    Dim rowCount As Long, colCount As Long
    Dim r As Long, outCol As Long

    Set ws = ActiveSheet

    oldCalc = Application.Calculation
    oldEvents = Application.EnableEvents
    oldScreen = Application.ScreenUpdating
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    Application.ScreenUpdating = False
    On Error GoTo ErrorHandler

    ' --- Lấy kích thước ---
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    If lastRow < 1 Then GoTo Finish
    lastCol = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
    If lastCol < 1 Then GoTo Finish

    data = ws.Range(ws.Cells(1, 1), ws.Cells(lastRow, lastCol)).Value

    ' === ĐIỂM SỬA: đánh dấu cột có header ở row 1 ===
    ReDim hasHeader(1 To UBound(data, 2))
    For j = 1 To UBound(data, 2)
        cellVal = data(1, j)
        If Not IsError(cellVal) Then
            If Trim(CStr(cellVal)) <> "" Then hasHeader(j) = True
        End If
    Next j

    ' --- 1. Điền tên khách hàng vào cột A ---
    customerName = ""
    For i = 1 To UBound(data, 1)
        cellVal = data(i, 1)
        If Not IsError(cellVal) Then
            val = Trim(CStr(cellVal))
            If val <> "" And InStr(1, val, "Total", vbTextCompare) = 0 Then
                customerName = val
            ElseIf val = "" And customerName <> "" Then
                data(i, 1) = customerName
            End If
        End If
    Next i

    ' --- 2. Đánh dấu dòng cần giữ ---
    ReDim keepRow(1 To UBound(data, 1))
    rowCount = 0
    For i = 1 To UBound(data, 1)
        isTotalRow = False
        isBlankRow = True
        blankCount = 0
        For j = 1 To UBound(data, 2)
            cellVal = data(i, j)
            If Not IsError(cellVal) Then
                val = Trim(CStr(cellVal))
                If val <> "" Then
                    isBlankRow = False
                    If InStr(1, val, "Total", vbTextCompare) > 0 Then
                        isTotalRow = True
                        Exit For
                    End If
                Else
                    ' === CHỈ đếm blank ở cột có header ===
                    If hasHeader(j) Then blankCount = blankCount + 1
                End If
            End If
        Next j
        If Not (isTotalRow Or isBlankRow Or (blankCount > 3)) Then
            keepRow(i) = True
            rowCount = rowCount + 1
        End If
    Next i

    If rowCount = 0 Then
        MsgBox "Khong con dong nao sau khi loc (tat ca deu bi coi la Total/trong/qua nhieu o trong)." & vbCrLf & _
               "Khong xoa gi ca de tranh mat du lieu.", vbExclamation
        GoTo Finish
    End If

    ' --- 3. Gom dòng cần giữ ---
    ReDim tempData(1 To rowCount, 1 To UBound(data, 2))
    r = 0
    For i = 1 To UBound(data, 1)
        If keepRow(i) Then
            r = r + 1
            For j = 1 To UBound(data, 2)
                tempData(r, j) = data(i, j)
            Next j
        End If
    Next i
    Erase data, keepRow

    ' --- 4. Đánh dấu cột cần giữ (không hoàn toàn trống) ---
    ReDim keepCol(1 To UBound(tempData, 2))
    colCount = 0
    For j = 1 To UBound(tempData, 2)
        colIsBlank = True
        For i = 1 To rowCount
            If Not IsEmpty(tempData(i, j)) Then
                colIsBlank = False
                Exit For
            End If
        Next i
        If Not colIsBlank Then
            keepCol(j) = True
            colCount = colCount + 1
        End If
    Next j

    If colCount = 0 Then GoTo Finish

    ' --- 5. Dựng mảng cuối + Trim ---
    ReDim finalData(1 To rowCount, 1 To colCount)
    outCol = 0
    For j = 1 To UBound(tempData, 2)
        If keepCol(j) Then
            outCol = outCol + 1
            For i = 1 To rowCount
                cellVal = tempData(i, j)
                If IsEmpty(cellVal) Then
                    ' để trống
                ElseIf IsError(cellVal) Then
                    finalData(i, outCol) = cellVal
                ElseIf IsNumeric(cellVal) Then
                    finalData(i, outCol) = cellVal
                Else
                    finalData(i, outCol) = Trim(CStr(cellVal))
                End If
            Next i
        End If
    Next j
    Erase tempData, keepCol, hasHeader

    ' --- 6. Xóa vùng cũ và ghi mảng mới ---
    ws.Range(ws.Cells(1, 1), ws.Cells(lastRow, lastCol)).ClearContents
    ws.Range(ws.Cells(1, 1), ws.Cells(rowCount, colCount)).Value = finalData

    ws.UsedRange.Columns.AutoFit

Finish:
    Application.Calculation = oldCalc
    Application.EnableEvents = oldEvents
    Application.ScreenUpdating = oldScreen
    MsgBox "Done! Giu lai " & rowCount & " dong / " & colCount & " cot (truoc: " & lastRow & "x" & lastCol & ")."
    Exit Sub
ErrorHandler:
    Application.Calculation = oldCalc
    Application.EnableEvents = oldEvents
    Application.ScreenUpdating = oldScreen
    MsgBox "Error: " & Err.Description, vbCritical
End Sub
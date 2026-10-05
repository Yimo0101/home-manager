' Home Manager - silent launcher (no window flash)
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
mainScript = dir & "\home_manager\main.pyw"
pyw = "C:\Users\HP\AppData\Local\Doubao\User Data\sandbox_runtime\bases\c98c5042338ed152c6f10ecd8591889f\python\pythonw.exe"

If fso.FileExists(pyw) Then
    sh.Run """" & pyw & """ """ & mainScript & """", 0, False
ElseIf fso.FileExists(mainScript) Then
    sh.Run "pyw -3 """ & mainScript & """", 0, False
End If

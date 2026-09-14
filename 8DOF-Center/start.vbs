Set WShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' 1. Фиксируем рабочую директорию проекта
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WShell.CurrentDirectory = ScriptDir

' 2. Динамически формируем путь к системному Python 3.11 для текущего пользователя
UserProfile = WShell.ExpandEnvironmentStrings("%USERPROFILE%")
PythonPath = UserProfile & "\AppData\Local\Programs\Python\Python311\pythonw.exe"

' Проверяем наличие корректного Python
If Not FSO.FileExists(PythonPath) Then
    ' Запасной вариант - пытаемся запустить обычный pythonw из PATH
    PythonPath = "pythonw.exe"
End If

' 3. Пути к заставке и проекту .toe
SplashScript = ScriptDir & "\data\PY cores\splash.py"
ToeFile = ScriptDir & "\8DOF.toe"

' 4. Запускаем сплэш-скрин
WShell.Run """" & PythonPath & """ """ & SplashScript & """", 0, False

' 5. Запускаем TouchDesigner
TDPath = "C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe"

If FSO.FileExists(TDPath) Then
    WShell.Run """" & TDPath & """ """ & ToeFile & """", 1, False
Else
    MsgBox "TouchDesigner не найден по пути:" & vbCrLf & TDPath, 16, "8DOF Launcher"
End If
Set WShell = CreateObject("WScript.Shell")

' 1. Запускаем сплэш-скрин
WShell.Run "pythonw.exe ""data\PY cores\splash.py""", 0, False

' 2. Запускаем TouchDesigner
WShell.Run """C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe"" ""8DOF.toe""", 1, False
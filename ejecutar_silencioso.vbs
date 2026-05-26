' ============================================================
' EJECUTAR_SILENCIOSO.VBS
' Corre main.py sin mostrar ninguna ventana negra.
' Guarda todo lo que imprime Python en "log.txt"
' para que puedas revisar si hubo errores.
' Task Scheduler apunta a ESTE archivo, no a main.py directo.
' ============================================================

' Crea el objeto que permite ejecutar comandos del sistema
Set WshShell = CreateObject("WScript.Shell")

' Construye el comando:
'   cd /d "carpeta"   → va a la carpeta del proyecto
'   &&                → si el cd funcionó, ejecuta lo siguiente
'   python main.py    → corre el buscador
'   >> log.txt 2>&1   → guarda TODA la salida (normal + errores) en log.txt
Dim comando
comando = "cmd /c cd /d ""C:\Users\HP\Documents\buscador-vuelos"" && " & _
            "set PYTHONIOENCODING=utf-8 && " & _
            "C:\Python314\python.exe main.py >> log.txt 2>&1"

' Ejecuta el comando:
'   Parametro 1: el comando a ejecutar
'   Parametro 2: 0 = ventana OCULTA (es lo que evita la ventana negra)
'   Parametro 3: False = no esperar a que termine (Task Scheduler lo gestiona)
WshShell.Run comando, 0, False

' Libera el objeto de memoria
Set WshShell = Nothing

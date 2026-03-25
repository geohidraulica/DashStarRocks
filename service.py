import servicemanager
import socket
import sys
import win32serviceutil
import win32service
import win32event
import subprocess
import os
import time
import logging

class DashStarRocksService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DashStarRocks"
    _svc_display_name_ = "DashStarRocks"
    _svc_description_ = "Dash StarRocks Web Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger('DashStarRocksService')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(r'C:\Users\Administrador\Desktop\web-api\DashStarRocks\service.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def SvcStop(self):
        self.logger.info("Servicio deteniéndose...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.logger.info("Terminando proceso del servidor...")
            self.process.terminate()
            self.process.wait(timeout=10)
        win32event.SetEvent(self.hWaitStop)
        self.logger.info("Servicio detenido")

    def SvcDoRun(self):
        try:
            self.logger.info("=" * 50)
            self.logger.info("Iniciando servicio DashStarRocks")
            
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  servicemanager.PYS_SERVICE_STARTED,
                                  (self._svc_name_, ''))
            
            self.logger.info("Esperando 5 segundos para estabilizar el sistema...")
            time.sleep(5)
            
            os.chdir(r"C:\Users\Administrador\Desktop\web-api\DashStarRocks")
            self.logger.info(f"Directorio de trabajo: {os.getcwd()}")
            
            if not os.path.exists("app.py"):
                self.logger.error("NO se encuentra app.py en el directorio actual!")
                raise FileNotFoundError("app.py no encontrado")
            
            cmd = [
                r"C:\Users\Administrador\AppData\Local\Programs\Python\Python310\python.exe",
                "-m", "waitress",
                "--host=0.0.0.0",
                "--port=8080",
                "app:server"
            ]
            
            self.logger.info(f"Ejecutando comando: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.logger.info(f"Servidor iniciado con PID: {self.process.pid}")
            
            import threading
            def log_output(pipe, level):
                for line in iter(pipe.readline, ''):
                    if line.strip():
                        self.logger.info(f"Server output: {line.strip()}")
            
            threading.Thread(target=log_output, args=(self.process.stdout, 'info'), daemon=True).start()
            threading.Thread(target=log_output, args=(self.process.stderr, 'error'), daemon=True).start()
            
            self.process.wait()
            self.logger.warning("El proceso del servidor ha terminado")
            
        except Exception as e:
            self.logger.error(f"Error en el servicio: {str(e)}", exc_info=True)
            raise

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(DashStarRocksService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(DashStarRocksService)

# Comandos para crear el servio windows : 

# 1 : python service.py install
# 2 : Abrir Power shell (Administrador) => sc.exe config DashStarRocks start= auto

# Configurar inicio automático
# sc.exe config DashStarRocks start= auto

# Iniciar servicio
# net start DashStarRocks

# Verificar estado
# sc.exe query DashStarRocks

# Detener el servicio primero (si está corriendo)
# net stop DashStarRocks

# Eliminar el servicio
# sc.exe delete DashStarRocks
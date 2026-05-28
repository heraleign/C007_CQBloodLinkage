"""Start uvicorn backend as a detached Windows process."""
import subprocess
import sys
import os

python_exe = sys.executable
backend_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(backend_dir, 'uvicorn.log')
pid_file = os.path.join(backend_dir, 'backend.pid')

proc = subprocess.Popen(
    [python_exe, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8001', '--reload'],
    cwd=backend_dir,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    stdout=open(log_file, 'w', encoding='utf-8'),
    stderr=subprocess.STDOUT,
    close_fds=True,
)

with open(pid_file, 'w') as f:
    f.write(str(proc.pid))

print(f'Backend started with PID: {proc.pid}')

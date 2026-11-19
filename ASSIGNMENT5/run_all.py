"""Run all Assignment 5 simulation programs in sequence."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for script in ('bgsim.py','feedsim.py','videosim.py'):
 print(f'\n=== Running {script} ===',flush=True)
 subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,check=True)
print('\nAll simulations completed. JSON outputs are saved in this folder.')

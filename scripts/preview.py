"""Run an isolated local preview without opening the owner's museum database."""
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('WONDER_DATA_DIR',str(Path(__file__).resolve().parents[1]/'.preview-data'))
import uvicorn
if __name__=='__main__':
    port = sys.argv[sys.argv.index('--port')+1] if '--port' in sys.argv else os.environ.get('PORT','3000')
    uvicorn.run('server:app',host='0.0.0.0',port=int(port))

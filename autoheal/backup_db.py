import sqlite3
import time
from pathlib import Path

SOURCE_DB = Path(__file__).parent / "data" / "shopsphere.db"
BACKUP_DIR = Path(__file__).parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

def execute_live_backup():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    target_file = BACKUP_DIR / f"shopsphere_backup_{timestamp}.db"
    
    print(f"Starting online hot backup: {SOURCE_DB} -> {target_file}")
    start_time = time.perf_counter()
    
    src_conn = sqlite3.connect(str(SOURCE_DB))
    dest_conn = sqlite3.connect(str(target_file))
    
    with dest_conn:
        src_conn.backup(dest_conn, pages=100, sleep=0.001)
        
    dest_conn.close()
    src_conn.close()
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    print(f"Backup completed successfully in {elapsed_ms:.2f}ms. File size: {target_file.stat().st_size} bytes")
    return str(target_file)

if __name__ == "__main__":
    execute_live_backup()

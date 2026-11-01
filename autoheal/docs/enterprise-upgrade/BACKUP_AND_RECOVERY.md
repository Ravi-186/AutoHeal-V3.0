# AutoHeal & ShopSphere: Backup and Disaster Recovery Procedure

**Author:** SRE & Database Architect  
**Document Ref:** `BCP-DR-001`  
**Date:** 2026-11-01  

---

## 1. Backup Strategy

SQLite in Write-Ahead-Logging (WAL) mode requires clean snapshotting using the native online backup API or safe checkpointing.

### 1.1 Automated Online Database Backup
```bash
# Execute safe online SQLite backup to backup directory
python -c "
import sqlite3, shutil, datetime
src = 'autoheal/data/shopsphere.db'
dst = f'autoheal/backups/shopsphere_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db'
conn_src = sqlite3.connect(src)
conn_dst = sqlite3.connect(dst)
conn_src.backup(conn_dst)
conn_dst.close()
conn_src.close()
print(f'Backup created: {dst}')
"
```

### 1.2 Telemetry Log Archival
```bash
# Archive telemetry CSV files older than 30 days
tar -czf autoheal/backups/telemetry_archive_$(date +%Y%m%d).tar.gz autoheal/data/*.csv
```

---

## 2. Disaster Recovery & Rollback Procedure

1. **Stop Application Services:** `sudo systemctl stop autoheal-backend autoheal-dashboard`
2. **Verify Database Integrity:** `sqlite3 autoheal/data/shopsphere.db "PRAGMA integrity_check;"`
3. **Restore from Snapshot:**
   ```bash
   cp autoheal/backups/shopsphere_backup_<timestamp>.db autoheal/data/shopsphere.db
   rm -f autoheal/data/shopsphere.db-wal autoheal/data/shopsphere.db-shm
   ```
4. **Re-seed and Initialize Schema:** `python -c "from shopsphere.database import seed_data; seed_data()"`
5. **Start Services & Verify Health:** `sudo systemctl start autoheal-backend autoheal-dashboard`
   - Probe `http://localhost:8000/api/health` -> verify `"status": "HEALTHY"`.

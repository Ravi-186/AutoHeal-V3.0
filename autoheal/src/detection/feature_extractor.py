import os
import pandas as pd
import numpy as np

def extract_features(data_dir):
    """Reads raw CSV logs and converts them into 1-minute time window features per device."""
    required_files = {
        'fw': os.path.join(data_dir, "firewall_logs.csv"),
        'logins': os.path.join(data_dir, "login_logs.csv"),
        'dns': os.path.join(data_dir, "dns_logs.csv"),
        'dev': os.path.join(data_dir, "device_logs.csv")
    }
    
    # Check if files exist and are not empty
    for name, path in required_files.items():
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return pd.DataFrame()
            
    try:
        fw = pd.read_csv(required_files['fw'], parse_dates=['timestamp'])
        logins = pd.read_csv(required_files['logins'], parse_dates=['timestamp'])
        dns = pd.read_csv(required_files['dns'], parse_dates=['timestamp'])
        dev = pd.read_csv(required_files['dev'], parse_dates=['timestamp'])
    except Exception:
        return pd.DataFrame()
    
    features = []
    
    # Combine all unique devices seen in the logs
    devices = set(fw['device_id'].unique()) | set(logins['device_id'].unique()) | set(dns['device_id'].unique()) | set(dev['device_id'].unique())
    
    for device_id in devices:
        df_fw = fw[fw['device_id'] == device_id].set_index('timestamp')
        df_logins = logins[logins['device_id'] == device_id].set_index('timestamp')
        df_dns = dns[dns['device_id'] == device_id].set_index('timestamp')
        df_dev = dev[dev['device_id'] == device_id].set_index('timestamp')
        
        # Resample firewall logs to 1-minute bins
        r_fw = df_fw.resample('1min').agg({
            'bytes_sent': 'sum',
            'bytes_received': 'sum',
            'action': 'count' 
        }).fillna(0).rename(columns={'action': 'connections'})
        
        # Resample login logs (count failed logins)
        df_logins['failed'] = (df_logins['status'] == 'FAILED').astype(int)
        r_logins = df_logins.resample('1min').agg({'failed': 'sum'}).fillna(0).rename(columns={'failed': 'failed_logins'})
        
        # Resample DNS logs
        r_dns = df_dns.resample('1min').agg({'domain': 'count'}).fillna(0).rename(columns={'domain': 'dns_requests'})
        
        # Resample device logs
        r_dev = df_dev.resample('1min').agg({'cpu_usage': 'mean', 'mem_usage': 'mean'}).ffill().fillna(0)
        
        # Join all features for this device
        df_device = pd.concat([r_fw, r_logins, r_dns, r_dev], axis=1).fillna(0)
        df_device['device_id'] = device_id
        features.append(df_device)
        
    if not features:
        return pd.DataFrame()
        
    result = pd.concat(features).reset_index()
    return result

def label_data(df, attack_labels):
    """Labels the feature dataset based on known attack windows."""
    df['is_attack'] = 0
    # The end of the 1-minute window
    df['window_end'] = df['timestamp'] + pd.Timedelta(minutes=1)
    
    for device_id, start, end in attack_labels:
        # A window is an attack if it overlaps with the attack duration
        mask = (df['device_id'] == device_id) & \
               (df['timestamp'] <= end) & \
               (df['window_end'] >= start)
        df.loc[mask, 'is_attack'] = 1
        
    df = df.drop(columns=['window_end'])
    return df

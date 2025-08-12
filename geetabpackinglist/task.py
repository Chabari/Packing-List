import frappe
import pysftp
import time
import math
import sys
import os
import traceback
import glob

@frappe.whitelist()
def getFiles():
    frappe.enqueue("geetabpackinglist.task.upload_file_to_sftp", queue='long', timeout=1800)
    
  
def upload_file_to_sftp():
    try:
        frappe.logger().info("Starting background backup upload...")
        list_of_files = glob.glob('/home/frappe/frappe-bench/sites/nfc.local/private/backups/*.sql.gz')
        latest_file = max(list_of_files, key=os.path.getctime)
        print("laaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaatest")
        print(latest_file)
        host = '143.110.161.178'
        port = 22
        username = 'frappe'
        password= 'M@za$1820'
        
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        conn = pysftp.Connection(host=host,port=port,username=username, password=password, cnopts=cnopts)
        print("connection established successfully")
        with conn.cd('/home/frappe/NFC'): 
            conn.put(latest_file, callback=lambda x,y: progressbar(x,y))

            frappe.logger().info("File upload successful.")
            # 4. Delete old files from remote server (older than 2 days)
            two_days_seconds = 1 * 24 * 60 * 60
            now = time.time()

            remote_files = conn.listdir_attr()
            for f in remote_files:
                remote_path = f.filename
                modified_time = f.st_mtime
                age = now - modified_time

                if age > two_days_seconds:
                    conn.remove(remote_path)
                    frappe.logger().info(f"Deleted old remote backup: {remote_path}")

        conn.close()

        
    except Exception as e:
        frappe.log_error(traceback.format_exc(), "Background Backup Upload Failed")
        frappe.logger().error(str(e))
   
  
def progressbar(x, y):
    ''' progressbar for the pysftp
    '''
    bar_len = 60
    filled_len = math.ceil(bar_len * x / float(y))
    percents = math.ceil(100.0 * x / float(y))
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    filesize = f'{math.ceil(y/1024):,} KB' if y > 1024 else f'{y} byte'
    sys.stdout.write(f'[{bar}] {percents}% {filesize}\r')
    sys.stdout.flush()
    
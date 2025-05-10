import shutil
import datetime

def backup_database():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy('requests.db', f'requests_backup_{timestamp}.db')
    print(f"Backup created: requests_backup_{timestamp}.db")

if __name__ == "__main__":
    backup_database()
import sqlite3
import csv

def import_requests(csv_file):
    conn = sqlite3.connect('requests.db')
    c = conn.cursor()
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            c.execute('''INSERT INTO Requests (date_added, equipment_id, fault_type_id, description, client_id, status, worker_id, comments)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (row['date_added'], row['equipment_id'], row['fault_type_id'], row['description'],
                       row['client_id'], row['status'], row['worker_id'] or None, row['comments']))
    
    conn.commit()
    conn.close()
    print("Data imported successfully!")

if __name__ == "__main__":
    import_requests('requests.csv')
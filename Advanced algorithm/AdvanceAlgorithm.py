# Emergency Response Priority Manager (Enhanced)
# Concepts used: Dynamic Array (list), Queue (FIFO), Insertion Sort, Linear Search, Loops, If/Else

# Incident format (7 columns):
# [incident_id, severity, severity_score, location_code, response_time, status, description]

# severity: "LOW"/"MEDIUM"/"HIGH"
# severity_score: number (0-100) (higher = more urgent)
# status: "OPEN"/"DISPATCHED"/"RESOLVED"


def status_value(status):
    if status == "OPEN":
        return 3
    elif status == "DISPATCHED":
        return 2
    else:
        return 1



def print_dataset(data):
    if len(data) == 0:
        print("\nDataset is empty\n")
        return

    print("\nIDX | ID   | SEV    | SCORE | LOC | RESPONSE_TIME       | STATUS      | DESCRIPTION")
    print("--------------------------------------------------------------------------------------")
    for i in range(len(data)):
        r = data[i]
        print(f"{i:3} | {r[0]:4} | {r[1]:6} | {r[2]:5} | {r[3]:3} | {r[4]:18} | {r[5]:10} | {r[6]}")
    print()


def add_incident_to_queue(queue):
    print("\n--- Add Incident to QUEUE ---")
    incident_id = int(input("Incident ID (number): "))
    severity = input("Severity (LOW/MEDIUM/HIGH): ").strip().upper()
    severity_score = int(input("Severity Score (0-100): "))
    location_code = int(input("Location Code (number): "))
    response_time = input("Response Time (YYYY-MM-DD HH:MM): ").strip()
    description = input("Description (text): ").strip()

    status = "OPEN"
    queue.append([incident_id, severity, severity_score, location_code, response_time, status, description])
    print("Added to the queue (FIFO). Status set to OPEN\n")

def process_queue(queue, data):
    if len(queue) == 0:
        print("Queue is empty. Nothing to process\n")
        return

    incident = queue.pop(0)
    data.append(incident)
    print("Moved one incident from queue to dataset\n")

def delete_by_index(data):
    if len(data) == 0:
        print("Dataset is empty\n")
        return

    idx = int(input("Enter dataset index to delete: "))
    if 0 <= idx < len(data):
        removed = data[idx]
        for i in range(idx, len(data) - 1):
            data[i] = data[i + 1]
        data.pop()
        print("Deleted:", removed, "\n")
    else:
        print("Invalid index\n")

def update_by_index(data):
    if len(data) == 0:
        print("Dataset is empty\n")
        return

    idx = int(input("Enter dataset index to update: "))
    if 0 <= idx < len(data):
        print("Current record is:", data[idx])

        incident_id = int(input("New Incident ID: "))
        severity = input("New Severity (LOW/MEDIUM/HIGH): ").strip().upper()
        severity_score = int(input("New Severity Score (0-100): "))
        location_code = int(input("New Location Code: "))
        response_time = input("New Response Time (YYYY-MM-DD HH:MM): ").strip()
        status = input("New Status (OPEN/DISPATCHED/RESOLVED): ").strip().upper()
        description = input("New Description: ").strip()

        data[idx] = [incident_id, severity, severity_score, location_code, response_time, status, description]
        print("Updated\n")
    else:
        print("Invalid index\n")


def change_status_by_id(data):
    if len(data) == 0:
        print("Dataset empty\n")
        return

    iid = int(input("Enter Incident ID to change status: "))
    new_status = input("Enter new status (OPEN/DISPATCHED/RESOLVED): ").strip().upper()

    for i in range(len(data)):
        if data[i][0] == iid:
            data[i][5] = new_status
            print("Status updated\n")
            return

    print("Incident ID not found\n")

def insertion_sort_priority(data):
    n = len(data)

    for i in range(1, n):
        key = data[i]
        j = i - 1

        while j >= 0 and (
            status_value(data[j][5]) < status_value(key[5]) or
            (status_value(data[j][5]) == status_value(key[5]) and data[j][2] < key[2]) or
            (status_value(data[j][5]) == status_value(key[5]) and data[j][2] == key[2] and data[j][4] > key[4])
        ):
            data[j + 1] = data[j]
            j -= 1

        data[j + 1] = key

    print("Dataset sorted by Status(desc), SeverityScore(desc), ResponseTime(asc).\n")


def filter_by_two(data):
    sev = input("Filter Severity (LOW/MEDIUM/HIGH): ").strip().upper()
    status = input("Filter Status (OPEN/DISPATCHED/RESOLVED): ").strip().upper()

    results = []
    for i in range(len(data)):
        if data[i][1] == sev and data[i][5] == status:
            results.append(data[i])

    print("\nFiltered results:")
    print_dataset(results)



def search_by_incident_id(data):
    iid = int(input("Enter Incident ID to search: "))
    for i in range(len(data)):
        if data[i][0] == iid:
            print("\nIncident found:")
            print_dataset([data[i]])
            return
    print("\n Incident not found.\n")

def show_complexity():
    print("""
--- Time & Space Complexity ---
Queue Enqueue (append):             O(1)
Queue Dequeue using pop(0):         O(n) (shifts in array-based queue)
Process Queue to dataset (append):  O(1)
Delete by index (shift):            O(n)
Update by index:                    O(1)
Insertion Sort (3 keys):            O(n^2) worst case, O(1) extra space
Filter (linear scan):               O(n)
Search by incident_id (linear):     O(n)
Space Complexity:                   O(1) extra (besides storing data)
#""")


def main():
    data = [
        [101, "HIGH",   90, 12, "2025-12-08 10:30", "OPEN",       "Fire in chemistry lab"],
        [102, "LOW",    20, 21, "2025-12-08 12:00", "RESOLVED",   "Minor injury"],
        [103, "MEDIUM", 60, 12, "2025-12-08 11:15", "DISPATCHED", "Power outage"],
        [104, "HIGH",   95, 34, "2025-12-08 09:50", "OPEN",       "Gas leak"],
        [105, "LOW",    25, 21, "2025-12-08 13:40", "OPEN",       "Equipment issue"]
    ]

    incident_queue = []

    while True:
        print("""
========= Emergency Response Priority Manager (Enhanced) =========
1) Show dataset
2) Add incident to QUEUE (new reports)
3) Process QUEUE -> move one to dataset
4) Delete incident by dataset index
5) Update incident by dataset index
6) Change status by Incident ID (OPEN/DISPATCHED/RESOLVED)
7) Sort dataset by priority (Insertion Sort)
8) Filter by Severity + Status
9) Search by Incident ID
10) Show time & space complexity
0) Exit
===============================================================
""")
        choice = input("Choose option: ").strip()

        if choice == "1":
            print_dataset(data)
        elif choice == "2":
            add_incident_to_queue(incident_queue)
        elif choice == "3":
            process_queue(incident_queue, data)
        elif choice == "4":
            delete_by_index(data)
        elif choice == "5":
            update_by_index(data)
        elif choice == "6":
            change_status_by_id(data)
        elif choice == "7":
            insertion_sort_priority(data)
        elif choice == "8":
            filter_by_two(data)
        elif choice == "9":
            search_by_incident_id(data)
        elif choice == "10":
            show_complexity()
        elif choice == "0":
            print("Bye")
            break
        else:
            print("Invalid choice.\n")


if __name__ == "__main__":
    main()

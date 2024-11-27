# main.py
import os
from create_poldb import create_poldb
from add_record import add_record
from search_records import search_records
from delete_record import delete_record

def setup_database(filename):
    # Определение структуры базы данных
    columns = [
        ("employee_id", "int", 4),
        ("first_name", "str", 30),
        ("last_name", "str", 30),
        ("department", "str", 20),
        ("position", "str", 30),
        ("salary", "float", 8),
        ("years_of_service", "int", 4)
    ]
    key_columns = ["employee_id"]

    # Создание базы данных
    create_poldb(filename, columns, key_columns)

    # Добавление записей
    employees = [
        {
            "employee_id": 1001,
            "first_name": "John",
            "last_name": "Doe",
            "department": "IT",
            "position": "Software Engineer",
            "salary": 75000.00,
            "years_of_service": 5
        },
        {
            "employee_id": 1002,
            "first_name": "Jane",
            "last_name": "Smith",
            "department": "HR",
            "position": "HR Manager",
            "salary": 80000.00,
            "years_of_service": 7
        },
        {
            "employee_id": 1003,
            "first_name": "Mike",
            "last_name": "Johnson",
            "department": "IT",
            "position": "System Administrator",
            "salary": 70000.00,
            "years_of_service": 3
        },
        {
            "employee_id": 1004,
            "first_name": "Emily",
            "last_name": "Brown",
            "department": "Marketing",
            "position": "Marketing Specialist",
            "salary": 65000.00,
            "years_of_service": 2
        },
        {
            "employee_id": 1005,
            "first_name": "David",
            "last_name": "Wilson",
            "department": "IT",
            "position": "Data Analyst",
            "salary": 72000.00,
            "years_of_service": 4
        }
    ]

    for employee in employees:
        add_record(filename, employee)

    print(f"База данных '{filename}' создана и заполнена.")

def perform_deletions(filename):
    # Удаление записи по ключевому столбцу
    print("\nУдаление сотрудника с employee_id = 1003")
    delete_record(filename, "employee_id", 1003)

    # Проверка удаления
    results = search_records(filename, "employee_id", 1003)
    print(f"Результаты поиска по employee_id = 1003 после удаления: {results}")

    # Удаление записей по неключевому столбцу
    print("\nУдаление всех сотрудников из отдела IT")
    delete_record(filename, "department", "IT")

    # Проверка удаления
    results = search_records(filename, "department", "IT")
    print(f"Результаты поиска по department = 'IT' после удаления: {results}")

def perform_searches(filename):
    # Поиск по ключевому столбцу (employee_id)
    print("\nПоиск сотрудника с ID 1001:")
    results = search_records(filename, "employee_id", 1001)
    for record in results:
        print(record)

    # Поиск по неключевому столбцу (department)
    print("\nПоиск сотрудников в отделе HR:")
    results = search_records(filename, "department", "HR")
    for record in results:
        print(record)

if __name__ == "__main__":
    db_filename = "employees.poldb"

    # Удаляем существующую базу данных, если она есть
    if os.path.exists(db_filename):
        os.remove(db_filename)

    # Создаем и заполняем базу данных
    setup_database(db_filename)

    # Выполняем удаления
    perform_deletions(db_filename)

    # Выполняем поисковые запросы
    perform_searches(db_filename)


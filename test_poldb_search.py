# test_poldb.py
import time
import random
from create_poldb import create_poldb
from poldb_structure import pack_value, get_type_code
from search_records import search_records

import struct
import os

def insert_records(filename, columns, num_records, search_column, search_value):
    """
    Вставляет записи в базу данных .poldb.
    :param filename: Имя файла базы данных
    :param columns: Список кортежей (имя_столбца, тип_данных, размер)
    :param num_records: Количество записей для вставки
    :param search_column: Столбец, по которому будет осуществляться поиск
    :param search_value: Искомое значение, которое гарантированно будет добавлено в записи
    """
    with open(filename, 'r+b') as file:
        # Чтение заголовка файла
        header = file.read(18)
        magic, version, num_columns, num_records_existing, record_size, data_offset = struct.unpack('>4sHHIHI', header)

        # Обновляем количество записей
        num_records_total = num_records_existing + num_records
        file.seek(8)  # Смещение для поля num_records
        file.write(struct.pack('>I', num_records_total))

        # Переходим к концу файла для записи новых записей
        file.seek(0, os.SEEK_END)

        # Генерируем записи
        for i in range(num_records):
            record = b''
            deleted_flag = b'\x00'  # Флаг удаления записи (\x00 - не удалена, \x01 - удалена)
            record += deleted_flag
            for col_name, col_type, col_size in columns:
                type_code = get_type_code(col_type)

                # Генерируем значение для столбца
                if col_name == search_column and i == num_records // 2:
                    # Вставляем искомое значение в середину записей
                    value = search_value
                elif col_type == 'int':
                    value = random.randint(1, num_records * 10)
                elif col_type == 'float':
                    value = random.uniform(1.0, num_records * 10.0)
                elif col_type == 'str':
                    value = f'str_{random.randint(1, num_records * 10)}'
                else:
                    value = None
                packed_value = pack_value(value, type_code, col_size)
                record += packed_value
            file.write(record)

def main():
    # Определяем схему базы данных
    columns = [
        ('id', 'int', 4),
        ('name', 'str', 50),
        ('age', 'int', 4),
        ('salary', 'float', 8),
        ('department', 'str', 20)
    ]
    key_columns = ['id']

    # Количество записей для тестирования
    record_counts = [1000, 5000, 10000, 50000, 100000]  # Уменьшим верхний предел для приемлемого времени выполнения

    # Значение для поиска
    search_column = 'name'
    search_value = 'search_target'  # Искомое значение для столбца 'name'

    # Словарь для хранения результатов
    timing_results = {}

    for num_records in record_counts:
        filename = f'test_db_{num_records}.poldb'
        print(f"\nСоздание базы данных '{filename}' с {num_records} записями...")
        # Создаем базу данных
        create_poldb(filename, columns, key_columns)
        # Вставляем записи, гарантируя наличие искомого значения
        insert_records(filename, columns, num_records, search_column, search_value)

        # Выполняем поиск
        print(f"Выполнение поиска в базе данных '{filename}'...")
        start_time = time.time()
        results = search_records(filename, search_column, search_value)
        end_time = time.time()
        elapsed_time = end_time - start_time
        timing_results[num_records] = elapsed_time
        print(f"Поиск завершен за {elapsed_time:.6f} секунд. Найдено записей: {len(results)}.")

        # Удаляем тестовую базу данных
        os.remove(filename)

    # Выводим временную статистику
    print("\nВременная статистика поиска:")
    for num_records, elapsed_time in timing_results.items():
        print(f"  {num_records} записей: {elapsed_time:.6f} секунд")

if __name__ == '__main__':
    main()

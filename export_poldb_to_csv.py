import struct
import csv
import os
import sys
from poldb_structure import unpack_value

def export_poldb_to_csv(poldb_filename, csv_filename):
    """
    Экспортирует файл базы данных Poldb в формат CSV.

    :param poldb_filename: Путь к файлу базы данных Poldb.
    :param csv_filename: Путь, где будет создан CSV-файл.
    """
    if not os.path.exists(poldb_filename):
        print(f"Ошибка: файл Poldb '{poldb_filename}' не существует.")
        return

    try:
        with open(poldb_filename, 'rb') as poldb_file:
            # Чтение заголовка
            header = poldb_file.read(18)
            magic, version, num_columns, num_records, record_size, data_offset = struct.unpack('>4sHHIHI', header)

            # Проверка магического числа
            if magic != b'PLDB':
                print(f"Ошибка: '{poldb_filename}' не является корректным файлом Poldb.")
                return

            # Чтение метаданных столбцов
            columns = []
            for _ in range(num_columns):
                col_data = poldb_file.read(36)
                col_name_bytes, type_code, col_size, is_key = struct.unpack('>32sBHB', col_data)
                col_name = col_name_bytes.decode('utf-8').rstrip('\0')
                columns.append((col_name, type_code, col_size))

            # Подготовка CSV-файла
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)

                # Запись заголовков столбцов
                header_row = [col[0] for col in columns]
                writer.writerow(header_row)

                # Чтение и запись записей
                for i in range(num_records):
                    record_pos = data_offset + i * record_size
                    poldb_file.seek(record_pos)
                    deleted_flag = poldb_file.read(1)
                    if deleted_flag == b'\x01':
                        continue  # Пропускаем удаленные записи

                    record_bytes = poldb_file.read(record_size - 1)
                    record = []
                    offset = 0
                    for col_name, type_code, col_size in columns:
                        value_bytes = record_bytes[offset:offset + col_size]
                        value = unpack_value(value_bytes, type_code, col_size)
                        record.append(value)
                        offset += col_size

                    writer.writerow(record)

        print(f"Экспорт успешно завершён. CSV-файл создан по пути '{csv_filename}'.")
    except Exception as e:
        print(f"Произошла ошибка при экспорте: {e}")

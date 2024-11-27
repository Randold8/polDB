# search_records.py
import struct
import os
from poldb_structure import unpack_value

def search_records(filename, column_name, search_value):
    """
    Ищет записи в базе данных по значению указанного столбца.

    :param filename: Имя файла базы данных
    :param column_name: Имя столбца для поиска
    :param search_value: Искомое значение
    :return: Список найденных записей
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл {filename} не существует.")

    with open(filename, 'rb') as file:
        # Чтение заголовка файла
        header = file.read(18)
        magic, version, num_columns, num_records, record_size, data_offset = struct.unpack('>4sHHIHI', header)

        # Чтение метаданных столбцов
        columns = []
        key_columns = []
        for _ in range(num_columns):
            col_data = file.read(36)
            col_name, type_code, col_size, is_key = struct.unpack('>32sBHB', col_data)
            col_name = col_name.decode('utf-8').rstrip('\0')
            columns.append((col_name, type_code, col_size))
            if is_key:
                key_columns.append(col_name)

        # Поиск нужного столбца
        target_column = next((col for col in columns if col[0] == column_name), None)
        if not target_column:
            raise ValueError(f"Столбец '{column_name}' не найден.")

        col_name, type_code, col_size = target_column
        col_index = columns.index(target_column)
        col_offset = 1 + sum(col[2] for col in columns[:col_index])  # +1 байт для учета флага "deleted"

        results = []

        # Линейный поиск (т.к. данные могут быть несортированными из-за удалений)
        for i in range(num_records):
            file.seek(data_offset + i * record_size)
            deleted_flag = file.read(1)
            if deleted_flag == b'\x01':
                continue  # Пропускаем удаленные записи
            file.seek(data_offset + i * record_size + col_offset)
            value_bytes = file.read(col_size)
            value = unpack_value(value_bytes, type_code, col_size)

            if value == search_value:
                # Найдено совпадение, читаем всю запись
                file.seek(data_offset + i * record_size)
                record_bytes = file.read(record_size)
                results.append(read_record(record_bytes, columns))

        return results

def read_record(record_bytes, columns):
    """Читает одну запись из байтовой строки."""
    record = {}
    offset = 1  # Пропускаем флаг "deleted"
    for col_name, type_code, col_size in columns:
        value_bytes = record_bytes[offset:offset + col_size]
        value = unpack_value(value_bytes, type_code, col_size)
        record[col_name] = value
        offset += col_size
    return record


# delete_record.py
import struct
import os
from poldb_structure import unpack_value

def delete_record(filename, column_name, value_to_delete):
    """
    Удаляет запись(и) из базы данных по значению указанного столбца.

    - Если столбец является ключевым, то удаляется первая найденная запись.
    - Если столбец не является ключевым, то удаляются все соответствующие записи.

    :param filename: Имя файла базы данных
    :param column_name: Имя столбца для поиска
    :param value_to_delete: Значение для удаления
    :return: Количество удаленных записей
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл {filename} не существует.")

    num_deleted = 0

    with open(filename, 'r+b') as file:
        # Чтение заголовка файла
        header = file.read(18)
        magic, version, num_columns, num_records_intheheader, record_size, data_offset = struct.unpack('>4sHHIHI', header)

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

        # Если столбец ключевой, то используем бинарный поиск для удаления одной записи
        if column_name in key_columns:
            left, right = 0, num_records_intheheader - 1
            while left <= right:
                mid = (left + right) // 2
                record_pos = data_offset + mid * record_size
                file.seek(record_pos)
                deleted_flag = file.read(1)
                if deleted_flag == b'\x01':
                    # Пропускаем удаленные записи
                    if mid < right:
                        mid += 1
                    else:
                        break
                    continue
                file.seek(record_pos + col_offset)
                value_bytes = file.read(col_size)
                value = unpack_value(value_bytes, type_code, col_size)
                if value == value_to_delete:
                    # Помечаем запись как удаленную
                    file.seek(record_pos)
                    file.write(b'\x01')
                    num_deleted += 1
                    break  # Удаляем только одну запись
                elif value < value_to_delete:
                    left = mid + 1
                else:
                    right = mid - 1
        else:
            # Линейный поиск и удаление всех соответствующих записей
            for i in range(num_records_intheheader):
                record_pos = data_offset + i * record_size
                file.seek(record_pos)
                deleted_flag = file.read(1)
                if deleted_flag == b'\x01':
                    continue
                file.seek(record_pos + col_offset)
                value_bytes = file.read(col_size)
                value = unpack_value(value_bytes, type_code, col_size)
                if value == value_to_delete:
                    # Помечаем запись как удаленную
                    file.seek(record_pos)
                    file.write(b'\x01')
                    num_deleted += 1

    print(f"Удалено записей: {num_deleted}")
    return num_deleted

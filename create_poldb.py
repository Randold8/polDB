# create_poldb.py
import struct
import os
from poldb_structure import get_type_code

def create_poldb(filename, columns, key_columns):
    """
    Создает новый файл базы данных .poldb.

    :param filename: Имя файла для создания
    :param columns: Список кортежей (имя_столбца, тип_данных, размер)
    :param key_columns: Список имен ключевых столбцов
    """
    if os.path.exists(filename):
        raise FileExistsError(f"Файл {filename} уже существует.")

    MAGIC_NUMBER = b'PLDB'
    VERSION = 1

    # Добавляем 1 байт к размеру записи для флага "deleted"
    record_size = 1 + sum(col[2] for col in columns)
    data_offset = 18 + len(columns) * 36

    with open(filename, 'wb') as file:
        # Запись заголовка файла
        file.write(struct.pack('>4sHHIHI',
                               MAGIC_NUMBER,
                               VERSION,
                               len(columns),
                               0,  # Изначально 0 записей
                               record_size,
                               data_offset))

        # Запись метаданных столбцов
        for col_name, col_type, col_size in columns:
            is_key = 1 if col_name in key_columns else 0
            file.write(struct.pack('>32sBHB',
                                   col_name.encode('utf-8').ljust(32, b'\0'),
                                   get_type_code(col_type),
                                   col_size,
                                   is_key))

    print(f"База данных '{filename}' успешно создана.")

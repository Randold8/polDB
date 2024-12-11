import csv
import struct
import os
from poldb_structure import get_type_code, pack_value

def import_csv_to_poldb(csv_filename, poldb_filename, key_columns, column_types, column_sizes):
    """
    Импортирует CSV-файл в формат базы данных Poldb.

    :param csv_filename: Путь к исходному CSV-файлу.
    :param poldb_filename: Путь, куда будет создан файл Poldb.
    :param key_columns: Список имен ключевых столбцов.
    :param column_types: Словарь типов данных столбцов {имя_столбца: тип_данных}.
    :param column_sizes: Словарь размеров столбцов {имя_столбца: размер_в_байтах}.
    """
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV-файл '{csv_filename}' не найден.")

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError("CSV-файл пуст.")

        # Проверяем, что все необходимые столбцы присутствуют
        missing_columns = [col for col in key_columns if col not in headers]
        if missing_columns:
            raise ValueError(f"Отсутствуют ключевые столбцы: {', '.join(missing_columns)}")

        columns = []
        for col_name in headers:
            if col_name not in column_types:
                raise ValueError(f"Неизвестный столбец '{col_name}'. Необходимо указать тип данных для этого столбца.")
            col_type = column_types[col_name]
            col_size = column_sizes[col_name]
            columns.append((col_name, col_type, col_size))

        # Создаем файл Poldb
        MAGIC_NUMBER = b'PLDB'
        VERSION = 1

        record_size = 1 + sum(col_size for _, _, col_size in columns)
        data_offset = 18 + len(columns) * 36

        with open(poldb_filename, 'wb') as poldb_file:
            # Запись заголовка файла
            poldb_file.write(struct.pack('>4sHHIHI',
                                         MAGIC_NUMBER,
                                         VERSION,
                                         len(columns),
                                         0,  # Количество записей будет обновляться по мере добавления
                                         record_size,
                                         data_offset))

            # Запись метаданных столбцов
            for col_name, col_type, col_size in columns:
                is_key = 1 if col_name in key_columns else 0
                poldb_file.write(struct.pack('>32sBHB',
                                             col_name.encode('utf-8').ljust(32, b'\0'),
                                             get_type_code(col_type),
                                             col_size,
                                             is_key))

            num_records = 0
            # Чтение и запись записей из CSV
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(columns):
                    raise ValueError(f"Ошибка в строке {row_number}: ожидается {len(columns)} столбцов, найдено {len(row)}.")

                record_data = {}
                for col_index, (col_name, col_type, col_size) in enumerate(columns):
                    value = row[col_index]
                    try:
                        if col_type == 'int':
                            value = int(value)
                        elif col_type == 'float':
                            value = float(value)
                        elif col_type == 'str':
                            value = str(value)
                            # Проверка длины строки
                            encoded_value = value.encode('utf-8')
                            if len(encoded_value) > col_size:
                                raise ValueError(f"Значение в строке {row_number}, столбце '{col_name}' превышает допустимую длину ({col_size} байт).")
                        else:
                            raise ValueError(f"Неизвестный тип данных '{col_type}' для столбца '{col_name}'.")
                    except ValueError as ve:
                        raise ValueError(f"Ошибка преобразования значения в строке {row_number}, столбце '{col_name}': {ve}")

                    record_data[col_name] = value

                # Запись записи в Poldb-файл
                # Флаг "deleted" = 0 (активная запись)
                poldb_file.write(b'\x00')
                for col_name, col_type, col_size in columns:
                    value = record_data[col_name]
                    packed_value = pack_value(value, get_type_code(col_type), col_size)
                    poldb_file.write(packed_value)

                num_records += 1

            # Обновление количества записей в заголовке
            poldb_file.seek(8)
            poldb_file.write(struct.pack('>I', num_records))

    print(f"Импорт успешно завершён. Файл Poldb создан по пути '{poldb_filename}'.")

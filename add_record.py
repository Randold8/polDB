# add_record.py
import struct
import os
from poldb_structure import pack_value, unpack_value

def add_record(filename, record_data):
    """
    Добавляет новую запись в файл базы данных .poldb.

    :param filename: Имя файла базы данных
    :param record_data: Словарь с данными записи {имя_столбца: значение}
    :return: True, если запись добавлена успешно, False в случае отказа
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл {filename} не существует.")

    with open(filename, 'r+b') as file:
        # Чтение заголовка файла
        header = file.read(18)
        magic, version, num_columns, num_records_intheheader, record_size, data_offset = struct.unpack('>4sHHIHI', header)
        # Чтение информации о списке свободных записей

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

        # Проверка наличия всех необходимых данных
        for col_name, _, _ in columns:
            if col_name not in record_data:
                raise ValueError(f"Отсутствует значение для столбца '{col_name}'")

        # Проверка уникальности каждого ключевого столбца
        for key_col in key_columns:
            if not is_value_unique(file, key_col, record_data[key_col], columns, num_records_intheheader, record_size, data_offset):
                print(f"Отказ: значение ключевого столбца '{key_col}' равно '{record_data[key_col]}', которое уже существует в базе данных.")
                return False

        # Ищем удаленную запись для перезаписи (реиспользование пространства)
        reused = False
        for i in range(num_records_intheheader):
            file.seek(data_offset + i * record_size)
            deleted_flag = file.read(1)
            if deleted_flag == b'\x01':  # Запись помечена как удаленная
                # Проверяем, что запись не используется
                file.seek(data_offset + i * record_size)
                file.write(b'\x00')  # Помечаем запись как активную
                for col_name, type_code, col_size in columns:
                    value = record_data[col_name]
                    packed_value = pack_value(value, type_code, col_size)
                    file.write(packed_value)
                reused = True
                break

        if not reused:
            # Добавление новой записи в конец файла
            file.seek(0, 2)  # Переход в конец файла
            file.write(b'\x00')  # Флаг "deleted" = 0 (активная запись)
            for col_name, type_code, col_size in columns:
                value = record_data[col_name]
                packed_value = pack_value(value, type_code, col_size)
                file.write(packed_value)
            # Обновление количества записей в заголовке
            num_records_intheheader += 1
            file.seek(8)
            file.write(struct.pack('>I', num_records_intheheader))

    print("Запись успешно добавлена.")
    return True

def is_value_unique(file, column_name, value_to_check, columns, num_records, record_size, data_offset):
    """
    Проверяет уникальность значения в заданном столбце.
    """
    # Найти метаданные столбца
    target_column = next((col for col in columns if col[0] == column_name), None)
    if not target_column:
        raise ValueError(f"Столбец '{column_name}' не найден.")

    col_name, type_code, col_size = target_column
    col_index = columns.index(target_column)
    col_offset = 1 + sum(col[2] for col in columns[:col_index])  # +1 байт для учета флага "deleted"

    # Выполнение линейного поиска по всем записям
    for i in range(num_records):
        file.seek(data_offset + i * record_size)
        deleted_flag = file.read(1)
        if deleted_flag == b'\x01':
            continue  # Пропускаем удаленные записи
        file.seek(data_offset + i * record_size + col_offset)
        value_bytes = file.read(col_size)
        existing_value = unpack_value(value_bytes, type_code, col_size)
        if existing_value == value_to_check:
            return False
    return True

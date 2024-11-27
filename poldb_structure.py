import struct

def get_type_code(type_name):
    """Возвращает код типа данных."""
    type_codes = {'int': 1, 'float': 2, 'str': 3}
    return type_codes.get(type_name, 0)

def pack_value(value, type_code, size):
    """Упаковывает значение в бинарный формат."""
    if type_code == 1:  # int
        return struct.pack('>i', value)
    elif type_code == 2:  # float
        return struct.pack('>d', value)
    elif type_code == 3:  # str
        # Обрезаем строку до максимального размера
        encoded_value = value.encode('utf-8')
        if len(encoded_value) > size:
            print(f"Предупреждение: строка '{value}' будет обрезана до {size} байт.")
            encoded_value = encoded_value[:size]
        return encoded_value.ljust(size, b'\0')
    else:
        raise ValueError(f"Неизвестный тип данных: {type_code}")


def unpack_value(value_bytes, type_code, size):
    """Распаковывает значение из бинарного формата."""
    if type_code == 1:  # int
        return struct.unpack('>i', value_bytes)[0]
    elif type_code == 2:  # float
        return struct.unpack('>d', value_bytes)[0]
    elif type_code == 3:  # str
        return value_bytes.decode('utf-8').rstrip('\0')
    else:
        raise ValueError(f"Неизвестный тип данных: {type_code}")


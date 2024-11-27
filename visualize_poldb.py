import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import os
from poldb_structure import unpack_value

def read_all_records(filename):
    """
    Считывает все записи из файла базы данных .poldb.

    :param filename: Имя файла базы данных
    :return: Список записей и метаданные столбцов
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл {filename} не существует.")

    with open(filename, 'rb') as file:
        # Чтение заголовка файла
        header = file.read(18)
        magic, version, num_columns, num_records, record_size, data_offset = struct.unpack('>4sHHIHI', header)

        # Чтение метаданных столбцов
        columns = []
        for _ in range(num_columns):
            col_data = file.read(36)
            col_name, type_code, col_size, is_key = struct.unpack('>32sBHB', col_data)
            col_name = col_name.decode('utf-8').rstrip('\0')
            columns.append({
                'name': col_name,
                'type_code': type_code,
                'size': col_size,
                'is_key': bool(is_key)
            })

        records = []

        for i in range(num_records):
            file.seek(data_offset + i * record_size)
            deleted_flag = file.read(1)
            if deleted_flag == b'\x01':
                continue  # Пропускаем удаленные записи
            record_bytes = file.read(record_size - 1)
            record = {}
            offset = 0
            for col in columns:
                col_size = col['size']
                type_code = col['type_code']
                value_bytes = record_bytes[offset:offset + col_size]
                value = unpack_value(value_bytes, type_code, col_size)
                record[col['name']] = value
                offset += col_size
            records.append(record)

    return records, columns

def visualize_poldb(filename):
    # Считываем данные из файла
    try:
        records, columns = read_all_records(filename)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{e}")
        return

    # Создаем главное окно
    root = tk.Tk()
    root.title(f"Просмотр базы данных: {os.path.basename(filename)}")
    root.geometry("800x600")

    # Создаем виджет Treeview для отображения таблицы
    tree = ttk.Treeview(root)
    tree.pack(fill=tk.BOTH, expand=True)

    # Определяем столбцы
    col_names = [col['name'] for col in columns]
    tree['columns'] = col_names

    # Форматируем колонки
    tree.column("#0", width=0, stretch=tk.NO)
    for col_name in col_names:
        tree.column(col_name, anchor=tk.W, width=100)
        tree.heading(col_name, text=col_name, anchor=tk.W)

    # Добавляем данные в таблицу
    for i, record in enumerate(records):
        values = [record.get(col_name, '') for col_name in col_names]
        tree.insert('', 'end', iid=i, values=values)

    # Добавляем возможность горизонтальной и вертикальной прокрутки
    scrollbar_y = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
    scrollbar_y.pack(side='right', fill='y')
    tree.configure(yscrollcommand=scrollbar_y.set)

    scrollbar_x = ttk.Scrollbar(root, orient='horizontal', command=tree.xview)
    scrollbar_x.pack(side='bottom', fill='x')
    tree.configure(xscrollcommand=scrollbar_x.set)

    # Запускаем главный цикл приложения
    root.mainloop()

def select_and_visualize():
    filename = filedialog.askopenfilename(
        title="Открыть файл базы данных",
        filetypes=(("PolDB files", "*.poldb"), ("Все файлы", "*.*"))
    )
    if filename:
        visualize_poldb(filename)

if __name__ == "__main__":
    # Создаем главное окно для выбора файла
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно

    select_and_visualize()

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import csv
import struct
import shutil



from poldb_structure import pack_value, unpack_value, get_type_code
from add_record import add_record
from search_records import search_records
from delete_record import delete_record
from create_poldb import create_poldb
from import_csv_to_poldb import import_csv_to_poldb


class PoldbGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Poldb Database Viewer")
        self.master.iconbitmap('img/athena.ico')  # Устанавливаем кастомную иконку
        self.filename = None
        self.columns = []
        self.key_columns = []
        self.data_indices = []  # List of record positions in the file
        self.create_widgets()

    def create_widgets(self):
        # Создание меню
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # Меню "Создать"
        self.create_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Создать", menu=self.create_menu)
        self.create_menu.add_command(label="Создать базу данных", command=self.open_create_database_window)
        self.create_menu.add_command(label="Создать из CSV", command=self.create_database_from_csv)

        # Меню "Файл"
        self.file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=self.file_menu)
        self.file_menu.add_command(label="Открыть", command=self.open_database)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Экспортировать в CSV", command=self.export_to_csv, state="disabled")
        self.file_menu.add_command(label="Создать резервную копию", command=self.create_backup, state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Выход", command=self.master.quit)

        # Меню "Редактировать"
        self.edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Редактировать", menu=self.edit_menu)
        self.edit_menu.add_command(label="Добавить запись", command=self.open_add_record_window, state="disabled")
        self.edit_menu.add_command(label="Удалить выбранные записи", command=self.delete_selected_records)
        self.edit_menu.add_command(label="Удалить записи по значению", command=self.open_delete_by_value_window)

        # Меню "Поиск"
        self.search_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Поиск", menu=self.search_menu)
        self.search_menu.add_command(label="Поиск по значению", command=self.open_search_window)

        # Создаем Frame для размещения Treeview и скроллбаров
        tree_frame = tk.Frame(self.master)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем вертикальный скроллбар
        vsb = tk.Scrollbar(tree_frame, orient="vertical")
        vsb.grid(row=0, column=1, sticky='ns')

        # Создаем горизонтальный скроллбар
        hsb = tk.Scrollbar(tree_frame, orient="horizontal")
        hsb.grid(row=1, column=0, sticky='ew')

        # Создаем Treeview
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.grid(row=0, column=0, sticky='nsew')

        # Привязываем скроллбары к Treeview
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Указываем, что область размещения растягивается при изменении размера окна
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Настройка стилей Treeview (остается без изменений)
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Настройка стиля для тега 'found' (выделение найденных записей)
        self.tree.tag_configure('found', background='yellow')
        self.style.configure("KeyColumn.Treeview.Cell", background="#d9ead3")
        self.style.configure("KeyColumn.Treeview.Heading", font=('TkDefaultFont', 10, 'bold'))
        self.style.configure("Treeview.KeyColumn", background="#d9ead3")

    def open_create_database_window(self):
        create_db_window = tk.Toplevel(self.master)
        create_db_window.title("Создать новую базу данных")

        # Ввод имени файла для базы данных
        tk.Label(create_db_window, text="Имя файла:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        filename_entry = tk.Entry(create_db_window)
        filename_entry.grid(row=0, column=1, padx=5, pady=5)

        # Ввод количества столбцов
        tk.Label(create_db_window, text="Количество столбцов:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        num_columns_var = tk.IntVar()
        num_columns_var.set(1)
        num_columns_spinbox = tk.Spinbox(create_db_window, from_=1, to=100, textvariable=num_columns_var, width=5)
        num_columns_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        columns_frame = tk.Frame(create_db_window)
        columns_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        columns_entries = []

        def update_columns_entries(*args):
            # Удаляем старые виджеты
            for widget in columns_frame.winfo_children():
                widget.destroy()
            columns_entries.clear()

            num_columns = num_columns_var.get()

            # Заголовки столбцов
            tk.Label(columns_frame, text="Столбец").grid(row=0, column=0, padx=5, pady=5)
            tk.Label(columns_frame, text="Имя столбца").grid(row=0, column=1, padx=5, pady=5)
            tk.Label(columns_frame, text="Тип").grid(row=0, column=2, padx=5, pady=5)
            tk.Label(columns_frame, text="Размер").grid(row=0, column=3, padx=5, pady=5)
            tk.Label(columns_frame, text="Ключ").grid(row=0, column=4, padx=5, pady=5)

            for i in range(num_columns):
                tk.Label(columns_frame, text=f"{i + 1}").grid(row=i + 1, column=0, padx=5, pady=5, sticky=tk.W)

                # Имя столбца
                name_entry = tk.Entry(columns_frame)
                name_entry.grid(row=i + 1, column=1, padx=5, pady=5)

                # Тип данных
                datatype_combo = ttk.Combobox(columns_frame, values=['int', 'float', 'str'], state='readonly', width=6)
                datatype_combo.current(0)
                datatype_combo.grid(row=i + 1, column=2, padx=5, pady=5)

                # Размер (для строк)
                size_entry = tk.Entry(columns_frame, width=5)
                size_entry.grid(row=i + 1, column=3, padx=5, pady=5)
                size_entry.insert(0, '4')  # Значение по умолчанию

                # Ключевой столбец
                key_var = tk.IntVar()
                key_checkbox = tk.Checkbutton(columns_frame, variable=key_var)
                key_checkbox.grid(row=i + 1, column=4, padx=5, pady=5)

                columns_entries.append({
                    'name': name_entry,
                    'type': datatype_combo,
                    'size': size_entry,
                    'key': key_var
                })

        num_columns_var.trace_add('write', update_columns_entries)
        update_columns_entries()

        def create_database():
            filename = filename_entry.get().strip()
            if not filename:
                messagebox.showerror("Ошибка", "Пожалуйста, введите имя файла базы данных.")
                return

            # Диалог сохранения файла
            filename = filedialog.asksaveasfilename(initialfile=filename, defaultextension=".poldb",
                                                    filetypes=[("Poldb файлы", "*.poldb"), ("Все файлы", "*.*")])
            if not filename:
                return

            columns = []
            key_columns = []

            for idx, entry in enumerate(columns_entries):
                col_name = entry['name'].get().strip()
                col_type = entry['type'].get()
                col_size = entry['size'].get().strip()
                is_key = entry['key'].get()

                if not col_name:
                    messagebox.showerror("Ошибка", f"Пожалуйста, введите имя для столбца {idx + 1}.")
                    return

                if col_type == 'str':
                    try:
                        col_size = int(col_size)
                        if col_size <= 0:
                            raise ValueError
                    except ValueError:
                        messagebox.showerror("Ошибка",
                                             f"Пожалуйста, введите корректный размер для строки в столбце {col_name}.")
                        return
                else:
                    col_size = 4  # Для int и float размер 4 байта

                columns.append((col_name, col_type, col_size))
                if is_key:
                    key_columns.append(col_name)

            # Проверяем, что есть хотя бы один ключевой столбец
            if not key_columns:
                messagebox.showerror("Ошибка", "Должен быть хотя бы один ключевой столбец.")
                return

            try:
                create_poldb(filename, columns, key_columns)
                messagebox.showinfo("Успех", f"База данных '{filename}' успешно создана.")
                create_db_window.destroy()
                # Открываем созданную базу данных
                self.filename = filename
                self.load_data()
                # Активируем пункты меню
                self.edit_menu.entryconfig("Добавить запись", state="normal")
                self.file_menu.entryconfig("Создать резервную копию", state="normal")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать базу данных:\n{e}")

        create_button = tk.Button(create_db_window, text="Создать", command=create_database)
        create_button.grid(row=3, column=0, columnspan=2, pady=10)

    def open_database(self):
        # File dialog to open the database file
        filename = filedialog.askopenfilename(title="Открыть базу данных Poldb",
                                              filetypes=[("Poldb файлы", "*.poldb"), ("Все файлы", "*.*")])
        if filename:
            # Сохраняем текущий путь к файлу на случай ошибки
            old_filename = self.filename
            try:
                # Устанавливаем временный файл для загрузки
                self.filename = filename
                self.load_data()
                # Активируем пункты меню
                self.edit_menu.entryconfig("Добавить запись", state="normal")
                self.file_menu.entryconfig("Экспортировать в CSV", state="normal")
                self.file_menu.entryconfig("Создать резервную копию", state="normal")
            except Exception as e:
                # Если произошла ошибка, показываем сообщение и возвращаем старое значение
                messagebox.showerror("Ошибка", f"Не удалось загрузить базу данных:\n{e}")
                self.filename = old_filename
        else:
            # Если пользователь закрыл диалоговое окно, ничего не делаем
            return

    def load_data(self):
        # Загрузка данных из базы данных Poldb
        try:
            with open(self.filename, 'rb') as file:
                # Чтение заголовка и проверка магического числа
                header = file.read(18)
                magic, version, num_columns, num_records, record_size, data_offset = struct.unpack('>4sHHIHI', header)

                if magic != b'PLDB':
                    raise ValueError("Неверный файл базы данных Poldb.")

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

                # Здесь очищаем существующие данные только после успешного чтения заголовка и метаданных
                self.columns = columns
                self.key_columns = key_columns
                self.data_indices = []

                # Удаляем тег 'found' со всех элементов
                for item_id in self.tree.get_children():
                    tags = self.tree.item(item_id, 'tags')
                    if 'found' in tags:
                        tags = tuple(tag for tag in tags if tag != 'found')
                        self.tree.item(item_id, tags=tags)

                # Очистка существующих данных в Treeview
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Настройка столбцов Treeview
                self.tree["columns"] = [col[0] for col in self.columns]
                self.tree["show"] = "headings"

                for col in self.columns:
                    col_name = col[0]
                    col_heading = col_name
                    if col_name in self.key_columns:
                        # Добавляем звездочку к имени ключевого столбца и делаем заголовок жирным
                        col_heading += " *"
                        self.tree.heading(col_name, text=col_heading,
                                          command=lambda _col=col_name: self.sort_by_column(_col, False))
                    else:
                        self.tree.heading(col_name, text=col_heading,
                                          command=lambda _col=col_name: self.sort_by_column(_col, False))
                    self.tree.column(col_name, anchor='center')

                # Чтение и отображение записей
                file.seek(data_offset)
                for i in range(num_records):
                    record_pos = data_offset + i * record_size
                    file.seek(record_pos)
                    deleted_flag = file.read(1)
                    if deleted_flag == b'\x01':
                        continue  # Пропускаем удаленные записи

                    record_bytes = file.read(record_size - 1)
                    record = {}
                    offset = 0
                    for col_name, type_code, col_size in self.columns:
                        value_bytes = record_bytes[offset:offset + col_size]
                        value = unpack_value(value_bytes, type_code, col_size)
                        record[col_name] = value
                        offset += col_size

                    # Вставляем данные в Treeview
                    item_values = [record[col[0]] for col in self.columns]
                    self.tree.insert('', tk.END, values=item_values)
                    self.data_indices.append(record_pos)

                self.master.title(f"Poldb Database Viewer - {os.path.basename(self.filename)}")
        except Exception as e:
            raise e  # Пробрасываем исключение, чтобы оно было обработано в open_database

    def on_double_click(self, event):
        # Handle double-click on a cell for editing
        item_id = self.tree.focus()
        if not item_id:
            return

        # Index of the selected record
        record_index = self.tree.index(item_id)

        # Column coordinates
        column = self.tree.identify_column(event.x)
        col_index = int(column.replace('#', '')) - 1

        # Check if the column is a key column
        col_name = self.columns[col_index][0]
        if col_name in self.key_columns:
            messagebox.showwarning("Редактирование запрещено", "Редактирование ключевых столбцов запрещено.")
            return

        # Get the current value
        current_value = self.tree.set(item_id, column)

        # Open a window to edit the value
        x, y, width, height = self.tree.bbox(item_id, column)
        edit_window = tk.Toplevel(self.master)
        edit_window.geometry(f"{width}x{height}+{self.master.winfo_rootx() + x}+{self.master.winfo_rooty() + y}")
        edit_window.overrideredirect(True)

        new_value_var = tk.StringVar()
        new_value_var.set(current_value)
        entry = tk.Entry(edit_window, textvariable=new_value_var)
        entry.focus()
        entry.select_range(0, tk.END)
        entry.pack()

        def on_save():
            new_value = new_value_var.get()
            # Validate and update the value
            type_code = self.columns[col_index][1]
            col_size = self.columns[col_index][2]

            try:
                if type_code == 1:  # int
                    new_value = int(new_value)
                elif type_code == 2:  # float
                    new_value = float(new_value)
                elif type_code == 3:  # str
                    new_value = str(new_value)
                    # Check string length
                    encoded_value = new_value.encode('utf-8')
                    if len(encoded_value) > col_size:
                        messagebox.showerror("Ошибка", f"Строка слишком длинная для столбца '{col_name}'.")
                        edit_window.destroy()
                        return
                else:
                    messagebox.showerror("Ошибка", f"Неизвестный тип данных для столбца '{col_name}'.")
                    edit_window.destroy()
                    return
            except ValueError:
                messagebox.showerror("Неверное значение", f"Введенное значение не соответствует типу столбца '{col_name}'.")
                edit_window.destroy()
                return

            # Update the value directly in the database file
            try:
                with open(self.filename, 'r+b') as file:
                    record_pos = self.data_indices[record_index]
                    file.seek(record_pos)
                    deleted_flag = file.read(1)
                    if deleted_flag == b'\x01':
                        messagebox.showerror("Ошибка", "Запись была удалена.")
                        edit_window.destroy()
                        return

                    # Calculate field offset
                    offset = 1  # Shift to account for 'deleted' flag
                    for i, (col, _, size) in enumerate(self.columns):
                        if i == col_index:
                            break
                        offset += size

                    # Move to the correct position in the record
                    file.seek(record_pos + offset)
                    # Pack the new value
                    packed_value = pack_value(new_value, type_code, col_size)
                    # Write the new value
                    file.write(packed_value)
                # Update the value in the interface
                self.tree.set(item_id, column, new_value)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")
            finally:
                edit_window.destroy()

        entry.bind('<Return>', lambda event: on_save())
        entry.bind('<FocusOut>', lambda event: edit_window.destroy())

    def open_add_record_window(self):
        if not self.filename:
            messagebox.showwarning("Предупреждение", "Сначала откройте базу данных.")
            return

        # Create a new window for entering data
        add_window = tk.Toplevel(self.master)
        add_window.title("Добавить новую запись")

        entries = {}
        for idx, (col_name, type_code, col_size) in enumerate(self.columns):
            tk.Label(add_window, text=col_name).grid(row=idx, column=0, sticky=tk.W, padx=5, pady=5)

            entry = tk.Entry(add_window)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            entries[col_name] = (entry, type_code, col_size)

        def save_new_record():
            new_record = {}
            try:
                for col_name, (entry, type_code, col_size) in entries.items():
                    value = entry.get()
                    if type_code == 1:  # int
                        value = int(value)
                    elif type_code == 2:  # float
                        value = float(value)
                    elif type_code == 3:  # str
                        value = str(value)
                        # Check string length
                        encoded_value = value.encode('utf-8')
                        if len(encoded_value) > col_size:
                            messagebox.showerror("Ошибка", f"Поле '{col_name}' слишком длинное.")
                            return
                    else:
                        messagebox.showerror("Ошибка", f"Неизвестный тип данных для поля '{col_name}'.")
                        return
                    new_record[col_name] = value

                # Use add_record function to add to the database
                result = add_record(self.filename, new_record)
                if result:
                    # Update the Treeview
                    self.append_record_to_treeview(new_record)
                    messagebox.showinfo("Успех", "Новая запись успешно добавлена.")
                    add_window.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось добавить запись. Возможно, ключевые поля не уникальны.")
            except ValueError as ve:
                messagebox.showerror("Ошибка", f"Неверное значение для поля.\n{ve}")

        save_button = tk.Button(add_window, text="Сохранить", command=save_new_record)
        save_button.grid(row=len(self.columns), column=0, columnspan=2, pady=10)

    def append_record_to_treeview(self, record):
        # Добавляем новую запись в Treeview
        item_values = [record[col[0]] for col in self.columns]
        item_id = self.tree.insert('', tk.END, values=item_values)
        # Применяем тег 'new_record' к новому элементу (если необходимо)
        self.tree.item(item_id, tags=('new_record',))
        # Добавляем позицию записи в data_indices
        with open(self.filename, 'rb') as file:
            # Читаем заголовок и получаем количество записей
            file.seek(0)
            header = file.read(18)
            magic, version, num_columns, num_records, record_size, data_offset = struct.unpack('>4sHHIHI', header)
            # Позиция новой записи
            new_record_pos = data_offset + (num_records - 1) * record_size
            self.data_indices.append(new_record_pos)

    def delete_selected_records(self):
        if not self.filename:
            messagebox.showwarning("Предупреждение", "Сначала откройте базу данных.")
            return

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Не выбраны записи для удаления.")
            return

        confirm = messagebox.askyesno("Подтверждение удаления",
                                      f"Вы действительно хотите удалить выбранные {len(selected_items)} записи?")
        if not confirm:
            return

        for item_id in selected_items:
            record_index = self.tree.index(item_id)
            record_pos = self.data_indices[record_index]

            # Получаем значения ключевых столбцов для удаления
            key_values = {}
            for idx, (col_name, _, _) in enumerate(self.columns):
                if col_name in self.key_columns:
                    key_values[col_name] = self.tree.set(item_id, self.columns[idx][0])

            # Используем функцию delete_record для удаления по каждому ключевому столбцу
            for key_col, key_value in key_values.items():
                # Приводим значение к правильному типу
                type_code = next(col[1] for col in self.columns if col[0] == key_col)
                if type_code == 1:
                    key_value = int(key_value)
                elif type_code == 2:
                    key_value = float(key_value)
                elif type_code == 3:
                    key_value = str(key_value)
                delete_record(self.filename, key_col, key_value)

        # Обновляем отображение данных
        self.load_data()

    def open_delete_by_value_window(self):
        if not self.filename:
            messagebox.showwarning("Предупреждение", "Сначала откройте базу данных.")
            return

        # Создаем новое окно для выбора столбца и значения
        delete_window = tk.Toplevel(self.master)
        delete_window.title("Удалить записи по значению")

        tk.Label(delete_window, text="Столбец:").grid(row=0, column=0, padx=5, pady=5)
        column_combo = ttk.Combobox(delete_window, values=[col[0] for col in self.columns], state='readonly')
        column_combo.grid(row=0, column=1, padx=5, pady=5)
        column_combo.current(0)

        tk.Label(delete_window, text="Значение:").grid(row=1, column=0, padx=5, pady=5)
        value_entry = tk.Entry(delete_window)
        value_entry.grid(row=1, column=1, padx=5, pady=5)

        def delete_by_value():
            column_name = column_combo.get()
            value = value_entry.get()
            type_code = next(col[1] for col in self.columns if col[0] == column_name)
            try:
                if type_code == 1:  # int
                    value = int(value)
                elif type_code == 2:  # float
                    value = float(value)
                elif type_code == 3:  # str
                    value = str(value)
            except ValueError:
                messagebox.showerror("Ошибка", "Введено неверное значение для выбранного столбца.")
                return

            confirm = messagebox.askyesno("Подтверждение удаления",
                                          f"Вы действительно хотите удалить записи, где {column_name} = {value}?")
            if not confirm:
                return

            # Используем функцию delete_record для удаления
            num_deleted = delete_record(self.filename, column_name, value)
            messagebox.showinfo("Удаление завершено", f"Удалено записей: {num_deleted}")

            # Обновляем отображение данных
            self.load_data()
            delete_window.destroy()

        delete_button = tk.Button(delete_window, text="Удалить", command=delete_by_value)
        delete_button.grid(row=2, column=0, columnspan=2, pady=10)

    def open_search_window(self):
        if not self.filename:
            messagebox.showwarning("Предупреждение", "Сначала откройте базу данных.")
            return

        # Создаем новое окно для ввода параметров поиска
        search_window = tk.Toplevel(self.master)
        search_window.title("Поиск по значению")

        tk.Label(search_window, text="Столбец:").grid(row=0, column=0, padx=5, pady=5)
        column_combo = ttk.Combobox(search_window, values=[col[0] for col in self.columns], state='readonly')
        column_combo.grid(row=0, column=1, padx=5, pady=5)
        column_combo.current(0)

        tk.Label(search_window, text="Значение:").grid(row=1, column=0, padx=5, pady=5)
        value_entry = tk.Entry(search_window)
        value_entry.grid(row=1, column=1, padx=5, pady=5)

        def perform_search():
            column_name = column_combo.get()
            search_value = value_entry.get()
            type_code = next(col[1] for col in self.columns if col[0] == column_name)
            try:
                if type_code == 1:  # int
                    search_value = int(search_value)
                elif type_code == 2:  # float
                    search_value = float(search_value)
                elif type_code == 3:  # str
                    search_value = str(search_value)
            except ValueError:
                messagebox.showerror("Ошибка", "Введено неверное значение для выбранного столбца.")
                return

            # Используем функцию search_records для поиска записей
            try:
                found_records = search_records(self.filename, column_name, search_value)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при поиске записей:\n{e}")
                return

            # Очистка предыдущего выделения
            for item_id in self.tree.get_children():
                self.tree.item(item_id, tags=())  # Удаляем все теги

            # Поиск и выделение найденных записей
            found_count = 0
            first_found_item_id = None  # Для хранения item_id первого найденного элемента
            for record in found_records:
                # Находим item_id записи в Treeview
                for item_id in self.tree.get_children():
                    match = True
                    for col_name in self.tree["columns"]:
                        tree_value = self.tree.set(item_id, col_name)
                        record_value = record[col_name]
                        # Приводим значения к строке для сравнения
                        if str(tree_value) != str(record_value):
                            match = False
                            break
                    if match:
                        self.tree.item(item_id, tags=('found',))
                        found_count += 1
                        if first_found_item_id is None:
                            first_found_item_id = item_id  # Сохраняем item_id первого найденного элемента
                        break

            # Если найдены записи, автоматически прокручиваем к первой найденной записи
            if first_found_item_id:
                self.tree.see(first_found_item_id)

            # Отображаем сообщение с количеством найденных записей
            if found_count > 0:
                messagebox.showinfo("Результаты поиска", f"Найдено {found_count} соответствующих записей.")
            else:
                messagebox.showinfo("Результаты поиска", "Записи не найдены.")

            # Закрываем окно поиска после завершения поиска
            search_window.destroy()

        # Создаем кнопку "Найти" вне функции perform_search()
        search_button = tk.Button(search_window, text="Найти", command=perform_search)
        search_button.grid(row=2, column=0, columnspan=2, pady=10)

    def export_to_csv(self):
        # Запрашиваем у пользователя путь для сохранения файла CSV
        csv_filename = filedialog.asksaveasfilename(title="Сохранить CSV файл",
                                                    defaultextension=".csv",
                                                    filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")])
        if not csv_filename:
            return  # Пользователь отменил диалог сохранения

        try:
            with open(self.filename, 'rb') as poldb_file:
                # Чтение заголовка
                header = poldb_file.read(18)
                magic, version, num_columns, num_records, record_size, data_offset = struct.unpack('>4sHHIHI',
                                                                                                   header)

                # Проверка магического числа
                if magic != b'PLDB':
                    messagebox.showerror("Ошибка", "Неверный файл базы данных Poldb.")
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

            messagebox.showinfo("Экспорт завершён", f"Файл успешно экспортирован в '{csv_filename}'.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при экспорте:\n{e}")

    def sort_by_column(self, col, reverse):
        # Получаем данные из Treeview
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]

        # Определяем тип данных столбца
        type_code = next((item[1] for item in self.columns if item[0] == col), 3)  # По умолчанию str

        # Определяем функцию для преобразования значений в соответствующий тип
        def convert(value):
            if type_code == 1:  # int
                try:
                    return int(value)
                except ValueError:
                    return 0
            elif type_code == 2:  # float
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            else:
                return str(value)

        # Применяем функцию преобразования к данным
        data = [(convert(value), child) for (value, child) in data]

        # Сортируем данные
        data.sort(reverse=reverse)

        # Перемещаем элементы в новом порядке
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        # Меняем направление сортировки для следующего клика
        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def create_backup(self):
        if not self.filename:
            messagebox.showwarning("Предупреждение", "Нет открытой базы данных для создания резервной копии.")
            return

        # Предлагаем выбрать место и имя для резервной копии
        backup_filename = filedialog.asksaveasfilename(title="Сохранить резервную копию как",
                                                       initialfile=os.path.basename(self.filename) + ".backup",
                                                       defaultextension=".poldb",
                                                       filetypes=[("Poldb файлы", "*.poldb"), ("Все файлы", "*.*")])
        if not backup_filename:
            return  # Пользователь отменил диалог сохранения

        try:
            shutil.copy2(self.filename, backup_filename)
            messagebox.showinfo("Успех", f"Резервная копия успешно создана по пути:\n{backup_filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать резервную копию:\n{e}")

    def create_database_from_csv(self):
        # Открываем диалог для выбора CSV-файла
        csv_filename = filedialog.askopenfilename(title="Выберите CSV-файл",
                                                  filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")])
        if not csv_filename:
            return  # Пользователь отменил диалог

        # Открываем диалог для сохранения Poldb-файла
        poldb_filename = filedialog.asksaveasfilename(title="Сохранить как Poldb-файл",
                                                      defaultextension=".poldb",
                                                      filetypes=[("Poldb файлы", "*.poldb"), ("Все файлы", "*.*")])
        if not poldb_filename:
            return  # Пользователь отменил диалог

        # Открываем окно для указания параметров импорта
        import_window = tk.Toplevel(self.master)
        import_window.title("Параметры импорта CSV")

        # Читаем заголовки CSV-файла
        try:
            with open(csv_filename, 'r', newline='', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file)
                headers = next(reader)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать CSV-файл:\n{e}")
            return

        # Отображаем список столбцов для ввода типов данных и указания ключевых столбцов
        entries = {}
        for idx, col_name in enumerate(headers):
            tk.Label(import_window, text=col_name).grid(row=idx, column=0, padx=5, pady=5)

            type_var = tk.StringVar(value='str')
            tk.OptionMenu(import_window, type_var, 'int', 'float', 'str').grid(row=idx, column=1, padx=5, pady=5)

            size_entry = tk.Entry(import_window)
            size_entry.insert(0, '50')  # Значение по умолчанию
            size_entry.grid(row=idx, column=2, padx=5, pady=5)

            key_var = tk.IntVar()
            tk.Checkbutton(import_window, variable=key_var).grid(row=idx, column=3, padx=5, pady=5)

            entries[col_name] = (type_var, size_entry, key_var)

        tk.Label(import_window, text="Тип данных").grid(row=0, column=1)
        tk.Label(import_window, text="Размер (байт)").grid(row=0, column=2)
        tk.Label(import_window, text="Ключевой").grid(row=0, column=3)

        def start_import():
            column_types = {}
            column_sizes = {}
            key_columns = []
            try:
                for col_name, (type_var, size_entry, key_var) in entries.items():
                    col_type = type_var.get()
                    size = int(size_entry.get())
                    if size <= 0:
                        raise ValueError(f"Размер столбца '{col_name}' должен быть больше 0.")
                    column_types[col_name] = col_type
                    column_sizes[col_name] = size
                    if key_var.get():
                        key_columns.append(col_name)

                if not key_columns:
                    raise ValueError("Необходимо указать хотя бы один ключевой столбец.")

                # Вызываем функцию импорта
                import_csv_to_poldb(csv_filename, poldb_filename, key_columns, column_types, column_sizes)

                messagebox.showinfo("Успех", f"База данных успешно создана по пути '{poldb_filename}'.")
                import_window.destroy()
                # Открываем созданную базу данных
                self.filename = poldb_filename
                self.load_data()
                self.edit_menu.entryconfig("Добавить запись", state="normal")
                self.file_menu.entryconfig("Экспортировать в CSV", state="normal")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при импорте CSV:\n{e}")

        import_button = tk.Button(import_window, text="Импортировать", command=start_import)
        import_button.grid(row=len(headers), column=0, columnspan=4, pady=10)




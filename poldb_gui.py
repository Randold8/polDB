import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import struct
import os

from poldb_structure import pack_value, unpack_value, get_type_code
from add_record import add_record
from search_records import search_records
from delete_record import delete_record

class PoldbGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Poldb Database Viewer")
        self.filename = None
        self.columns = []
        self.key_columns = []
        self.data_indices = []  # List of record positions in the file
        self.create_widgets()

    def create_widgets(self):
        # Create menu
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)


        # Add 'File' menu
        self.file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=self.file_menu)
        self.file_menu.add_command(label="Открыть", command=self.open_database)
        self.file_menu.add_command(label="Добавить запись", command=self.open_add_record_window, state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Выход", command=self.master.quit)

        # Добавляем меню 'Редактировать' и подменю для удаления
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Редактировать", menu=edit_menu)
        edit_menu.add_command(label="Удалить выбранные записи", command=self.delete_selected_records)
        edit_menu.add_command(label="Удалить записи по значению", command=self.open_delete_by_value_window)

        search_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Поиск", menu=search_menu)
        search_menu.add_command(label="Поиск по значению", command=self.open_search_window)

        # Create Treeview widget for displaying data
        self.tree = ttk.Treeview(self.master)
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Создаем стиль для Treeview и устанавливаем тему 'clam'
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Установите тему на 'clam', 'alt' или 'default'

        # Настройка стиля для тега 'found' (выделение найденных записей)
        self.tree.tag_configure('found', background='yellow')
        self.style.configure("KeyColumn.Treeview.Cell", background="#d9ead3")  # Light green background
        self.style.configure("KeyColumn.Treeview.Heading", font=('TkDefaultFont', 10, 'bold'))
        # Создаем стиль для ключевых столбцов
        self.style.configure("Treeview.KeyColumn", background="#d9ead3")

    def open_database(self):
        # File dialog to open the database file
        self.filename = filedialog.askopenfilename(title="Открыть базу данных Poldb",
                                                   filetypes=[("Poldb файлы", "*.poldb"), ("Все файлы", "*.*")])
        if self.filename:
            self.load_data()
            # Enable 'Add Record' menu item
            self.file_menu.entryconfig("Добавить запись", state="normal")

    def load_data(self):
        # Загрузка данных из базы данных Poldb
        try:
            with open(self.filename, 'rb') as file:
                # Чтение заголовка
                header = file.read(18)
                magic, version, num_columns, num_records, record_size, data_offset = struct.unpack('>4sHHIHI', header)

                # Проверка магического числа
                if magic != b'PLDB':
                    messagebox.showerror("Ошибка", "Неверный файл базы данных Poldb.")
                    return

                # Чтение метаданных столбцов
                self.columns = []
                self.key_columns = []
                for _ in range(num_columns):
                    col_data = file.read(36)
                    col_name, type_code, col_size, is_key = struct.unpack('>32sBHB', col_data)
                    col_name = col_name.decode('utf-8').rstrip('\0')
                    self.columns.append((col_name, type_code, col_size))
                    if is_key:
                        self.key_columns.append(col_name)
                # Удаляем тег 'found' с всех элементов
                for item_id in self.tree.get_children():
                    tags = self.tree.item(item_id, 'tags')
                    if 'found' in tags:
                        tags = tuple(tag for tag in tags if tag != 'found')
                        self.tree.item(item_id, tags=tags)

                # Очистка существующих данных в Treeview
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Настройка столбцов Treeview без использования опции style
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
                self.data_indices = []
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

                    # Вставляем данные в Treeview без использования стилей
                    item_values = [record[col[0]] for col in self.columns]
                    self.tree.insert('', tk.END, values=item_values)
                    self.data_indices.append(record_pos)
                self.master.title(f"Poldb Database Viewer - {os.path.basename(self.filename)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить базу данных:\n{e}")

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

            # Очистка предыдущего выделения
            for item_id in self.tree.get_children():
                self.tree.item(item_id, tags=())  # Удаляем все теги

            # Поиск и выделение найденных записей
            found_count = 0
            for item_id in self.tree.get_children():
                value = self.tree.set(item_id, column_name)
                try:
                    if type_code == 1:
                        value = int(value)
                    elif type_code == 2:
                        value = float(value)
                    elif type_code == 3:
                        value = str(value)
                except ValueError:
                    continue  # Пропускаем, если значение нельзя привести к нужному типу

                if value == search_value:
                    # Устанавливаем тег 'found' для выделения
                    self.tree.item(item_id, tags=('found',))
                    found_count += 1

            # Отображаем сообщение с количеством найденных записей
            if found_count > 0:
                messagebox.showinfo("Результаты поиска", f"Найдено {found_count} соответствующих записей.")
            else:
                messagebox.showinfo("Результаты поиска", "Записи не найдены.")

            search_window.destroy()

        search_button = tk.Button(search_window, text="Найти", command=perform_search)
        search_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Убираем функцию save_changes, так как изменения сохраняются сразу в файл
if __name__ == "__main__":
    root = tk.Tk()
    app = PoldbGUI(root)
    root.mainloop()



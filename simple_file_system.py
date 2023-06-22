import os
import pickle
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk


class FileSystem:
    def __init__(self):
        self.bitmap = [0] * 1024
        self.fat = {}
        self.root = {'entries': {}}

    def create(self, path, content):
        size = len(content)
        # Find free space
        start = None
        count = 0
        for i, bit in enumerate(self.bitmap):
            if bit == 0:
                if start is None:
                    start = i
                count += 1
                if count >= size:
                    break
            else:
                start = None
                count = 0

        if count < size:
            return False

        # Update bitmap and FAT
        for i in range(start, start + size):
            self.bitmap[i] = 1
        address = start * 1024
        self.fat[path] = {'address': address, 'length': size, 'content': content}

        # Update directory entries
        dirs = path.split('/')
        current = self.root
        for d in dirs[:-1]:
            if d not in current['entries']:
                current['entries'][d] = {'entries': {}}
            current = current['entries'][d]
        current['entries'][dirs[-1]] = self.fat[path]

        return True

    def delete(self, path):
        if path not in self.fat:
            return False

        # Update bitmap and FAT
        start = self.fat[path]['address'] // 1024
        size = self.fat[path]['length']
        for i in range(start, start + size):
            self.bitmap[i] = 0
        del self.fat[path]

        # Update directory entries
        dirs = path.split('/')
        current = self.root
        for d in dirs[:-1]:
            current = current['entries'][d]
        del current['entries'][dirs[-1]]

        # Set file length to 0
        self.fat[path] = {'address': None, 'length': 0}

        return True

    def read(self, path):
        if path not in self.fat:
            return None
        return {'length': self.fat[path]['length'], 'content': self.fat[path]['content']}

    def write(self, path, content):
        # Delete original file
        self.delete(path)

        # Create new file
        if not self.create(path, content):
            return False

        return True


class FileSystemGUI(tk.Tk):
    def __init__(self, file_system):
        super().__init__()
        self.file_system = file_system
        self.title("Simple File System")
        self.geometry("400x610")

        self.create_widgets()

    def create_widgets(self):
        self.help_button = tk.Button(self, text="info", bg='blue', fg='white', command=self.show_help)
        self.help_button.grid(row=0, column=2, padx=0, pady=5)

        self.path_label = tk.Label(self, text="File path:")
        self.path_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.path_entry = tk.Entry(self)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        self.content_label = tk.Label(self, text="File content:")
        self.content_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.content_entry = tk.Entry(self)
        self.content_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=2, column=0, padx=50, pady=5, columnspan=4, sticky='w')
        self.create_button = tk.Button(self.button_frame, text="创建", command=self.create_file)
        self.create_button.grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        self.delete_button = tk.Button(self.button_frame, text="删除", command=self.delete_file)
        self.delete_button.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.read_button = tk.Button(self.button_frame, text="读取", command=self.read_file)
        self.read_button.grid(row=2, column=2, padx=5, pady=5, sticky='ew')
        self.write_button = tk.Button(self.button_frame, text="写入", command=self.write_file)
        self.write_button.grid(row=2, column=3, padx=5, pady=5, sticky='ew')
        self.reset_button = tk.Button(self.button_frame, text="重置文件系统", command=self.reset_filesystem)
        self.reset_button.grid(row=2, column=4, padx=5, pady=5, sticky='ew')

        self.file_tree = ttk.Treeview(self, height=10)
        self.file_tree.grid(row=5, column=0, padx=5, pady=5, columnspan=2)

        self.file_tree_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.file_tree.yview)
        self.file_tree_scrollbar.grid(row=5, column=2, pady=5, sticky='ns')
        self.file_tree.configure(yscrollcommand=self.file_tree_scrollbar.set)

        self.memory_usage_label = tk.Label(self, text="空闲空间管理:")
        self.memory_usage_label.grid(row=6, column=0, padx=5, pady=5, sticky='w')

        self.memory_usage = tk.Text(self, wrap=tk.WORD, height=15, width=50)
        self.memory_usage.grid(row=7, column=0, padx=5, pady=1, columnspan=2)
        self.memory_usage.config(state=tk.DISABLED)

        self.file_tree.bind('<<TreeviewSelect>>', self.fill_path_from_tree)
        self.file_tree.bind('<Double-Button-1>', self.read_file_from_tree)

        self.update_display()

    def show_help(self):
        help_text = (
            "1. 运行程序后，您将看到一个图形界面，中间是是树状文件结构视图，下方是存储空间使用情况。\n\n"
            "2. 要创建一个文件，请输入文件路径（例如file或者dir1/file1等）和文件内容，然后单击“创建”按钮。如果操作成功，您将看到文件已添加到树状视图中，并且存储空间使用情况有所更新。点击对应的目录会自动填充路径。\n\n"
            "3. 要删除一个文件，请在树状视图中单击选择要删除的文件（因为支持自动填充），也可以手动输入路径，然后单击工具栏上的“删除”按钮。如果操作成功，您将看到文件已从树状视图中删除，并且存储空间使用情况有所更新。\n\n"
            "4. 要读取一个文件，请在树状视图中双击选择要读取的文件，您也可以单击工具栏上的“读取”按钮。在弹出的对话框中，您将看到文件的位置、大小、内容。\n\n"
            "5. 要写入一个文件，请在树状视图中选择要写入的文件（因为支持自动填充），也可以手动输入路径，输入新的文件内容，然后单击工具栏上的“写入”按钮。如果操作成功，您将看到存储空间使用情况有所更新。\n\n"
            "6. 要重置文件系统，请单击工具栏上的“重置文件系统”按钮。这将清除所有文件和目录，并重置存储空间使用情况。\n\n"
            "7. 要退出程序，请单击右上角的叉号，文件系统的信息会被保存，下次运行会自动恢复。"
        )
        messagebox.showinfo("使用说明", help_text)

    def reset_filesystem(self):
        self.file_system = FileSystem()
        messagebox.showinfo("Success", "File system reset.")
        self.update_display()

    def fill_path_from_tree(self, event):
        def get_path(node):
            parent = self.file_tree.parent(node)
            if parent:
                return get_path(parent) + '/' + self.file_tree.item(node, 'text')
            else:
                return self.file_tree.item(node, 'text')

        selected_item = self.file_tree.selection()
        if selected_item:
            path = get_path(selected_item[0])
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def read_file_from_tree(self, event):
        selected_item = self.file_tree.selection()
        if selected_item:
            path = self.get_path_from_tree(selected_item[0])
            self.read_file()
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def get_path_from_tree(self, node):
        parent = self.file_tree.parent(node)
        if parent:
            return self.get_path_from_tree(parent) + '/' + self.file_tree.item(node, 'text')
        else:
            return self.file_tree.item(node, 'text')

    def update_display(self):
        self.memory_usage.config(state=tk.NORMAL)

        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        self.memory_usage.delete('1.0', tk.END)

        self.display_file_structure(self.file_system.root)
        self.display_memory_usage()

        self.memory_usage.config(state=tk.DISABLED)

    def display_file_structure(self, current, parent=''):
        for entry, data in current['entries'].items():
            if 'address' in data:
                node_id = self.file_tree.insert(parent, 'end', text=entry, tags='file')
            else:
                node_id = self.file_tree.insert(parent, 'end', text=entry, tags='directory')
                self.file_tree.item(node_id, open=True)  # 展开目录
                self.display_file_structure(data, node_id)

    def display_memory_usage(self):
        for i, bit in enumerate(self.file_system.bitmap):
            self.memory_usage.insert(tk.END, str(bit))
            if (i + 1) % 32 == 0:
                self.memory_usage.insert(tk.END, '\n')

    def create_file(self):
        path = self.path_entry.get()
        content = self.content_entry.get()  # Assuming content is input in the content_entry field
        if not path or not content:
            messagebox.showerror("Error", "Please input path and content.")
            return
        if self.file_system.create(path, content):
            messagebox.showinfo("Success", "File created.")
            self.update_display()
        else:
            messagebox.showerror("Error", "Failed to create file.")

    def delete_file(self):
        path = self.path_entry.get()
        if not path:
            messagebox.showerror("Error", "Please input path.")
            return
        if self.file_system.delete(path):
            messagebox.showinfo("Success", "File deleted.")
            self.update_display()
        else:
            messagebox.showerror("Error", "Failed to delete file.")

    def read_file(self):
        path = self.path_entry.get()
        if not path:
            messagebox.showerror("Error", "Please input path.")
            return
        file_info = self.file_system.read(path)
        if file_info:
            messagebox.showinfo("File Info",
                                f"Address: {self.file_system.fat[path]['address']}\nLength: {file_info['length']}\nContent: {file_info['content']}")
        else:
            messagebox.showerror("Error", "Failed to read file.")

    def write_file(self):
        path = self.path_entry.get()
        content = self.content_entry.get()
        if not path or not content:
            messagebox.showerror("Error", "Please input path and content.")
            return
        if self.file_system.write(path, content):
            messagebox.showinfo("Success", "File updated.")
            self.update_display()
        else:
            messagebox.showerror("Error", "Failed to write file.")


def main():
    # Load the file system from disk (if it exists)
    if os.path.exists('filesystem.pickle'):
        with open('filesystem.pickle', 'rb') as f:
            file_system = pickle.load(f)
    else:
        file_system = FileSystem()

    fs_gui = FileSystemGUI(file_system)
    fs_gui.protocol("WM_DELETE_WINDOW", fs_gui.quit)
    fs_gui.mainloop()

    # Save the file system to disk
    with open("filesystem.pickle", "wb") as f:
        pickle.dump(fs_gui.file_system, f)


if __name__ == "__main__":
    main()


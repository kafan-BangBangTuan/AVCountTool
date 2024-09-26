import os
import sys
import hashlib
import threading
import queue
from tkinter import (
    Tk, Frame, Label, Text, Button, Scrollbar, filedialog,
    messagebox, END, BOTH, LEFT, RIGHT, Y, X, TOP, BOTTOM
)

class WorkerThread(threading.Thread):
    def __init__(self, directory, result_queue):
        super().__init__()
        self.directory = directory
        self.result_queue = result_queue
        self.md5_dict = {}

    def run(self):
        self.md5_dict = self.walk_directory(self.directory)
        file_count = len(self.md5_dict)
        self.result_queue.put(('update_file_count', file_count, self.md5_dict))

    def walk_directory(self, directory):
        md5_dict = {}
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'rb') as f:
                        md5 = hashlib.md5(f.read()).hexdigest()
                        md5_dict[filepath] = md5
                except Exception as e:
                    # 可以选择在日志中记录无法读取的文件
                    pass
        return md5_dict

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('杀毒软件查杀个数统计工具  by:123456aaaafsdeg')
        self.setup_ui()
        self.worker = None
        self.initial_md5_dict = {}
        self.result_queue = queue.Queue()
        self.check_queue()

    def setup_ui(self):
        # 获取屏幕尺寸并设置窗口大小
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(800, screen_width - 200)
        window_height = min(600, screen_height - 200)
        self.root.geometry(f"{window_width}x{window_height}+100+100")

        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # 杀毒软件部分
        label1 = Label(main_frame, text='杀毒软件：')
        label1.pack(anchor='w')

        self.edit1 = Text(main_frame, height=2)
        self.edit1.pack(fill=X, pady=(0, 10))
        self.edit1.insert(END, '请输入杀毒软件名称')
        self.edit1.bind("<FocusIn>", self.clear_placeholder1)

        # 目录选择部分
        label2 = Label(main_frame, text='目录：')
        label2.pack(anchor='w')

        dir_frame = Frame(main_frame)
        dir_frame.pack(fill=X, pady=(0, 10))

        self.edit2 = Text(dir_frame, height=2)
        self.edit2.pack(side=LEFT, fill=X, expand=True)
        self.edit2.insert(END, '请选择目录')
        self.edit2.bind("<FocusIn>", self.clear_placeholder2)

        btn_select = Button(dir_frame, text='选择目录', command=self.select_directory)
        btn_select.pack(side=LEFT, padx=(5, 0))

        # 输出日志部分
        label3 = Label(main_frame, text='输出：')
        label3.pack(anchor='w')

        text_frame = Frame(main_frame)
        text_frame.pack(fill=BOTH, expand=True)

        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.edit3 = Text(text_frame, wrap='none', yscrollcommand=scrollbar.set, state='disabled')
        self.edit3.pack(fill=BOTH, expand=True)
        scrollbar.config(command=self.edit3.yview)

        # 按钮部分
        btn_frame = Frame(main_frame)
        btn_frame.pack(fill=X, pady=(10, 0))

        self.btn_first_stat = Button(btn_frame, text='首次统计', command=self.first_stat)
        self.btn_first_stat.pack(side=LEFT, expand=True, fill=X, padx=(0,5))

        self.btn_continue_stat = Button(btn_frame, text='继续统计', command=self.continue_stat, state='disabled')
        self.btn_continue_stat.pack(side=LEFT, expand=True, fill=X, padx=5)

        self.btn_export_log = Button(btn_frame, text='导出日志', command=self.export_log)
        self.btn_export_log.pack(side=LEFT, expand=True, fill=X, padx=(5,0))

    def clear_placeholder1(self, event):
        current_text = self.edit1.get("1.0", END).strip()
        if current_text == '请输入杀毒软件名称':
            self.edit1.delete("1.0", END)

    def clear_placeholder2(self, event):
        current_text = self.edit2.get("1.0", END).strip()
        if current_text == '请选择目录':
            self.edit2.delete("1.0", END)

    def select_directory(self):
        directory = filedialog.askdirectory(title="选择目录")
        if directory:
            self.edit2.config(state='normal')
            self.edit2.delete("1.0", END)
            self.edit2.insert(END, directory)
            self.edit2.config(state='disabled')

    def first_stat(self):
        antivirus_name = self.edit1.get("1.0", END).strip()
        directory = self.edit2.get("1.0", END).strip()

        if not antivirus_name or antivirus_name == '请输入杀毒软件名称':
            messagebox.showerror('错误', '请填写杀毒软件')
            return
        if not directory or directory == '请选择目录':
            messagebox.showerror('错误', '请选择目录')
            return
        if not os.path.exists(directory):
            messagebox.showerror('错误', '目录不存在，请重新选择')
            return
        if not os.access(directory, os.R_OK):
            messagebox.showerror('错误', '目录不可读取，请重新选择')
            return

        self.edit3.config(state='normal')
        self.edit3.delete("1.0", END)
        self.edit3.insert(END, f"杀毒软件：{antivirus_name}\n")
        self.edit3.insert(END, f"文件夹：{directory}\n")
        self.edit3.config(state='disabled')

        # 启动后台线程
        self.worker = WorkerThread(directory, self.result_queue)
        self.worker.start()

        messagebox.showinfo('提示', '首次统计已完成，请使用杀毒软件查杀并处理')
        self.btn_continue_stat.config(state='normal')

    def update_file_count(self, file_count, md5_dict):
        self.edit3.config(state='normal')
        self.edit3.insert(END, f"文件数量：{file_count}\n")
        self.edit3.insert(END, "===========================================================\n\n")
        self.edit3.config(state='disabled')
        self.initial_md5_dict = md5_dict.copy()

    def continue_stat(self):
        directory = self.edit2.get("1.0", END).strip()

        if not os.path.exists(directory):
            messagebox.showerror('错误', '目录不存在，请重新选择')
            return
        if not os.access(directory, os.R_OK):
            messagebox.showerror('错误', '目录不可读，请重新选择')
            return

        response = messagebox.askquestion('提示', '杀毒软件是否查杀完成？', icon='question')
        if response != 'yes':
            return

        # 计算当前目录的MD5
        current_md5_dict = {}
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'rb') as f:
                            md5 = hashlib.md5(f.read()).hexdigest()
                            current_md5_dict[filepath] = md5
                    except:
                        pass
        except Exception as e:
            messagebox.showerror('错误', f'读取目录时出错: {e}')
            return

        remaining_files = [f for f in self.initial_md5_dict if f in current_md5_dict]
        deleted_files = [f for f in self.initial_md5_dict if f not in current_md5_dict]
        changed_files = [f for f in remaining_files if self.initial_md5_dict[f] != current_md5_dict[f]]

        self.edit3.config(state='normal')
        self.edit3.insert(END, "\n删除个数：{}\n".format(len(deleted_files)))
        self.edit3.insert(END, "清除个数：{}\n".format(len(changed_files)))
        self.edit3.insert(END, "剩余个数：{}\n".format(len(remaining_files)))
        self.edit3.insert(END, "\n===========================================================\n\n")

        for file in remaining_files:
            if file in changed_files:
                self.edit3.insert(END, f"{file} -- 已清除\n")
            else:
                self.edit3.insert(END, f"{file} -- 未检出\n")
        for file in deleted_files:
            self.edit3.insert(END, f"{file} -- 已检出\n")

        self.edit3.config(state='disabled')

    def export_log(self):
        log_content = self.edit3.get("1.0", END).strip()
        if not log_content:
            messagebox.showwarning('警告', '日志内容为空，无法导出。')
            return

        file_path = filedialog.asksaveasfilename(
            title='导出日志',
            defaultextension='.txt',
            filetypes=[('Text Files', '*.txt')]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo('成功', '日志已成功导出。')
            except Exception as e:
                messagebox.showerror('错误', f'导出日志时出错: {e}')

    def check_queue(self):
        try:
            while True:
                message = self.result_queue.get_nowait()
                if message[0] == 'update_file_count':
                    _, file_count, md5_dict = message
                    self.update_file_count(file_count, md5_dict)
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)  # 每100毫秒检查一次队列

if __name__ == '__main__':
    root = Tk()
    app = App(root)
    root.mainloop()

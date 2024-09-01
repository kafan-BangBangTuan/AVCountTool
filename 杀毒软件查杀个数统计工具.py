import sys
import hashlib
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox, QDesktopWidget)
from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    update_signal = pyqtSignal(int)

    def __init__(self, directory, parent=None):
        super(Worker, self).__init__(parent)
        self.directory = directory
        self.md5_dict = {}

    def run(self):
        self.md5_dict = self.walk_directory(self.directory)
        file_count = len(self.md5_dict)
        self.update_signal.emit(file_count)

    def walk_directory(self, directory):
        md5_dict = {}
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                with open(filepath, 'rb') as f:
                    md5_dict[filepath] = hashlib.md5(f.read()).hexdigest()
        return md5_dict

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()
        self.worker = None
        self.initial_md5_dict = {}

    def initUI(self):
        self.setWindowTitle('杀毒软件查杀个数统计工具  by:123456aaaafsdeg')
        layout = QVBoxLayout(self)

        # 获取屏幕的尺寸
        screen = QDesktopWidget().screenGeometry()
        screenWidth = screen.width()
        screenHeight = screen.height()

        # 设置窗口大小
        self.setGeometry(100, 100, min(800, screenWidth - 200), min(600, screenHeight - 200))

        # 杀毒软件
        self.label1 = QLabel('杀毒软件：')
        self.edit1 = QTextEdit()
        self.edit1.setPlaceholderText('请输入杀毒软件名称')
        self.edit1.setMaximumHeight(50)  # 设置最大高度
        layout.addWidget(self.label1)
        layout.addWidget(self.edit1)

        # 目录
        self.label2 = QLabel('目录：')
        self.edit2 = QTextEdit()
        self.edit2.setPlaceholderText('请选择目录')
        self.edit2.setMaximumHeight(50)  # 设置最大高度
        self.btn_select = QPushButton('选择目录')
        self.btn_select.clicked.connect(self.select_directory)
        layout.addWidget(self.label2)
        layout.addWidget(self.edit2)
        layout.addWidget(self.btn_select)

        # 输出
        self.edit3 = QTextEdit()
        self.edit3.setReadOnly(True)
        layout.addWidget(self.edit3)
        layout.setStretchFactor(self.edit3, 10) 

        # 按钮
        self.btn_first_stat = QPushButton('首次统计')
        self.btn_first_stat.clicked.connect(self.first_stat)
        self.btn_continue_stat = QPushButton('继续统计')
        self.btn_continue_stat.clicked.connect(self.continue_stat)
        self.btn_export_log = QPushButton('导出日志')
        self.btn_export_log.clicked.connect(self.export_log)

        self.btn_first_stat.setEnabled(True)
        self.btn_continue_stat.setEnabled(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_first_stat)
        btn_layout.addWidget(self.btn_continue_stat)
        btn_layout.addWidget(self.btn_export_log)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.edit2.setText(directory)

    def first_stat(self):
        antivirus_name = self.edit1.toPlainText().strip()
        directory = self.edit2.toPlainText().strip()

        if not antivirus_name:
            QMessageBox.critical(self, '错误', '请填写杀毒软件')
            return
        if not directory:
            QMessageBox.critical(self, '错误', '请选择目录')
            return
        if not os.path.exists(directory):
            QMessageBox.critical(self, '错误', '目录不存在，请重新选择')
            return
        if not os.access(directory, os.R_OK):
            QMessageBox.critical(self, '错误', '目录不可读取，请重新选择')
            return

        self.edit3.clear()
        self.edit3.append(f"杀毒软件：{antivirus_name}")
        self.edit3.append(f"文件夹：{directory}")

        self.worker = Worker(directory)
        self.worker.update_signal.connect(self.update_file_count)
        self.worker.start()

        QMessageBox.information(self, '提示', '首次统计已完成，请使用杀毒软件查杀并处理')
        self.btn_continue_stat.setEnabled(True)

    def update_file_count(self, file_count):
        self.edit3.append(f"文件数量：{file_count}")
        
        self.edit3.append(f"===========================================================")
        self.edit3.append(f"")
        self.initial_md5_dict = self.worker.md5_dict.copy()

    def continue_stat(self):
        directory = self.edit2.toPlainText().strip()

        if not os.path.exists(directory):
            QMessageBox.critical(self, '错误', '目录不存在，请重新选择')
            return
        if not os.access(directory, os.R_OK):
            QMessageBox.critical(self, '错误', '目录不可读，请重新选择')
            return

        response = QMessageBox.question(self, '提示', '杀毒软件是否查杀完成？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.No:
            return

        current_md5_dict = Worker(directory).walk_directory(directory)
        remaining_files = [f for f in self.initial_md5_dict if f in current_md5_dict]
        deleted_files = [f for f in self.initial_md5_dict if f not in current_md5_dict]
        changed_files = [f for f in remaining_files if self.initial_md5_dict[f] != current_md5_dict[f]]
        
        self.edit3.append(f"")
        self.edit3.append(f"删除个数：{len(deleted_files)}")
        self.edit3.append(f"清除个数：{len(changed_files)}")
        self.edit3.append(f"剩余个数：{len(remaining_files)}")
        
        self.edit3.append(f"")
        self.edit3.append(f"===========================================================")
        self.edit3.append(f"")
        for file in remaining_files:
            if file in changed_files:
                self.edit3.append(f"{file} -- 已清除")
            else:
                self.edit3.append(f"{file} -- 未检出")
        for file in deleted_files:
            self.edit3.append(f"{file} -- 已检出")

    def export_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, '导出日志', '', 'Text Files (*.txt)')
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.edit3.toPlainText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
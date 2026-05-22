#!/usr/bin/python3

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QGroupBox
)
from PyQt5.QtCore import Qt, QDir, QDirIterator
from PyQt5.QtGui import QFont


class CSVGeneratorWindow(QMainWindow):
    def __init__(self, default_dir: str = ""):
        super().__init__()
        self.setWindowTitle("Generate Initial CSV Dataset")
        self.resize(700, 480)
        self.generated_csv_path = None

        self.default_dir = default_dir

        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # ==================== ROOT DIRECTORY ====================
        group_dir = QGroupBox("1. Root Directory (Recursive)")
        form1 = QFormLayout()
        form1.setLabelAlignment(Qt.AlignRight)

        self.btn_dir = QPushButton("Select Root Directory")
        self.btn_dir.clicked.connect(self.select_root_dir)
        self.line_dir = QLineEdit()
        self.line_dir.setMinimumHeight(38)
        #self.line_dir.setFont(QFont("", 11))
        if self.default_dir:
            self.line_dir.setText(self.default_dir)

        h_dir = QHBoxLayout()
        h_dir.addWidget(self.line_dir)
        form1.addRow(self.btn_dir, h_dir)

        group_dir.setLayout(form1)
        layout.addWidget(group_dir)

        # ==================== FILTER ====================
        group_filter = QGroupBox("2. File Filter")
        form2 = QFormLayout()

        self.line_filter = QLineEdit("*.png *.jpg *.jpeg *.bmp")
        #self.line_filter.setFont(QFont("", 11))
        self.line_filter.setMinimumHeight(38)
        form2.addRow("Extensions (space separated):", self.line_filter)

        group_filter.setLayout(form2)
        layout.addWidget(group_filter)

        # ==================== OUTPUT CSV ====================
        group_out = QGroupBox("3. Output CSV File")
        form3 = QFormLayout()

        self.btn_output = QPushButton("Select Output CSV")
        self.btn_output.clicked.connect(self.select_output_csv)
        self.line_output = QLineEdit()
        self.line_output.setMinimumHeight(38)
        #self.line_output.setFont(QFont("", 11))
        self.line_output.setPlaceholderText("/path/to/dataset_labels.csv")

        h_out = QHBoxLayout()
        h_out.addWidget(self.line_output)
        form3.addRow(self.btn_output, h_out)

        group_out.setLayout(form3)
        layout.addWidget(group_out)

        # ==================== COLUMN NAMES ====================
        group_cols = QGroupBox("4. Column Names in CSV")
        form4 = QFormLayout()

        self.line_col_filepath = QLineEdit("filepath")
        self.line_col_filepath.setMinimumHeight(36)
        self.line_col_label = QLineEdit("label")
        self.line_col_label.setMinimumHeight(36)

        form4.addRow("Filepath Column:", self.line_col_filepath)
        form4.addRow("Label Column:", self.line_col_label)

        group_cols.setLayout(form4)
        layout.addWidget(group_cols)

        # ==================== PROGRESS ====================
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # ==================== BUTTONS ====================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_generate = QPushButton("Generate CSV")
        #self.btn_generate.setFont(QFont("", 12, QFont.Bold))
        self.btn_generate.clicked.connect(self.generate_csv)

        self.btn_finish = QPushButton("Finish & Return")
        #self.btn_finish.setFont(QFont("", 12))
        self.btn_finish.clicked.connect(self.finish_and_return)

        btn_layout.addWidget(self.btn_generate)
        btn_layout.addWidget(self.btn_finish)
        layout.addLayout(btn_layout)

    def select_root_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Root Directory", self.line_dir.text())
        if dir_path:
            self.line_dir.setText(dir_path)

    def select_output_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
            self.line_output.setText(file_path)

    def generate_csv(self):
        root_dir = self.line_dir.text().strip()
        output_csv = self.line_output.text().strip()
        filter_text = self.line_filter.text().strip()

        if not root_dir or not os.path.exists(root_dir):
            QMessageBox.warning(self, "Error", "Please select a valid root directory!")
            return
        if not output_csv:
            QMessageBox.warning(self, "Error", "Please specify output CSV file!")
            return

        self.btn_generate.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        QApplication.processEvents()

        try:
            # Prepare filters
            filters = filter_text.split() if filter_text else ["*.png", "*.jpg", "*.jpeg", "*.bmp"]
            if not any(f.startswith("*.") for f in filters):
                filters = ["*." + f.strip("*.") for f in filters]

            # Recursive search
            images = []
            it = QDirIterator(root_dir, filters, QDir.Files, QDirIterator.Subdirectories)
            while it.hasNext():
                file_path = it.next()
                rel_path = QDir(root_dir).relativeFilePath(file_path)
                images.append(rel_path)
                self.progress.setValue(min(len(images) % 1000, 100))
                QApplication.processEvents()

            if not images:
                QMessageBox.warning(self, "Warning", "No images found with the specified filters!")
                self.btn_generate.setEnabled(True)
                return

            # Sort naturally
            images.sort(key=natural_sort_key)

            # Write CSV
            col_filepath = self.line_col_filepath.text().strip() or "filepath"
            col_label = self.line_col_label.text().strip() or "label"

            with open(output_csv, "w", encoding="utf-8", newline="") as f:
                f.write(f"{col_filepath},{col_label}\n")
                for img in images:
                    f.write(f"{img},\n")   # label vazio

            self.generated_csv_path = output_csv

            QMessageBox.information(self, "Success", 
                                  f"CSV generated successfully!\n\n"
                                  f"Total images: {len(images)}\n"
                                  f"File: {output_csv}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate CSV:\n{str(e)}")
        finally:
            self.btn_generate.setEnabled(True)
            self.progress.setVisible(False)

    def finish_and_return(self):
        if self.generated_csv_path:
            self.close()
        else:
            reply = QMessageBox.question(self, "Exit", 
                                         "No CSV was generated. Close anyway?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.close()

    def closeEvent(self, event):
        if self.generated_csv_path:
            event.accept()
        else:
            reply = QMessageBox.question(self, "Exit", 
                                         "Close without generating CSV?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()


def natural_sort_key(s):
    import re
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Permite passar diretório como argumento
    default_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    
    window = CSVGeneratorWindow(default_dir)
    window.show()
    app.exec_()
    
    # Se quiser retornar o caminho via stdout (útil para chamar de outro programa)
    if window.generated_csv_path:
        print(f"CSV_GENERATED:{window.generated_csv_path}")

import sys
import math
import json
import csv
import logging

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QStackedWidget,
    QSplitter, QGroupBox, QFileDialog,
    QShortcut  # <-- добавлен импорт QShortcut
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QDoubleValidator, QKeySequence  # <-- добавлен QKeySequence

from database import DatabaseManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("calc.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор площади и периметра")
        self.resize(1000, 700)
        self.setMinimumSize(900, 600)

        # Инициализация настроек
        self.settings = QSettings("MyCompany", "AreaPerimeterCalc")

        # Инициализация БД
        self.db = DatabaseManager()

        self._setup_ui()
        self._bind_signals()

        # Восстановление геометрии и состояния
        self.restore_geometry()

        # Восстановление выбранной фигуры и единиц
        figure_index = self.settings.value("figure_index", 0, type=int)
        if 0 <= figure_index < self.figure_combo.count():
            self.figure_combo.setCurrentIndex(figure_index)

        unit_index = self.settings.value("unit_index", 0, type=int)
        if 0 <= unit_index < self.unit_combo.count():
            self.unit_combo.setCurrentIndex(unit_index)

        # Восстановление темы
        theme = self.settings.value("theme", "light")
        self.apply_theme(theme)
        idx = 0 if theme == "light" else 1
        self.theme_combo.setCurrentIndex(idx)

        self._refresh_history()

        logging.info("Приложение запущено.")

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая панель
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        title = QLabel("Расчёт площади и периметра")
        title.setObjectName("mainTitle")
        left_layout.addWidget(title)

        # Блок выбора фигуры и единиц
        selector_layout = QHBoxLayout()
        self.figure_combo = QComboBox()
        self.figure_combo.addItems([
            "Прямоугольник", "Квадрат", "Круг",
            "Треугольник", "Параллелограмм", "Трапеция", "Ромб"
        ])
        selector_layout.addWidget(QLabel("Фигура:"))
        selector_layout.addWidget(self.figure_combo)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["см", "м"])
        selector_layout.addWidget(QLabel("Единицы:"))
        selector_layout.addWidget(self.unit_combo)
        selector_layout.addStretch()

        left_layout.addLayout(selector_layout)

        # Стек параметров
        self.params_stack = QStackedWidget()
        self._create_param_widgets()
        left_layout.addWidget(self.params_stack)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_calc = QPushButton("Рассчитать")
        self.btn_calc.setObjectName("calcBtn")
        self.btn_clear = QPushButton("Очистить поля")
        btn_layout.addWidget(self.btn_calc)
        btn_layout.addWidget(self.btn_clear)
        left_layout.addLayout(btn_layout)

        # Результат
        result_group = QGroupBox("Результат")
        result_layout = QVBoxLayout(result_group)
        self.lbl_area = QLabel("Площадь: —")
        self.lbl_perimeter = QLabel("Периметр: —")
        result_layout.addWidget(self.lbl_area)
        result_layout.addWidget(self.lbl_perimeter)
        left_layout.addWidget(result_group)

        # Блок настроек (тема)
        bonus_group = QGroupBox("Настройки")
        bonus_layout = QVBoxLayout(bonus_group)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        theme_layout.addWidget(self.theme_combo)
        bonus_layout.addLayout(theme_layout)

        left_layout.addWidget(bonus_group)
        left_layout.addStretch()

        # Правая панель (история)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        history_title = QLabel("История вычислений")
        history_title.setObjectName("historyTitle")
        right_layout.addWidget(history_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Фигура", "Параметры", "Площадь", "Периметр", "Дата"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        right_layout.addWidget(self.history_table)

        # Кнопки управления историей + экспорт/импорт
        hist_btn_layout = QHBoxLayout()
        self.btn_delete_selected = QPushButton("Удалить выбранную")
        self.btn_clear_history = QPushButton("Очистить всё")
        hist_btn_layout.addWidget(self.btn_delete_selected)
        hist_btn_layout.addWidget(self.btn_clear_history)

        self.btn_export_csv = QPushButton("Экспорт CSV")
        self.btn_export_json = QPushButton("Экспорт JSON")
        self.btn_import_csv = QPushButton("Импорт CSV")
        self.btn_import_json = QPushButton("Импорт JSON")
        hist_btn_layout.addWidget(self.btn_export_csv)
        hist_btn_layout.addWidget(self.btn_export_json)
        hist_btn_layout.addWidget(self.btn_import_csv)
        hist_btn_layout.addWidget(self.btn_import_json)

        right_layout.addLayout(hist_btn_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 550])
        main_layout.addWidget(splitter)

        # Применяем стиль по умолчанию (светлый)
        self._apply_styles("light")

        # ---------- Горячие клавиши (добавлены в этом коммите) ----------
        # Ctrl+Enter -> Рассчитать
        self.shortcut_calc = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_calc.activated.connect(self._calculate)

        # Ctrl+Shift+C -> Очистить поля
        self.shortcut_clear = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.shortcut_clear.activated.connect(self._clear_fields)

        # Del -> Удалить выбранную запись из истории
        self.shortcut_delete = QShortcut(QKeySequence("Del"), self)
        self.shortcut_delete.activated.connect(self._delete_selected_history)

        # Ctrl+Q -> Выход (с подтверждением)
        self.shortcut_exit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_exit.activated.connect(self.close)  # self.close вызывает closeEvent

    def _create_param_widgets(self):
        self.input_fields = {}
        figures_params = {
            "Прямоугольник": [("Длина", "a"), ("Ширина", "b")],
            "Квадрат": [("Сторона", "a")],
            "Круг": [("Радиус", "r")],
            "Треугольник": [("Сторона a", "a"), ("Сторона b", "b"), ("Сторона c", "c")],
            "Параллелограмм": [("Основание", "a"), ("Высота", "h"), ("Боковая сторона", "b")],
            "Трапеция": [("Основание a", "a"), ("Основание b", "b"), ("Высота", "h"),
                         ("Боковая сторона c", "c"), ("Боковая сторона d", "d")],
            "Ромб": [("Сторона", "a"), ("Высота", "h")]
        }
        for figure_type, params in figures_params.items():
            widget = QWidget()
            layout = QFormLayout(widget)
            fields = {}
            for label_text, param_name in params:
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(f"Введите {label_text.lower()}")
                validator = QDoubleValidator(0.0, 1e9, 5)
                line_edit.setValidator(validator)
                layout.addRow(label_text + ":", line_edit)
                fields[param_name] = line_edit
            self.input_fields[figure_type] = fields
            self.params_stack.addWidget(widget)
        self.params_stack.setCurrentIndex(0)

    def _apply_styles(self, theme="light"):
        """Применяет QSS стили в зависимости от темы."""
        if theme == "light":
            style = """
            QMainWindow { background-color: #f0f2f5; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 6px; margin-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { background-color: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton#calcBtn { background-color: #2196F3; }
            QPushButton#calcBtn:hover { background-color: #1e87db; }
            QPushButton#calcBtn:pressed { background-color: #1a78c2; }
            QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 6px; background-color: white; }
            QLineEdit:focus { border: 2px solid #2196F3; }
            QComboBox { border: 1px solid #ccc; border-radius: 4px; padding: 5px; background-color: white; }
            QComboBox:on { border: 2px solid #2196F3; }
            QTableWidget { gridline-color: #d0d0d0; background-color: white; alternate-background-color: #fafafa; }
            QTableWidget::item { background-color: white; color: black; }
            QTableWidget::item:selected { background-color: #cce5ff; color: black; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #ccc; font-weight: bold; color: black; }
            QTableCornerButton::section { background-color: #e0e0e0; border: 1px solid #ccc; }
            QLabel#mainTitle { font-size: 20px; font-weight: bold; color: #333; padding: 10px 0; }
            QLabel#historyTitle { font-size: 16px; font-weight: bold; color: #333; }
            QSplitter::handle { background-color: #d0d0d0; width: 2px; }
            QScrollBar:vertical { background: #f0f0f0; width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background: #c0c0c0; border-radius: 6px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #a0a0a0; }
            QScrollBar:horizontal { background: #f0f0f0; height: 12px; border-radius: 6px; }
            QScrollBar::handle:horizontal { background: #c0c0c0; border-radius: 6px; min-width: 20px; }
            QScrollBar::handle:horizontal:hover { background: #a0a0a0; }
            """
        else:  # dark
            style = """
            QMainWindow { background-color: #2b2b2b; }
            QGroupBox { font-weight: bold; border: 1px solid #555; border-radius: 6px; margin-top: 8px; color: #eee; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { background-color: #3a3a3a; color: #eee; border: 1px solid #555; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton:pressed { background-color: #2a2a2a; }
            QPushButton#calcBtn { background-color: #1e88e5; }
            QPushButton#calcBtn:hover { background-color: #42a5f5; }
            QPushButton#calcBtn:pressed { background-color: #1565c0; }
            QLineEdit { border: 1px solid #555; border-radius: 4px; padding: 6px; background-color: #3c3c3c; color: #eee; }
            QLineEdit:focus { border: 2px solid #1e88e5; }
            QComboBox { border: 1px solid #555; border-radius: 4px; padding: 5px; background-color: #3c3c3c; color: #eee; }
            QComboBox:on { border: 2px solid #1e88e5; }
            QTableWidget {
                gridline-color: #555;
                background-color: #2b2b2b;
                alternate-background-color: #333333;
                color: #eee;
            }
            QTableWidget::item {
                background-color: #2b2b2b;
                color: #eee;
            }
            QTableWidget::item:selected {
                background-color: #1e88e5;
                color: white;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #eee;
                padding: 4px;
                border: 1px solid #555;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #3a3a3a;
                border: 1px solid #555;
            }
            QLabel#mainTitle { font-size: 20px; font-weight: bold; color: #eee; padding: 10px 0; }
            QLabel#historyTitle { font-size: 16px; font-weight: bold; color: #eee; }
            QSplitter::handle { background-color: #555; width: 2px; }
            QLabel { color: #eee; }
            QScrollBar:vertical { background: #3a3a3a; width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background: #5a5a5a; border-radius: 6px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #7a7a7a; }
            QScrollBar:horizontal { background: #3a3a3a; height: 12px; border-radius: 6px; }
            QScrollBar::handle:horizontal { background: #5a5a5a; border-radius: 6px; min-width: 20px; }
            QScrollBar::handle:horizontal:hover { background: #7a7a7a; }
            """
        self.setStyleSheet(style)

    def _bind_signals(self):
        self.figure_combo.currentIndexChanged.connect(self._on_figure_changed)
        self.btn_calc.clicked.connect(self._calculate)
        self.btn_clear.clicked.connect(self._clear_fields)
        self.btn_delete_selected.clicked.connect(self._delete_selected_history)
        self.btn_clear_history.clicked.connect(self._clear_all_history)
        self.btn_export_csv.clicked.connect(lambda: self._export_data("csv"))
        self.btn_export_json.clicked.connect(lambda: self._export_data("json"))
        self.btn_import_csv.clicked.connect(lambda: self._import_data("csv"))
        self.btn_import_json.clicked.connect(lambda: self._import_data("json"))

        # Тема
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)

    def _on_figure_changed(self, index):
        self.params_stack.setCurrentIndex(index)
        self._clear_fields()
        self.lbl_area.setText("Площадь: —")
        self.lbl_perimeter.setText("Периметр: —")

    def _on_theme_changed(self, theme_text):
        theme = "light" if theme_text == "Светлая" else "dark"
        self.apply_theme(theme)
        self.settings.setValue("theme", theme)

    def apply_theme(self, theme):
        self._apply_styles(theme)
        self.current_theme = theme

    def _get_current_figure(self):
        return self.figure_combo.currentText()

    def _get_current_unit(self):
        return self.unit_combo.currentText()

    def _get_params_from_ui(self):
        figure = self._get_current_figure()
        fields = self.input_fields.get(figure, {})
        params = {}
        for name, line_edit in fields.items():
            text = line_edit.text().strip()
            if not text:
                return None
            try:
                value = float(text)
                if value <= 0:
                    return None
                params[name] = value
            except ValueError:
                return None
        return params

    def _validate_triangle(self, params):
        a = params.get('a')
        b = params.get('b')
        c = params.get('c')
        if a is None or b is None or c is None:
            return False
        return (a + b > c) and (a + c > b) and (b + c > a)

    def _calculate(self):
        figure = self._get_current_figure()
        unit = self._get_current_unit()
        params = self._get_params_from_ui()
        if params is None:
            QMessageBox.warning(self, "Ошибка ввода",
                                "Пожалуйста, заполните все поля положительными числами.")
            return
        if figure == "Треугольник" and not self._validate_triangle(params):
            QMessageBox.warning(self, "Ошибка валидации",
                                "Не выполнено неравенство треугольника (сумма двух сторон должна быть больше третьей).")
            return

        area = None
        perimeter = None
        try:
            if figure == "Прямоугольник":
                a = params['a']; b = params['b']
                area = a * b
                perimeter = 2 * (a + b)
            elif figure == "Квадрат":
                a = params['a']
                area = a ** 2
                perimeter = 4 * a
            elif figure == "Круг":
                r = params['r']
                area = math.pi * r ** 2
                perimeter = 2 * math.pi * r
            elif figure == "Треугольник":
                a = params['a']; b = params['b']; c = params['c']
                s = (a + b + c) / 2
                area = math.sqrt(s * (s - a) * (s - b) * (s - c))
                perimeter = a + b + c
            elif figure == "Параллелограмм":
                a = params['a']; h = params['h']; b = params['b']
                area = a * h
                perimeter = 2 * (a + b)
            elif figure == "Трапеция":
                a = params['a']; b = params['b']; h = params['h']
                c = params['c']; d = params['d']
                area = (a + b) * h / 2
                perimeter = a + b + c + d
            elif figure == "Ромб":
                a = params['a']; h = params['h']
                area = a * h
                perimeter = 4 * a
        except Exception as e:
            logging.error(f"Ошибка вычисления: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить расчёт: {e}")
            return

        area_str = f"{area:.4f} {unit}²" if area is not None else "—"
        perim_str = f"{perimeter:.4f} {unit}" if perimeter is not None else "—"
        self.lbl_area.setText("Площадь: " + area_str)
        self.lbl_perimeter.setText("Периметр: " + perim_str)

        self.db.insert_record(figure, params, unit, area, perimeter)
        self._refresh_history()

        logging.info(f"Расчёт выполнен: {figure}, площадь={area}, периметр={perimeter}, единицы={unit}")

    def _clear_fields(self):
        figure = self._get_current_figure()
        fields = self.input_fields.get(figure, {})
        for line_edit in fields.values():
            line_edit.clear()
        self.lbl_area.setText("Площадь: —")
        self.lbl_perimeter.setText("Периметр: —")

    def _refresh_history(self):
        records = self.db.get_all_records()
        self.history_table.setRowCount(0)
        for i, rec in enumerate(records):
            self.history_table.insertRow(i)
            self.history_table.setItem(i, 0, QTableWidgetItem(rec['figure_type']))
            params = json.loads(rec['params'])
            unit = rec['unit']
            params_str = ', '.join(f"{k}={v:.2f}{unit}" if isinstance(v, float) else f"{k}={v}{unit}" for k, v in params.items())
            self.history_table.setItem(i, 1, QTableWidgetItem(params_str))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{rec['area']:.4f} {unit}²" if rec['area'] else "—"))
            self.history_table.setItem(i, 3, QTableWidgetItem(f"{rec['perimeter']:.4f} {unit}" if rec['perimeter'] else "—"))
            self.history_table.setItem(i, 4, QTableWidgetItem(rec['timestamp']))
            self.history_table.item(i, 0).setData(Qt.UserRole, rec['id'])

    def _delete_selected_history(self):
        selected = self.history_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Внимание", "Выберите запись для удаления.")
            return
        row = selected[0].row()
        item = self.history_table.item(row, 0)
        if not item:
            return
        record_id = item.data(Qt.UserRole)
        if QMessageBox.question(self, "Подтверждение", "Удалить выбранную запись?",
                                 QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_record(record_id)
            self._refresh_history()

    def _clear_all_history(self):
        if QMessageBox.question(self, "Подтверждение", "Удалить всю историю?",
                                 QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.clear_history()
            self._refresh_history()

    def _export_data(self, format_type):
        records = self.db.get_all_records()
        if not records:
            QMessageBox.information(self, "Экспорт", "Нет данных для экспорта.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", "",
            f"{format_type.upper()} files (*.{format_type})"
        )
        if not path:
            return
        try:
            if format_type == "csv":
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["figure_type", "params", "unit", "area", "perimeter", "timestamp"])
                    for rec in records:
                        writer.writerow([
                            rec['figure_type'],
                            rec['params'],
                            rec['unit'],
                            rec['area'],
                            rec['perimeter'],
                            rec['timestamp']
                        ])
            elif format_type == "json":
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump([dict(rec) for rec in records], f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Экспорт", f"Данные успешно экспортированы в {format_type.upper()}.")
        except Exception as e:
            logging.error(f"Ошибка экспорта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать: {e}")

    def _import_data(self, format_type):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл", "",
            f"{format_type.upper()} files (*.{format_type})"
        )
        if not path:
            return
        try:
            if format_type == "csv":
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        params = json.loads(row['params'])
                        unit = row['unit']
                        area = float(row['area']) if row['area'] else None
                        perimeter = float(row['perimeter']) if row['perimeter'] else None
                        self.db.insert_record(row['figure_type'], params, unit, area, perimeter)
            elif format_type == "json":
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rec in data:
                        self.db.insert_record(
                            rec['figure_type'], json.loads(rec['params']),
                            rec['unit'], rec['area'], rec['perimeter']
                        )
            self._refresh_history()
            QMessageBox.information(self, "Импорт", f"Данные успешно импортированы из {format_type.upper()}.")
        except Exception as e:
            logging.error(f"Ошибка импорта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать: {e}")

    def save_geometry(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("figure_index", self.figure_combo.currentIndex())
        self.settings.setValue("unit_index", self.unit_combo.currentIndex())
        if hasattr(self, 'current_theme'):
            self.settings.setValue("theme", self.current_theme)

    def restore_geometry(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Выход",
                                      "Вы уверены, что хотите выйти?",
                                      QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                      QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save_geometry()
            self.db.close()
            logging.info("Приложение закрыто.")
            event.accept()
        elif reply == QMessageBox.No:
            event.ignore()
        else:
            event.ignore()
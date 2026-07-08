import sys
import math  # <-- добавлен импорт
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QStackedWidget,
    QSplitter, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор площади и периметра")
        self.resize(1000, 700)
        self.setMinimumSize(900, 600)
        self._setup_ui()
        self._bind_signals()

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

        # Выбор фигуры
        self.figure_combo = QComboBox()
        self.figure_combo.addItems([
            "Прямоугольник", "Квадрат", "Круг",
            "Треугольник", "Параллелограмм", "Трапеция", "Ромб"
        ])
        left_layout.addWidget(QLabel("Фигура:"))
        left_layout.addWidget(self.figure_combo)

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
        left_layout.addStretch()

        # Правая панель (история – пока пустая)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        history_title = QLabel("История вычислений")
        history_title.setObjectName("historyTitle")
        right_layout.addWidget(history_title)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(0)
        right_layout.addWidget(self.history_table)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 550])
        main_layout.addWidget(splitter)

        self._apply_styles()

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
                layout.addRow(label_text + ":", line_edit)
                fields[param_name] = line_edit
            self.input_fields[figure_type] = fields
            self.params_stack.addWidget(widget)
        self.params_stack.setCurrentIndex(0)

    def _apply_styles(self):
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
        QLabel#mainTitle { font-size: 20px; font-weight: bold; color: #333; padding: 10px 0; }
        QLabel#historyTitle { font-size: 16px; font-weight: bold; color: #333; }
        QSplitter::handle { background-color: #d0d0d0; width: 2px; }
        """
        self.setStyleSheet(style)

    def _bind_signals(self):
        self.figure_combo.currentIndexChanged.connect(self._on_figure_changed)
        self.btn_calc.clicked.connect(self._calculate)
        self.btn_clear.clicked.connect(self._clear_fields)

    def _on_figure_changed(self, index):
        self.params_stack.setCurrentIndex(index)
        self._clear_fields()
        self.lbl_area.setText("Площадь: —")
        self.lbl_perimeter.setText("Периметр: —")

    def _get_current_figure(self):
        return self.figure_combo.currentText()

    # ---------- Новая реальная реализация ----------
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

    def _calculate(self):
        figure = self._get_current_figure()
        params = self._get_params_from_ui()
        if params is None:
            QMessageBox.warning(self, "Ошибка ввода",
                                "Пожалуйста, заполните все поля положительными числами.")
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
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить расчёт: {e}")
            return

        self.lbl_area.setText(f"Площадь: {area:.4f}" if area is not None else "Площадь: —")
        self.lbl_perimeter.setText(f"Периметр: {perimeter:.4f}" if perimeter is not None else "Периметр: —")

    def _clear_fields(self):
        figure = self._get_current_figure()
        fields = self.input_fields.get(figure, {})
        for line_edit in fields.values():
            line_edit.clear()
        self.lbl_area.setText("Площадь: —")
        self.lbl_perimeter.setText("Периметр: —")
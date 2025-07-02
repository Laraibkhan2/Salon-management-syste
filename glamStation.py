import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QStackedWidget, QGroupBox, QFormLayout, QSpinBox, QListWidget, QTimeEdit
)
from PyQt5.QtGui import QFont, QPixmap, QPalette, QBrush, QColor, QLinearGradient
from PyQt5.QtCore import Qt, QTime
from collections import defaultdict
import random

# --------------------- Service Management -------------------------
class ServiceManager:
    _services = {
        'Hair Wash': {"cost": 500, "duration": 4, "priority": 3},
        'Haircut': {"cost": 800, "duration": 6, "priority": 2},
        'Manicure': {"cost": 300, "duration": 3, "priority": 3},
        'VIP Facial': {"cost": 1500, "duration": 5, "priority": 1},
        'Bridal Makeup': {"cost": 5000, "duration": 10, "priority": 1},
        'Mehndi Design': {"cost": 1200, "duration": 7, "priority": 2}
    }

    @classmethod
    def get_services(cls):
        return cls._services

    @classmethod
    def get_service(cls, name):
        return cls._services.get(name)

    @classmethod
    def add_service(cls, name, cost, duration, priority):
        cls._services[name] = {"cost": cost, "duration": duration, "priority": priority}

    @classmethod
    def update_service(cls, name, cost, duration, priority):
        if name in cls._services:
            cls._services[name] = {"cost": cost, "duration": duration, "priority": priority}

    @classmethod
    def delete_service(cls, name):
        if name in cls._services:
            del cls._services[name]

    @classmethod
    def get_service_names(cls):
        return list(cls._services.keys())


# --------------------- Staff Management -------------------------
class StaffManager:
    _staff = {
        'Hair Stylist': ["Sara", "Mehak", "Aaima"],
        'Makeup Artist': ["Ayesha", "Farheen", "Farzeen"],
        'Mehndi Artist': ["Eshah", "Maryam"],
        'Receptionist': ["Farzana"],
        'Waxing/Threading Expert': ["Fatima", "Laraib"],
        'Massage Expert': ["Umaima", "Darkshan"]
    }

    _shift_duration = 8  # hours
    _break_duration = 0.5  # hours (30 minutes)
    _quantum = 0.5  # hours (30 minutes)
    _breaks_per_shift = 2  # Each staff gets 2 breaks per shift

    @classmethod
    def get_staff_roles(cls):
        return list(cls._staff.keys())

    @classmethod
    def get_staff_members(cls, role):
        return cls._staff.get(role, [])

    @classmethod
    def add_staff_member(cls, role, name):
        if role in cls._staff:
            if name not in cls._staff[role]:
                cls._staff[role].append(name)
                return True
        else:
            cls._staff[role] = [name]
            return True
        return False

    @classmethod
    def remove_staff_member(cls, role, name):
        if role in cls._staff and name in cls._staff[role]:
            cls._staff[role].remove(name)
            return True
        return False

    @classmethod
    def generate_schedule(cls):
        schedule = {}
        shift_start_hour = 9  # 9:00 AM
        shift_end_hour = 17  # 5:00 PM

        for role, members in cls._staff.items():
            if not members:  # Skip if no staff in this role
                continue

            role_schedule = {}

            # Calculate total work minutes and break intervals
            total_work_minutes = (shift_end_hour - shift_start_hour) * 60
            break_interval = total_work_minutes // (cls._breaks_per_shift + 1)

            # Calculate staggered break offsets for first break
            break_offset = break_interval  # Start breaks after first work period
            break_offset_increment = break_interval // max(1, len(members))

            for member in members:
                shifts = []
                current_time = shift_start_hour * 60  # Start at 9:00 AM in minutes

                # First work period before first break
                first_break_time = current_time + break_offset
                if current_time < first_break_time:
                    shifts.append(("Work", current_time, first_break_time))

                # First break
                break_end = first_break_time + int(cls._break_duration * 60)
                shifts.append(("Break", first_break_time, break_end))
                current_time = break_end

                # Update break offset for next staff member
                break_offset = (break_offset + break_offset_increment) % break_interval

                # Remaining work periods and breaks
                remaining_work_time = shift_end_hour * 60 - current_time
                remaining_break_interval = remaining_work_time // cls._breaks_per_shift

                for i in range(1, cls._breaks_per_shift + 1):
                    work_end = current_time + remaining_break_interval
                    if current_time < work_end:
                        shifts.append(("Work", current_time, work_end))

                    if i < cls._breaks_per_shift and work_end < shift_end_hour * 60:
                        break_start = work_end
                        break_end = break_start + int(cls._break_duration * 60)
                        shifts.append(("Break", break_start, break_end))
                        current_time = break_end

                role_schedule[member] = shifts

            schedule[role] = role_schedule

        return schedule

    @classmethod
    def format_time(cls, minutes):
        hours = minutes // 60
        mins = minutes % 60
        ampm = "AM" if hours < 12 else "PM"
        hours = hours if hours <= 12 else hours - 12
        return f"{hours:02d}:{mins:02d} {ampm}"


# --------------------- Customer and Scheduling Logic -------------------------
class Customer:
    def __init__(self, name, services, arrival_time=0):
        self.name = name
        self.services = services  # List of service names
        self.arrival_time = arrival_time
        self.service_data = [ServiceManager.get_service(service) or
                             {"duration": 5, "cost": 0, "priority": 3}
                             for service in services]
        self.total_duration = sum(service["duration"] for service in self.service_data)
        self.total_cost = sum(service["cost"] for service in self.service_data)
        self.priority = min(service["priority"] for service in self.service_data)  # Highest priority service
        self.waiting_time = 0
        self.start_time = 0
        self.end_time = 0


def fcfs(customers):
    customers_sorted = sorted(customers, key=lambda x: x.arrival_time)
    time = 0
    results = []

    for customer in customers_sorted:
        if time < customer.arrival_time:
            time = customer.arrival_time

        customer.start_time = time
        customer.end_time = time + customer.total_duration
        customer.waiting_time = customer.start_time - customer.arrival_time

        # Calculate dynamic waiting time based on queue length
        queue_length = len([c for c in customers_sorted if c.arrival_time < customer.arrival_time])
        if queue_length > 3:  # If more than 3 customers ahead
            customer.waiting_time += 120  # Add 2 hours
        elif queue_length > 1:  # If 2-3 customers ahead
            customer.waiting_time += 30  # Add 30 minutes
        else:
            customer.waiting_time += 15  # Minimum 15 minutes wait

        results.append(customer)
        time = customer.end_time

    return results

def priority_scheduling(customers):
    customers_sorted = sorted(customers, key=lambda x: x.priority)  # Lower value = higher priority
    time = 0
    results = []

    for customer in customers_sorted:
        if time < customer.arrival_time:
            time = customer.arrival_time

        customer.start_time = time
        customer.end_time = time + customer.total_duration
        customer.waiting_time = customer.start_time - customer.arrival_time
        results.append(customer)
        time = customer.end_time

    return results

# --------------------- GUI Screens -------------------------
class HomeScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()

        # Set more vibrant pink background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 182, 193))  # Brighter pink background
        self.setPalette(palette)

        layout.addStretch(1)

        title = QLabel("\ud83d\udc96 Welcome to GlamStation \ud83d\udc96")
        title.setFont(QFont('Comic Sans MS', 24))
        title.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(20)

        btn_booking = self.create_cute_button("Customer Booking", "#FF6B8B")
        btn_booking.clicked.connect(lambda: parent.setCurrentIndex(1))

        btn_service = self.create_cute_button("Services Management", "#4E9AF1")
        btn_service.clicked.connect(lambda: parent.setCurrentIndex(2))

        btn_staff = self.create_cute_button("Staff Scheduling", "#5CB85C")
        btn_staff.clicked.connect(lambda: parent.setCurrentIndex(3))

        button_layout.addWidget(btn_booking)
        button_layout.addWidget(btn_service)
        button_layout.addWidget(btn_staff)

        layout.addStretch(1)
        layout.addWidget(button_container)
        layout.addStretch(2)

        self.setLayout(layout)

    def create_cute_button(self, text, color):
        btn = QPushButton(text)
        btn.setFont(QFont('Comic Sans MS', 14))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 15px;
                padding: 12px 25px;
                border: 2px solid #FFFFFF;
                min-width: 200px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color, 0.8)};
                border: 2px solid #FFD166;
            }}
        """)
        return btn

    def darken_color(self, hex_color, factor=0.7):
        color = QColor(hex_color)
        return color.darker(int(100 * factor)).name()

from PyQt5.QtWidgets import QInputDialog
class BookingScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.customers = []
        self.current_services = []  # To store services for current customer
        layout = QVBoxLayout()

        # Set cute background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 248, 255))  # Alice blue background
        self.setPalette(palette)

        title = QLabel("\ud83d\udcc5 Booking & Scheduling")
        title.setFont(QFont('Arial', 20))
        title.setStyleSheet("color: #6B5B95;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Customer Details Form
        form_group = QGroupBox("Customer Details")
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter customer name")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #CCCCCC;
            }
        """)

        self.service_box = QComboBox()
        self.service_box.addItems(ServiceManager.get_service_names())
        self.service_box.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #CCCCCC;
            }
        """)

        self.add_service_btn = QPushButton("Add Service")
        self.add_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #A2D2FF;
                color: #333333;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #8FBDEB;
            }
        """)
        self.add_service_btn.clicked.connect(self.add_service_to_list)

        self.selected_services_list = QListWidget()
        self.selected_services_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #CCCCCC;
            }
        """)

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Service:", self.service_box)
        form_layout.addRow(self.add_service_btn)
        form_layout.addRow("Selected Services:", self.selected_services_list)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        confirm_btn = self.create_button("Confirm Booking", "#B5EAD7")
        confirm_btn.clicked.connect(self.confirm_booking)

        schedule_btn = self.create_button("View Schedule", "#FFB7B2")
        schedule_btn.clicked.connect(self.view_schedule)

        home_btn = self.create_button("Back to Home", "#E2F0CB")
        home_btn.clicked.connect(lambda: parent.setCurrentIndex(0))

        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(schedule_btn)
        btn_layout.addWidget(home_btn)
        layout.addLayout(btn_layout)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Customer", "Services", "Start", "End", "Waiting", "Total Cost"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #CCCCCC;
            }
            QHeaderView::section {
                background-color: #B8B8B8;
                padding: 5px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def create_button(self, text, color):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 10))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #333333;
                border-radius: 10px;
                padding: 8px 15px;
                border: 1px solid #CCCCCC;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)
        return btn

    def darken_color(self, hex_color, factor=0.8):
        color = QColor(hex_color)
        return color.darker(int(100 * factor)).name()

    def add_service_to_list(self):
        service = self.service_box.currentText()
        if service:
            self.current_services.append(service)
            self.selected_services_list.addItem(service)

    def confirm_booking(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter customer name!")
            return

        if not self.current_services:
            QMessageBox.warning(self, "Error", "Please add at least one service!")
            return

        # Create customer with all selected services
        self.customers.append(Customer(name, self.current_services.copy()))

        # Generate bill
        customer = self.customers[-1]
        bill_details = f"Customer: {name}\nServices:\n"
        for service in customer.services:
            service_data = ServiceManager.get_service(service)
            bill_details += f"- {service}: Rs. {service_data['cost']} ({service_data['duration']} mins)\n"

        bill_details += f"\nTotal Cost: Rs. {customer.total_cost}"
        QMessageBox.information(self, "Booking Confirmed", bill_details)

        # Reset form
        self.name_input.clear()
        self.current_services.clear()
        self.selected_services_list.clear()


    def view_schedule(self):  
        if not self.customers:
            QMessageBox.warning(self, "Error", "No bookings yet!")
            return

        # Let user choose scheduling type
        algorithm, ok = QInputDialog.getItem(
            self,
            "Choose Scheduling Algorithm",
            "Select one:",
            ["FCFS (First Come First Serve)", "Priority Scheduling"],
            0,
            False
        )

        if not ok:
            return

        if algorithm.startswith("FCFS"):
            scheduled_customers = fcfs(self.customers)
        else:
            scheduled_customers = priority_scheduling(self.customers)

        self.table.setRowCount(len(scheduled_customers))

        for row, customer in enumerate(scheduled_customers):
            self.table.setItem(row, 0, QTableWidgetItem(customer.name))
            self.table.setItem(row, 1, QTableWidgetItem(", ".join(customer.services)))
            self.table.setItem(row, 2, QTableWidgetItem(str(customer.start_time)))
            self.table.setItem(row, 3, QTableWidgetItem(str(customer.end_time)))
            self.table.setItem(row, 4, QTableWidgetItem(f"{customer.waiting_time} mins"))
            self.table.setItem(row, 5, QTableWidgetItem(f"Rs. {customer.total_cost}"))

class ServiceScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()

        # Set cute background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 245, 238))  # Seashell background
        self.setPalette(palette)

        title = QLabel("\ud83d\udc84 Services Management ")  # Changed to lipstick emoji
        title.setFont(QFont('Arial', 20))
        title.setStyleSheet("color: #6B5B95;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Service management form
        form_group = QGroupBox("Service Details")
        form_layout = QFormLayout()

        self.service_name = QLineEdit()
        self.service_name.setPlaceholderText("Service name")
        self.service_name.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #CCCCCC;")

        self.service_cost = QSpinBox()
        self.service_cost.setRange(0, 10000)
        self.service_cost.setValue(500)
        self.service_cost.setPrefix("Rs. ")
        self.service_cost.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #CCCCCC;")

        form_layout.addRow("Service Name:", self.service_name)
        form_layout.addRow("Service Cost:", self.service_cost)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons for service management
        btn_layout = QHBoxLayout()
        add_btn = self.create_button("Add Service", "#A2D2FF")
        add_btn.clicked.connect(self.add_service)

        update_btn = self.create_button("Update Service", "#FFD166")
        update_btn.clicked.connect(self.update_service)

        delete_btn = self.create_button("Delete Service", "#EF476F")
        delete_btn.clicked.connect(self.delete_service)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(update_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

        # Services table
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(2)
        self.services_table.setHorizontalHeaderLabels(["Service", "Cost (Rs)"])
        self.services_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #CCCCCC;
            }
            QHeaderView::section {
                background-color: #B8B8B8;
                padding: 5px;
                border-radius: 5px;
            }
        """)
        self.services_table.cellClicked.connect(self.service_selected)
        layout.addWidget(self.services_table)

        # Back button
        back_btn = self.create_button("Back to Home", "#E2F0CB")
        back_btn.clicked.connect(lambda: parent.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)
        self.load_services()

    def create_button(self, text, color):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 10))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #333333;
                border-radius: 10px;
                padding: 8px 15px;
                border: 1px solid #CCCCCC;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)
        return btn

    def darken_color(self, hex_color, factor=0.8):
        color = QColor(hex_color)
        return color.darker(int(100 * factor)).name()

    def load_services(self):
        services = ServiceManager.get_services()
        self.services_table.setRowCount(len(services))

        for row, (name, details) in enumerate(services.items()):
            self.services_table.setItem(row, 0, QTableWidgetItem(name))
            self.services_table.setItem(row, 1, QTableWidgetItem(f"Rs. {details['cost']}"))

    def service_selected(self, row, col):
        name = self.services_table.item(row, 0).text()
        service = ServiceManager.get_service(name)
        if service:
            self.service_name.setText(name)
            self.service_cost.setValue(service["cost"])

    def add_service(self):
        name = self.service_name.text().strip()
        cost = self.service_cost.value()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a service name!")
            return

        if name in ServiceManager.get_services():
            QMessageBox.warning(self, "Error", "Service already exists! Use Update instead.")
            return

        # Default duration and priority for new services
        duration = 5
        priority = 3
        ServiceManager.add_service(name, cost, duration, priority)
        self.load_services()
        self.update_booking_services()
        QMessageBox.information(self, "Success", "Service added successfully!")

        self.clear_form()

    def update_service(self):
        name = self.service_name.text().strip()
        cost = self.service_cost.value()

        if not name:
            QMessageBox.warning(self, "Error", "Please select a service to update!")
            return

        if name not in ServiceManager.get_services():
            QMessageBox.warning(self, "Error", "Service doesn't exist! Use Add instead.")
            return

        # Keep existing duration and priority when updating
        service = ServiceManager.get_service(name)
        duration = service["duration"] if service else 5
        priority = service["priority"] if service else 3
        ServiceManager.update_service(name, cost, duration, priority)
        self.load_services()
        self.update_booking_services()
        QMessageBox.information(self, "Success", "Service updated successfully!")
        self.clear_form()

    def delete_service(self):
        name = self.service_name.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please select a service to delete!")
            return

        if name not in ServiceManager.get_services():
            QMessageBox.warning(self, "Error", "Service doesn't exist!")
            return

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete '{name}' service?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            ServiceManager.delete_service(name)
            self.load_services()
            self.update_booking_services()
            QMessageBox.information(self, "Success", "Service deleted successfully!")
            self.clear_form()

    def update_booking_services(self):
        booking_screen = self.parent.widget(1)
        booking_screen.service_box.clear()
        booking_screen.service_box.addItems(ServiceManager.get_service_names())

    def clear_form(self):
        self.service_name.clear()
        self.service_cost.setValue(500)


class StaffSchedulingScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        # Main layout with some spacing
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Set beautiful gradient background
        self.setAutoFillBackground(True)
        palette = self.palette()
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0, QColor(255, 240, 245))  # Light pink
        gradient.setColorAt(1, QColor(255, 255, 255))  # White
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        # Title with nice styling
        title = QLabel("\u2728 Staff Scheduling \u2728")  # Sparkle emoji
        title.setFont(QFont('Comic Sans MS', 24))
        title.setStyleSheet("""
            QLabel {
                color: #6B5B95;
                padding: 10px;
                background: rgba(255,255,255,0.7);
                border-radius: 10px;
                border: 1px solid #DAB6FF;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Create a container for the main content
        main_content = QWidget()
        main_content.setStyleSheet("background: rgba(255,255,255,0.8); border-radius: 15px;")
        content_layout = QHBoxLayout(main_content)
        content_layout.setContentsMargins(15, 15, 15, 15)

        # Left side - Staff Management
        left_panel = QGroupBox("Staff Management")
        left_panel.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #6B5B95;
                border: 2px solid #DAB6FF;
                border-radius: 10px;
                margin-top: 20px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
        """)
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)

        # Stylish combo box
        self.role_box = QComboBox()
        self.role_box.addItems(StaffManager.get_staff_roles())
        self.role_box.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #DAB6FF;
                min-width: 200px;
            }
            QComboBox::drop-down {
                width: 25px;
                border-left: 1px solid #DAB6FF;
            }
        """)
        self.role_box.currentTextChanged.connect(self.update_staff_members)

        # Stylish line edit
        self.staff_name = QLineEdit()
        self.staff_name.setPlaceholderText("Enter staff name")
        self.staff_name.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #DAB6FF;
            }
        """)

        # Time edit with better styling
        self.shift_start = QTimeEdit()
        self.shift_start.setDisplayFormat("hh:mm AP")
        self.shift_start.setTime(QTime(9, 0))  # Default shift start at 9:00 AM
        self.shift_start.setStyleSheet("""
            QTimeEdit {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #DAB6FF;
            }
        """)

        # Spin boxes with consistent styling
        spinbox_style = """
            QSpinBox {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #DAB6FF;
            }
        """
        self.shift_duration = QSpinBox()
        self.shift_duration.setRange(1, 12)
        self.shift_duration.setValue(8)
        self.shift_duration.setSuffix(" hours")
        self.shift_duration.setStyleSheet(spinbox_style)

        self.break_duration = QSpinBox()
        self.break_duration.setRange(15, 120)
        self.break_duration.setValue(30)
        self.break_duration.setSuffix(" mins")
        self.break_duration.setStyleSheet(spinbox_style)

        # Add form rows
        form_layout.addRow(QLabel("Role:"), self.role_box)
        form_layout.addRow(QLabel("Name:"), self.staff_name)
        form_layout.addRow(QLabel("Shift Start:"), self.shift_start)
        form_layout.addRow(QLabel("Shift Duration:"), self.shift_duration)
        form_layout.addRow(QLabel("Break Duration:"), self.break_duration)

        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)

        # Add Staff button with nice gradient
        self.add_staff_btn = QPushButton("➕ Add Staff")
        self.add_staff_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #A2D2FF, stop:1 #8FBDEB);
                color: white;
                border-radius: 8px;
                padding: 10px 15px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8FBDEB, stop:1 #7DAAD9);
            }
        """)
        self.add_staff_btn.clicked.connect(self.add_staff_member)

        # Remove Staff button with nice gradient
        self.remove_staff_btn = QPushButton("➖ Remove Staff")
        self.remove_staff_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFB7B2, stop:1 #EBA8A3);
                color: white;
                border-radius: 8px;
                padding: 10px 15px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #EBA8A3, stop:1 #D99994);
            }
        """)
        self.remove_staff_btn.clicked.connect(self.remove_staff_member)

        button_layout.addWidget(self.add_staff_btn)
        button_layout.addWidget(self.remove_staff_btn)
        form_layout.addRow(button_container)

        # Staff list with nice styling
        staff_list_label = QLabel("Current Staff:")
        staff_list_label.setStyleSheet("font-weight: bold; color: #6B5B95;")
        form_layout.addRow(staff_list_label)

        self.staff_list = QListWidget()
        self.staff_list.setStyleSheet("""
            QListWidget {
                background: white;
                border-radius: 5px;
                border: 1px solid #DAB6FF;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #EEE;
            }
            QListWidget::item:selected {
                background: #DAB6FF;
                color: white;
            }
        """)
        form_layout.addRow(self.staff_list)

        left_panel.setLayout(form_layout)
        content_layout.addWidget(left_panel, 1)  # 1:3 ratio

        # Right side - Schedule
        right_panel = QWidget()
        right_panel.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Generate button with nice effect
        self.generate_btn = QPushButton("\u2728 Generate Today's Schedule \u2728")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #B5EAD7, stop:1 #A1D7C3);
                color: #333;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #A1D7C3, stop:1 #8EC4AF);
            }
        """)
        self.generate_btn.clicked.connect(self.generate_schedule)
        right_layout.addWidget(self.generate_btn)

        # Schedule table with modern styling
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels(["Role", "Staff", "Shift Times", "Break Times"])
        self.schedule_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border-radius: 10px;
                border: 2px solid #DAB6FF;
                gridline-color: #EEE;
                font-size: 14px;
            }
            QHeaderView::section {
                background: #6B5B95;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background: #6B5B95;
                border: none;
            }
        """)
        self.schedule_table.verticalHeader().setVisible(False)
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.schedule_table)

        content_layout.addWidget(right_panel, 3)  # 1:3 ratio
        layout.addWidget(main_content)

        # Back button with nice styling
        back_btn = QPushButton("\u2190 Back to Home")
        back_btn.setStyleSheet("""
            QPushButton {
                background: #E2F0CB;
                color: #333;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                border: 1px solid #CCC;
            }
            QPushButton:hover {
                background: #D1E0BA;
            }
        """)
        back_btn.clicked.connect(lambda: parent.setCurrentIndex(0))
        layout.addWidget(back_btn, 0, Qt.AlignLeft)

        self.setLayout(layout)
        self.update_staff_members()

    def update_staff_members(self):
        role = self.role_box.currentText()
        self.staff_list.clear()
        self.staff_list.addItems(StaffManager.get_staff_members(role))

    def add_staff_member(self):
        role = self.role_box.currentText()
        name = self.staff_name.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter staff name!")
            return

        if StaffManager.add_staff_member(role, name):
            self.update_staff_members()
            self.staff_name.clear()
            QMessageBox.information(self, "Success", f"{name} added to {role} role!")
        else:
            QMessageBox.warning(self, "Error", f"{name} already exists in {role}!")

    def remove_staff_member(self):
        role = self.role_box.currentText()
        selected_items = self.staff_list.selectedItems()

        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a staff member to remove!")
            return

        name = selected_items[0].text()
        reply = QMessageBox.question(self, 'Confirm Remove',
                                     f"Are you sure you want to remove {name} from {role}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if StaffManager.remove_staff_member(role, name):
                self.update_staff_members()
                QMessageBox.information(self, "Success", f"{name} removed from {role} role!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to remove {name} from {role}!")

    def generate_schedule(self):
        # Update class variables with current GUI values
        StaffManager._shift_duration = self.shift_duration.value()
        StaffManager._break_duration = self.break_duration.value() / 60  # Convert to hours

        schedule = StaffManager.generate_schedule()
        self.schedule_table.setRowCount(0)  # Clear table

        row = 0
        for role, staff_schedule in schedule.items():
            for staff, shifts in staff_schedule.items():
                # Filter out breaks and work periods
                work_shifts = [s for s in shifts if s[0] == "Work"]
                break_shifts = [s for s in shifts if s[0] == "Break"]

                # Format shift times
                if work_shifts:
                    start_time = StaffManager.format_time(work_shifts[0][1])
                    end_time = StaffManager.format_time(work_shifts[-1][2])
                    shift_time = f"{start_time} - {end_time}"
                else:
                    shift_time = "Not scheduled"

                # Format break times
                break_times = []
                for b in break_shifts:
                    start = StaffManager.format_time(b[1])
                    end = StaffManager.format_time(b[2])
                    break_times.append(f"{start}-{end}")
                break_str = "\n".join(break_times) if break_times else "No breaks"

                # Add to table
                self.schedule_table.insertRow(row)
                self.schedule_table.setItem(row, 0, QTableWidgetItem(role))
                self.schedule_table.setItem(row, 1, QTableWidgetItem(staff))
                self.schedule_table.setItem(row, 2, QTableWidgetItem(shift_time))
                self.schedule_table.setItem(row, 3, QTableWidgetItem(break_str))
                row += 1

        self.schedule_table.resizeRowsToContents()


class GlamStationApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GlamStation ")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Arial';
            }
        """)

        self.home = HomeScreen(self)
        self.booking = BookingScreen(self)
        self.service = ServiceScreen(self)
        self.staff = StaffSchedulingScreen(self)

        self.addWidget(self.home)
        self.addWidget(self.booking)
        self.addWidget(self.service)
        self.addWidget(self.staff)
        self.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GlamStationApp()
    window.show()
    sys.exit(app.exec_())

import sys
import json
import os
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from todo import Ui_MainWindow

class Task:
    """Task data model"""
    def __init__(self):
        self.id = ""
        self.title = ""
        self.description = ""
        self.priority = "medium"  # low, medium, high
        self.due_date = ""
        self.completed = False
        self.created_date = datetime.now().strftime("%Y-%m-%d")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date,
            "completed": self.completed,
            "created_date": self.created_date
        }
    
    def from_dict(self, data):
        self.id = data.get("id", "")
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.priority = data.get("priority", "medium")
        self.due_date = data.get("due_date", "")
        self.completed = data.get("completed", False)
        self.created_date = data.get("created_date", "")

class TodoApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle("To-Do List App")
        self.tasks = []
        self.data_file = "tasks.json"
        
        # Setup UI
        self.setup_ui()
        
        # Load saved tasks
        self.load_tasks()
        
        # Refresh display
        self.refresh_task_list()
        self.update_stats()
        
    def setup_ui(self):
        """Setup UI components and connections"""
        # Set current date in due date picker
        self.ui.due_date.setDate(QDate.currentDate())
        
        # Connect buttons to functions
        self.ui.add_btn.clicked.connect(self.add_task)
        self.ui.delete_btn.clicked.connect(self.delete_task)
        self.ui.delete_btn_2.clicked.connect(self.complete_task)  # DONE button
        self.ui.task_list.itemClicked.connect(self.task_selected)
        
        # Initially disable delete and complete buttons
        self.ui.delete_btn.setEnabled(False)
        self.ui.delete_btn_2.setEnabled(False)
        
        # Set focus to title input
        self.ui.title_input.setFocus()
        
    def add_task(self):
        """Add a new task"""
        title = self.ui.title_input.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Warning", "Please enter a task title!")
            return
        
        # Create new task
        task = Task()
        task.id = str(len(self.tasks) + 1)
        task.title = title
        task.description = self.ui.desc_input.toPlainText()
        task.priority = self.ui.priority_combo.currentText().lower()
        task.due_date = self.ui.due_date.date().toString("yyyy-MM-dd")
        
        self.tasks.append(task)
        self.save_tasks()
        self.refresh_task_list()
        self.clear_inputs()
        self.update_stats()
        
        QMessageBox.information(self, "Success", "Task added successfully!")
        
    def delete_task(self):
        """Delete selected task"""
        current_item = self.ui.task_list.currentItem()
        if not current_item:
            return
        
        task_id = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     "Are you sure you want to delete this task?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.tasks = [t for t in self.tasks if t.id != task_id]
            self.save_tasks()
            self.refresh_task_list()
            self.clear_inputs()
            self.update_stats()
            
    def complete_task(self):
        """Mark task as complete"""
        current_item = self.ui.task_list.currentItem()
        if not current_item:
            return
        
        task_id = current_item.data(Qt.UserRole)
        
        for task in self.tasks:
            if task.id == task_id:
                task.completed = True
                break
        
        self.save_tasks()
        self.refresh_task_list()
        self.clear_inputs()
        self.update_stats()
        
        QMessageBox.information(self, "Success", "Task marked as complete!")
        
    def task_selected(self, item):
        """When a task is selected, show its details"""
        self.ui.delete_btn.setEnabled(True)
        self.ui.delete_btn_2.setEnabled(True)
        
        task_id = item.data(Qt.UserRole)
        
        for task in self.tasks:
            if task.id == task_id:
                self.ui.title_input.setText(task.title)
                self.ui.desc_input.setPlainText(task.description)
                
                # Set priority combo box (low, medium, high)
                if task.priority == "low":
                    self.ui.priority_combo.setCurrentIndex(0)
                elif task.priority == "medium":
                    self.ui.priority_combo.setCurrentIndex(1)
                else:
                    self.ui.priority_combo.setCurrentIndex(2)
                
                if task.due_date:
                    date = QDate.fromString(task.due_date, "yyyy-MM-dd")
                    self.ui.due_date.setDate(date)
                break
    
    def refresh_task_list(self):
        """Refresh the task list display"""
        self.ui.task_list.clear()
        
        for task in self.tasks:
            # Format task display with emoji indicators
            if task.completed:
                status = "✅"
            else:
                status = "○"
            
            # Priority emoji
            if task.priority == "high":
                priority_emoji = "🔴"
            elif task.priority == "medium":
                priority_emoji = "🟡"
            else:
                priority_emoji = "🟢"
            
            display_text = f"{status} {priority_emoji} {task.title}"
            
            if task.due_date:
                display_text += f" (Due: {task.due_date})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, task.id)
            
            # Set color based on status and priority
            if task.completed:
                item.setForeground(QtCore.Qt.gray)
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
            elif task.priority == "high":
                item.setForeground(QtCore.Qt.red)
            elif task.priority == "medium":
                item.setForeground(QtCore.Qt.darkYellow)
            else:
                item.setForeground(QtCore.Qt.darkGreen)
            
            self.ui.task_list.addItem(item)
    
    def update_stats(self):
        """Update statistics display"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.completed])
        pending = total - completed
        
        # Count by priority
        high_pending = len([t for t in self.tasks if t.priority == "high" and not t.completed])
        medium_pending = len([t for t in self.tasks if t.priority == "medium" and not t.completed])
        low_pending = len([t for t in self.tasks if t.priority == "low" and not t.completed])
        
        stats_text = (f"📊 Statistics | Total: {total} | "
                     f"✅ Completed: {completed} | "
                     f"⏳ Pending: {pending} | "
                     f"🔴 High: {high_pending} | "
                     f"🟡 Medium: {medium_pending} | "
                     f"🟢 Low: {low_pending}")
        
        self.ui.stats_label.setText(stats_text)
    
    def clear_inputs(self):
        """Clear all input fields"""
        self.ui.title_input.clear()
        self.ui.desc_input.clear()
        self.ui.priority_combo.setCurrentIndex(0)  # low
        self.ui.due_date.setDate(QDate.currentDate())
        self.ui.delete_btn.setEnabled(False)
        self.ui.delete_btn_2.setEnabled(False)
        self.ui.title_input.setFocus()
    
    def save_tasks(self):
        """Save tasks to JSON file"""
        tasks_data = [task.to_dict() for task in self.tasks]
        
        with open(self.data_file, 'w') as f:
            json.dump(tasks_data, f, indent=2)
    
    def load_tasks(self):
        """Load tasks from JSON file"""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, 'r') as f:
                tasks_data = json.load(f)
            
            self.tasks = []
            for data in tasks_data:
                task = Task()
                task.from_dict(data)
                self.tasks.append(task)
        except Exception as e:
            print(f"Error loading tasks: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = TodoApp()
    window.show()
    sys.exit(app.exec_())
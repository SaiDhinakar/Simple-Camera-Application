import cv2 as cv
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from datetime import datetime
import os

class VideoRecorder(QThread):
    recording_started = pyqtSignal()  # Signal to notify the start of recording
    recording_stopped = pyqtSignal(str)  # Signal to notify the end of recording with the video path

    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.out = None
        self.is_recording = False
        self.temp_file_name = f'Recorder_{datetime.now().strftime("%Y%m%d_%H%M%S")}.avi'

    def run(self):
        """Run the video recording in a separate thread."""
        frame_width = int(self.cap.get(cv.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        self.out = cv.VideoWriter(self.temp_file_name, cv.VideoWriter_fourcc(*'XVID'), 30.0, (frame_width, frame_height))
        self.is_recording = True
        self.recording_started.emit()

        while self.is_recording:
            ret, frame = self.cap.read()
            if ret:
                self.out.write(frame)

        self.out.release()
        self.recording_stopped.emit(self.temp_file_name)

    def stop(self):
        """Stop the recording."""
        self.is_recording = False


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = cv.VideoCapture(0)  # Camera capture object
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 ms
        self.video_thread = None

    def initUI(self):
        self.setWindowTitle("Camera Application")
        self.resize(900, 600)

        # Create widgets
        self.photo_btn = QPushButton("Capture Photo")
        self.video_btn = QPushButton("Record Video")
        self.picture_box = QLabel("Image will appear here!")

        # Layout setup
        master_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(self.picture_box)
        col2.addWidget(self.photo_btn)
        col2.addWidget(self.video_btn)

        master_layout.addLayout(col1, 80)
        master_layout.addLayout(col2, 20)
        self.setLayout(master_layout)

        # Connect button actions
        self.photo_btn.clicked.connect(self.save_image)
        self.video_btn.clicked.connect(self.toggle_video_recording)

    def update_frame(self):
        """Update the displayed camera frame in the QLabel."""
        ret, frame = self.cap.read()
        if ret:
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            frame = cv.flip(frame, 1)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            scaled_image = qt_image.scaled(self.picture_box.width(), self.picture_box.height(), Qt.KeepAspectRatio)
            self.picture_box.setPixmap(QPixmap.fromImage(scaled_image))

    def save_image(self):
        """Capture and save the current frame as an image."""
        ret, frame = self.cap.read()
        if ret:
            save_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
            if save_dir:
                file_name = f'capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
                path = os.path.join(save_dir, file_name)
                cv.imwrite(path, frame)

    def toggle_video_recording(self):
        """Start or stop video recording."""
        if self.video_thread is None or not self.video_thread.is_recording:
            self.start_video_recording()
        else:
            self.stop_video_recording()

    def start_video_recording(self):
        """Start recording video using a QThread."""
        self.video_thread = VideoRecorder(self.cap)
        self.video_thread.recording_started.connect(self.on_recording_started)
        self.video_thread.recording_stopped.connect(self.on_recording_stopped)
        self.video_thread.start()

    def on_recording_started(self):
        """Handle UI changes when recording starts."""
        self.video_btn.setText("Stop Recording")

    def on_recording_stopped(self, temp_file_name):
        """Handle UI changes and save video after recording stops."""
        self.video_btn.setText("Record Video")

        # Prompt user to select a directory to save the video
        save_dir = QFileDialog.getExistingDirectory(self, "Select Directory to Save Video")
        if save_dir:
            # Move the video file to the chosen directory
            final_path = os.path.join(save_dir, temp_file_name)
            os.rename(temp_file_name, final_path)

            # Show a message that the video was saved
            QMessageBox.information(self, "Video Saved", f"Video saved to: {final_path}")

        self.video_thread = None

    def stop_video_recording(self):
        """Stop the video recording."""
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread.wait()

    def closeEvent(self, event):
        """Handle cleanup when the application is closed."""
        self.cap.release()
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread.wait()

if __name__ == '__main__':
    app = QApplication([])
    cam = CameraApp()
    # change theme as dark
    cam.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
    cam.setWindowIcon(QIcon("Camera_Moto_30013.ico"))
    cam.show()
    app.exec_()

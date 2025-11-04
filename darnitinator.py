from PyQt6.QtWidgets import (
    QAbstractItemView, 
    QApplication, 
    QListWidgetItem, 
    QMainWindow, 
    QStyle, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QListWidget, 
    QToolButton, 
    QFrame,
    QSplitter
)
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize

from moviepy.editor import VideoFileClip
import sys
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Video Editor")
        self.setGeometry(100, 100, 1000, 600)

        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)

        # TOP HALF (Media Panel + Video Preview)
        top_half_layout = QHBoxLayout()

        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Half: Media Panel
        media_panel = QFrame()
        media_panel.setFrameShape(QFrame.Shape.StyledPanel)
        media_layout = QVBoxLayout(media_panel)
        media_layout.addWidget(QLabel("Media"))

        media_list = QListWidget()
        media_list.setViewMode(QListWidget.ViewMode.IconMode)       # switch to grid layout
        media_list.setIconSize(QSize(96, 96))                       # thumbnail size
        media_list.setResizeMode(QListWidget.ResizeMode.Adjust)     # auto-adjust layout
        media_list.setMovement(QListWidget.Movement.Static)         # fixed item positions
        media_list.setSpacing(10)                                   # space between items
        media_list.setWrapping(True)                                # allow wrapping to next row
        media_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        media_list.setUniformItemSizes(True)
        media_list.setGridSize(QSize(120, 120))
        
        media_layout.addWidget(media_list)

        # Temporary stuff for testing
        media_folder = "test"
        supported_formats = (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".avi", ".mkv")

        if os.path.exists(media_folder):
            for filename in os.listdir(media_folder):
                if filename.lower().endswith(supported_formats):
                    full_path = os.path.join(media_folder, filename)
                    item = QListWidgetItem(filename)

                    # Image / GIF
                    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                        pixmap = QPixmap(full_path)
                        if not pixmap.isNull():
                            icon = QIcon(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                            item.setIcon(icon)

                    # Video file
                    elif filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                        pixmap = self.get_video_thumbnail(full_path)
                        if pixmap:
                            item.setIcon(QIcon(pixmap))
                        else:
                            # fallback generic icon
                            icon = window.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
                            item.setIcon(icon)

                    media_list.addItem(item)
        else:
            media_list.addItem("[Folder not found]")

        # Adjust appearance
        media_list.setIconSize(QSize(64, 64))


        # Right Half: Video Preview + Playback Controls
        preview_panel = QFrame()
        preview_panel.setFrameShape(QFrame.Shape.StyledPanel)
        preview_layout = QVBoxLayout(preview_panel)

        preview_label = QLabel("Video Preview Area")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("background-color: #333; color: white; padding: 10px;")
        preview_layout.addWidget(preview_label)

        # Playback Controls
        controls_layout = QHBoxLayout()
        play_btn = QToolButton()
        pause_btn = QToolButton()
        stop_btn = QToolButton()

        play_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        pause_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        stop_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
    
        # Set button color based on system theme
        button_color = "white" if self.detect_darkmode_in_windows() else "black"

        play_btn.setIcon(self.tint_icon(play_icon, QColor(button_color)))
        pause_btn.setIcon(self.tint_icon(pause_icon, QColor(button_color)))
        stop_btn.setIcon(self.tint_icon(stop_icon, QColor(button_color)))

        for btn in (play_btn, pause_btn, stop_btn):
            btn.setStyleSheet("""
                QToolButton {
                    background-color: #444;
                    border: none;
                    border-radius: 4px;
                    padding: 3px;
                }
                QToolButton:hover {
                    background-color: #555;
                }
            """)

        controls_layout.addStretch()  # pushes everything to the center
        controls_layout.addWidget(play_btn)
        controls_layout.addWidget(pause_btn)
        controls_layout.addWidget(stop_btn)
        controls_layout.addStretch() 
        preview_layout.addLayout(controls_layout)

        top_splitter.addWidget(media_panel)
        top_splitter.addWidget(preview_panel)
        top_splitter.setSizes([300, 700])
        top_half_layout.addWidget(top_splitter)


        # BOTTOM HALF (Timeline) 
        timeline_panel = QFrame()
        timeline_panel.setFrameShape(QFrame.Shape.StyledPanel)
        timeline_layout = QVBoxLayout(timeline_panel)
        timeline_label = QLabel("Timeline Area")
        timeline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timeline_label.setStyleSheet("background-color: #555; color: white; padding: 10px;")
        timeline_layout.addWidget(timeline_label)

        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        vertical_splitter.addWidget(top_splitter)
        vertical_splitter.addWidget(timeline_panel)
        vertical_splitter.setSizes([500, 200])
        main_layout.addWidget(vertical_splitter)

    def get_video_thumbnail(self, path, width=64, height=64):
        try:
            clip = VideoFileClip(path)
            frame = clip.get_frame(0)  # get first frame as NumPy array (H, W, 3)
            clip.close()
            
            # Convert NumPy array (RGB) → QImage → QPixmap
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            print(f"Could not generate thumbnail for {path}: {e}")
            return None

    def tint_icon(self, icon, color=QColor("white"), size=24):
            pixmap = icon.pixmap(size, size)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), color)
            painter.end()
            return QIcon(pixmap)
    
    # Courtesy of https://stackoverflow.com/a/65349866
    def detect_darkmode_in_windows(self): 
        try:
            import winreg
        except ImportError:
            return False
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        try:
            reg_key = winreg.OpenKey(registry, reg_keypath)
        except FileNotFoundError:
            return False

        for i in range(1024):
            try:
                value_name, value, _ = winreg.EnumValue(reg_key, i)
                if value_name == 'AppsUseLightTheme':
                    return value == 0
            except OSError:
                break
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
 

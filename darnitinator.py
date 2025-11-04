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
from PyQt6.QtCore import QTimer, Qt, QSize, QUrl
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

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
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Half: Media Panel
        media_panel = QFrame()
        media_panel.setFrameShape(QFrame.Shape.StyledPanel)
        media_layout = QVBoxLayout(media_panel)
        media_layout.addWidget(QLabel("Media"))

        self.media_list = QListWidget()
        self.media_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.media_list.setIconSize(QSize(96, 96))
        self.media_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.media_list.setMovement(QListWidget.Movement.Static)
        self.media_list.setSpacing(10)
        self.media_list.setWrapping(True)
        self.media_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.media_list.setUniformItemSizes(True)
        self.media_list.setGridSize(QSize(120, 120))
        media_layout.addWidget(self.media_list)

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

                    self.media_list.addItem(item)
        else:
            self.media_list.addItem("[Folder not found]")

        # Adjust appearance
        self.media_list.setIconSize(QSize(64, 64))


        # Right Half: Video Preview + Playback Controls
        preview_panel = QFrame()
        preview_panel.setFrameShape(QFrame.Shape.StyledPanel)
        preview_layout = QVBoxLayout(preview_panel)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #000;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000;")
        self.image_label.hide()  # Hidden by default

        # We'll toggle between the two layouts accordingly
        preview_layout.addWidget(self.video_widget)
        preview_layout.addWidget(self.image_label)

        # --- Media Player Setup ---
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

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
        top_splitter.setStretchFactor(0, 35)
        top_splitter.setStretchFactor(1, 65)

        self.media_list.itemClicked.connect(self.play_selected_media)


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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image_display()




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
    
    def play_selected_media(self, item):
        file_name = item.text()
        file_path = os.path.join("test", file_name)

        self.player.stop()
        ext = os.path.splitext(file_path)[1].lower()

        if ext in (".png", ".jpg", ".jpeg"):
            self.video_widget.hide()
            self.image_label.show()

            pixmap = QPixmap(file_path)
            self.current_image = pixmap  # Store original pixmap for future scaling
            self.update_image_display()

        else:
            self.image_label.hide()
            self.video_widget.show()
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()

    def update_image_display(self):
        if hasattr(self, "current_image") and not self.current_image.isNull():
            target_size = self.image_label.size()
            scaled = self.current_image.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)







if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
 

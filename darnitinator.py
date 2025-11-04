from PyQt6.QtWidgets import (
    QAbstractItemView, 
    QApplication, 
    QListWidgetItem, 
    QMainWindow,
    QScrollArea, 
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
from TimelineWidget import TimelineWidget
import sys
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.timeline = [] # holds media clips
        self.current_time = 0.0 # playhead position


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

        # Media Player
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

        self.timeline_widget = TimelineWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setWidget(self.timeline_widget)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        timeline_layout.addWidget(scroll)
        self.timeline_widget.playhead_moved.connect(self.on_playhead_moved)


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
        ext = os.path.splitext(file_path)[1].lower()

        # Determine clip duration
        if ext in (".png", ".jpg", ".jpeg"):
            duration = 5.0
            media_type = "image"
        else:
            media_type = "video"
            try:
                from moviepy.editor import VideoFileClip
                with VideoFileClip(file_path) as clip:
                    duration = clip.duration
            except Exception as e:
                print(f"Error reading video duration: {e}")
                return

        # Add clip to project timeline
        self.timeline.append({
            "path": file_path,
            "start": self.current_time,
            "duration": duration,
            "type": media_type
        })
        self.timeline_widget.setTimeline(self.timeline)

        # Advance playhead
        self.current_time += duration
        self.timeline_widget.setTimeline(self.timeline)
        self.timeline_widget.setPlayheadPosition(self.current_time)


    def update_image_display(self):
        if hasattr(self, "current_image") and not self.current_image.isNull():
            target_size = self.image_label.size()
            scaled = self.current_image.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

    def on_playhead_moved(self, new_time):
        self.current_time = new_time
        self.timeline_widget.setPlayheadPosition(new_time)
        self.show_media_at_time(new_time)
        

    def show_media_at_time(self, time_s: float):
        active_clip = None
        for clip in self.timeline:
            start, dur = clip["start"], clip["duration"]
            if start <= time_s < start + dur:
                active_clip = clip
                break

        if not active_clip:
            # nothing playing at this time
            self.player.stop()
            self.video_widget.hide()
            self.image_label.hide()
            return

        path = active_clip["path"]
        ext = os.path.splitext(path)[1].lower()

        # Handle video files
        if ext in (".mp4", ".mov", ".avi", ".mkv"):
            # Only reload if it's a new video
            if self.current_media_path() != path:
                self.player.setSource(QUrl.fromLocalFile(path))
            self.video_widget.show()
            self.image_label.hide()
            self.player.setPosition(int((time_s - active_clip["start"]) * 1000))
            self.player.play()

        # Handle images
        elif ext in (".png", ".jpg", ".jpeg", ".gif"):
            pixmap = QPixmap(path)
            self.image_label.setPixmap(
                pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            self.image_label.show()
            self.video_widget.hide()
            self.player.stop()

    def current_media_path(self):
        src = self.player.source()
        if isinstance(src, QUrl):
            return src.toLocalFile()
        elif isinstance(src, str):
            return src
        return ""

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
 

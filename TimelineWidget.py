from PyQt6.QtWidgets import QWidget, QScrollArea, QHBoxLayout
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import QSize, Qt, QRectF, pyqtSignal

import os

class TimelineWidget(QWidget):
    playhead_moved = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timeline = []  # list of clips
        self.pixels_per_second = 100  # zoom level
        self.track_height = 60
        self.playhead_position = 0.0
        self.dragging_playhead = False
        self.setMinimumHeight(self.track_height + 20)

    def setTimeline(self, clips):
        """Update the displayed clips."""
        self.timeline = clips
        self.updateGeometry()
        self.adjustSize()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#222"))

        for clip in self.timeline:
            start_x = clip["start"] * self.pixels_per_second
            width = clip["duration"] * self.pixels_per_second
            rect = QRectF(start_x, 10, width, self.track_height)

            color = QColor("#44aaff") if clip["type"] == "video" else QColor("#88cc44")
            painter.fillRect(rect, color)

            painter.setPen(Qt.GlobalColor.white)
            painter.drawRect(rect)

            # Clip label
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(rect.adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, os.path.basename(clip["path"]))

        playhead_x = int(self.playhead_position * self.pixels_per_second)
        painter.setPen(QColor("#ffffff"))
        painter.drawLine(playhead_x, 0, playhead_x, self.height())

        painter.end()

    def sizeHint(self):
        if not self.timeline:
            return super().sizeHint()
        end_time = max(c["start"] + c["duration"] for c in self.timeline)
        width = int(end_time * self.pixels_per_second)
        return QSize(width, self.track_height + 20)
    
    def setPlayheadPosition(self, time_sec):
        self.playhead_position = max(0.0, time_sec)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = event.position().x(), event.position().y()
            playhead_x = int(self.playhead_position * self.pixels_per_second)
            clicked_clip = self.clip_at_pos(x, y)

            if abs(x - playhead_x) <= 5:
                # Dragging playhead
                self.dragging_playhead = True
                self.dragging_clip = None
            elif clicked_clip:
                # Dragging clip
                self.dragging_playhead = False
                self.dragging_clip = clicked_clip
                self.drag_offset = x - clicked_clip["start"] * self.pixels_per_second
            else:
                # Clicked empty space → move playhead
                self.dragging_playhead = False
                self.dragging_clip = None
                new_time = max(0, x / self.pixels_per_second)
                self.setPlayheadPosition(new_time)
                self.playhead_moved.emit(new_time)
                self.update()

    def mouseMoveEvent(self, event):
        x = event.position().x()

        if self.dragging_playhead:
            x = max(0, min(x, self.width()))
            new_time = x / self.pixels_per_second
            self.setPlayheadPosition(new_time)
            self.playhead_moved.emit(new_time)
            self.update()

        elif self.dragging_clip:
            new_start = (x - self.drag_offset) / self.pixels_per_second
            new_start = max(0, new_start)
            self.dragging_clip["start"] = new_start
            self.updateGeometry()
            self.update()


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_playhead = False
            if hasattr(self, "dragging_clip") and self.dragging_clip:
                self.dragging_clip = None


    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event):
        self.unsetCursor()

    def clip_at_pos(self, x, y):
        for clip in self.timeline:
            start_x = clip["start"] * self.pixels_per_second
            width = clip["duration"] * self.pixels_per_second
            rect = QRectF(start_x, 10, width, self.track_height)
            if rect.contains(x, y):
                return clip
        return None


    



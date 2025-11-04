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
        # self.current_time = 0.0 # Playhead time
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
        # self.current_time = time_sec
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            playhead_x = int(self.playhead_position * self.pixels_per_second)

            # Check if the click is near the playhead (within ±5 px)
            if abs(x - playhead_x) <= 5:
                # User clicked ON the playhead → enable dragging
                self.dragging_playhead = True
            else:
                # User clicked elsewhere → just move playhead instantly
                self.dragging_playhead = False
                new_time = max(0, x / self.pixels_per_second)
                self.setPlayheadPosition(new_time)
                self.playhead_moved.emit(new_time)
                self.update()

            # If clicked ON the playhead, still update position to allow immediate visual feedback
            if self.dragging_playhead:
                new_time = max(0, x / self.pixels_per_second)
                self.setPlayheadPosition(new_time)
                self.playhead_moved.emit(new_time)
                self.update()



    def mouseMoveEvent(self, event):
        if self.dragging_playhead:
            x = event.position().x()
            x = max(0, min(x, self.width()))
            new_time = x / self.pixels_per_second
            self.setPlayheadPosition(new_time)
            self.playhead_moved.emit(new_time)
            self.update()


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_playhead = False


    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event):
        self.unsetCursor()


    



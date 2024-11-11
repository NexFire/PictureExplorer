from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene,QMessageBox,QSizePolicy,QAbstractScrollArea,QLabel,QGraphicsOpacityEffect
from PyQt5.QtGui import QPixmap,QImage,QFont
from PyQt5.QtCore import Qt, QRectF,pyqtSignal
from pathlib import Path
import os

class ImageViewer(QGraphicsView):
    viewportChanged = pyqtSignal(float, float, float, float)
    mouseClicked=pyqtSignal(object)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        #self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.NoFocus)
        self.pixmap_item=None
        self.image=None
        self.dragging=False
        self.initial_zoom=1.0
        self.scrollbarVisible=False

        self.overlay_label = QLabel("Image", self)
        self.overlay_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 128); padding: 5px;")
        
        # Set up font and opacity effect for the overlay label
        font = QFont("Arial", 11)
        self.overlay_label.setFont(font)
        
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.9)  # Set the desired transparency level
        self.overlay_label.setGraphicsEffect(opacity_effect)
        self.move_label()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.move_label()
    def move_label(self):
        label_height = self.overlay_label.sizeHint().height()
        padding = 15
        y = self.height() - label_height - (self.horizontalScrollBar().height() if self.horizontalScrollBar().isVisible() else 0)
        self.overlay_label.move(0, y)

    def load_image(self,image_path,viewport=None,common_path=None):
        self.image=QImage(image_path)
        if self.image.isNull():
            self.show_error("Error","Failed to load image")
            return
        pixmap = QPixmap.fromImage(self.image)
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)
        self.pixmap_item=self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        if viewport:
            self.fitInView(self.scene.sceneRect(),Qt.KeepAspectRatio)
            self.update_view_port(*viewport)
        else:
            self.fitInView(self.scene.sceneRect(),Qt.KeepAspectRatio)

        if(os.path.samefile(common_path,image_path)):
            parts=Path(os.path.dirname(image_path)).parts
            self.label_set_text(str(Path(*parts[len(parts)-3:len(parts)])))
        else:
            self.label_set_text( os.path.relpath(os.path.dirname(image_path),common_path))
        self.update()

    def setSize(self,width,height):
        self.setMinimumSize(width,height)

    def label_set_text(self,text):
        self.overlay_label.setText(text)
        self.overlay_label.adjustSize()
        self.move_label()
    #The x and y is in percentage so that it handles even when two different sizes of pictures are inserted format is 0-1
    def update_view_port(self,topLX,topLY,width,height):
        if self.image is None:
            return
        img_width, img_height = self.image.width(), self.image.height()     
        rect=QRectF(topLX*img_width,topLY*img_height,width*img_width,height*img_height)
        self.fitInView(rect,Qt.KeepAspectRatio)

    def show_error(self,title,message):
        alert=QMessageBox()
        alert.setWindowTitle(title)
        alert.setText(message)
        alert.setIcon(QMessageBox.warning)
        alert.setStandardButtons(QMessageBox.Ok)
        alert.exec_()
    
    def get_current_viewport_percentages(self):
        if self.image is None:
            return None

        # Get the visible scene rect in view
        visible_scene_rect = self.mapToScene(self.viewport().rect()).boundingRect()

        # Calculate percentages based on the image dimensions
        img_width, img_height = self.image.width(), self.image.height()
        topLX = (visible_scene_rect.left() / img_width)
        topLY = (visible_scene_rect.top() / img_height)
        width = (visible_scene_rect.width() / img_width) 
        height = (visible_scene_rect.height() / img_height)

        return topLX, topLY, width,height

    #Reseting the view
    def reset_view(self):
        if self.image:
            self.fitInView(self.scene.sceneRect(),Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(1.25, 1.25)  # Zoom in
        else:
            self.scale(0.8, 0.8)  # Zoom out
        if self.horizontalScrollBar().isVisible() and not self.scrollbarVisible:
            self.move_label()
            self.scrollbarVisible=True
        else:
            if self.scrollbarVisible:
                self.move_label()
                self.scrollbarVisible=False

        # Emit the updated viewport after zooming
        self.emit_viewport_change()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.is_dragging = False
        self.emit_viewport_change()
        if event.modifiers() & Qt.ControlModifier:
            self.mouseClicked.emit(self)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.emit_viewport_change()
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.is_dragging = True

    def emit_viewport_change(self):
        topLX, topLY, width, height = self.get_current_viewport_percentages()
        self.viewportChanged.emit(topLX, topLY, width, height)
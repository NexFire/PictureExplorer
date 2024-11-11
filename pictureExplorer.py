#je potřeba pak optimalizovat commonpath tahání
#optimalizovat label update
#dořešit bugy s zobrazováním obrázků proč se při prvním loadu nezobrazuje správně danej obrázek
import sys
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication,QMainWindow,QPushButton,QAction,QStatusBar,QWidget,QGridLayout,QVBoxLayout,QMessageBox,QFileDialog,QHBoxLayout,QSpacerItem,QSizePolicy,QGraphicsView,QGraphicsScene
from imageViewer import ImageViewer
from PyQt5.QtCore import Qt
import os
import glob
import math

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Picture Explorer")
        self.setMinimumSize(400, 300)
        self.initParts()
        self.initMenuBar()
        self.setStatusBar(QStatusBar(self))
        self.images=[]
        self.image_index=0
        self.images_max_index=0
        self.isolated_views=[]
        self.viewport=None


    def initParts(self):
        central_widget=QWidget()
        self.main_layout=QGridLayout()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)
        self.viewers=[]

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def show_error(self,title,message):
        alert=QMessageBox()
        alert.setWindowTitle(title)
        alert.setText(message)
        alert.setIcon(QMessageBox.warning)
        alert.setStandardButtons(QMessageBox.Ok)
        alert.exec_()
    
    def add_dir(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Select Directory",options=QFileDialog.DontUseNativeDialog)
        if not selected_dir:
            return
        image_extensions = ("*.jpg", "*.jpeg", "*.png")
        image_paths=[]
        for extension in image_extensions:
            image_paths.extend(glob.glob(os.path.join(selected_dir,extension)))
        image_paths.sort(key=lambda x: os.path.basename(x).lower())
        self.images.append(image_paths)
        new_viewer = ImageViewer(self)
        self.viewers.append(new_viewer)
        self.update_layout()
        self.calculate_max_index()

    def update_layout(self):
        self.clear_grid_layout()
        
        if(len(self.viewers)==1):
            self.max_per_row=1
        if(len(self.viewers)>1):
            self.max_per_row=2
        if(len(self.viewers)>4):
            self.max_per_row=3

        for i, viewer in enumerate(self.viewers):
            self.main_layout.addWidget(viewer,i//self.max_per_row,i%self.max_per_row)

        self.main_layout.update()
        QApplication.processEvents()
        for i in range(math.ceil(len(self.viewers)/self.max_per_row)):
            self.main_layout.setRowStretch(i, 1)  # Make all rows stretch equally
        self.main_layout.setRowStretch(math.ceil(len(self.viewers)/self.max_per_row), 0)
        for j in range(self.max_per_row):
            self.main_layout.setColumnStretch(j, 1)
        self.main_layout.setColumnStretch(self.max_per_row,0)

        self.update_connections()
        # Update the layout to show the changes
        self.main_layout.update()
        
    def update_connections(self):
        for viewer in self.viewers:
            viewer.mouseClicked.connect(self.mouse_click_event)
            if viewer not in self.isolated_views:
                viewer.viewportChanged.connect(self.get_viewport)
            for subViewer in self.viewers:
                if viewer!=subViewer and (viewer not in self.isolated_views) and (subViewer not in self.isolated_views):
                    viewer.viewportChanged.connect(subViewer.update_view_port)

    def get_viewport(self,topLX,topLY,width,height):
        self.viewport=(topLX,topLY,width,height)

    def update_picture(self):
        if len(self.images)<=0:
            return
        common_path=os.path.commonpath([self.images[viewer_index][self.image_index] for viewer_index in range(len(self.viewers))])
        for viewer_index in range(len(self.viewers)):
            self.viewers[viewer_index].load_image(self.images[viewer_index][self.image_index],self.viewport,common_path)

    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Left:
            self.image_index-=1
            self.check_max_index()
            self.update_picture()
        elif event.key() == Qt.Key_Right:
            self.image_index+=1
            self.check_max_index()
            self.update_picture()


    def mouse_click_event(self, widget):
        for index,viewer in enumerate(self.viewers):
            if widget==viewer:
                del self.viewers[index]
                del self.images[index]
                break
        for index,viewer in enumerate(self.isolated_views):
            if widget==viewer:
                del self.isolated_views[index]
                break
        self.update_layout()
        self.update_picture()


    def calculate_max_index(self):
        self.images_max_index=min(len(sub_list) for sub_list in self.images)
        self.check_max_index()
        self.update_picture()


    def check_max_index(self):
        if self.image_index>=self.images_max_index:
            self.image_index=self.images_max_index-1
        elif self.image_index<0:
            self.image_index=0

    def remove_dir(self):
        pass

    def initMenuBar(self):
        menu_bar=self.menuBar()
        #This adds the menuBar
        file_menu=menu_bar.addMenu("&File")
        #This creates the actions in menu bar
        #---Add 
        self.add_action=QAction("Add",self)
        self.add_action.setStatusTip("This will add the directory")
        self.add_action.setShortcut("Ctrl+A")
        self.add_action.triggered.connect(self.add_dir)

        #---Remove
        self.remove_action=QAction("Remove",self)
        self.remove_action.setStatusTip("This will remove the directory")
        self.remove_action.setShortcut("Ctrl+R")
        self.remove_action.triggered.connect(self.remove_dir)

        #This adds the actions into the menus
        file_menu.addAction(self.add_action)
        file_menu.addAction(self.remove_action)


    def clear_grid_layout(self):
        # Remove all widgets and items from the grid layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)  # Deletes the widget properly
                del widget
            else:
                # If it's a nested layout or spacer, remove it as well
                layout_item = item.layout()
                if layout_item is not None:
                    self.clear_nested_layout(layout_item)
            self.main_layout.removeItem(item)

    def clear_nested_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_nested_layout(item.layout())
            layout.removeItem(item)



if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



import sys, csv, os
from PyQt6 import QtWidgets, QtGui, QtCore
from PIL import Image

class MapEditor(QtWidgets.QMainWindow):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("軽量マップ座標エディタ")
        self.resize(1200, 800)

        # --- 状態 ---
        self.points = []        # [(x,y) 画像座標]
        self.selected_index = None
        self.drag_point = None
        self.drag_map = False
        self.last_mouse = None
        self.scale = 1.0
        self.min_scale = 0.2
        self.max_scale = 5.0
        self.current_csv_path = None

        # --- 画像 ---
        self.img = Image.open(image_path).convert("RGBA")
        self.img_width, self.img_height = self.img.size
        self.qpix = QtGui.QPixmap.fromImage(
            QtGui.QImage(self.img.tobytes(), self.img_width, self.img_height, QtGui.QImage.Format.Format_RGBA8888)
        )

        # --- GraphicsView/Scene ---
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        self.setCentralWidget(self.view)

        self.img_item = QtWidgets.QGraphicsPixmapItem(self.qpix)
        self.scene.addItem(self.img_item)

        self.point_items = []

        # --- UI ---
        dock = QtWidgets.QDockWidget("操作パネル")
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        w = QtWidgets.QWidget()
        dock.setWidget(w)
        layout = QtWidgets.QVBoxLayout(w)

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)
        self.list_widget.currentRowChanged.connect(self.select_point)

        btn_edit = QtWidgets.QPushButton("点編集")
        btn_edit.clicked.connect(self.edit_point)
        layout.addWidget(btn_edit)

        btn_delete = QtWidgets.QPushButton("点削除")
        btn_delete.clicked.connect(self.delete_point)
        layout.addWidget(btn_delete)

        btn_load = QtWidgets.QPushButton("CSV読み込み")
        btn_load.clicked.connect(self.load_csv)
        layout.addWidget(btn_load)

        btn_save = QtWidgets.QPushButton("CSV保存")
        btn_save.clicked.connect(self.save_csv)
        layout.addWidget(btn_save)

        btn_finish = QtWidgets.QPushButton("完了終了")
        btn_finish.clicked.connect(self.close)
        layout.addWidget(btn_finish)
        layout.addStretch()

        # --- イベント ---
        self.view.viewport().installEventFilter(self)
        self.view.setMouseTracking(True)

    # --- ポイント描画（画像座標をScene座標に変換） ---
    def update_points(self):
        for item in self.point_items:
            self.scene.removeItem(item)
        self.point_items.clear()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        img_pos = self.img_item.pos()
        for i, (x, y) in enumerate(self.points):
            brush = QtGui.QBrush(QtGui.QColor("white")) if i==self.selected_index else QtGui.QBrush(QtGui.QColor("red"))
            scene_x = x * self.scale + img_pos.x()
            scene_y = y * self.scale + img_pos.y()
            ellipse = self.scene.addEllipse(scene_x-4, scene_y-4, 8, 8, brush=brush)
            self.point_items.append(ellipse)
            self.list_widget.addItem(f"{i+1}: ({int(x)},{int(y)})")
        self.list_widget.blockSignals(False)

    def select_point(self, index):
        if index >= 0 and index < len(self.points):
            self.selected_index = index
        else:
            self.selected_index = None
        self.update_points()

    def edit_point(self):
        if self.selected_index is None: return
        x, y = self.points[self.selected_index]
        nx, ok1 = QtWidgets.QInputDialog.getInt(self, "X座標", "X座標:", int(x))
        if not ok1: return
        ny, ok2 = QtWidgets.QInputDialog.getInt(self, "Y座標", "Y座標:", int(y))
        if not ok2: return
        self.points[self.selected_index] = (nx, ny)
        self.update_points()

    def delete_point(self):
        if self.selected_index is None: return
        self.points.pop(self.selected_index)
        self.selected_index = None
        self.update_points()

    # --- CSV ---
    def load_csv(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "CSV読み込み", filter="CSV Files (*.csv)")
        if not path: return
        self.points.clear()
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    x = float(row.get('x', 0))
                    y = float(row.get('y', 0))
                    self.points.append((x, y))
                except: continue
        self.current_csv_path = path
        self.update_points()

    def save_csv(self):
        if not self.points:
            QtWidgets.QMessageBox.warning(self, "警告", "保存する点がありません")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "CSV保存", filter="CSV Files (*.csv)")
        if not path: return
        fieldnames = ['x','y']
        if self.current_csv_path and os.path.exists(self.current_csv_path):
            with open(self.current_csv_path,newline='',encoding='utf-8') as f:
                reader = csv.DictReader(f)
                extra_fields = [fn for fn in reader.fieldnames if fn not in fieldnames]
                fieldnames += extra_fields
        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i,(x,y) in enumerate(self.points):
                row = {'x':x,'y':y}
                writer.writerow(row)
        self.current_csv_path = path

    # --- イベントフィルター ---
    def eventFilter(self, source, event):
        pos = None
        if hasattr(event,'position'):
            pos = self.view.mapToScene(event.position().toPoint())
        elif hasattr(event,'pos'):
            pos = self.view.mapToScene(event.pos())
        if pos is None: return super().eventFilter(source,event)

        img_pos = self.img_item.pos()

        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if event.button() == QtCore.Qt.MouseButton.RightButton:
                self.drag_map = True
                self.last_mouse = pos
            elif event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier:
                # 選択も画像座標に変換して判定
                nearest, idx = self.find_nearest(pos)
                if idx is not None: self.selected_index = idx
            elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                if self.selected_index is not None:
                    self.drag_point = self.selected_index
            else:
                # 追加時だけカメラ逆算して画像座標に変換
                img_x = (pos.x() - img_pos.x()) / self.scale
                img_y = (pos.y() - img_pos.y()) / self.scale
                self.points.append((img_x, img_y))
            self.update_points()

        elif event.type() == QtCore.QEvent.Type.MouseMove:
            if self.drag_map and self.last_mouse is not None:
                delta = pos - self.last_mouse
                self.img_item.moveBy(delta.x(), delta.y())
                self.last_mouse = pos
                self.update_points()
            elif self.drag_point is not None:
                img_x = (pos.x() - img_pos.x()) / self.scale
                img_y = (pos.y() - img_pos.y()) / self.scale
                self.points[self.drag_point] = (img_x, img_y)
                self.update_points()

        elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            self.drag_map = False
            self.drag_point = None

        elif event.type() == QtCore.QEvent.Type.Wheel:
            old_scale = self.scale
            delta = event.angleDelta().y()
            factor = 1.1 if delta>0 else 1/1.1
            new_scale = max(self.min_scale, min(self.max_scale, old_scale*factor))
            factor = new_scale / old_scale
            self.scale = new_scale
            self.img_item.setScale(new_scale)
            # マウス中心で位置調整
            img_pos = self.img_item.pos()
            dx = pos.x() - (pos.x() - img_pos.x()) * factor - img_pos.x()
            dy = pos.y() - (pos.y() - img_pos.y()) * factor - img_pos.y()
            self.img_item.moveBy(dx, dy)
            self.update_points()

        return super().eventFilter(source, event)

    def find_nearest(self, pos, max_dist=20):
        if not self.points: return None, None
        img_pos = self.img_item.pos()
        pts_scene = [(x*self.scale+img_pos.x(), y*self.scale+img_pos.y()) for x,y in self.points]
        dist = [((sx-pos.x())**2 + (sy-pos.y())**2)**0.5 for sx,sy in pts_scene]
        idx = dist.index(min(dist))
        if dist[idx] <= max_dist: return pts_scene[idx], idx
        return None, None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "画像選択", filter="画像 (*.png *.jpg *.bmp)")
    if not path: sys.exit()
    win = MapEditor(path)
    win.show()
    sys.exit(app.exec())

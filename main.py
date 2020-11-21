import cv2
import sys
import numpy as np
from PIL import Image
from config import SettingsData, WaysData
from PyQt5 import QtCore, QtGui, QtWidgets
# библиотека с помощью которой можно перевести opencv изображение в изображение, для библиотеки pyqt
# для установки pip install qimage2ndarray==1.8.3
import qimage2ndarray


class Handler:
    def __init__(self, wb, inverse, flips_v, flips_g, brightness, contrast, face):
        self.wb = wb
        self.inverse = inverse
        self.flips_v = flips_v
        self.flips_g = flips_g
        self.contrast = contrast
        self.face = face
        self.brightness = brightness

        self.face_cascade_db = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def wb_handler(self, frame):
        if self.wb.isChecked():
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame

    def inverse_handler(self, frame):
        if self.inverse.isChecked():
            return 255 - frame
        return frame

    def flips_handler(self, frame):
        if self.flips_v.isChecked():
            frame = cv2.flip(frame, 0)

        if self.flips_g.isChecked():
            frame = cv2.flip(frame, 1)

        return frame

    def brightness_handler(self, frame):
        value = (self.brightness.value() + 50) / 100

        def contrast(c):
            return c * value

        img = Image.fromarray(frame)
        img = img.point(contrast)

        return np.asarray(img)

    def contrast_handler(self, frame):
        level = self.contrast.value()
        if level == 0:
            return frame

        factor = (259 * (level + 255)) / (255 * (259 - level))

        def contrast(c):
            return 128 + factor * (c - 128)

        img = Image.fromarray(frame)
        img = img.point(contrast)

        return np.asarray(img)

    def face_handler(self, frame):
        if self.face.isChecked():
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade_db.detectMultiScale(gray, 1.1, 19)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 200, 70), 2)
        return frame

    def get_num_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade_db.detectMultiScale(gray, 1.1, 19)
        return len(faces)

    def get_wb(self):
        return self.wb.isChecked()

    def get_inverse(self):
        return self.inverse.isChecked()

    def get_flips_v(self):
        return self.flips_v.isChecked()

    def get_flips_g(self):
        return self.flips_g.isChecked()

    def get_face(self):
        return self.face.isChecked()

    def get_brightness(self):
        return self.brightness.value()

    def get_contrast(self):
        return self.contrast.value()

    def __call__(self, frame):
        frame = self.face_handler(frame)
        frame = self.contrast_handler(frame)
        frame = self.brightness_handler(frame)
        frame = self.wb_handler(frame)
        frame = self.inverse_handler(frame)
        frame = self.flips_handler(frame)
        return frame


class Window(QtWidgets.QTabWidget):
    def __init__(self, width=640, heigh=480, fps=30):  # размеры видеоокна, кол-во кадров в секунду
        QtWidgets.QWidget.__init__(self)
        self.video_size = QtCore.QSize(width, heigh)
        self.camera_capture = cv2.VideoCapture(cv2.CAP_DSHOW)
        self.video_captutre = cv2.VideoCapture()

        self.video = False
        self.pause = False
        self.frame_timer = QtCore.QTimer()
        self.fps = fps
        # main window
        self.frame_label = QtWidgets.QLabel(self)
        self.quit_button = QtWidgets.QPushButton(self)
        self.pause_button = QtWidgets.QPushButton(self)
        self.make_photo_button = QtWidgets.QPushButton(self)
        self.advanced_setting_check_box = QtWidgets.QCheckBox(self)
        self.open_from_database_button = QtWidgets.QPushButton(self)

        # advanced settings layout
        self.contrast_label = QtWidgets.QLabel(self)
        self.wb_check_box = QtWidgets.QCheckBox(self)
        self.contrast_slider = QtWidgets.QSlider(self)
        self.brightness_label = QtWidgets.QLabel(self)
        self.face_check_box = QtWidgets.QCheckBox(self)
        self.brightness_slider = QtWidgets.QSlider(self)
        self.flip_v_check_box = QtWidgets.QCheckBox(self)
        self.flip_g_check_box = QtWidgets.QCheckBox(self)
        self.db_button_open = QtWidgets.QPushButton(self)
        self.db_button_save = QtWidgets.QPushButton(self)
        self.open_all_button = QtWidgets.QPushButton(self)
        self.inversion_colors_check_box = QtWidgets.QCheckBox(self)

        self.advanced_setting_widgets = [self.wb_check_box,
                                         self.inversion_colors_check_box,
                                         self.flip_v_check_box,
                                         self.flip_g_check_box,
                                         self.face_check_box,
                                         self.brightness_label,
                                         self.brightness_slider,
                                         self.contrast_label,
                                         self.contrast_slider,
                                         self.db_button_save,
                                         self.db_button_open]

        self.main_layout = QtWidgets.QGridLayout(self)
        self.advanced_setting_layout = QtWidgets.QVBoxLayout(self)
        self.temp_layout = QtWidgets.QVBoxLayout(self)

        self.handler = Handler(wb=self.wb_check_box,
                               inverse=self.inversion_colors_check_box,
                               flips_v=self.flip_v_check_box,
                               flips_g=self.flip_g_check_box,
                               brightness=self.brightness_slider,
                               contrast=self.contrast_slider,
                               face=self.face_check_box)

        self.setup_ui()
        self.setup_camera(fps)

    def setup_ui(self):
        '''настройка виджетов pyqt'''
        self.frame_label.setFixedSize(self.video_size)

        self.brightness_slider.setValue(50)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setOrientation(QtCore.Qt.Horizontal)

        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(100)
        self.contrast_slider.setOrientation(QtCore.Qt.Horizontal)

        self.quit_button.setText('Quit')
        self.pause_button.setText('Pause')
        self.open_all_button.setText('Открыть')
        self.brightness_label.setText('Яркость')
        self.contrast_label.setText('Контрастность')
        self.make_photo_button.setText('Сделать фото')
        self.db_button_open.setText('Открыть настройки')
        self.face_check_box.setText('Распознавание лиц')
        self.db_button_save.setText('Сохранить настройки')
        self.wb_check_box.setText('Черно-белое изображение')
        self.flip_v_check_box.setText('Отразить по вертикали')
        self.flip_g_check_box.setText('Отразить по горизонтали')
        self.inversion_colors_check_box.setText('Инвертировать цвета')
        self.open_from_database_button.setText('Поиск по количеству лиц')
        self.advanced_setting_check_box.setText('Открыть расширенные настройки')

        self.contrast_label.setMaximumHeight(20)
        self.brightness_label.setMaximumHeight(20)

        self.quit_button.clicked.connect(self.close_win)
        self.pause_button.clicked.connect(self.play_pause)
        self.open_all_button.clicked.connect(self.open_file)
        self.db_button_open.clicked.connect(self.open_settigns)
        self.db_button_save.clicked.connect(self.save_settings)
        self.make_photo_button.clicked.connect(self.save_photo)
        self.open_from_database_button.clicked.connect(self.open_from_database)
        self.advanced_setting_check_box.stateChanged.connect(self.hide_advanced_widgets)

        self.advanced_setting_layout.addWidget(self.advanced_setting_check_box)

        for widget in self.advanced_setting_widgets:
            self.temp_layout.addWidget(widget)
        self.advanced_setting_layout.addLayout(self.temp_layout)

        self.main_layout.addWidget(self.frame_label, 0, 0, 1, 3)  # y, x, sizey, sizex
        self.main_layout.addWidget(self.quit_button, 2, 4, 1, 1)
        self.main_layout.addWidget(self.pause_button, 2, 3, 1, 1)
        self.main_layout.addWidget(self.open_all_button, 2, 1, 1, 1)
        self.main_layout.addWidget(self.open_all_button, 2, 1, 1, 1)
        self.main_layout.addWidget(self.make_photo_button, 2, 0, 1, 1)
        self.main_layout.addWidget(self.open_from_database_button, 2, 2, 1, 1)

        self.main_layout.addLayout(self.advanced_setting_layout, 0, 3, 2, 1)

        for widget in self.advanced_setting_widgets:
            widget.hide()

        self.setLayout(self.main_layout)

    def setup_camera(self, fps):
        '''подключение камеры и её настройка'''
        self.camera_capture.set(3, self.video_size.width())
        self.camera_capture.set(4, self.video_size.height())

        self.frame_timer.timeout.connect(self.display_video_stream)
        self.frame_timer.start(int(1000 / fps))

    def display_video_stream(self):
        '''функция транслирующая изображение с камеры на виджет'''
        if not self.pause:
            if self.video:
                try:
                    ret, frame = self.video_captutre.read()
                    frame = cv2.resize(frame, (self.video_size.width(), self.video_size.height()),
                                       interpolation=cv2.INTER_AREA)
                    self.old_frame = frame
                except Exception as E:
                    print(E)
                    frame = self.old_frame
            else:
                ret, frame = self.camera_capture.read()
                frame = cv2.flip(frame, 1)
                self.old_frame = frame
        else:
            ret = True
            frame = self.old_frame

        if not ret:
            return False

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = self.handler(frame)

        image = qimage2ndarray.array2qimage(frame)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))

    def play_pause(self, *a):
        if a[0]:
            self.pause = False

        if self.pause:
            self.pause_button.setText('Pause')
        else:
            self.pause_button.setText('Play')

        if a[0]:
            self.pause_button.setText('Переключить на камеру')

        self.pause = not self.pause

    def hide_advanced_widgets(self):
        if self.advanced_setting_check_box.isChecked():
            for widget in self.advanced_setting_widgets:
                widget.show()
        else:
            for widget in self.advanced_setting_widgets:
                widget.hide()

    def save_photo(self):
        way = list(QtWidgets.QFileDialog.getSaveFileName(self, 'Save photo',
                                                         filter='All Files (*);;*.png;;*.jpg'))
        if way[0]:
            name = way[0].split('/')[-1]
            WaysData.create(way=way[0], name=name,
                            additional=self.handler.get_num_faces(self.old_frame))
            image = cv2.cvtColor(self.handler(self.old_frame), cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image, mode='RGB')
            image.save(way[0])

    def open_photo(self, way):
        # way = QtWidgets.QFileDialog.getOpenFileName(self, 'Open photo', '')[0]
        if isinstance(way, tuple):
            way = way[0]
        if way:
            self.video = False
            image = cv2.cvtColor(qimage2ndarray.imread(way), cv2.COLOR_BGR2RGB)

            self.old_frame = cv2.resize(image,
                                        (self.video_size.width(), self.video_size.height()),
                                        interpolation=cv2.INTER_AREA)
            self.play_pause(1)

    def open_video(self, way):
        if self.open_all_button.text() == 'Открыть':
            # way = QtWidgets.QFileDialog.getOpenFileName(self, 'Open', filter='Video: (*.mp4)')
            if way[0]:
                self.video_captutre.open(way[0])
                self.video = True
                self.open_all_button.setText('Закрыть видео')
                if self.pause_button.text() == 'Переключить на камеру':
                    self.pause_button.click()
        else:
            self.open_all_button.setText('Открыть')
            self.pause_button.setText('Pause')
            self.video = False
            self.pause = False

    def open_file(self):
        if self.open_all_button.text() != 'Закрыть видео':
            try:
                video_expansions = {'.mp4', '.mpg', '.mpeg'}
                photo_expansions = {'.jpg', '.jpeg', '.bmp', '.png'}
                all_expansions = video_expansions | photo_expansions

                way = QtWidgets.QFileDialog.getOpenFileName(self, 'Open',
                                                            filter=f'All Files (*);;{";;".join("*" + i for i in all_expansions)}')

                if way[1].replace('*', '') in video_expansions or \
                        any(map(lambda x: x in way[0].split(' / ')[-1], video_expansions)):
                    self.open_video(way)
                    print('video')

                elif way[1].replace('*', '') in photo_expansions or \
                        any(map(lambda x: x in way[0].split('/')[-1], photo_expansions)):
                    self.open_photo(way)
            except Exception as e:
                print(e)
        else:
            self.open_video(None)

    def open_from_database(self):
        faces_quantity, ok = QtWidgets.QInputDialog.getInt(self, 'Открыть',
                                                           'Введите количество лиц на фото')
        ways = {}
        for i in WaysData.select():
            if i.additional == faces_quantity:
                ways[i.name] = (i.way, i.id)

        if ways:
            name, ok = QtWidgets.QInputDialog.getItem(self, 'Photo', 'Выберите фото:',
                                                      [name for name in ways], 0, False)
            if name and ok:
                if self.open_all_button.text() == 'Закрыть видео':
                    self.open_all_button.click()
                try:
                    self.open_photo(way=ways[name][0])
                except:
                    QtWidgets.QMessageBox.critical(self, "Ошибка",
                                                   "Выбранный файл был перемещен или удален.\n"
                                                   "Данное имя было автоматически удалено.",
                                                   QtWidgets.QMessageBox.Ok)
                    WaysData.delete_by_id(ways[name][1])
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка",
                                           "Фото с таким количеством лиц не найдено",
                                           QtWidgets.QMessageBox.Ok)

    def save_settings(self):
        names = [elem.name for elem in SettingsData.select()]
        name, ok = QtWidgets.QInputDialog.getText(self, 'Name', 'Введите имя настроек')
        if name.replace(' ', ''):
            while name in names:
                name, ok = QtWidgets.QInputDialog.getText(self, 'Name', 'Это имя уже занято')
        if name.replace(' ', ''):
            SettingsData.create(name=name,
                                wb=self.handler.get_wb(),
                                invert=self.handler.get_inverse(),
                                flip_v=self.handler.get_flips_v(),
                                flip_g=self.handler.get_flips_g(),
                                face=self.handler.get_face(),
                                brightnes=self.handler.get_brightness(),
                                contrast=self.handler.get_contrast())

    def open_settigns(self):
        names = [elem.name for elem in SettingsData.select()]
        if names:
            name, ok = QtWidgets.QInputDialog.getItem(self, 'Settigns', 'Выберите настройки:',
                                                      names, 0, False)
            if name and ok:
                for elem in SettingsData.select():
                    if elem.name == name:
                        current = elem
                        break

                self.wb_check_box.setChecked(current.wb)
                self.inversion_colors_check_box.setChecked(current.invert)
                self.flip_v_check_box.setChecked(current.flip_v)
                self.flip_g_check_box.setChecked(current.flip_g)
                self.face_check_box.setChecked(current.face)
                self.brightness_slider.setValue(current.brightnes)
                self.contrast_slider.setValue(current.contrast)
        else:
            SettingsData.create(name='default',
                                wb=False,
                                invert=False,
                                flip_v=False,
                                flip_g=False,
                                face=False,
                                brightnes=1,
                                contrast=0)
            self.open_settigns()

    def close_win(self):
        '''закрывает все окна opencv и pyqt'''
        self.camera_capture.release()
        self.video_captutre.release()
        cv2.destroyAllWindows()
        self.close()


if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication(sys.argv)
        ex = Window()
        ex.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
        cv2.destroyAllWindows()
        exit(0)

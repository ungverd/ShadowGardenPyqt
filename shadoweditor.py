import sys
import os
from shutil import copyfile
from enum import Enum
import wave
import csv
import subprocess
from typing import List, Dict
# import serial
# import Usbhost

from PyQt5 import QtCore, QtGui, QtWidgets
from loguru import logger

import ui

_translate = QtCore.QCoreApplication.translate

FRAMERATE = 48000
SAMPLEWIDTH = 2  # 2 bytes == 16 bits
SAMPLEFMT = 's16'  # ffmpeg format

BLACK = (0, 0, 0)
RED = (200, 0, 0)
GRAY = (100, 100, 100)


# EMULATION WITH KEYS
class Usbhost:
    @staticmethod
    def get_device_port():
        return 500


class serial:
    class Serial(QtWidgets.QWidget):
        def __init__(self):
            self.i = 0
            self.values = list()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def readall(self):
            res = b'\r'.join(b'Card: 1234 %i' % i for i in self.values)
            self.values = []
            return res
# end of emulation


class FileFormat(Enum):
    NOT_MUSIC = 1
    CORRECT = 2
    INCORRECT = 3


class State(Enum):
    NOTHING_SELECTED = 1
    DEST_SELECTED = 2
    SOURCE_SELECTED = 3
    FILES_READY = 4


class ShadowUi(QtWidgets.QMainWindow, ui.Ui_MainWindow):

    #  EMULATION WITH KEYS #
    def keyPressEvent(self, e):
        if hasattr(self, 'ser'):
            self.ser.values.append(self.ser.i)
            self.ser.i += 1
    # END OF EMULATION

    def __init__(self):
        super().__init__()
        self.state: State = State.NOTHING_SELECTED
        self.setupUi(self)
        self.BtnCreateDest.clicked.connect(self.create_dest_folder)
        self.BtnChooseDest.clicked.connect(self.select_folder)
        self.LinePathDest.editingFinished.connect(self.get_folder_from_field)
        self.BtnChooseSource.clicked.connect(self.select_folder)
        self.BtnConvert.clicked.connect(lambda: self.process_files(self.copy_and_convert))
        self.BtnSkip.clicked.connect(lambda: self.process_files(self.copyOnly))
        self.LinePathSource.editingFinished.connect(self.get_folder_from_field)

        self.folder_names: List[str] = list()
        self.dest: str = ""
        self.source: str = ""
        self.classify_dict: Dict[str, FileFormat] = dict()
        self.filesInFolder = QtGui.QStandardItemModel()
        self.LstFiles.setModel(self.filesInFolder)
        self.foldersInFolder = QtGui.QStandardItemModel()
        self.LstDirs.setModel(self.foldersInFolder)

        self.timer = QtCore.QTimer()
        self.BtnCards.clicked.connect(self.applyCards)

    def select_folder(self):
        """
        selects and returns folder and calls ui function
        :return:
        """
        sender = self.sender()
        (ui_function, folder_field) = (self.select_dest_ui, 'dest') if sender == self.BtnChooseDest \
            else (self.select_target_ui_and_convert, 'source')
        title = "Выберите папку"
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, title, os.path.dirname(os.path.abspath(__file__)))
        if folder:
            setattr(self, folder_field, folder)
            ui_function()

    def create_dest_folder(self):
        """
        creates new folder in current folder and writes it name to dest field.
        If New name is already used, nes folder's name is 'New1" etc
        :return:
        """
        cur_path = os.getcwd()
        full_path = os.path.join(cur_path, "new")
        if not os.path.isdir(full_path):
            os.mkdir(full_path)
        else:
            i = 1
            new_name = full_path + str(i)
            while os.path.isdir(new_name):
                i += 1
                new_name = full_path + str(i)
            os.mkdir(new_name)
            full_path = new_name
        self.dest = full_path
        self.select_dest_ui()

    def get_folder_from_field(self):
        """
        writes manually added path to dist/source field and calls corresponding ui function
        """
        sender = self.sender()
        folder = sender.text()
        ui_function, field_folder = (self.select_dest_ui, 'dest') if sender == self.LinePathDest \
            else (self.select_target_ui_and_convert, 'source')
        if os.path.exists(folder):
            result_path = folder if os.path.isdir(folder) else os.path.split(folder)[0]
            setattr(self, field_folder,result_path)
            ui_function()
        elif sender.text():
            error_message("Выбранной папки не существует")

    def select_dest_ui(self):
        """
        makes ui for state "destination folder selected"
        :return:
        """
        self.source = ""
        self.classify_dict = dict()
        self.state = State.DEST_SELECTED
        self.BtnChooseSource.setEnabled(True)
        self.LinePathSource.setEnabled(True)
        self.LinePathSource.clear()
        self.filesInFolder.clear()
        self.BtnConvert.setEnabled(False)
        self.BtnSkip.setEnabled(False)
        self.foldersInFolder.clear()
        self.BtnCards.setEnabled(False)
        self.LblDest.setText("Выбрана папка: %s" % self.dest)
        self.LblSource.setText("Выбрана папка:")

    def insert_item_with_color(self, text: str, color):
        """
        addds coloured item
        :param text: text for item
        :param color: color for item
        :return:
        """
        item = QtGui.QStandardItem(text)
        item.setForeground(QtGui.QBrush(QtGui.QColor(*color)))
        self.filesInFolder.appendRow(item)

    def select_target_ui_and_convert(self):
        """
        scans all files in selected folder and adds them to file list
        correct files have black font color, not sound files have gray font color and sound files with incorrect format
        have red colour and we may convert them
        :return:
        """
        for filename in os.listdir(self.source):
            src: str = os.path.join(self.source, filename)
            try:
                res = check_file_format(src)
                self.classify_dict[src] = res
                if res == FileFormat.CORRECT:
                    self.insert_item_with_color(filename, BLACK)
                    self.BtnSkip.setEnabled(True)
                elif res == FileFormat.NOT_MUSIC:
                    self.insert_item_with_color(filename, GRAY)
                else:
                    self.insert_item_with_color(filename, RED)
                    self.BtnConvert.setEnabled(True)
            except (FileNotFoundError, OSError):
                error_message("ошибка открытия файла %s" % src)
                continue

    def copy_and_convert(self, src: str, dst: str, convert: bool) -> bool:
        """
        convert file from src path to dest path using correct format (wav, 16bit, 48000) or just copy in format is good
        :param src: source file
        :param dst:dest file
        :return: status of operation
        """
        res = self.classifyDict[src]
        if res == FileFormat.good:
            if src != dst:
                copyfile(src, dst)
            return True
        elif res == FileFormat.bad and convert:
            code = subprocess.call('ffmpeg -i "%s" -ar %d -sample_fmt %s "%s"' %
                                   (src, FRAMERATE, SAMPLEFMT, dst), shell=True)
            if code == 0:
                return True
            else:
                print("Error converting file %s" % src)
                return False
        return False

    def process_files(self, func):
        """

        :param func:
        :return:
        """
        #get new file name
        src_path = self.source
        basename = os.path.basename(src_path)
        full_dest = os.path.join(self.dest, basename)
        if not os.path.isdir(full_dest):
            os.mkdir(full_dest)
        else:
            i = 1
            new_name = full_dest + str(i)
            while os.path.isdir(new_name):
                i += 1
                new_name = full_dest + str(i)
            os.mkdir(new_name)
            full_dest = new_name
            basename = os.path.basename(full_dest)
        self.folder_names.append(basename)
        self.foldersInFolder.appendRow(QtGui.QStandardItem(basename))

        for filename in os.listdir(src_path):
            src = os.path.join(src_path, filename)
            dst_name = filename[:-4] + ".wav"
            dst = os.path.join(full_dest, dst_name)
            func(src, dst, True) #возвращает true, если это был подходящий файл, и false, если нет

        self.filesInFolder.clear()
        self.BtnCards.setEnabled(True)
        self.BtnConvert.setEnabled(False)
        self.BtnSkip.setEnabled(False)

    def timertick(self):
        try:
            next(self.gen)
        except StopIteration:
            pass


    def applyCards(self):
        self.color_next_dir(-1)
        self.gen = self.timertick_gen()
        self.timer.timeout.connect(self.timertick)
        self.timer.start(1)


    def timertick_gen(self):
        i = 0
        port = Usbhost.get_device_port()
        with Serial.Serial(port, baudrate=115200, timeout=0.1) as self.ser:
            with open(os.path.join(self.dest, 'folders.csv'), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, dialect='excel')
                previous = ""
                while i < len(self.folder_names):
                    answer = self.ser.readall().decode('utf-8').split('\r')
                    for line in answer:
                        if line.startswith("Card: ") and line != previous and i < len(self.folder_names):
                            previous = line
                            words = line.split(" ")
                            writer.writerow([words[1], words[2], self.folder_names[i]])
                            self.color_next_dir(i)
                            i += 1
                    yield
        self.timer.stop()


    def color_next_dir(self, i):
        white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        blue = QtGui.QBrush(QtGui.QColor(200, 200, 255))
        if i >= 0:
            self.foldersInFolder.item(i).setBackground(white)
        if i + 1 < self.foldersInFolder.rowCount():
            self.foldersInFolder.item(i + 1).setBackground(blue)


def check_file_format(path):
    """
    checks if file is soundfile and correct
    :param path: path to file
    :return:  FileFormat.NOT_MUSIC for not sound files, FileFormat.INCORRECT for not .wav or incorrect
    samplewidth or incorrect framerate
    """
    if os.path.splitext(path)[1] in (".mp3", ".oog"):
        return FileFormat.INCORRECT
    if os.path.splitext(path)[1] == ".wav":
        try:
            with wave.open(path, mode='rb') as sound:
                if sound.getsampwidth() == SAMPLEWIDTH and sound.getframerate() == FRAMERATE:
                    return FileFormat.CORRECT
                return FileFormat.INCORRECT
        except wave.Error:
            return FileFormat.NOT_MUSIC
    return FileFormat.NOT_MUSIC


def error_message(text):
    """
    shows error window with text
    :param text: error text
    :return:
    """
    error = QtWidgets.QMessageBox()
    error.setIcon(QtWidgets.QMessageBox.Critical)
    error.setText(text)
    error.setWindowTitle('Ошибка открытия файла')
    error.setStandardButtons(QtWidgets.QMessageBox.Ok)
    error.exec_()


def setup_exception_logging():
    # generating our hook
    # Back up the reference to the exceptionhook
    sys._excepthook = sys.excepthook

    def my_exception_hook(exctype, value, traceback):
        # Print the error and traceback
        logger.exception(f"{exctype}, {value}, {traceback}")
        # Call the normal Exception hook after
        sys._excepthook(exctype, value, traceback)
        # sys.exit(1)

    # Set the exception hook to our wrapping function
    sys.excepthook = my_exception_hook


def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    else:
        return os.path.join(os.path.abspath("."), relative)


@logger.catch
def main():
    setup_exception_logging()
    app = QtWidgets.QApplication(sys.argv)
    window = ShadowUi()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()

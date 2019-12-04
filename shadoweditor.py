import sys
import os
from shutil import copyfile
from enum import Enum
import wave
import csv
import subprocess

#import serial

#import Usbhost

from PyQt5 import QtCore, QtGui, QtWidgets
from loguru import logger

import ui

_translate = QtCore.QCoreApplication.translate

FRAMERATE = 48000
SAMPLEWIDTH = 2 #2 bytes == 16 bits
SAMPLEFMT = 's16' #ffmpeg format

BLACK = (0, 0, 0)
RED = (200, 0, 0)
GRAY = (100, 100, 100)

######### EMULATION WITH KEYS ##################################

class Usbhost:
    @staticmethod
    def get_device_port():
        return 500

class serial:
    class Serial(QtWidgets.QWidget):
        def __init__(self, *args, **kwargs):
            self.i = 0
            self.values = []
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def readall(self):
            res = b'\r'.join(b'Card: 1234 %i' % i for i in self.values)
            self.values = []
            return res

##################################################################

class FileFormat(Enum):
    notMusic = 1
    good = 2
    bad = 3

class ShadowUi(QtWidgets.QMainWindow, ui.Ui_MainWindow):

    ################################ EMULATION WITH KEYS ##################################
    def keyPressEvent(self, e):
        if hasattr(self, 'ser'):
            self.ser.values.append(self.ser.i)
            self.ser.i += 1
    ##########################################################################################

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.BtnCreate1.clicked.connect(self.createDestFolder)
        self.BtnChoose1.clicked.connect(self.selectDestFolder)
        self.LinePath1.editingFinished.connect(self.typeDestFolder)
        self.BtnChoose2.clicked.connect(self.selectFolder)
        self.LinePath2.editingFinished.connect(self.typeFolder)
        self.filesInFolder = QtGui.QStandardItemModel()
        self.LstFiles.setModel(self.filesInFolder)
        self.foldersInFolder = QtGui.QStandardItemModel()
        self.LstDirs.setModel(self.foldersInFolder)
        self.BtnConvert.clicked.connect(lambda : self.convertOrCopy(self.convert))
        self.BtnSkip.clicked.connect(lambda : self.convertOrCopy(self.copyOnly))
        self.folder_names = []
        self.timer = QtCore.QTimer()
        self.BtnCards.clicked.connect(self.applyCards)



    def selectDestFolder(self, event):
        dest = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "select directory",
            os.path.dirname(os.path.abspath(__file__)))
        if dest:
            self.dest = dest
            self.doAfterSelectDest()

    def createDestFolder(self):
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
        self.doAfterSelectDest()

    def typeDestFolder(self):
        dest = self.LinePath1.text()
        if os.path.isdir(dest):
            self.dest = dest
            self.doAfterSelectDest()
        else:
            self.LinePath1.clear()

    def doAfterSelectDest(self):
        self.BtnCreate1.hide()
        self.BtnChoose1.hide()
        self.LinePath1.hide()
        self.LblDest = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.LblDest.setFont(font)
        self.LblDest.setObjectName("LblDest")
        self.gridLayout.addWidget(self.LblDest, 3, 1, 1, 1)
        _translate = QtCore.QCoreApplication.translate
        self.LblDest.setText(_translate("LblDest", "Запись ведется в папку %s" % self.dest))

    def selectFolder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "select directory",
            os.path.dirname(os.path.abspath(__file__)))
        if path:
            self.path = path
            self.doAfterEnterPath()


    def typeFolder(self):
        path = self.LinePath2.text()
        if os.path.isdir(path):
            self.path = path
            self.doAfterEnterPath()
        else:
            self.LinePath2.clear()


    def insertItemWithColor(self, text, color):
        item = QtGui.QStandardItem(text)
        item.setForeground(QtGui.QBrush(QtGui.QColor(*color)))
        self.filesInFolder.appendRow(item)

        
    def doAfterEnterPath(self):
        haveToConvert = False
        haveToCopy = False #можно делать активной только имеющую смысл кнопку
        try:
            self.classifyDict = {}
            for filename in os.listdir(self.path):
                src = os.path.join(self.path, filename)
                res = self.classifyFile(src)
                self.classifyDict[src] = res
                if res == FileFormat.good:
                    self.insertItemWithColor(filename, BLACK)
                    haveToCopy = True
                elif res == FileFormat.notMusic:
                    self.insertItemWithColor(filename, GRAY)
                else:
                    self.insertItemWithColor(filename, RED)
                    haveToConvert = True

            self.BtnConvert.setEnabled(haveToConvert)
            self.BtnSkip.setEnabled(haveToCopy)

        except (FileNotFoundError, OSError):
            error_message("ошибка открытия файла")


        
    def classifyFile(self, path):
        if len(path) >= 4:
            if path[-4:] in (".mp3", ".oog"):
                return FileFormat.bad
            elif path[-4:] == ".wav":
                try:
                    with wave.open(path, mode='rb') as sound:
                        if sound.getsampwidth() == SAMPLEWIDTH and sound.getframerate() == FRAMERATE:
                            return FileFormat.good
                        else:
                            return FileFormat.bad
                except wave.Error:
                    return FileFormat.notMusic
        return FileFormat.notMusic


    def convert(self, src, dst):
        res = self.classifyDict[src]
        if res == FileFormat.good:
            if src != dst:
                copyfile(src, dst)
            return True
        elif res == FileFormat.bad:
            code = subprocess.call('ffmpeg -i "%s" -ar %d -sample_fmt %s "%s"' % (src, FRAMERATE, SAMPLEFMT, dst), shell=True)
            if code == 0:
                return True
            else:
                print ("Error converting file %s" % src)
                return False

    def copyOnly(self, src, dst):
        if self.classifyDict[src] == FileFormat.good:
            if src != dst:
                copyfile(src, dst)
            return True


    def convertOrCopy(self, func):
        src_path = self.path
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
            func(src, dst) #возвращает true, если это был подходящий файл, и false, если нет
        
        self.filesInFolder.clear()
        self.BtnCards.setEnabled(True)


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
        with serial.Serial(port, baudrate=115200, timeout=0.1) as self.ser:
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

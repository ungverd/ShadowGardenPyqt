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
from dataclasses import dataclass, field

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
        def __init__(self, port, baudrate, timeout):
            super().__init__()
            self.i = 0
            self.values = list()
            self.port = port
            self.baudrate = baudrate
            self.timeout = timeout
            self.previous = ""

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
    PROCESSING = 5


@dataclass
class MusicProcessor:
    state: State = State.NOTHING_SELECTED
    folder_names: List[str] = field(default_factory=list)
    classify_dict: Dict[str, FileFormat] = field(default_factory=dict)
    dest: str = ""
    source: str = ""
    last_folder = ""
    ser = None
    csv_file = None
    current: int = 0


class ShadowUi(QtWidgets.QMainWindow, ui.Ui_MainWindow):

    #  EMULATION WITH KEYS #
    def keyPressEvent(self, e):
        if self.state.state == State.PROCESSING:
            self.state.ser.values.append(self.state.ser.i)
            self.state.ser.i += 1
        e.accept()
    # END OF EMULATION

    def __init__(self):
        super().__init__()
        self.state: MusicProcessor = MusicProcessor()
        self.setupUi(self)
        self.BtnCreateDest.clicked.connect(self.create_dest_folder)
        self.BtnChooseDest.clicked.connect(self.select_folder)
        self.LinePathDest.editingFinished.connect(self.get_folder_from_field)
        self.BtnChooseSource.clicked.connect(self.select_folder)
        self.BtnConvert.clicked.connect(self.process_files)
        self.BtnSkip.clicked.connect(self.process_files)
        self.LinePathSource.editingFinished.connect(self.get_folder_from_field)
        self.BtnCards.clicked.connect(self.apply_cards_prepare)
        self.BtnStop.clicked.connect(self.tear_down)
        self.BtnReady.clicked.connect(self.files_ready)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timertick)
        self.filesInFolder = QtGui.QStandardItemModel()
        self.LstFiles.setModel(self.filesInFolder)
        self.foldersInFolder = QtGui.QStandardItemModel()
        self.LstDirs.setModel(self.foldersInFolder)

        self.all_controls = [self.BtnChooseDest, self.BtnCreateDest, self.LinePathDest,
                             self.BtnChooseSource, self.LinePathSource, self.BtnConvert, self.BtnSkip, self.BtnReady,
                             self.BtnCards, self.BtnStop]

    def select_folder(self):
        """
        selects and returns folder and calls ui function
        :return:
        """
        sender = self.sender()
        if sender == self.BtnChooseDest and self.state.source:
            reply = QtWidgets.QMessageBox.question(self, 'Сброс', "Остальные данные будут сброшены, продолжить?",
                                                   QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return
        (ui_function, folder_field) = (self.select_dest_ui, 'dest') if sender == self.BtnChooseDest \
            else (self.select_target_ui_and_convert, 'source')
        title = "Выберите папку"
        current_folder = os.path.dirname(os.path.abspath(__file__)) if not self.state.last_folder\
            else self.state.last_folder
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, title, current_folder)
        if folder:
            self.state.last_folder = folder
            setattr(self.state, folder_field, folder)
            ui_function()

    def create_dest_folder(self):
        """
        creates new folder in current folder and writes it name to dest field.
        If New name is already used, nes folder's name is 'New1" etc
        :return:
        """
        cur_path: str = os.getcwd()
        full_path: str = os.path.join(cur_path, "new")
        full_path = create_new_folder(full_path)
        self.state.dest = full_path
        self.select_dest_ui()

    def get_folder_from_field(self):
        """
        writes manually added path to dist/source field and calls corresponding ui function
        """
        sender = self.sender()
        if sender == self.LinePathDest and self.state.source:
            if self.LinePathDest.text() and self.LinePathDest.text != self.state.dest:
                reply = QtWidgets.QMessageBox.question(self, 'Сброс', "Остальные данные будут сброшены, продолжить?",
                                                       QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.No:
                    return
        folder = sender.text()
        ui_function, field_folder = (self.select_dest_ui, 'dest') if sender == self.LinePathDest \
            else (self.select_target_ui_and_convert, 'source')
        if os.path.exists(folder):
            result_path = folder if os.path.isdir(folder) else os.path.split(folder)[0]
            setattr(self.state, field_folder, result_path)
            ui_function()
        elif sender.text():
            message_popup("Выбранной папки не существует", 'error')

    def select_dest_ui(self):
        """
        makes ui for state "destination folder selected"
        :return:
        """
        self.state = MusicProcessor(state=State.DEST_SELECTED, dest=self.state.dest)
        self.BtnChooseSource.setEnabled(True)
        self.LinePathSource.setEnabled(True)
        self.LinePathSource.clear()
        self.filesInFolder.clear()
        self.BtnConvert.setEnabled(False)
        self.BtnSkip.setEnabled(False)
        self.foldersInFolder.clear()
        self.BtnCards.setEnabled(False)
        self.LblDest.setText("Выбрана папка: %s" % self.state.dest)
        self.LblSource.setText("Выбрана папка:")
        self.BtnStop.setEnabled(False)
        self.BtnReady.setEnabled(False)
        self.LblProgress.setText("")

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
        self.LblSource.setText("Выбрана папка: %s" % self.state.source)
        if self.state.source != self.LinePathSource.text():
            self.LinePathSource.clear()
        self.BtnConvert.setEnabled(False)
        self.BtnSkip.setEnabled(False)
        self.filesInFolder.clear()

        for filename in os.listdir(self.state.source):
            src: str = os.path.join(self.state.source, filename)
            try:
                res = check_file_format(src)
                self.state.classify_dict[src] = res
                if res == FileFormat.CORRECT:
                    self.insert_item_with_color(filename, BLACK)
                    self.BtnSkip.setEnabled(True)
                elif res == FileFormat.NOT_MUSIC:
                    self.insert_item_with_color(filename, GRAY)
                else:
                    self.insert_item_with_color(filename, RED)
                    self.BtnConvert.setEnabled(True)
            except (FileNotFoundError, OSError):
                message_popup("Ошибка открытия файла %s" % src, 'error')
                continue
        self.state.state = State.SOURCE_SELECTED
        if self.BtnSkip.isEnabled() or self.BtnConvert.isEnabled():
            self.BtnReady.setEnabled(True)

    def copy_and_convert(self, src: str, dst: str, convert: bool) -> bool:
        """
        convert file from src path to dest path using correct format (wav, 16bit, 48000) or just copy in format is good
        :param convert: convert files or skip them
        :param src: source file
        :param dst:dest file
        :return: status of operation (False only in is musical file and was not converted)
        """
        res = self.state.classify_dict[src]
        if res == FileFormat.CORRECT:
            if src != dst:
                copyfile(src, dst)
            return True
        elif res == FileFormat.INCORRECT and convert:
            try:
                subprocess.check_call('ffmpeg -i "%s" -ar %d -sample_fmt %s "%s"' % (src, FRAMERATE, SAMPLEFMT, dst),
                                      shell=False)
                return True
            except subprocess.CalledProcessError:
                print("Error converting file %s" % src)
                return False
        return True

    def process_files(self):
        """
        creates new folder in dest folder and for every file in selected dest folder copies it, converts or skips
        :return:
        """
        sender = self.sender()
        full_dest: str = create_new_folder(os.path.join(self.state.dest, os.path.basename(self.state.source)))
        basename = os.path.basename(full_dest)
        self.state.folder_names.append(basename)
        self.foldersInFolder.appendRow(QtGui.QStandardItem(basename))
        filelist: List[str] = os.listdir(self.state.source)
        self.disable_all()
        for filename in filelist:
            src_full = os.path.join(self.state.source, filename)
            dst_filename = os.path.splitext(filename)[0] + '.wav'
            dst_full = os.path.join(full_dest, dst_filename)
            must_convert = True if sender == self.BtnConvert else False
            print(filelist.index(filename))
            self.LblProgress.setText("Конвертируется %i файл из %i" % (filelist.index(filename) + 1, len(filelist)))
            res = self.copy_and_convert(src_full, dst_full, must_convert)
            if not res:
                message_popup('Не удалось конвертировать файл %s' % src_full, 'error')
        self.set_converted_ui()

    def files_ready(self):
        """
        folder selection ended
        :return:
        """
        self.state.state = State.FILES_READY
        self.set_files_ready_ui()

    def apply_cards_prepare(self):
        """
        preparation for cards usr
        :return:
        """
        self.color_next_dir(-1)
        port = Usbhost.get_device_port()
        self.state.ser = serial.Serial(port, baudrate=115200, timeout=0.1)
        self.state.csv_file = open(os.path.join(self.state.dest, 'folders.csv'), 'w', newline='')
        self.state.state = State.PROCESSING
        self.timer.start(1000)
        self.BtnStop.setEnabled(True)
        self.BtnCards.setEnabled(False)

    def timertick(self):
        """
        timer tick
        if we are in processing state, try to read cards
        :return:
        """
        if self.state.state == State.PROCESSING:
            writer = csv.writer(self.state.csv_file, dialect='excel')
            if self.state.current < len(self.state.folder_names):
                answer = self.state.ser.readall().decode('utf-8').split('\r')
                for line in answer:
                    if line.startswith("Card: "):
                        if line != self.state.last_folder and self.state.current < len(self.state.folder_names):
                            self.state.last_folder = line
                            words = line.split()
                            writer.writerow([words[1], words[2], self.state.folder_names[self.state.current]])
                            self.color_next_dir(self.state.current)
                            self.state.current += 1
            else:
                message_popup("Запись карточек окончена", "info")
                self.tear_down()

    def tear_down(self):
        """
        clears state and closes all files and ports
        :return:
        """
        self.timer.stop()
        if self.state.ser:
            self.state.ser.close()
        if self.state.csv_file:
            self.state.csv_file.close()
        self.state = MusicProcessor()
        self.select_dest_ui()

    def color_next_dir(self, i: int):
        """
        colors current dir in list (if any) back in white
        colors next dir (if any) in blue
        :param i:
        :return:
        """
        white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        blue = QtGui.QBrush(QtGui.QColor(200, 200, 255))
        if i >= 0:
            self.foldersInFolder.item(i).setBackground(white)
        if i + 1 < self.foldersInFolder.rowCount():
            self.foldersInFolder.item(i + 1).setBackground(blue)

    def set_files_ready_ui(self):
        """
        sets ui for files ready status
        :return:
        """
        self.BtnCards.setEnabled(True)
        self.BtnConvert.setEnabled(False)
        self.BtnSkip.setEnabled(False)
        self.BtnChooseSource.setEnabled(False)
        self.LinePathSource.setEnabled(False)
        self.BtnReady.setEnabled(False)

    def disable_all(self):
        """
        disables all controls
        :return:
        """
        print("disable")
        for control in self.all_controls:
            control.setEnabled(False)

    def set_converted_ui(self):
        """
        enables all controls available after conversion
        :return:
        """
        for_enable = [self.BtnCreateDest, self.BtnChooseDest, self.LinePathDest, self.BtnChooseSource,
                      self.LinePathSource, self.BtnReady]
        for control in for_enable:
            control.setEnabled(True)

    def closeEvent(self, event):
        """
        closes all files and ports before closing
        :param event:
        :return:
        """
        self.tear_down()
        event.accept()


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


def create_new_folder(folder: str) -> str:
    """
    creates new folder in path, if folder already exists, creates
    :param folder: name for folder to create
    :return: name of really created folder
    """
    if not os.path.isdir(folder):
        os.mkdir(folder)
        return folder
    i = 1
    new_name = folder + str(i)
    while os.path.isdir(new_name):
        i += 1
        new_name = folder + str(i)
    os.mkdir(new_name)
    return new_name


def message_popup(text: str, message_type: str):
    """
    shows error window with text
    :param message_type: error or info
    :param text: error text
    :return:
    """
    message = QtWidgets.QMessageBox()
    if message_type == 'error':
        message.setIcon(QtWidgets.QMessageBox.Critical)
        message.setWindowTitle('Ошибка!')
    else:
        message.setIcon(QtWidgets.QMessageBox.Information)
        message.setWindowTitle('')
    message.setText(text)
    message.setStandardButtons(QtWidgets.QMessageBox.Ok)
    message.exec_()


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

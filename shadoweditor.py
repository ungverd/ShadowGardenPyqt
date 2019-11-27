import sys
import os
from shutil import copyfile
from enum import Enum
import wave
import csv
import subprocess

import serial

#import Usbhost

from PyQt5 import QtCore, QtGui, QtWidgets
from loguru import logger

import ui

_translate = QtCore.QCoreApplication.translate

FRAMERATE = 48000
SAMPLEWIDTH = 2 #2 bytes == 16 bits
SAMPLEFMT = 's16' #ffmpeg format

class FileFormat(Enum):
    notMusic = 1
    good = 2
    bad = 3

class ShadowUi(QtWidgets.QMainWindow, ui.Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.BtnCreate1.clicked.connect(self.createDestFolder)
        self.BtnChoose1.clicked.connect(self.selectDestFolder)
        self.LinePath1.editingFinished.connect(self.typeDestFolder)
        
    def classifyFile(self, path):
        if len(path) >= 4:
            if path[-4:] in (".mp3", ".oog"):
                return FileFormat.bad
            elif path[-4:] == ".wav":
                try:
                    sound = wave.open(path, mode='rb')
                    if sound.getsampwidth() == SAMPLEWIDTH and sound.getframerate() == FRAMERATE:
                        return FileFormat.good
                    else:
                        return FileFormat.bad
                except wave.Error:
                    return FileFormat.notMusic
        return FileFormat.notMusic


    def convert(self, src, dst):
        res = self.classifyFile(src)
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
        if self.classifyFile(src) == FileFormat.good:
            if src != dst:
                copyfile(src, dst)
            return True


    def convertOrCopy(self, func):
        src_path = master.path
        basename = os.path.basename(src_path)
        full_dest = os.path.join(master.dest, basename)
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
        writeMusicObj.folder_names.append(basename)
        folder = enterSourceObj.tree.insert("", 'end', text=basename)
        writeMusicObj.folders_in_tree.append(folder)
        for filename in os.listdir(src_path):
            src = os.path.join(src_path, filename)
            dst_name = filename[:-4] + ".wav"
            dst = os.path.join(full_dest, dst_name)
            if func(src, dst):
                enterSourceObj.tree.insert(folder, "end", text=dst_name)



    def doAfterEnterPath(self):
        haveToConvert = False
        haveToCopy = False
        try:
            for filename in os.listdir(master.path):
                src = os.path.join(master.path, filename)
                res = self.classifyFile(src)
                if res == FileFormat.good:
                    convertCopyObj.currentfolder.insert("", 'end', text=filename)
                    haveToCopy = True
                elif res == FileFormat.notMusic:
                    convertCopyObj.currentfolder.insert("", 'end', text=filename, tags = ('grey',))
                else:
                    convertCopyObj.currentfolder.insert("", 'end', text=filename, tags = ('red',))
                    haveToConvert = True

            enterSourceObj.end()

            if haveToConvert:
                convertCopyObj.addTop(convertCopyObj.convertOrCopyLabel)
                convertCopyObj.addTop(convertCopyObj.convB)
            if haveToCopy:
                convertCopyObj.addTop(convertCopyObj.copyB)

            convertCopyObj.begin()

        except (FileNotFoundError, OSError):
            enterSourceObj.add(enterSourceObj.notValidPathLabel)
            enterSourceObj.clearField()

    def selectFolder(self):
        self.path =  filedialog.askdirectory(initialdir = "/")
        self.doAfterEnterPath()

    def applyCards(self):
        enterSourceObj.end()
        writeMusicObj.begin()
        gen = self.contextGen()
        gen.send(None)
        master.after_idle(self.recursive, gen, 0)


    def recursive(self, gen, i):
        res = gen.send(i)
        if i <= len(writeMusicObj.folder_names):
            if res:
                master.after_idle(self.recursive, gen, i+1)
            else:
                master.after_idle(self.recursive, gen, i)

    def contextGen(self):
        tree = writeMusicObj.tree
        names = writeMusicObj.folder_names
        folders = writeMusicObj.folders_in_tree
        port = Usbhost.get_device_port()
        with serial.Serial(port, baudrate=115200, timeout=0.1) as ser:
            with open(os.path.join(master.dest, 'folders.csv'), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, dialect='excel')
                previous = ""
                while True:
                    i = yield(True)
                    if i > 0 and i <= len(names):
                        name = names[i-1]
                        folder = folders[i-1]

                        done = False
                        while not done:
                            answer = ser.readall().decode('utf-8').split('\r')
                            _ = yield(False)
                            for line in answer:
                                if line.startswith("Card: ") and line != previous:
                                    previous = line
                                    words = line.split(" ")
                                    writer.writerow([words[1], words[2], name])
                                    done = True

                        tree.item(folder, tags=())
                    if i < len(names):
                        tree.item(folders[i], tags=('active'))
                    
                    
    def selectDestFolder(self, event):
        self.dest = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "select directory",
            os.path.dirname(os.path.abspath(__file__)), 
            '*.mp3')
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
        enterDestObj.end()
        enterSourceObj.begin()

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

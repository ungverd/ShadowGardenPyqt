# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(591, 661)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.LblHelp = QtWidgets.QLabel(self.centralwidget)
        self.LblHelp.setObjectName("LblHelp")
        self.gridLayout.addWidget(self.LblHelp, 12, 1, 1, 1)
        self.BtnCreate1 = QtWidgets.QPushButton(self.centralwidget)
        self.BtnCreate1.setObjectName("BtnCreate1")
        self.gridLayout.addWidget(self.BtnCreate1, 1, 1, 1, 1)
        self.BtnSkip = QtWidgets.QPushButton(self.centralwidget)
        self.BtnSkip.setEnabled(False)
        self.BtnSkip.setObjectName("BtnSkip")
        self.gridLayout.addWidget(self.BtnSkip, 13, 2, 1, 1)
        self.LinePath2 = QtWidgets.QLineEdit(self.centralwidget)
        self.LinePath2.setObjectName("LinePath2")
        self.gridLayout.addWidget(self.LinePath2, 8, 1, 1, 2)
        self.LblStep3 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.LblStep3.setFont(font)
        self.LblStep3.setObjectName("LblStep3")
        self.gridLayout.addWidget(self.LblStep3, 14, 1, 1, 1)
        self.LblStep2 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.LblStep2.setFont(font)
        self.LblStep2.setObjectName("LblStep2")
        self.gridLayout.addWidget(self.LblStep2, 4, 1, 1, 1)
        self.BtnCards = QtWidgets.QPushButton(self.centralwidget)
        self.BtnCards.setEnabled(False)
        self.BtnCards.setObjectName("BtnCards")
        self.gridLayout.addWidget(self.BtnCards, 15, 1, 1, 2)
        self.BtnChoose1 = QtWidgets.QPushButton(self.centralwidget)
        self.BtnChoose1.setObjectName("BtnChoose1")
        self.gridLayout.addWidget(self.BtnChoose1, 1, 2, 1, 1)
        self.LblFormat = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(6)
        self.LblFormat.setFont(font)
        self.LblFormat.setObjectName("LblFormat")
        self.gridLayout.addWidget(self.LblFormat, 16, 1, 1, 2)
        self.LinePath1 = QtWidgets.QLineEdit(self.centralwidget)
        self.LinePath1.setObjectName("LinePath1")
        self.gridLayout.addWidget(self.LinePath1, 3, 1, 1, 2)
        self.LblPath1 = QtWidgets.QLabel(self.centralwidget)
        self.LblPath1.setObjectName("LblPath1")
        self.gridLayout.addWidget(self.LblPath1, 2, 1, 1, 2)
        self.LblPath2 = QtWidgets.QLabel(self.centralwidget)
        self.LblPath2.setObjectName("LblPath2")
        self.gridLayout.addWidget(self.LblPath2, 6, 1, 1, 1)
        self.LblFiles = QtWidgets.QLabel(self.centralwidget)
        self.LblFiles.setObjectName("LblFiles")
        self.gridLayout.addWidget(self.LblFiles, 9, 1, 1, 1)
        self.BtnConvert = QtWidgets.QPushButton(self.centralwidget)
        self.BtnConvert.setEnabled(False)
        self.BtnConvert.setObjectName("BtnConvert")
        self.gridLayout.addWidget(self.BtnConvert, 12, 2, 1, 1)
        self.LstFiles = QtWidgets.QListView(self.centralwidget)
        self.LstFiles.setObjectName("LstFiles")
        self.gridLayout.addWidget(self.LstFiles, 11, 1, 1, 2)
        self.LblStep1 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.LblStep1.setFont(font)
        self.LblStep1.setObjectName("LblStep1")
        self.gridLayout.addWidget(self.LblStep1, 0, 1, 1, 2)
        self.BtnChoose2 = QtWidgets.QPushButton(self.centralwidget)
        self.BtnChoose2.setObjectName("BtnChoose2")
        self.gridLayout.addWidget(self.BtnChoose2, 7, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 591, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Настройка Сада Теней"))
        self.LblHelp.setText(_translate("MainWindow", "Файлы в неподходящем формате выделены красным. \n"
"Для конвертации нажмите «Конвертировать»\n"
"Или эти файлы можно пропустить"))
        self.BtnCreate1.setText(_translate("MainWindow", "Создать папку"))
        self.BtnSkip.setText(_translate("MainWindow", "Пропустить"))
        self.LblStep3.setText(_translate("MainWindow", "Шаг2. Соотнести с карточками"))
        self.LblStep2.setText(_translate("MainWindow", "Шаг2. Выбор папки с музыкой"))
        self.BtnCards.setText(_translate("MainWindow", "Начать соотносить"))
        self.BtnChoose1.setText(_translate("MainWindow", "Выбрать папку"))
        self.LblFormat.setText(_translate("MainWindow", "Для справки: подходящий формат wav, 16бит, частота 48000 "))
        self.LblPath1.setText(_translate("MainWindow", "ИЛИ введите путь до папки"))
        self.LblPath2.setText(_translate("MainWindow", "Или введите путь до папки"))
        self.LblFiles.setText(_translate("MainWindow", "Файлы в папке:"))
        self.BtnConvert.setText(_translate("MainWindow", "Конвертировать"))
        self.LblStep1.setText(_translate("MainWindow", "Шаг1. Выбор папки для итоговых файлов"))
        self.BtnChoose2.setText(_translate("MainWindow", "Выбрать папку"))

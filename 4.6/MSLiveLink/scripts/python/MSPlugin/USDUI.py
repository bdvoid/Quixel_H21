from PySide6 import QtGui, QtCore, QtWidgets


class USDOptions(QtWidgets.QWidget):
    def __init__(self, usdOptions, settingsCallback):
        super(USDOptions, self).__init__()
        self.usdOptions = usdOptions
        self.settingsCallback = settingsCallback
        
        self.SetupOptionsW()

    def SetupOptionsW(self):
        self.widgetVBLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.widgetVBLayout)

        self.uiBox = QtWidgets.QGroupBox("USD Options :")
        self.widgetVBLayout.addWidget(self.uiBox)

        # Main UI Layout
        self.uiLayout = QtWidgets.QGridLayout()
        self.uiBox.setLayout(self.uiLayout)

        # Material type
        materialTypeText = QtWidgets.QLabel("USD Material")
        self.materialTypeDrop = QtWidgets.QComboBox()
        self.materialTypeDrop.setToolTip("Material type to create on USD stage")

        self.uiLayout.addWidget(materialTypeText, 0, 0)
        self.uiLayout.addWidget(self.materialTypeDrop, 0, 1)

        usdMaterials = ["Karma", "Renderman", "Arnold", "Redshift_USD"]
        self.materialTypeDrop.addItems(usdMaterials)

        # Select saved option if valid
        if self.usdOptions["USDMaterial"] in usdMaterials:
            materialIndex = self.materialTypeDrop.findText(self.usdOptions["USDMaterial"])
            if materialIndex >= 0:
                self.materialTypeDrop.setCurrentIndex(materialIndex)

        self.materialTypeDrop.currentIndexChanged.connect(self.materialChanged)

        # Regex validator
        self.refpathRegexp = QtCore.QRegularExpression("+")
        refpathValidator = QtGui.QRegularExpressionValidator(self.refpathRegexp)
        # Not attached here—checkbox/text input logic may attach later

    def miscOptionChanged(self, optionObject, state):
        optionName = optionObject.objectName()
        self.usdOptions[optionName] = state
        self.settingsChanged()

    def materialChanged(self, index):
        self.usdOptions["USDMaterial"] = self.materialTypeDrop.itemText(index)
        self.settingsChanged()

    def textInputChanged(self, optionObject):
        text = optionObject.text()

        if text == self.usdOptions.get(optionObject.objectName(), ""):
            return

        if self.refpathRegexp.match(text).hasMatch():
            optionObject.setStyleSheet("border: 1px solid black")
            self.usdOptions[optionObject.objectName()] = text
            self.settingsChanged()
        else:
            optionObject.setStyleSheet("border: 1px solid red")

    def settingsChanged(self):
        self.settingsCallback("USDOptions", self.usdOptions)

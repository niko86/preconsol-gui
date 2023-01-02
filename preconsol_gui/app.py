import sys

import matplotlib as mpl

mpl.use('QtAgg')

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtCore import QAbstractTableModel, QObject, Qt, Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog,
                               QHBoxLayout, QMainWindow, QPushButton,
                               QTableView, QVBoxLayout, QWidget)

from app_modules import Casagrande_PreConsolidation, ProcessAGS


class Signaller(QObject):
    reset_data = Signal()


class PreconsolidationModel(QAbstractTableModel):

    signal = Signal()

    def __init__(self, data):
        super(PreconsolidationModel, self).__init__()
        self._data = data


    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
            # ADDED LINES
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter


    def rowCount(self, index):
        return self._data.shape[0]


    def columnCount(self, index):
        return self._data.shape[1]


    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled

        return super().flags(index) | Qt.ItemIsEditable  # add editable flag.


    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])


    def setData(self, index, value, role):
        if role == Qt.EditRole:
            # Set the value into the frame.
            self._data.iloc[index.row(), index.column()] = float(value) # Hacky conversion to float
            self.signal.emit()
            return True

        return False


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.data = None
        self.title = 'Casagrande Preconsolidation Estimation Tool'
        self.setWindowTitle(self.title)

        # Instantiate dependencies
        self.consol = Casagrande_PreConsolidation()
        self.canvas = self.consol.get_canvas()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.set_plot_navigation_bar()

        # Create widget
        self.btn_load_ags = QPushButton("Load AGS File ...")
        self.cbx_samples = QComboBox()
        self.parent_layout = QHBoxLayout()
        self.plot_layout = QVBoxLayout()
        self.plot_widget = QWidget()
        self.table = QTableView()
        self.table_layout = QVBoxLayout()

        # Connect init signals
        self.btn_load_ags.clicked.connect(self.btn_load_ags_clicked)
        self.cbx_samples.currentIndexChanged.connect(self.cbx_samples_changed)

        # Set layouts
        self.table_layout.addWidget(self.btn_load_ags)
        self.table_layout.addWidget(self.cbx_samples)
        self.table_layout.addWidget(self.table)
        self.plot_layout.addWidget(self.toolbar)
        self.plot_layout.addWidget(self.canvas)
        self.parent_layout.addLayout(self.table_layout, 1)
        self.parent_layout.addLayout(self.plot_layout, 4)

        # Create a placeholder widget to hold our toolbar and canvas.
        self.plot_widget.setLayout(self.parent_layout)
        self.setCentralWidget(self.plot_widget)
        return


    def btn_load_ags_clicked(self, data):
        dlg = QFileDialog(self)
        dlg.setWindowTitle("HELLO!")
        file_name, _ = dlg.getOpenFileName(self, "Open AGS file ...", "", "AGS files (*.ags)", "AGS files (*.ags)")
        try:
            ags = ProcessAGS(file_name)
            self.data = ags.get_cons_for_preconsolidation()
            self.samples = self.data['SAMP_NAME'].unique()
            self.cbx_samples.addItems(self.samples)
        except FileExistsError:
            print("File does not exist")
        return


    def cbx_samples_changed(self, i):
        self.sample_data = self.data[self.data['SAMP_NAME'] == self.samples[i]]
        self.sample_data = self.sample_data[['CONS_INCF','CONS_INCE']].reset_index(drop=True)
        self.create_table()
        return


    def set_plot_navigation_bar(self):
        unwanted_buttons = ["Back", "Forward", "Subplots"]

        # icons_buttons = {
        #     "Home": QtGui.QIcon(":/icons/penguin.png"),
        #     "Pan": QtGui.QIcon(":/icons/monkey.png"),
        #     "Zoom": QtGui.QIcon(":/icons/penguin.png"),
        # }

        for action in self.toolbar.actions():
            if action.text() in unwanted_buttons:
                self.toolbar.removeAction(action)
            # if action.text() in icons_buttons:
            #     action.setIcon(icons_buttons.get(action.text(), QtGui.QIcon()))
        return


    def create_table(self):
        self.model = PreconsolidationModel(self.sample_data)
        self.model.signal.connect(self.set_plot)
        self.table.setModel(self.model)
        self.set_plot()
        return


    def set_plot(self):
        self.consol.set_data(axial_loads_kpa=self.sample_data['CONS_INCF'].values, void_ratios=self.sample_data['CONS_INCE'].values)
        self.consol.set_interactive()
        return


if __name__ == "__main__":  
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
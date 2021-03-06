import sys
import time

from PySide2 import QtWidgets

from Code import Util
from Code import AperturasStd
from Code import Configuracion
from Code.Engines import Priorities
from Code.SQL import UtilSQL
import Code
from Code.Kibitzers import Kibitzers
from Code.Kibitzers import WKibBase
from Code.Kibitzers import WKibLinea
from Code.Kibitzers import WKibBooks
from Code.Kibitzers import WKibIndex
from Code.Kibitzers import WKibStEval
from Code.Kibitzers import WKibGaviota
from Code.QT import QTUtil

from Code.Constantes import *


class Orden:
    def __init__(self):
        self.key = ""
        self.titulo = ""
        self.dv = {}


class CPU:
    def __init__(self, fdb):

        self.ipc = UtilSQL.IPC(fdb, False)

        self.configuracion = None
        self.configMotor = None
        self.titulo = None

        self.ventana = None
        self.engine = None

    def run(self):
        # Primero espera la orden de lucas
        while True:
            orden = self.recibe()
            if orden:
                break
            time.sleep(0.1)

        self.procesa(orden)

    def recibe(self):
        dv = self.ipc.pop()
        if not dv:
            return None

        orden = Orden()
        orden.key = dv["__CLAVE__"]
        orden.dv = dv
        return orden

    def procesa(self, orden):
        key = orden.key
        if key == KIBRUN_CONFIGURACION:
            user = orden.dv["USER"]
            self.configuracion = Configuracion.Configuracion(user)
            self.configuracion.lee()
            self.configuracion.leeConfTableros()
            Code.configuracion = self.configuracion
            AperturasStd.reset()
            self.numkibitzer = orden.dv["NUMKIBITZER"]
            kibitzers = Kibitzers.Kibitzers()
            self.kibitzer = kibitzers.kibitzer(self.numkibitzer)
            prioridad = self.kibitzer.prioridad

            priorities = Priorities.priorities

            if prioridad != priorities.normal:
                self.prioridad = priorities.value(prioridad)
            else:
                self.prioridad = None

            self.titulo = self.kibitzer.name

            self.key_video = "Kibitzers%s" % self.kibitzer.huella
            self.dic_video = self.configuracion.restore_video(self.key_video)

            self.tipo = self.kibitzer.tipo
            self.position_before = self.kibitzer.position_before
            self.lanzaVentana()

        elif key == KIBRUN_FEN:
            self.fen, self.fenBase = orden.dv["FEN"].split("|")
            fen = self.fenBase if self.position_before else self.fen
            if self.tipo == KIB_THREATS:
                li = fen.split(" ")
                li[1] = "w" if li[1] == "b" else "b"
                li[3] = "-"  # Hay que tener cuidado con la captura al paso, stockfish crash.
                fen = " ".join(li)
            self.ventana.ponFen(fen)

        elif key == KIBRUN_STOP:
            self.ventana.stop()

        elif key == KIBRUN_CLOSE:
            self.ipc.close()
            self.ventana.finalizar()
            self.ventana.reject()

    def save_video(self, dic):
        self.configuracion.save_video(self.key_video, dic)

    def lanzaVentana(self):
        app = QtWidgets.QApplication([])

        app.setStyle(QtWidgets.QStyleFactory.create(self.configuracion.x_style))
        QtWidgets.QApplication.setPalette(QtWidgets.QApplication.style().standardPalette())

        self.configuracion.releeTRA()

        if self.tipo == KIB_BESTMOVE:
            self.ventana = WKibBase.WKibBase(self)

        elif self.tipo == KIB_CANDIDATES:
            self.ventana = WKibBase.WKibBase(self)

        elif self.tipo == KIB_THREATS:
            self.ventana = WKibBase.WKibBase(self)

        elif self.tipo == KIB_BESTMOVE_ONELINE:
            self.ventana = WKibLinea.WKibLinea(self)

        elif self.tipo == KIB_POLYGLOT:
            self.ventana = WKibBooks.WPolyglot(self)

        elif self.tipo in KIB_INDEXES:
            self.ventana = WKibIndex.WKibIndex(self)

        elif self.tipo == KIB_STOCKFISH:
            self.ventana = WKibStEval.WStEval(self)

        elif self.tipo == KIB_GAVIOTA:
            self.ventana = WKibGaviota.WGaviota(self)

        self.ventana.show()

        # Code.gc = QTUtil.GarbageCollector()

        return app.exec_()

    def compruebaInput(self):
        if self.ventana:
            orden = self.recibe()
            if orden:
                self.procesa(orden)

    def dispatch(self, texto):
        if texto:
            self.ventana.ponTexto(texto)
        QTUtil.refresh_gui()

        return True


def run(fdb):
    sys.stderr = Util.Log("./bug.kibitzers")

    cpu = CPU(fdb)
    cpu.run()

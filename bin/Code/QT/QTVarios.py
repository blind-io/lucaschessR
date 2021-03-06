import os

from PySide2 import QtCore, QtGui, QtWidgets, QtSvg

from Code.QT import Colocacion
from Code.QT import Controles
from Code.QT import Iconos
from Code.QT import QTUtil
from Code.QT import QTUtil2
from Code.QT import FormLayout
from Code import Util
import Code


class WDialogo(QtWidgets.QDialog):
    def __init__(self, main_window, titulo, icono, extparam):
        QtWidgets.QDialog.__init__(self, main_window)
        self.key_video = extparam
        self.liGrids = []
        self.liSplitters = []
        self.setWindowTitle(titulo)
        self.setWindowIcon(icono)
        self.setWindowFlags(
            QtCore.Qt.Dialog
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )

    def register_grid(self, grid):
        self.liGrids.append(grid)

    def register_splitter(self, splitter, name):
        self.liSplitters.append((splitter, name))

    def save_video(self, dic_extended=None):
        dic = {} if dic_extended is None else dic_extended

        pos = self.pos()
        dic["_POSICION_"] = "%d,%d" % (pos.x(), pos.y())

        tam = self.size()
        dic["_SIZE_"] = "%d,%d" % (tam.width(), tam.height())

        for grid in self.liGrids:
            grid.save_video(dic)

        for sp, name in self.liSplitters:
            dic["SP_%s" % name] = sp.sizes()

        Code.configuracion.save_video(self.key_video, dic)
        return dic

    def restore_dicvideo(self):
        return Code.configuracion.restore_video(self.key_video)

    def restore_video(self, siTam=True, anchoDefecto=None, altoDefecto=None, dicDef=None):
        dic = self.restore_dicvideo()
        if not dic:
            dic = dicDef
        wE, hE = QTUtil.tamEscritorio()
        if dic:
            if "_POSICION_" in dic:
                x, y = dic["_POSICION_"].split(",")
                x = int(x)
                y = int(y)
                if not (0 <= x <= (wE - 50)):
                    x = 0
                if not (0 <= y <= (hE - 50)):
                    y = 0
                self.move(x, y)
            for grid in self.liGrids:
                grid.restore_video(dic)
                grid.releerColumnas()
            for sp, name in self.liSplitters:
                k = "SP_%s" % name
                if k in dic:
                    sp.setSizes(dic[k])
            if siTam:
                if not ("_SIZE_" in dic):
                    w, h = self.width(), self.height()
                    for k in dic:
                        if k.startswith("_TAMA"):
                            w, h = dic[k].split(",")
                else:
                    w, h = dic["_SIZE_"].split(",")
                w = int(w)
                h = int(h)
                if w > wE:
                    w = wE
                elif w < 20:
                    w = 20
                if h > (hE - 40):
                    h = hE - 40
                elif h < 20:
                    h = 20
                self.resize(w, h)
            return True
        else:
            if anchoDefecto or altoDefecto:
                if anchoDefecto is None:
                    anchoDefecto = self.width()
                if altoDefecto is None:
                    altoDefecto = self.height()
                if anchoDefecto > wE:
                    anchoDefecto = wE
                if altoDefecto > (hE - 40):
                    altoDefecto = hE - 40
                self.resize(anchoDefecto, altoDefecto)

        return False

    def accept(self):
        self.save_video()
        super().accept()
        # self.close()
        # Evita excepción al salir del programa
        # ver: https://stackoverflow.com/a/36826593/3324704
        self.deleteLater()

    def reject(self):
        self.save_video()
        super().reject()
        self.deleteLater()

    def closeEvent(self, event):  # Cierre con X
        # Evita excepción al salir del programa
        # ver: https://stackoverflow.com/a/36826593/3324704
        self.deleteLater()


class BlancasNegras(QtWidgets.QDialog):
    def __init__(self, parent):
        super(BlancasNegras, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint)

        icoP = Code.todasPiezas.iconoDefecto("K")
        icop = Code.todasPiezas.iconoDefecto("k")
        self.setWindowTitle(_("Choose Color"))
        self.setWindowIcon(icoP)

        btBlancas = Controles.PB(self, "", rutina=self.accept, plano=False).ponIcono(icoP, tamIcon=64)
        btNegras = Controles.PB(self, "", rutina=self.negras, plano=False).ponIcono(icop, tamIcon=64)

        self.resultado = True

        ly = Colocacion.H().control(btBlancas).control(btNegras)
        ly.margen(10)
        self.setLayout(ly)

    def negras(self):
        self.resultado = False
        self.accept()


def blancasNegras(owner):
    w = BlancasNegras(owner)
    if w.exec_():
        return w.resultado
    return None


class BlancasNegrasTiempo(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint)

        icoP = Code.todasPiezas.iconoDefecto("K")
        icop = Code.todasPiezas.iconoDefecto("k")
        self.setWindowTitle(_("Choose Color"))
        self.setWindowIcon(icoP)

        btBlancas = Controles.PB(self, "", rutina=self.blancas, plano=False).ponIcono(icoP, tamIcon=64)
        btNegras = Controles.PB(self, "", rutina=self.negras, plano=False).ponIcono(icop, tamIcon=64)

        # Tiempo
        self.edMinutos, self.lbMinutos = QTUtil2.spinBoxLB(self, 5, 0, 999, maxTam=50, etiqueta=_("Total minutes"))
        self.edSegundos, self.lbSegundos = QTUtil2.spinBoxLB(
            self, 10, 0, 999, maxTam=50, etiqueta=_("Seconds added per move")
        )
        ly = Colocacion.G()
        ly.controld(self.lbMinutos, 0, 0).control(self.edMinutos, 0, 1)
        ly.controld(self.lbSegundos, 0, 2).control(self.edSegundos, 0, 3)
        self.gbT = Controles.GB(self, _("Time"), ly).conectar(self.cambiaTiempo)
        self.cambiaTiempo()

        # Fast moves
        self.chb_fastmoves = Controles.CHB(self, _("Fast moves"), False)

        self.color = None

        ly = Colocacion.H().control(btBlancas).control(btNegras)
        ly.margen(10)
        layout = Colocacion.V().otro(ly).espacio(10).control(self.gbT).control(self.chb_fastmoves).margen(5)
        self.setLayout(layout)

    def resultado(self):
        return (
            self.color,
            self.gbT.isChecked(),
            self.edMinutos.valor(),
            self.edSegundos.valor(),
            self.chb_fastmoves.valor(),
        )

    def cambiaTiempo(self):
        si = self.gbT.isChecked()
        for control in (self.edMinutos, self.lbMinutos, self.edSegundos, self.lbSegundos):
            control.setVisible(si)

    def blancas(self):
        self.color = True
        self.accept()

    def negras(self):
        self.color = False
        self.accept()


def blancasNegrasTiempo(owner):
    w = BlancasNegrasTiempo(owner)
    if w.exec_():
        return w.resultado()
    return None


class Tiempo(QtWidgets.QDialog):
    def __init__(self, parent, minMinutos, minSegundos, maxMinutos, maxSegundos):
        super(Tiempo, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint)

        self.setWindowTitle(_("Time"))
        self.setWindowIcon(Iconos.MoverTiempo())

        tb = QTUtil2.tbAcceptCancel(self)

        # Tiempo
        self.edMinutos, self.lbMinutos = QTUtil2.spinBoxLB(
            self, 10, minMinutos, maxMinutos, maxTam=50, etiqueta=_("Total minutes")
        )
        self.edSegundos, self.lbSegundos = QTUtil2.spinBoxLB(
            self, 0, minSegundos, maxSegundos, maxTam=50, etiqueta=_("Seconds added per move")
        )

        # # Tiempo
        lyT = Colocacion.G()
        lyT.controld(self.lbMinutos, 0, 0).control(self.edMinutos, 0, 1)
        lyT.controld(self.lbSegundos, 1, 0).control(self.edSegundos, 1, 1).margen(20)

        ly = Colocacion.V().control(tb).espacio(20).otro(lyT)
        self.setLayout(ly)

    def aceptar(self):
        self.accept()

    def resultado(self):
        minutos = self.edMinutos.value()
        segundos = self.edSegundos.value()

        return minutos, segundos


def vtime(owner, minMinutos=1, minSegundos=0, maxMinutos=999, maxSegundos=999):
    w = Tiempo(owner, minMinutos, minSegundos, maxMinutos, maxSegundos)
    if w.exec_():
        return w.resultado()
    return None


def lyBotonesMovimiento(
    owner,
    key,
    siLibre=True,
    siMas=False,
    siTiempo=True,
    must_save=False,
    siGrabarTodos=False,
    siJugar=False,
    rutina=None,
    tamIcon=16,
    liMasAcciones=None,
):
    li_acciones = []

    def x(tit, tr, icono):
        li_acciones.append((tr, icono, key + tit))

    li_acciones.append(None)
    x("MoverInicio", _("First move"), Iconos.MoverInicio())
    li_acciones.append(None)
    x("MoverAtras", _("Previous move"), Iconos.MoverAtras())
    li_acciones.append(None)
    x("MoverAdelante", _("Next move"), Iconos.MoverAdelante())
    li_acciones.append(None)
    x("MoverFinal", _("Last move"), Iconos.MoverFinal())
    li_acciones.append(None)
    if siLibre:
        x("MoverLibre", _("Analysis of variation"), Iconos.MoverLibre())
        li_acciones.append(None)
    if siJugar:
        x("MoverJugar", _("Play"), Iconos.MoverJugar())
        li_acciones.append(None)
    if siTiempo:
        x("MoverTiempo", _("Timed movement"), Iconos.MoverTiempo())
    li_acciones.append(None)
    if must_save:
        x("MoverGrabar", _("Save"), Iconos.MoverGrabar())
        li_acciones.append(None)
    if siGrabarTodos:
        li_acciones.append((_("Save") + "++", Iconos.MoverGrabarTodos(), key + "MoverGrabarTodos"))
        li_acciones.append(None)
    if siMas:
        x("MoverMas", _("New analysis"), Iconos.MoverMas())

    if liMasAcciones:
        for trad, tit, icono in liMasAcciones:
            li_acciones.append(None)
            li_acciones.append((trad, icono, key + tit))

    tb = Controles.TB(owner, li_acciones, False, tamIcon=tamIcon, rutina=rutina)
    ly = Colocacion.H().relleno().control(tb).relleno()
    return ly, tb


class LCNumero(QtWidgets.QWidget):
    def __init__(self, maxdigits):
        QtWidgets.QWidget.__init__(self)

        f = Controles.TipoLetra("", 11, 80, False, False, False, None)

        ly = Colocacion.H()
        self.liLB = []
        for x in range(maxdigits):
            lb = QtWidgets.QLabel(self)
            lb.setStyleSheet("* { border: 2px solid black; padding: 2px; margin: 0px;}")
            lb.setFont(f)
            ly.control(lb)
            self.liLB.append(lb)
            lb.hide()
            lb.setFixedWidth(32)
            lb.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(ly)

    def pon(self, number):
        c = str(number)
        n = len(c)
        for x in range(n):
            lb = self.liLB[x]
            lb.setText(c[x])
            lb.show()
        for x in range(n, len(self.liLB)):
            self.liLB[x].hide()


class TwoImages(QtWidgets.QLabel):
    def __init__(self, pmTrue, pmFalse):
        self.pm = {True: pmTrue, False: pmFalse}
        self.pmFalse = pmFalse
        QtWidgets.QLabel.__init__(self)
        self.valor(False)

    def valor(self, ok=None):
        if ok is None:
            return self._valor
        else:
            self._valor = ok
            self.setPixmap(self.pm[ok])

    def mousePressEvent(self, event):
        self.valor(not self._valor)


def svg2ico(svg, tam):
    pm = QtGui.QPixmap(tam, tam)
    pm.fill(QtCore.Qt.transparent)
    qb = QtCore.QByteArray(svg)
    render = QtSvg.QSvgRenderer(qb)
    painter = QtGui.QPainter()
    painter.begin(pm)
    render.render(painter)
    painter.end()
    ico = QtGui.QIcon(pm)
    return ico


def fsvg2ico(fsvg, tam):
    with open(fsvg, "rb") as f:
        svg = f.read()
        return svg2ico(svg, tam)


def svg2pm(svg, tam):
    pm = QtGui.QPixmap(tam, tam)
    pm.fill(QtCore.Qt.transparent)
    qb = QtCore.QByteArray(svg)
    render = QtSvg.QSvgRenderer(qb)
    painter = QtGui.QPainter()
    painter.begin(pm)
    render.render(painter)
    painter.end()
    return pm


def fsvg2pm(fsvg, tam):
    with open(fsvg, "rb") as f:
        svg = f.read()
        return svg2pm(svg, tam)


class LBPieza(Controles.LB):
    def __init__(self, owner, pieza, tablero, tam):
        self.pieza = pieza
        self.owner = owner
        pixmap = tablero.piezas.pixmap(pieza, tam=tam)
        self.dragpixmap = pixmap
        Controles.LB.__init__(self, owner)
        self.ponImagen(pixmap).anchoFijo(tam).altoFijo(tam)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.owner.startDrag(self)


class ListaPiezas(QtWidgets.QWidget):
    def __init__(self, owner, lista, tablero, tam=None, margen=None):
        QtWidgets.QWidget.__init__(self)

        self.owner = owner
        # self.tablero = tablero = owner.tablero

        if tam is None:
            tam = tablero.anchoPieza

        liLB = []
        for fila, valor in enumerate(lista.split(";")):
            for columna, pieza in enumerate(valor.split(",")):
                lb = LBPieza(self, pieza, tablero, tam)
                liLB.append((lb, fila, columna))

        layout = Colocacion.G()
        for lb, fila, columna in liLB:
            layout.control(lb, fila, columna)
        if margen is not None:
            layout.margen(margen)

            # l1 = Colocacion.H().otro(layout).relleno()
            # if margen:
            # l1.margen(margen)
            # l2 = Colocacion.V().otro(l1)
            # if margen:
            # l2.margen(margen)

        self.setLayout(layout)

    def startDrag(self, lb):

        pixmap = lb.dragpixmap
        pieza = lb.pieza
        itemData = QtCore.QByteArray(pieza.encode("utf-8"))

        self.owner.ultimaPieza = pieza
        self.owner.ponCursor()

        mimeData = QtCore.QMimeData()
        mimeData.setData("image/x-lc-dato", itemData)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(QtCore.QPoint(pixmap.width() // 2, pixmap.height() // 2))
        drag.setPixmap(pixmap)

        drag.exec_(QtCore.Qt.MoveAction)


def rondoPuntos(shuffle=True):
    nico = Util.Rondo(
        Iconos.PuntoAmarillo(),
        Iconos.PuntoNaranja(),
        Iconos.PuntoVerde(),
        Iconos.PuntoAzul(),
        Iconos.PuntoMagenta(),
        Iconos.PuntoRojo(),
    )
    if shuffle:
        nico.shuffle()
    return nico


def rondoColores(shuffle=True):
    nico = Util.Rondo(
        Iconos.Amarillo(), Iconos.Naranja(), Iconos.Verde(), Iconos.Azul(), Iconos.Magenta(), Iconos.Rojo()
    )
    if shuffle:
        nico.shuffle()
    return nico


class LCMenu(Controles.Menu):
    def __init__(self, parent, puntos=None):
        configuracion = Code.configuracion
        if not puntos:
            puntos = configuracion.x_menu_points
        bold = configuracion.x_menu_bold
        Controles.Menu.__init__(self, parent, puntos=puntos, siBold=bold)


class LCMenuRondo(LCMenu):
    def __init__(self, parent, puntos=None):
        LCMenu.__init__(self, parent, puntos)
        self.rondo = rondoPuntos()

    def opcion(self, key, rotulo, icono=None, is_disabled=False, tipoLetra=None, siChecked=None):
        if icono is None:
            icono = self.rondo.otro()
        LCMenu.opcion(self, key, rotulo, icono, is_disabled, tipoLetra, siChecked)

    # def submenu(self, rotulo, icono=None, is_disabled=False):
    #     if icono is None:
    #         icono = self.rondo.otro()
    #     return LCMenu.submenu(self, rotulo, icono, is_disabled)
    #


class LCMenuPiezas(Controles.Menu):
    def __init__(self, parent, titulo=None, icono=None, is_disabled=False, puntos=None, siBold=True):
        Controles.Menu.__init__(self, parent, titulo, icono, is_disabled, puntos, siBold)
        self.ponTipoLetra("Chess Alpha 2", 16)

    def alpha2(self, key):
        # d = {
        #     "K": "n",
        #     "Q": "m",
        #     "R": "l",
        #     "B": "j",
        #     "N": "k",
        #     "P": "i",
        #     "k": "N",
        #     "q": "M",
        #     "r": "L",
        #     "b": "J",
        #     "n": "K",
        #     "p": "I",
        # }
        return key  # "".join([d[c] for c in key])

    def opcion(self, clave, rotulo, icono=None, is_disabled=False, tipo_letra=None, siChecked=False):
        Controles.Menu.opcion(
            self, clave, self.alpha2(rotulo), icono=icono, is_disabled=is_disabled, siChecked=siChecked
        )

    def submenu(self, rotulo, icono=None, is_disabled=False):
        menu = LCMenuPiezas(self, self.alpha2(rotulo), icono, is_disabled)
        self.addMenu(menu)
        return menu


class ImportarFichero(QtWidgets.QDialog):
    def __init__(self, parent, titulo, siErroneos, siWorkDone, icono):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint)

        self.setWindowTitle(titulo)
        self.setWindowIcon(icono)
        self.fontB = f = Controles.TipoLetra(puntos=10, peso=75)

        self.siErroneos = siErroneos
        self.siWorkDone = siWorkDone

        self.is_canceled = False

        lbRotLeidos = Controles.LB(self, _("Games read") + ":").ponFuente(f)
        self.lbLeidos = Controles.LB(self, "0").ponFuente(f)

        if siErroneos:
            lbRotErroneos = Controles.LB(self, _("Erroneous") + ":").ponFuente(f)
            self.lbErroneos = Controles.LB(self, "0").ponFuente(f)
        else:
            lbRotErroneos = None

        self.lbRotDuplicados = lbRotDuplicados = Controles.LB(self, _("Duplicated") + ":").ponFuente(f)
        self.lbDuplicados = Controles.LB(self, "0").ponFuente(f)

        self.lbRotImportados = lbRotImportados = Controles.LB(self, _("Imported") + ":").ponFuente(f)
        self.lbImportados = Controles.LB(self, "0").ponFuente(f)

        if self.siWorkDone:
            lbRotWorkDone = Controles.LB(self, _("Work done") + ":").ponFuente(f)
            self.lbWorkDone = Controles.LB(self, "0.00%").ponFuente(f)
        else:
            lbRotWorkDone = None

        self.btCancelarSeguir = Controles.PB(self, _("Cancel"), self.cancelar, plano=False).ponIcono(Iconos.Delete())

        ly = Colocacion.G().margen(20)
        ly.controld(lbRotLeidos, 0, 0).controld(self.lbLeidos, 0, 1)
        if siErroneos:
            ly.controld(lbRotErroneos, 1, 0).controld(self.lbErroneos, 1, 1)
        ly.controld(lbRotDuplicados, 2, 0).controld(self.lbDuplicados, 2, 1)
        ly.controld(lbRotImportados, 3, 0).controld(self.lbImportados, 3, 1)
        if self.siWorkDone:
            ly.controld(lbRotWorkDone, 4, 0).controld(self.lbWorkDone, 4, 1)

        lyBT = Colocacion.H().relleno().control(self.btCancelarSeguir)

        layout = Colocacion.V()
        layout.otro(ly)
        layout.espacio(20)
        layout.otro(lyBT)

        self.setLayout(layout)

    def pon_titulo(self, titulo):
        self.setWindowTitle(titulo)

    def hide_duplicates(self):
        self.lbRotDuplicados.hide()
        self.lbDuplicados.hide()

    def cancelar(self):
        self.is_canceled = True
        self.ponContinuar()

    def ponExportados(self):
        self.lbRotImportados.ponTexto(_("Exported") + ":")

    def ponSaving(self):
        self.btCancelarSeguir.setDisabled(True)
        self.btCancelarSeguir.ponTexto(_("Saving..."))
        self.btCancelarSeguir.ponFuente(self.fontB)
        self.btCancelarSeguir.ponIcono(Iconos.Grabar())
        QTUtil.refresh_gui()

    def ponContinuar(self):
        self.btCancelarSeguir.ponTexto(_("Continue"))
        self.btCancelarSeguir.conectar(self.continuar)
        self.btCancelarSeguir.ponFuente(self.fontB)
        self.btCancelarSeguir.ponIcono(Iconos.Aceptar())
        self.btCancelarSeguir.setDisabled(False)
        QTUtil.refresh_gui()

    def continuar(self):
        self.accept()

    def actualiza(self, leidos, erroneos, duplicados, importados, workdone=0):
        def pts(x):
            return "{:,}".format(x).replace(",", ".")

        self.lbLeidos.ponTexto(pts(leidos))
        if self.siErroneos:
            self.lbErroneos.ponTexto(pts(erroneos))
        self.lbDuplicados.ponTexto(pts(duplicados))
        self.lbImportados.ponTexto(pts(importados))
        if self.siWorkDone:
            self.lbWorkDone.ponTexto("%d%%" % int(workdone))
        QTUtil.refresh_gui()
        return not self.is_canceled


class ImportarFicheroPGN(ImportarFichero):
    def __init__(self, parent):
        ImportarFichero.__init__(self, parent, _("PGN file"), True, True, Iconos.PGN())


class ImportarFicheroFNS(ImportarFichero):
    def __init__(self, parent):
        ImportarFichero.__init__(self, parent, _("FNS file"), True, False, Iconos.Fichero())


class ImportarFicheroDB(ImportarFichero):
    def __init__(self, parent):
        ImportarFichero.__init__(self, parent, _("Database file"), False, True, Iconos.Database())

    def actualiza(self, leidos, erroneos, duplicados, importados, workdone=0):
        return ImportarFichero.actualiza(self, leidos, 0, duplicados, importados, workdone)


class MensajeFics(QtWidgets.QDialog):
    def __init__(self, parent, mens):
        QtWidgets.QDialog.__init__(self, parent)

        self.setWindowTitle(_("Fics-Elo"))
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint)
        self.setWindowIcon(Iconos.Fics())
        self.setStyleSheet("QDialog, QLabel { background: #E3F1F9 }")

        lbm = Controles.LB(self, "<big><b>%s</b></big>" % mens)
        self.bt = Controles.PB(self, _("One moment please..."), rutina=self.final, plano=True)
        self.bt.setDisabled(True)
        self.siFinalizado = False

        ly = Colocacion.G().control(lbm, 0, 0).controlc(self.bt, 1, 0)

        ly.margen(20)

        self.setLayout(ly)

    def continua(self):
        self.bt.ponTexto(_("Continue"))
        self.bt.ponPlano(False)
        self.bt.setDisabled(False)
        self.mostrar()

    def colocaCentrado(self, owner):
        self.move(
            owner.x() + owner.width() // 2 - self.width() // 2, owner.y() + owner.height() // 2 - self.height() // 2
        )
        QTUtil.refresh_gui()
        self.show()
        QTUtil.refresh_gui()
        return self

    def mostrar(self):
        QTUtil.refresh_gui()
        self.exec_()
        QTUtil.refresh_gui()

    def final(self):
        if not self.siFinalizado:
            self.accept()
        self.siFinalizado = True
        QTUtil.refresh_gui()


class MensajeFide(QtWidgets.QDialog):
    def __init__(self, parent, mens):
        QtWidgets.QDialog.__init__(self, parent)

        self.setWindowTitle(_("Fide-Elo"))
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint)
        self.setWindowIcon(Iconos.Fide())
        self.setStyleSheet("QDialog, QLabel { background: #E9E9E9 }")

        lbm = Controles.LB(self, "<big><b>%s</b></big>" % mens)
        self.bt = Controles.PB(self, _("One moment please..."), rutina=self.final, plano=True)
        self.bt.setDisabled(True)
        self.siFinalizado = False

        ly = Colocacion.G().control(lbm, 0, 0).controlc(self.bt, 1, 0)

        ly.margen(20)

        self.setLayout(ly)

    def continua(self):
        self.bt.ponTexto(_("Continue"))
        self.bt.ponPlano(False)
        self.bt.setDisabled(False)
        self.mostrar()

    def colocaCentrado(self, owner):
        self.move(owner.x() + owner.width() / 2 - self.width() / 2, owner.y() + owner.height() / 2 - self.height() / 2)
        QTUtil.refresh_gui()
        self.show()
        QTUtil.refresh_gui()
        return self

    def mostrar(self):
        QTUtil.refresh_gui()
        self.exec_()
        QTUtil.refresh_gui()

    def final(self):
        if not self.siFinalizado:
            self.accept()
        self.siFinalizado = True
        QTUtil.refresh_gui()


def select_pgn(wowner):
    configuracion = Code.configuracion
    path = QTUtil2.leeFichero(wowner, configuracion.pgn_folder(), "pgn")
    if path:
        carpeta, fichero = os.path.split(path)
        configuracion.save_pgn_folder(carpeta)
    return path


def select_pgns(wowner):
    configuracion = Code.configuracion
    files = QTUtil2.leeFicheros(wowner, configuracion.pgn_folder(), "pgn")
    if files:
        path = files[0]
        carpeta, fichero = os.path.split(path)
        configuracion.save_pgn_folder(carpeta)
    return files


def select_ext(wowner, ext):
    configuracion = Code.configuracion
    path = QTUtil2.leeFichero(wowner, configuracion.x_save_folder, ext)
    if path:
        carpeta, fichero = os.path.split(path)
        if configuracion.x_save_folder != carpeta:
            configuracion.x_save_folder = carpeta
            configuracion.graba()
    return path


def list_irina():
    return (
        ("Monkey", _("Monkey"), Iconos.Monkey()),
        ("Donkey", _("Donkey"), Iconos.Donkey()),
        ("Bull", _("Bull"), Iconos.Bull()),
        ("Wolf", _("Wolf"), Iconos.Wolf()),
        ("Lion", _("Lion"), Iconos.Lion()),
        ("Rat", _("Rat"), Iconos.Rat()),
        ("Snake", _("Snake"), Iconos.Snake()),
        ("Steven", _("Steven"), Iconos.Steven()),
    )


class ElemDB:
    def __init__(self, path, is_folder):
        self.is_folder = is_folder
        self.path = path
        self.name = os.path.basename(path)
        if is_folder:
            self.li_elems = self.read(path)
        else:
            self.name = self.name[: self.name.rindex(".")]

    @staticmethod
    def read(folder):
        li = []
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isdir(path):
                li.append(ElemDB(path, True))
            elif f.endswith(".lcdb") or f.endswith(".lcdblink"):
                li.append(ElemDB(path, False))
        return li

    def remove(self, path):
        for n, elem in enumerate(self.li_elems):
            if elem.is_folder:
                elem.remove(path)
            elif Util.same_path(path, elem.path):
                del self.li_elems[n]
                return

    def is_empty(self):
        for n, elem in enumerate(self.li_elems):
            if elem.is_folder:
                if not elem.is_empty():
                    return False
            else:
                return False
        return True

    def remove_empties(self):
        li = []
        for n, elem in enumerate(self.li_elems):
            if elem.is_folder:
                elem.remove_empties()
                if elem.is_empty():
                    li.append(n)
        if len(li) > 0:
            li.sort(reverse=True)
            for n in li:
                del self.li_elems[n]

    def add_submenu(self, submenu, rondo, indicador_previo=None):
        self.li_elems.sort(key=lambda x: x.name.lower())
        previo = "" if indicador_previo is None else indicador_previo
        for elem in self.li_elems:
            if elem.is_folder:
                subsubmenu = submenu.submenu(elem.name, Iconos.Carpeta())
                elem.add_submenu(subsubmenu, rondo, indicador_previo)
        for elem in self.li_elems:
            if not elem.is_folder:
                submenu.opcion(previo + elem.path, elem.name, rondo.otro())


def lista_db(configuracion, siAll):
    lista = ElemDB(configuracion.folder_databases(), True)
    if not siAll:
        lista.remove(configuracion.get_last_database())
    lista.remove_empties()
    return None if lista.is_empty() else lista


def select_db(owner, configuracion, siAll, siNew):
    lista = lista_db(configuracion, siAll)
    if lista is None and not siNew:
        return None

    menu = LCMenu(owner)
    rp = rondoPuntos()
    if lista:
        lista.add_submenu(menu, rp)
    if siNew:
        menu.separador()
        menu.opcion(":n", _("Create new"), Iconos.DatabaseMas())
    return menu.lanza()


def menuDB(submenu, configuracion, siAll, indicador_previo=None):
    lista = lista_db(configuracion, siAll)
    if lista is None:
        return None

    rp = rondoPuntos()
    lista.add_submenu(submenu, rp, indicador_previo=indicador_previo)


class ReadAnnotation(QtWidgets.QDialog):
    def __init__(self, parent, objetivo):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)

        self.edAnotacion = Controles.ED(self, "")
        btAceptar = Controles.PB(self, "", rutina=self.aceptar).ponIcono(Iconos.Aceptar())
        btCancelar = Controles.PB(self, "", rutina=self.cancelar).ponIcono(Iconos.Cancelar())
        btAyuda = Controles.PB(self, "", rutina=self.ayuda).ponIcono(Iconos.AyudaGR())

        self.objetivo = objetivo
        self.conAyuda = False
        self.errores = 0
        self.resultado = None

        layout = (
            Colocacion.H()
            .relleno(1)
            .control(btAyuda)
            .control(self.edAnotacion)
            .control(btAceptar)
            .control(btCancelar)
            .margen(3)
        )
        self.setLayout(layout)
        self.move(parent.x() + parent.tablero.width() - 212, parent.y() + parent.tablero.y() - 3)

    def aceptar(self):
        txt = self.edAnotacion.texto()
        txt = txt.strip().replace(" ", "").upper()

        if txt:
            if txt == self.objetivo.upper():
                self.resultado = self.conAyuda, self.errores
                self.accept()
            else:
                self.errores += 1
                self.edAnotacion.setStyleSheet("QWidget { color: red }")

    def cancelar(self):
        self.reject()

    def ayuda(self):
        self.conAyuda = True
        self.edAnotacion.ponTexto(self.objetivo)


class LCTB(Controles.TBrutina):
    def __init__(self, parent, li_acciones=None, siTexto=True, tamIcon=None, puntos=None, background=None, style=None):
        configuracion = Code.configuracion
        Controles.TBrutina.__init__(
            self,
            parent,
            li_acciones=li_acciones,
            siTexto=siTexto,
            tamIcon=tamIcon,
            puntos=configuracion.x_tb_fontpoints if puntos is None else puntos,
            background=background,
            style=configuracion.tipoIconos() if style is None else style,
        )


def change_interval(owner, configuracion):
    form = FormLayout.FormLayout(owner, _("Replay game"), Iconos.Pelicula_Repetir(), anchoMinimo=250)
    form.separador()
    form.float(_("Duration of interval (secs)"), configuracion.x_interval_replay / 1000)
    form.separador()
    resultado = form.run()
    if resultado is None:
        return None
    accion, liResp = resultado
    vtime = liResp[0]
    if vtime > 0.01:
        configuracion.x_interval_replay = int(vtime * 1000)
        configuracion.graba()

import time

from PySide2 import QtWidgets, QtCore

from Code import Game
from Code.QT import Colocacion
from Code.QT import Columnas
from Code.QT import Controles
from Code.QT import FormLayout
from Code.QT import Grid
from Code.QT import Iconos
from Code.QT import QTUtil
from Code.QT import QTUtil2
from Code.QT import QTVarios
from Code.QT import Tablero
from Code import TrListas
from Code import Util
from Code.SQL import UtilSQL


class LearnPGNs(UtilSQL.DictSQL):
    def __init__(self, fichero):
        UtilSQL.DictSQL.__init__(self, fichero)
        self.regKeys = self.keys(True, True)

    def leeRegistro(self, num):
        return self.__getitem__(self.regKeys[num])

    def append(self, valor):
        k = str(Util.today())
        self.__setitem__(k, valor)
        self.regKeys = self.keys(True, True)

    def cambiaRegistro(self, num, valor):
        self.__setitem__(self.regKeys[num], valor)

    def borraRegistro(self, num):
        self.__delitem__(self.regKeys[num])
        self.regKeys = self.keys(True, True)

    def borraLista(self, li):
        li.sort()
        li.reverse()
        for x in li:
            self.__delitem__(self.regKeys[x])
        self.pack()
        self.regKeys = self.keys(True, True)


class WLearnBase(QTVarios.WDialogo):
    def __init__(self, procesador):

        titulo = _("Memorize a game")
        QTVarios.WDialogo.__init__(self, procesador.main_window, titulo, Iconos.LearnGame(), "learngame")

        self.procesador = procesador
        self.configuracion = procesador.configuracion

        self.db = LearnPGNs(self.configuracion.ficheroLearnPGN)

        # Historico
        o_columns = Columnas.ListaColumnas()

        def creaCol(key, rotulo, centered=True):
            o_columns.nueva(key, rotulo, 80, centered=centered)

        # # Claves segun orden estandar
        liBasic = ("EVENT", "SITE", "DATE", "ROUND", "WHITE", "BLACK", "RESULT", "ECO", "FEN", "WHITEELO", "BLACKELO")
        for key in liBasic:
            rotulo = TrListas.pgnLabel(key)
            creaCol(key, rotulo, key != "EVENT")
        self.grid = Grid.Grid(self, o_columns, siSelecFilas=True, siSeleccionMultiple=True)
        self.grid.setMinimumWidth(self.grid.anchoColumnas() + 20)

        # Tool bar
        li_acciones = (
            (_("Close"), Iconos.MainMenu(), self.terminar),
            None,
            (_("New"), Iconos.Nuevo(), self.nuevo),
            None,
            (_("Remove"), Iconos.Borrar(), self.borrar),
            None,
            (_("Learn"), Iconos.Empezar(), self.empezar),
        )
        self.tb = QTVarios.LCTB(self, li_acciones)

        # Colocamos
        lyTB = Colocacion.H().control(self.tb).margen(0)
        ly = Colocacion.V().otro(lyTB).control(self.grid).margen(3)

        self.setLayout(ly)

        self.register_grid(self.grid)
        self.restore_video(siTam=False)

        self.grid.gotop()

    def grid_doble_click(self, grid, fila, columna):
        self.empezar()

    def grid_num_datos(self, grid):
        return len(self.db)

    def grid_dato(self, grid, fila, oColumna):
        col = oColumna.clave
        reg = self.db.leeRegistro(fila)
        game = Game.Game()
        game.restore(reg["GAME"])
        return game.get_tag(col)

    def terminar(self):
        self.save_video()
        self.db.close()
        self.accept()

    def nuevo(self):
        game = self.procesador.select_1_pgn(self)
        if game and len(game) > 0:
            reg = {"GAME": game.save()}
            self.db.append(reg)
            self.grid.refresh()
            self.grid.gotop()

    def borrar(self):
        li = self.grid.recnosSeleccionados()
        if len(li) > 0:
            if QTUtil2.pregunta(self, _("Do you want to delete all selected records?")):
                self.db.borraLista(li)
        self.grid.gotop()
        self.grid.refresh()

    def empezar(self):
        li = self.grid.recnosSeleccionados()
        if len(li) > 0:
            w = WLearn1(self, li[0])
            w.exec_()


class WLearn1(QTVarios.WDialogo):
    def __init__(self, owner, numRegistro):

        QTVarios.WDialogo.__init__(self, owner, _("Learn a game"), Iconos.PGN(), "learn1game")

        self.owner = owner
        self.db = owner.db
        self.procesador = owner.procesador
        self.configuracion = self.procesador.configuracion
        self.numRegistro = numRegistro
        self.registro = self.db.leeRegistro(numRegistro)

        self.game = Game.Game()
        self.game.restore(self.registro["GAME"])

        self.lbRotulo = Controles.LB(self, self.rotulo()).ponTipoLetra(puntos=12).ponColorFondoN("#076C9F", "#EFEFEF")

        self.liIntentos = self.registro.get("LIINTENTOS", [])

        o_columns = Columnas.ListaColumnas()
        o_columns.nueva("DATE", _("Date"), 100, centered=True)
        o_columns.nueva("LEVEL", _("Level"), 80, centered=True)
        o_columns.nueva("COLOR", _("Play with"), 80, centered=True)
        o_columns.nueva("ERRORS", _("Errors"), 80, centered=True)
        o_columns.nueva("HINTS", _("Hints"), 80, centered=True)
        o_columns.nueva("TIME", _("Time"), 80, centered=True)
        self.grid = Grid.Grid(self, o_columns, siSelecFilas=True, siSeleccionMultiple=True)
        self.grid.setMinimumWidth(self.grid.anchoColumnas() + 20)

        # Tool bar
        li_acciones = (
            (_("Close"), Iconos.MainMenu(), self.terminar),
            None,
            (_("Train"), Iconos.Empezar(), self.empezar),
            None,
            (_("Remove"), Iconos.Borrar(), self.borrar),
            None,
        )
        self.tb = Controles.TBrutina(self, li_acciones)

        # Colocamos
        lyTB = Colocacion.H().control(self.tb).margen(0)
        ly = Colocacion.V().otro(lyTB).control(self.grid).control(self.lbRotulo).margen(3)

        self.setLayout(ly)

        self.register_grid(self.grid)
        self.restore_video(siTam=False)

        self.grid.gotop()

    def rotulo(self):
        r = self.registro

        def x(k):
            return r.get(k, "")

        return "%s-%s : %s %s %s" % (x("WHITE"), x("BLACK"), x("DATE"), x("EVENT"), x("SITE"))

    def grid_num_datos(self, grid):
        return len(self.liIntentos)

    def grid_dato(self, grid, fila, oColumna):
        col = oColumna.clave
        reg = self.liIntentos[fila]

        if col == "DATE":
            f = reg["DATE"]
            return "%02d/%02d/%d-%02d:%02d" % (f.day, f.month, f.year, f.hour, f.minute)
        if col == "LEVEL":
            return str(reg["LEVEL"])
        if col == "COLOR":
            c = reg["COLOR"]
            if c == "b":
                return _("Black")
            elif c == "w":
                return _("White")
            else:
                return _("White") + "+" + _("Black")
        if col == "ERRORS":
            return str(reg["ERRORS"])
        if col == "HINTS":
            return str(reg["HINTS"])
        if col == "TIME":
            s = reg["SECONDS"]
            m = s // 60
            s -= m * 60
            return "%2d' %02d\"" % (m, s)

    def guardar(self, dic):
        self.liIntentos.insert(0, dic)
        self.grid.refresh()
        self.grid.gotop()
        self.registro["LIINTENTOS"] = self.liIntentos
        self.db.cambiaRegistro(self.numRegistro, self.registro)

    def terminar(self):
        self.save_video()
        self.accept()

    def borrar(self):
        li = self.grid.recnosSeleccionados()
        if len(li) > 0:
            if QTUtil2.pregunta(self, _("Do you want to delete all selected records?")):
                li.sort()
                li.reverse()
                for x in li:
                    del self.liIntentos[x]
        self.grid.gotop()
        self.grid.refresh()

    def empezar(self):
        regBase = self.liIntentos[0] if self.liIntentos else {}

        liGen = [(None, None)]

        liGen.append((FormLayout.Spinbox(_("Level"), 0, len(self.game), 40), regBase.get("LEVEL", 0)))
        liGen.append((None, None))
        liGen.append((None, _("User play with") + ":"))
        liGen.append((_("White"), "w" in regBase.get("COLOR", "bw")))
        liGen.append((_("Black"), "b" in regBase.get("COLOR", "bw")))
        liGen.append((None, None))
        liGen.append((_("Show clock"), True))

        resultado = FormLayout.fedit(
            liGen, title=_("New try"), anchoMinimo=200, parent=self, icon=Iconos.TutorialesCrear()
        )
        if resultado is None:
            return

        accion, liResp = resultado
        level = liResp[0]
        white = liResp[1]
        black = liResp[2]
        if not (white or black):
            return
        siClock = liResp[3]

        w = WLearnPuente(self, self.game, level, white, black, siClock)
        w.exec_()


class WLearnPuente(QTVarios.WDialogo):
    INICIO, FINAL_JUEGO, REPLAY, REPLAY_CONTINUE = range(4)

    def __init__(self, owner, game, nivel, white, black, siClock):

        QTVarios.WDialogo.__init__(self, owner, owner.rotulo(), Iconos.PGN(), "learnpuente")

        self.owner = owner
        self.procesador = owner.procesador
        self.configuracion = self.procesador.configuracion
        self.game = game
        self.nivel = nivel
        self.white = white
        self.black = black
        self.siClock = siClock

        self.repTiempo = 3000
        self.repWorking = False

        # Tool bar
        self.tb = Controles.TBrutina(self, [])

        self.pon_toolbar(self.INICIO)

        # Tableros
        config_board = self.configuracion.config_board("LEARNPGN", 48)

        self.tableroIni = Tablero.Tablero(self, config_board)
        self.tableroIni.crea()
        self.tableroIni.set_dispatcher(self.mueve_humano, None)
        self.lbIni = (
            Controles.LB(self).alinCentrado().ponColorFondoN("#076C9F", "#EFEFEF").anchoMinimo(self.tableroIni.ancho)
        )
        lyIni = Colocacion.V().control(self.tableroIni).control(self.lbIni)

        self.tableroFin = Tablero.TableroEstatico(self, config_board)
        self.tableroFin.crea()
        self.lbFin = (
            Controles.LB(self).alinCentrado().ponColorFondoN("#076C9F", "#EFEFEF").anchoMinimo(self.tableroFin.ancho)
        )
        lyFin = Colocacion.V().control(self.tableroFin).control(self.lbFin)

        # Rotulo vtime
        f = Controles.TipoLetra(puntos=30, peso=75)
        self.lbReloj = (
            Controles.LB(self, "00:00")
            .ponFuente(f)
            .alinCentrado()
            .ponColorFondoN("#076C9F", "#EFEFEF")
            .anchoMinimo(200)
        )
        self.lbReloj.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Raised)

        # Movimientos
        flb = Controles.TipoLetra(puntos=11)
        self.lbInfo = Controles.LB(self).anchoFijo(200).ponWrap().ponFuente(flb)

        # Layout
        lyC = Colocacion.V().control(self.lbReloj).control(self.lbInfo).relleno()
        lyTM = Colocacion.H().otro(lyIni).otro(lyC).otro(lyFin).relleno()

        ly = Colocacion.V().control(self.tb).otro(lyTM).relleno().margen(3)

        self.setLayout(ly)

        self.restore_video()
        self.adjustSize()

        if siClock:
            QtCore.QTimer.singleShot(500, self.ajustaReloj)
        else:
            self.lbReloj.hide()

        self.reset()

    def process_toolbar(self):
        getattr(self, self.sender().clave)()

    def pon_toolbar(self, tipo):

        if tipo == self.INICIO:
            li_acciones = (
                (_("Cancel"), Iconos.Cancelar(), self.cancelar),
                None,
                (_("Reinit"), Iconos.Reiniciar(), self.reset),
                None,
                (_("Help"), Iconos.AyudaGR(), self.ayuda),
                None,
            )
        elif tipo == self.FINAL_JUEGO:
            li_acciones = (
                (_("Close"), Iconos.MainMenu(), self.final),
                None,
                (_("Reinit"), Iconos.Reiniciar(), self.reset),
                None,
                (_("Replay game"), Iconos.Pelicula(), self.replay),
                None,
            )
        elif tipo == self.REPLAY:
            li_acciones = (
                (_("Cancel"), Iconos.Cancelar(), self.repCancelar),
                None,
                (_("Reinit"), Iconos.Inicio(), self.repReiniciar),
                None,
                (_("Slow"), Iconos.Pelicula_Lento(), self.repSlow),
                None,
                (_("Pause"), Iconos.Pelicula_Pausa(), self.repPause),
                None,
                (_("Fast"), Iconos.Pelicula_Rapido(), self.repFast),
                None,
            )
        elif tipo == self.REPLAY_CONTINUE:
            li_acciones = (
                (_("Cancel"), Iconos.Cancelar(), self.repCancelar),
                None,
                (_("Continue"), Iconos.Pelicula_Seguir(), self.repContinue),
                None,
            )
        self.tb.reset(li_acciones)

    def replay(self):
        self.pon_toolbar(self.REPLAY)

        self.repJugada = -1
        self.repWorking = True
        self.tableroIni.setposition(self.game.first_position)
        self.replayDispatch()

    def replayDispatch(self):
        QTUtil.refresh_gui()
        if not self.repWorking:
            return
        self.repJugada += 1
        self.ponInfo()
        num_moves = len(self.game)
        if self.repJugada == num_moves:
            self.pon_toolbar(self.FINAL_JUEGO)
            return

        move = self.game.move(self.repJugada)
        self.tableroIni.setposition(move.position)
        self.tableroIni.ponFlechaSC(move.from_sq, move.to_sq)
        self.lbIni.ponTexto("%d/%d" % (self.repJugada + 1, num_moves))

        self.tableroFin.setposition(move.position)
        self.tableroFin.ponFlechaSC(move.from_sq, move.to_sq)
        self.lbFin.ponTexto("%d/%d" % (self.repJugada + 1, num_moves))

        QtCore.QTimer.singleShot(self.repTiempo, self.replayDispatch)

    def repCancelar(self):
        self.repWorking = False
        self.pon_toolbar(self.FINAL_JUEGO)
        self.ponInfo()

    def repReiniciar(self):
        self.repJugada = -1

    def repSlow(self):
        self.repTiempo += 500

    def repFast(self):
        if self.repTiempo >= 800:
            self.repTiempo -= 500
        else:
            self.repTiempo = 200

    def repPause(self):
        self.repWorking = False
        self.pon_toolbar(self.REPLAY_CONTINUE)

    def repContinue(self):
        self.repWorking = True
        self.pon_toolbar(self.REPLAY)
        self.replayDispatch()

    def reset(self):
        self.time_base = time.time()
        self.tableroIni.setposition(self.game.first_position)

        self.movActual = -1

        self.errors = 0
        self.hints = 0

        self.siguiente()

    def ponInfo(self):
        njg = self.repJugada if self.repWorking else self.movActual - 1
        txtPGN = self.game.pgn_translated(hastaJugada=njg)
        texto = "<big><center><b>%s</b>: %d<br><b>%s</b>: %d</center><br><br>%s</big>" % (
            _("Errors"),
            self.errors,
            _("Hints"),
            self.hints,
            txtPGN,
        )
        self.lbInfo.ponTexto(texto)

    def siguiente(self):
        num_moves = len(self.game)
        self.movActual += 1
        self.ponInfo()
        self.lbIni.ponTexto("%d/%d" % (self.movActual, num_moves))
        if self.movActual == num_moves:
            self.finalJuego()
            return

        move = self.game.move(self.movActual)

        self.tableroIni.setposition(move.position_before)
        if self.movActual > 0:
            jgant = self.game.move(self.movActual - 1)
            self.tableroIni.ponFlechaSC(jgant.from_sq, jgant.to_sq)

        mfin = self.movActual + self.nivel - 1
        if self.nivel == 0:
            mfin += 1
        if mfin >= num_moves:
            mfin = num_moves - 1

        jgf = self.game.move(mfin)
        self.tableroFin.setposition(jgf.position)
        if self.nivel == 0:
            self.tableroFin.ponFlechaSC(jgf.from_sq, jgf.to_sq)
        self.lbFin.ponTexto("%d/%d" % (mfin + 1, num_moves))

        color = move.position_before.is_white

        if (color and self.white) or (not color and self.black):
            self.tableroIni.activaColor(color)
        else:
            self.siguiente()

    def mueve_humano(self, from_sq, to_sq, promotion=""):

        move = self.game.move(self.movActual)

        # Peon coronando
        if not promotion and move.position_before.siPeonCoronando(from_sq, to_sq):
            promotion = self.tableroIni.peonCoronando(move.position_before.is_white)
            if promotion is None:
                promotion = "q"

        if from_sq == move.from_sq and to_sq == move.to_sq and promotion.lower() == move.promotion.lower():
            self.tableroIni.ponFlechaSC(from_sq, to_sq)
            self.siguiente()
            return False  # Que actualice solo siguiente
        else:
            if to_sq != from_sq:
                self.errors += 1
                self.tableroIni.ponFlechasTmp([(move.from_sq, move.to_sq, False)])
            self.ponInfo()
            return False

    def ayuda(self):

        move = self.game.move(self.movActual)
        self.tableroIni.ponFlechaSC(move.from_sq, move.to_sq)
        self.hints += 1

        self.ponInfo()

    def guardar(self):
        color = ""
        if self.white:
            color += "w"
        if self.black:
            color += "b"
        dic = {}
        dic["SECONDS"] = time.time() - self.time_base
        dic["DATE"] = Util.today()
        dic["LEVEL"] = self.nivel
        dic["COLOR"] = color
        dic["HINTS"] = self.hints
        dic["ERRORS"] = self.errors
        self.owner.guardar(dic)

    def finalJuego(self):
        self.siClock = False
        num_moves = len(self.game)
        self.lbIni.ponTexto("%d/%d" % (num_moves, num_moves))
        self.tableroIni.setposition(self.game.last_position)
        self.guardar()

        self.pon_toolbar(self.FINAL_JUEGO)

    def final(self):
        self.siClock = False
        self.save_video()
        self.accept()

    def cancelar(self):
        self.final()

    def ajustaReloj(self):
        if self.siClock:
            s = int(time.time() - self.time_base)

            m = s // 60
            s -= m * 60

            self.lbReloj.ponTexto("%02d:%02d" % (m, s))
            QtCore.QTimer.singleShot(500, self.ajustaReloj)

# -*- coding: utf-8 -*-
"""Ponto de entrada do VideoVox."""
import wx

from infra import caminhos
from ui.janela_principal import MainFrame


class App(wx.App):

    def OnInit(self):

        frame = MainFrame()

        frame.Show()

        return True


def main(pasta_programa):
    caminhos.definir_pasta_programa(pasta_programa)

    app = App(False)

    app.MainLoop()

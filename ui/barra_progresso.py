# -*- coding: utf-8 -*-
"""Barra de progresso acessivel a leitores de tela.

- A barra e nativa (msctls_progress32): o leitor de tela anuncia o papel
  "barra de progresso" e o valor em percentual, e acompanha as mudancas
  conforme a configuracao dele (bipes ou fala).
- Ela aceita foco pelo Tab, para ser consultada a qualquer momento sem travar
  a navegacao pelo resto da janela. Oculta, sai da ordem de tabulacao.
- O nome acessivel vem do rotulo visivel imediatamente anterior (e assim que o
  Windows nomeia barras de progresso). Por isso rotulo e barra sao criados e
  movidos juntos, nessa ordem.
- Ao mudar de etapa, o rotulo muda e o leitor de tela e avisado da troca de
  nome da barra.
"""
import ctypes
import sys

import wx

from core.progresso import ETAPA_AUDIO, ETAPA_IMAGENS

_EVENT_OBJECT_NAMECHANGE = 0x800C
_OBJID_CLIENT = -4
_CHILDID_SELF = 0


class _BarraFocavel(wx.Gauge):
    def AcceptsFocus(self):
        return self.IsShown()

    def AcceptsFocusFromKeyboard(self):
        return self.IsShown()


def _descrever_etapa(progresso):
    if progresso.etapa == ETAPA_AUDIO:
        return "gerando o áudio"
    return "gerando os quadros do vídeo"


class BarraProgresso:
    """Rotulo + barra, criados no `painel` e inseridos no `sizer` na
    `posicao` indicada. Comecam ocultos (sem ocupar espaco). `antes_de` e o
    controle que vem logo depois da barra na ordem de tabulacao."""

    def __init__(self, painel, sizer, posicao, antes_de):
        self.painel = painel
        self.rotulo = wx.StaticText(painel, label="")
        self.barra = _BarraFocavel(
            painel, range=100, style=wx.GA_HORIZONTAL | wx.GA_SMOOTH
        )
        # Ordem de tabulacao (e de janelas): rotulo, barra, `antes_de`.
        self.rotulo.MoveBeforeInTabOrder(antes_de)
        self.barra.MoveBeforeInTabOrder(antes_de)

        self.linha = wx.BoxSizer(wx.HORIZONTAL)
        self.linha.Add(self.rotulo, 0, wx.ALL | wx.CENTER, 5)
        self.linha.Add(self.barra, 1, wx.ALL | wx.CENTER, 5)
        sizer.Insert(posicao, self.linha, 0, wx.EXPAND)

        self.operacao = ""
        self.ativa = False
        self.rotulo.Hide()
        self.barra.Hide()

    def iniciar(self, operacao, focar):
        """Mostra a barra zerada para `operacao` (ex.: "Salvando o vídeo
        base"). Com `focar`, move o foco para a barra (use quando o controle
        focado vai ser desabilitado, para o foco nao se perder)."""
        self.operacao = operacao
        self.ativa = True
        self._definir_rotulo(f"{operacao}: preparando")
        self.barra.SetValue(0)
        self.rotulo.Show()
        self.barra.Show()
        self.painel.Layout()
        if focar:
            self.barra.SetFocus()

    def atualizar(self, progresso):
        if not self.ativa:
            return
        if progresso.etapa == ETAPA_IMAGENS:
            atual = min(progresso.feitos + 1, progresso.total)
            rotulo = f"{self.operacao}: imagem {atual} de {progresso.total}"
        else:
            rotulo = (
                f"{self.operacao}: {_descrever_etapa(progresso)} "
                f"(etapa {progresso.numero_etapa} de {progresso.total_etapas})"
            )
        if rotulo != self.rotulo.GetLabel():
            self._definir_rotulo(rotulo)
        self.barra.SetValue(progresso.percentual)

    def encerrar(self, devolver_foco_para):
        """Oculta a barra. Se o foco estava nela, vai para
        `devolver_foco_para` (que ja deve estar habilitado)."""
        self.ativa = False
        if self.barra.HasFocus():
            devolver_foco_para.SetFocus()
        self.rotulo.Hide()
        self.barra.Hide()
        self.painel.Layout()

    def tem_foco(self):
        return self.barra.HasFocus()

    def _definir_rotulo(self, texto):
        self.rotulo.SetLabel(texto)
        self.painel.Layout()
        # O nome da barra vem do rotulo: avisa o leitor de tela que mudou.
        if sys.platform == "win32" and self.barra.IsShown():
            ctypes.windll.user32.NotifyWinEvent(
                _EVENT_OBJECT_NAMECHANGE, self.barra.GetHandle(),
                _OBJID_CLIENT, _CHILDID_SELF
            )

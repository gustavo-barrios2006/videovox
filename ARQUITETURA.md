# Arquitetura do VideoVox

```
videovox.pyw      lançador: prepara stdout/stderr e chama app.main()
app.py            cria o wx.App e a janela principal
core/             regras do VideoVox, puras (sem wx, sem MoviePy)
motor/            único lugar que usa o MoviePy
servicos/         casos de uso: o que o usuário pede (gerar vídeo, salvar projeto...)
infra/            pastas, arquivos temporários e registro de erros
ui/               único lugar que usa o wx (janela, abas, diálogos)
tests/            testes com pytest (core e serviços, sem interface)
```

## Regra das dependências

```
ui  ──►  servicos  ──►  core
              │
              └──►  motor  ──►  MoviePy
```

- `core` não importa nenhum outro pacote do app.
- `servicos` usa `core` e `motor`, nunca `ui` nem `wx`.
- Só `motor` importa `moviepy`. Contornos de bugs da biblioteca e parâmetros
  do ffmpeg ficam lá.
- `ui` chama `servicos`; nunca abre clipes do MoviePy diretamente.

## Onde colocar cada coisa

| Mudança | Pacote |
|---|---|
| Regra de cálculo (tempo, sequência, tamanho do quadro, validação) | `core/` |
| Nova opção de lista/combo (ajustes, resoluções, presets) | `core/opcoes.py` |
| Operação com MoviePy/ffmpeg | `motor/` |
| Novo fluxo que o usuário dispara | `servicos/` + botão em `ui/` |
| Mudança no formato do `.wvp` | `servicos/projeto_io.py` (suba `VERSAO_FORMATO`) |
| Nova tela, aba ou diálogo | `ui/abas/` ou `ui/dialogos/` |

## Interface

- Tarefas demoradas rodam com `ui.tarefas.executar_em_segundo_plano`; a
  função executada não mexe em widgets e devolve o resultado com
  `wx.CallAfter`. Leia valores de widgets antes de iniciar a tarefa.
- Progresso: os serviços aceitam `ao_progredir(Progresso)` (`core/progresso.py`);
  o `motor/progresso.py` converte o progresso do MoviePy (blocos de áudio e
  quadros de vídeo, contagem exata). Na interface, use `ui/barra_progresso.py`:
  barra nativa (o NVDA bipa/fala conforme a configuração dele), alcançável pelo
  Tab, com o nome acessível vindo do rótulo visível logo antes dela.
- Ao capturar um erro de uma tarefa, registre-o com `infra.log.registrar_erro`
  e mostre `mensagem_com_registro(...)`, que diz ao usuário onde está o
  `erro.txt` (ao lado do executável ou, sem permissão de escrita, em
  `%LOCALAPPDATA%\VideoVox`). Erros não tratados são registrados
  automaticamente.
- A seção de áudio (`ui/abas/secao_audios.py`) cria os controles no mesmo
  painel da aba Criar Videoclipe, e não num subpainel: a ordem de tabulação
  da aba segue a ordem de criação dos controles. Mantenha os mnemônicos (`&`)
  e a ordem de tabulação ao adicionar controles.

## Testes

```
python -m pytest
```

A etapa de testes roda no workflow de release antes do build; uma release só
é publicada se os testes passarem.

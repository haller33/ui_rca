# 🗣️ UI_RCA — YouTube Comments Explorer

**UI on raylib and Python for visualize the db_rca and perform filtering**

Uma interface gráfica desktop para explorar, buscar e filtrar comentários do YouTube, alimentada pelos dados coletados e estruturados no [db_rca](https://github.com/haller33/db_rca). Desenvolvida com **raylib** e **Python**, a aplicação oferece uma experiência leve e responsiva para análise de interações em vídeos e lives.

## ✨ Funcionalidades

- 🔍 **Busca textual** – localize comentários por palavra‑chave no autor ou no conteúdo da mensagem.
- 📅 **Filtro por intervalo de datas** – visualize apenas comentários dentro de um período específico (formato `AAAA-MM-DD`).
- 🔄 **Sincronização com arquivos JSON** – importe novos comentários a partir da pasta `db_rca/raw`, evitando duplicatas.
- 🌗 **Temas claro e escuro (Solarized)** – alternância de cores para maior conforto visual.
- 🖱️ **Navegação simplificada** – clique nos campos, use o teclado para digitar e a roda do mouse para rolar a lista.
- ⚡ **Interface leve e eficiente** – construída sobre a biblioteca gráfica raylib, com renderização direta e baixo consumo de recursos.

## 🧱 Estrutura do Projeto

```
ui_rca/
├── ui.py                 # Aplicação principal (interface e lógica)
├── shell.nix             # Ambiente de desenvolvimento Nix
├── .gitmodules           # Submódulo apontando para db_rca
├── db_rca/               # Submódulo com banco SQLite e dados brutos
│   ├── comments.db       # Banco de dados dos comentários
│   └── raw/              # Arquivos JSON sincronizáveis (.live_chat.json)
└── README.md             # Este arquivo
```

> O diretório `db_rca` é um [submódulo Git](https://git-scm.com/book/en/v2/Git-Tools-Submodules). Clone este repositório com `--recursive` para obter automaticamente todo o conteúdo.

## 🧰 Tecnologias Utilizadas

| Camada           | Tecnologias                                                                 |
| ---------------- | --------------------------------------------------------------------------- |
| **Interface**    | [raylib](https://www.raylib.com/) + [pyray](https://github.com/electronstudio/raylib-python-cffi) (bindings Python) |
| **Banco de Dados** | SQLite3                                                                     |
| **Linguagem**    | Python 3                                                                    |
| **Empacotamento** | Nix (opcional, para ambiente reprodutível)                                 |

## 📦 Pré‑requisitos e Instalação

### 🔧 Via Python tradicional

1. **Clone o repositório com submódulos**:
   ```bash
   git clone --recursive https://github.com/haller33/ui_rca.git
   cd ui_rca
   ```

2. **Instale as dependências Python**:
   - [pyray](https://pypi.org/project/raylib/) (bindings para raylib)
   - Nenhuma outra dependência externa é necessária – o projeto usa apenas a biblioteca padrão do Python + pyray.

   ```bash
   pip install raylib
   ```

3. **Certifique‑se de que o banco de dados existe**:
   O caminho esperado é `./db_rca/comments.db`. Se o arquivo não estiver presente, a sincronização inicial criará a estrutura e os dados conforme os arquivos JSON disponíveis.

### 🐚 Usando Nix (recomendado para ambiente reprodutível)

Se você utiliza Nix ou NixOS, o arquivo `shell.nix` já configura todas as dependências (raylib, OpenGL, SQLite, etc.) e ativa um ambiente virtual Python automaticamente.

```bash
nix-shell
```

Dentro do shell, o comando `pip install raylib` é executado automaticamente, e o ambiente fica pronto para executar a interface.

## 🚀 Como Usar

1. **Execute a aplicação**:
   ```bash
   python ui.py
   ```

2. **Interface principal**:

   - **Campo de busca** – digite uma palavra‑chave e pressione `ENTER` ou clique em **BUSCAR**.
   - **Filtro de datas** – preencha os campos *Início* e *Fim* no formato `AAAA-MM-DD` e clique em **DATA**.
   - **Sincronizar** – clique em **SINCRONIZAR** para varrer a pasta `db_rca/raw` e importar novos comentários (apenas arquivos com extensão `.live_chat.json` são processados).
   - **Limpar filtros** – clique em **LIMPAR** para remover todos os filtros e exibir novamente os comentários mais recentes.
   - **Alternar tema** – clique no ícone de lua ou sol (canto superior direito) para mudar entre os temas claro e escuro Solarized.

3. **Navegação**:
   - Os resultados aparecem na área central. Role a lista com a **roda do mouse**.
   - Cada item mostra o nome do autor, a data/hora (formato `DD/MM/AAAA HH:MM`) e o conteúdo da mensagem.

## 🔄 Sincronização com Arquivos JSON

O processo de sincronização (`sync_database()`) percorre a pasta `db_rca/raw` em busca de arquivos `.live_chat.json`. Para cada arquivo, ele:

- Lê a lista de comentários (espera um array ou um dicionário contendo as chaves `comments` ou `items`).
- Extrai autor, mensagem e timestamp (em microssegundos) usando as funções `parse_comment_from_json()`.
- Insere apenas comentários ainda não existentes no banco (verificação por autor, mensagem e timestamp).

Essa estratégia evita duplicatas e permite adicionar novos dados de forma incremental.

## 🗄️ Esquema do Banco de Dados

A tabela principal (`comments`) possui a seguinte estrutura:

| Coluna          | Tipo      | Descrição                                 |
| --------------- | --------- | ----------------------------------------- |
| `author`        | TEXT      | Nome do autor do comentário               |
| `message`       | TEXT      | Conteúdo do comentário                    |
| `timestamp_usec`| INTEGER   | Timestamp em microssegundos desde a época |

A aplicação consulta essa tabela com suporte a busca textual (`LIKE`) e filtro por intervalo de datas.

## 🎨 Personalização

- **Cores**: As paletas **Solarized** (clara e escura) estão definidas no início do `ui.py`. Você pode alterar os valores RGB para adaptar o esquema de cores.
- **Dimensões da janela**: Ajuste as constantes `SCREEN_WIDTH` e `SCREEN_HEIGHT` conforme sua preferência.
- **Quantidade de resultados**: A função `get_filtered_comments()` possui um parâmetro `limit` (padrão = 50). Altere conforme a necessidade de performance.

## 📄 Licença

Este projeto está sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) (se disponível) para mais detalhes. Caso contrário, considere que os termos da licença MIT se aplicam por padrão, conforme indicado nos metadados do repositório.

## 👏 Agradecimentos

- [raylib](https://www.raylib.com/) – pela biblioteca gráfica simples e poderosa.
- [Solarized](https://ethanschoonover.com/solarized/) – pelas paletas de cores harmoniosas.
- O repositório [db_rca](https://github.com/haller33/db_rca) – que fornece a base de dados e os scripts de coleta.

---

> ⚠️ **Nota**: Este projeto depende do submódulo `db_rca`. Caso tenha clonado sem `--recursive`, execute `git submodule update --init --recursive` para obter os dados e o banco de exemplo.

Desenvolvido com ❤️ por [haller33](https://github.com/haller33).

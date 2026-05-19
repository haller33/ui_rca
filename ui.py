import pyray as pr
import sqlite3
import os
import json
import glob
import time
from datetime import datetime

# --- Configuração ---
DB_PATH = os.path.join(os.path.dirname(__file__), "./db_rca/comments.db")
RAW_DIR = os.path.join(os.path.dirname(__file__), "./db_rca/raw")
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 800

# --- Paletas Solarized ---
SOLARIZED_LIGHT = {
    "bg": pr.Color(253, 246, 227, 255),      # #fdf6e3
    "panel": pr.Color(238, 232, 213, 255),   # #eee8d5
    "text": pr.Color(101, 123, 131, 255),    # #657b83
    "text_bright": pr.Color(88, 110, 117, 255), # #586e75
    "accent": pr.Color(38, 139, 210, 255),   # #268bd2
    "hover": pr.Color(42, 161, 152, 255),    # #2aa198
    "success": pr.Color(133, 153, 0, 255),   # #859900
    "error": pr.Color(220, 50, 47, 255),     # #dc322f
    "border": pr.Color(147, 161, 161, 255),  # #93a1a1
}

SOLARIZED_DARK = {
    "bg": pr.Color(0, 43, 54, 255),          # #002b36
    "panel": pr.Color(7, 54, 66, 255),       # #073642
    "text": pr.Color(131, 148, 150, 255),    # #839496
    "text_bright": pr.Color(147, 161, 161, 255), # #93a1a1
    "accent": pr.Color(38, 139, 210, 255),   # #268bd2
    "hover": pr.Color(42, 161, 152, 255),    # #2aa198
    "success": pr.Color(133, 153, 0, 255),   # #859900
    "error": pr.Color(220, 50, 47, 255),     # #dc322f
    "border": pr.Color(101, 123, 131, 255),  # #657b83
}

# Tema atual (True = claro, False = escuro)
tema_claro = True

def get_colors():
    return SOLARIZED_LIGHT if tema_claro else SOLARIZED_DARK

# --- Função auxiliar para timestamp vindo do SQLite (pode ser str ou int) ---
def safe_timestamp_to_int(ts):
    if ts is None:
        return 0
    if isinstance(ts, str):
        return int(ts)
    return ts

# --- Sincronia com arquivos JSON ---
def parse_comment_from_json(data):
    """Extrai autor, mensagem e timestamp_usec de um objeto JSON de comentário."""
    author = data.get("author") or data.get("authorChannelId", {}).get("displayName", "Desconhecido")
    message = data.get("message") or data.get("messageText", "")
    ts = data.get("timestamp_usec") or data.get("timestampUsec")
    if ts is None:
        ts_sec = data.get("timestamp")
        if ts_sec:
            ts = int(float(ts_sec) * 1_000_000)
    return author, message, ts

def comment_exists(cursor, author, message, timestamp_usec):
    cursor.execute("SELECT 1 FROM comments WHERE author = ? AND message = ? AND timestamp_usec = ?",
                   (author, message, timestamp_usec))
    return cursor.fetchone() is not None

def sync_database(db_path, raw_dir, status_callback=None):
    """Varre arquivos JSON e insere novos comentários no banco de dados."""
    if not os.path.exists(raw_dir):
        if status_callback:
            status_callback("Pasta de dados brutos não encontrada: " + raw_dir)
        return 0

    json_files = glob.glob(os.path.join(raw_dir, "*.live_chat.json"), recursive=False)
    if not json_files:
        if status_callback:
            status_callback("Nenhum arquivo .live_chat.json encontrado em " + raw_dir)
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    novos = 0
    total = len(json_files)

    for idx, filepath in enumerate(json_files):
        if status_callback:
            status_callback(f"Sincronizando {idx+1}/{total}: {os.path.basename(filepath)}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                lista_comentarios = dados.get("comments") or dados.get("items") or []
            elif isinstance(dados, list):
                lista_comentarios = dados
            else:
                continue

            for item in lista_comentarios:
                autor, mensagem, ts = parse_comment_from_json(item)
                if not mensagem or not ts:
                    continue
                if not comment_exists(cursor, autor, mensagem, ts):
                    cursor.execute("INSERT INTO comments (author, message, timestamp_usec) VALUES (?, ?, ?)",
                                   (autor, mensagem, ts))
                    novos += 1
            conn.commit()
        except Exception as e:
            print(f"Erro ao processar {filepath}: {e}")
            continue

    conn.close()
    if status_callback:
        status_callback(f"Sincronização concluída. {novos} novos comentários adicionados.")
    return novos

# --- Consulta ao banco com filtros ---
def get_filtered_comments(keyword=None, start_usec=None, end_usec=None, limit=50):
    """Busca comentários correspondentes à palavra-chave e/ou intervalo de datas."""
    conditions = []
    params = []
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        conditions.append("(author LIKE ? OR message LIKE ?)")
        params.extend([kw, kw])
    if start_usec is not None:
        conditions.append("timestamp_usec >= ?")
        params.append(start_usec)
    if end_usec is not None:
        conditions.append("timestamp_usec <= ?")
        params.append(end_usec)

    query = "SELECT author, message, timestamp_usec FROM comments"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY timestamp_usec DESC LIMIT ?"
    params.append(limit)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Erro no banco de dados: {e}")
        return []

# --- Conversão de data string para microssegundos ---
def date_str_to_usec(date_str, end_of_day=False):
    """Converte YYYY-MM-DD para microssegundos desde a época. Se end_of_day=True, define 23:59:59.999999."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return int(dt.timestamp() * 1_000_000)
    except ValueError:
        return None

# --- Aplicação principal ---
def main():
    global tema_claro
    pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Explorador de Comentários do YouTube")
    pr.set_target_fps(60)

    # Estado da UI
    texto_busca = ""
    data_inicio_str = ""
    data_fim_str = ""
    mensagem_status = ""
    timer_status = 0.0
    resultados = []
    scroll_resultados = 0

    # Foco atual
    foco = None  # "busca", "data_inicio", "data_fim"

    # Retângulos dos elementos
    busca_rect = pr.Rectangle(50, 80, 400, 40)
    btn_busca_rect = pr.Rectangle(470, 80, 100, 40)
    area_resultados_rect = pr.Rectangle(50, 150, 1000, 600)
    btn_sincronizar_rect = pr.Rectangle(700, 80, 140, 40)
    btn_data_busca_rect = pr.Rectangle(860, 80, 100, 40)
    btn_limpar_rect = pr.Rectangle(970, 80, 80, 40)
    btn_tema_rect = pr.Rectangle(SCREEN_WIDTH - 60, 20, 40, 40)
    data_inicio_rect = pr.Rectangle(700, 140, 150, 35)
    data_fim_rect = pr.Rectangle(870, 140, 150, 35)

    def desenhar_campo_texto(rect, texto, ativo, placeholder=""):
        cores = get_colors()
        cor_borda = cores["accent"] if ativo else cores["border"]
        pr.draw_rectangle_lines_ex(rect, 2, cor_borda)
        pr.draw_rectangle_rec(rect, cores["panel"])
        exibir = texto if texto else placeholder
        cor_texto = cores["text"] if texto else cores["text_bright"]
        if ativo and (int(pr.get_time() * 2) % 2) == 0:
            exibir += "|"
        pr.draw_text(exibir, int(rect.x) + 8, int(rect.y) + 8, 20, cor_texto)

    while not pr.window_should_close():
        mouse_pos = pr.get_mouse_position()
        dt = pr.get_frame_time()
        if timer_status > 0:
            timer_status -= dt
        else:
            mensagem_status = ""

        cores = get_colors()

        # --- Clique do mouse para definir foco ---
        if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            if pr.check_collision_point_rec(mouse_pos, busca_rect):
                foco = "busca"
            elif pr.check_collision_point_rec(mouse_pos, data_inicio_rect):
                foco = "data_inicio"
            elif pr.check_collision_point_rec(mouse_pos, data_fim_rect):
                foco = "data_fim"
            elif pr.check_collision_point_rec(mouse_pos, btn_tema_rect):
                tema_claro = not tema_claro
                cores = get_colors()
            else:
                foco = None

        # --- Entrada de teclado para o campo focado ---
        if foco:
            tecla = pr.get_char_pressed()
            while tecla > 0:
                if 32 <= tecla <= 125 or tecla >= 160:
                    if foco == "busca":
                        texto_busca += chr(tecla)
                    elif foco == "data_inicio":
                        data_inicio_str += chr(tecla)
                    elif foco == "data_fim":
                        data_fim_str += chr(tecla)
                tecla = pr.get_char_pressed()

            if pr.is_key_pressed(pr.KEY_BACKSPACE) or pr.is_key_pressed_repeat(pr.KEY_BACKSPACE):
                if foco == "busca":
                    texto_busca = texto_busca[:-1]
                elif foco == "data_inicio":
                    data_inicio_str = data_inicio_str[:-1]
                elif foco == "data_fim":
                    data_fim_str = data_fim_str[:-1]

            if pr.is_key_pressed(pr.KEY_ENTER):
                if foco == "busca":
                    resultados = get_filtered_comments(keyword=texto_busca)
                    scroll_resultados = 0

        # --- Ações dos botões ---
        hover_busca = pr.check_collision_point_rec(mouse_pos, btn_busca_rect)
        if hover_busca and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            resultados = get_filtered_comments(keyword=texto_busca)
            scroll_resultados = 0
            mensagem_status = f"Encontrados {len(resultados)} comentários."
            timer_status = 2.0

        hover_sinc = pr.check_collision_point_rec(mouse_pos, btn_sincronizar_rect)
        if hover_sinc and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            def callback_status(msg):
                nonlocal mensagem_status, timer_status
                mensagem_status = msg
                timer_status = 2.0
                pr.begin_drawing()
                pr.end_drawing()
            sync_database(DB_PATH, RAW_DIR, callback_status)

        hover_data = pr.check_collision_point_rec(mouse_pos, btn_data_busca_rect)
        if hover_data and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            inicio_usec = date_str_to_usec(data_inicio_str) if data_inicio_str else None
            fim_usec = date_str_to_usec(data_fim_str, end_of_day=True) if data_fim_str else None
            if (data_inicio_str and inicio_usec is None) or (data_fim_str and fim_usec is None):
                mensagem_status = "Formato de data inválido. Use AAAA-MM-DD."
                timer_status = 2.0
            else:
                resultados = get_filtered_comments(keyword=texto_busca, start_usec=inicio_usec, end_usec=fim_usec)
                scroll_resultados = 0
                mensagem_status = f"Encontrados {len(resultados)} comentários."
                timer_status = 2.0

        hover_limpar = pr.check_collision_point_rec(mouse_pos, btn_limpar_rect)
        if hover_limpar and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            texto_busca = ""
            data_inicio_str = ""
            data_fim_str = ""
            resultados = get_filtered_comments()
            scroll_resultados = 0
            mensagem_status = "Filtros limpos. Mostrando comentários recentes."
            timer_status = 2.0

        # --- Roda do mouse para rolar resultados (CORRIGIDO) ---
        scroll_amount = pr.get_mouse_wheel_move()
        if scroll_amount != 0 and pr.check_collision_point_rec(mouse_pos, area_resultados_rect):
            scroll_resultados -= int(scroll_amount * 2)   # converte para inteiro
            altura_item = 70
            max_scroll = max(0, len(resultados) - int(area_resultados_rect.height / altura_item))
            scroll_resultados = max(0, min(scroll_resultados, max_scroll))
            scroll_resultados = int(scroll_resultados)   # garante inteiro

        # --- Desenho da interface ---
        pr.begin_drawing()
        pr.clear_background(cores["bg"])

        # Cabeçalho
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, 60, cores["accent"])
        pr.draw_text("Explorador de Comentários do YouTube", 50, 15, 30, pr.WHITE)

        # Botão de tema
        icone_tema = "🌙" if tema_claro else "☀️"
        btn_tema_cor = cores["hover"] if pr.check_collision_point_rec(mouse_pos, btn_tema_rect) else cores["panel"]
        pr.draw_rectangle_rec(btn_tema_rect, btn_tema_cor)
        pr.draw_rectangle_lines_ex(btn_tema_rect, 2, cores["border"])
        pr.draw_text(icone_tema, int(btn_tema_rect.x) + 8, int(btn_tema_rect.y) + 5, 28, cores["text"])

        # Campo de busca
        pr.draw_text("Buscar por palavra‑chave (autor ou mensagem):", 50, 60, 16, cores["text"])
        desenhar_campo_texto(busca_rect, texto_busca, foco == "busca", "Digite a palavra‑chave...")
        pr.draw_rectangle_rec(btn_busca_rect, cores["hover"] if hover_busca else cores["accent"])
        pr.draw_text("BUSCAR", int(btn_busca_rect.x) + 20, int(btn_busca_rect.y) + 10, 20, pr.WHITE)

        # Botões de ação
        pr.draw_rectangle_rec(btn_sincronizar_rect, cores["hover"] if hover_sinc else cores["accent"])
        pr.draw_text("SINCRONIZAR", int(btn_sincronizar_rect.x) + 20, int(btn_sincronizar_rect.y) + 10, 18, pr.WHITE)

        pr.draw_rectangle_rec(btn_data_busca_rect, cores["hover"] if hover_data else cores["accent"])
        pr.draw_text("DATA", int(btn_data_busca_rect.x) + 30, int(btn_data_busca_rect.y) + 10, 18, pr.WHITE)

        pr.draw_rectangle_rec(btn_limpar_rect, cores["hover"] if hover_limpar else cores["error"])
        pr.draw_text("LIMPAR", int(btn_limpar_rect.x) + 12, int(btn_limpar_rect.y) + 10, 18, pr.WHITE)

        # Campos de data
        desenhar_campo_texto(data_inicio_rect, data_inicio_str, foco == "data_inicio", "Início AAAA-MM-DD")
        desenhar_campo_texto(data_fim_rect, data_fim_str, foco == "data_fim", "Fim AAAA-MM-DD")

        # Área de resultados
        pr.draw_rectangle_rec(area_resultados_rect, cores["panel"])
        pr.draw_rectangle_lines_ex(area_resultados_rect, 2, cores["border"])
        pr.draw_text("Comentários", int(area_resultados_rect.x) + 10, int(area_resultados_rect.y) - 25, 18, cores["accent"])

        if not resultados:
            msg = "Nenhum comentário encontrado." if (texto_busca or data_inicio_str or data_fim_str) else "Digite uma palavra‑chave ou use filtros de data."
            pr.draw_text(msg, int(area_resultados_rect.x) + 20, int(area_resultados_rect.y) + 30, 20, cores["text_bright"])
        else:
            idx_inicio = int(scroll_resultados)   # Garante inteiro para range()
            y_offset = area_resultados_rect.y + 10
            limite_y = area_resultados_rect.y + area_resultados_rect.height - 10
            for i in range(idx_inicio, min(len(resultados), idx_inicio + 50)):
                autor, mensagem, ts_raw = resultados[i]
                ts = safe_timestamp_to_int(ts_raw)
                dt_obj = datetime.fromtimestamp(ts / 1_000_000)
                data_str = dt_obj.strftime("%d/%m/%Y %H:%M")
                msg_exibida = mensagem if len(mensagem) < 80 else mensagem[:77] + "..."

                pr.draw_text(f"{autor} ({data_str})", int(area_resultados_rect.x) + 15, int(y_offset), 16, cores["accent"])
                pr.draw_text(msg_exibida, int(area_resultados_rect.x) + 15, int(y_offset) + 22, 18, cores["text"])

                # Linha separadora
                x1 = int(area_resultados_rect.x) + 10
                y1 = int(y_offset) + 48
                x2 = int(area_resultados_rect.x + area_resultados_rect.width - 10)
                y2 = int(y_offset + 48)
                pr.draw_line(x1, y1, x2, y2, cores["border"])

                y_offset += 70
                if y_offset + 50 > limite_y:
                    break

            # Indicadores de rolagem
            if scroll_resultados > 0:
                pr.draw_text("▲", int(area_resultados_rect.x + area_resultados_rect.width - 25), int(area_resultados_rect.y + 5), 20, cores["text_bright"])
            if scroll_resultados + int(area_resultados_rect.height / 70) < len(resultados):
                pr.draw_text("▼", int(area_resultados_rect.x + area_resultados_rect.width - 25), int(area_resultados_rect.y + area_resultados_rect.height - 25), 20, cores["text_bright"])

        # Mensagem de status
        if mensagem_status:
            cor = cores["error"] if ("erro" in mensagem_status.lower() or "inválido" in mensagem_status.lower()) else cores["success"]
            pr.draw_text(mensagem_status, 50, SCREEN_HEIGHT - 30, 18, cor)

        pr.end_drawing()

    pr.close_window()

if __name__ == "__main__":
    main()

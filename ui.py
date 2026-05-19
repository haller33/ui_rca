import pyray as pr
import sqlite3
import os
from datetime import datetime

# --- Configuração ---
DB_PATH = os.path.join(os.path.dirname(__file__), "./db_rca/comments.db")
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
limite_resultados = 50  # limite de resultados exibidos (pode ser alterado com +/-)

def get_colors():
    return SOLARIZED_LIGHT if tema_claro else SOLARIZED_DARK

def safe_timestamp_to_int(ts):
    if ts is None:
        return 0
    if isinstance(ts, str):
        return int(ts)
    return ts

def get_filtered_comments(keyword=None, start_usec=None, end_usec=None, limit=50):
    """Busca comentários e retorna (resultados, total_disponivel)"""
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

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # Query para contar total (sem limite)
    count_query = f"SELECT COUNT(*) FROM comments{where_clause}"
    # Query para buscar com limite
    data_query = f"SELECT author, message, timestamp_usec FROM comments{where_clause} ORDER BY timestamp_usec DESC LIMIT ?"
    data_params = params + [limit]

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        cursor.execute(data_query, data_params)
        results = cursor.fetchall()
        conn.close()
        return results, total
    except Exception as e:
        print(f"Erro no banco de dados: {e}")
        return [], 0

def date_str_to_usec(date_str, end_of_day=False):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return int(dt.timestamp() * 1_000_000)
    except ValueError:
        return None

def main():
    global tema_claro, limite_resultados
    pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Explorador de Comentários do YouTube")
    pr.set_target_fps(60)
    pr.set_exit_key(pr.KEY_NULL)  # tratamos ESC manualmente

    # Estado
    texto_busca = ""
    data_inicio_str = ""
    data_fim_str = ""
    mensagem_status = ""
    timer_status = 0.0
    resultados = []
    total_resultados = 0
    scroll_resultados = 0
    foco = None  # "busca", "data_inicio", "data_fim"

    # Variáveis para efeito de clique nos botões
    btn_click_timer = 0.0
    btn_hover_data = False

    def atualizar_resultados():
        nonlocal resultados, total_resultados, scroll_resultados
        inicio_usec = date_str_to_usec(data_inicio_str) if data_inicio_str else None
        fim_usec = date_str_to_usec(data_fim_str, end_of_day=True) if data_fim_str else None
        if (data_inicio_str and inicio_usec is None) or (data_fim_str and fim_usec is None):
            mensagem_status = "Formato de data inválido. Use AAAA-MM-DD."
            timer_status = 2.0
            return
        resultados, total_resultados = get_filtered_comments(
            keyword=texto_busca,
            start_usec=inicio_usec,
            end_usec=fim_usec,
            limit=limite_resultados
        )
        scroll_resultados = 0
        if len(resultados) > 0:
            mensagem_status = f"Encontrados {len(resultados)} de {total_resultados} comentários (limite: {limite_resultados})."
        else:
            mensagem_status = "Nenhum comentário encontrado."
        timer_status = 2.0

    # Layout dinâmico (será recalculado a cada frame se a janela for redimensionada)
    def atualizar_layout():
        width = pr.get_screen_width()
        height = pr.get_screen_height()
        # Retângulos proporcionais
        busca_rect = pr.Rectangle(50, 80, 400, 40)
        btn_busca_rect = pr.Rectangle(470, 80, 100, 40)
        area_resultados_rect = pr.Rectangle(50, 150, width - 100, height - 200)
        btn_data_busca_rect = pr.Rectangle(width - 250, 80, 100, 40)
        btn_limpar_rect = pr.Rectangle(width - 130, 80, 80, 40)
        btn_tema_rect = pr.Rectangle(width - 60, 20, 40, 40)
        data_inicio_rect = pr.Rectangle(width - 380, 140, 150, 35)
        data_fim_rect = pr.Rectangle(width - 210, 140, 150, 35)
        return (busca_rect, btn_busca_rect, area_resultados_rect, btn_data_busca_rect,
                btn_limpar_rect, btn_tema_rect, data_inicio_rect, data_fim_rect)

    # Inicialização
    (busca_rect, btn_busca_rect, area_resultados_rect, btn_data_busca_rect,
     btn_limpar_rect, btn_tema_rect, data_inicio_rect, data_fim_rect) = atualizar_layout()
    # Carrega comentários iniciais
    atualizar_resultados()

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
        # Redimensionamento
        if pr.is_window_resized():
            (busca_rect, btn_busca_rect, area_resultados_rect, btn_data_busca_rect,
             btn_limpar_rect, btn_tema_rect, data_inicio_rect, data_fim_rect) = atualizar_layout()

        mouse_pos = pr.get_mouse_position()
        dt = pr.get_frame_time()
        if timer_status > 0:
            timer_status -= dt
        else:
            mensagem_status = ""

        # Efeito de clique nos botões
        if btn_click_timer > 0:
            btn_click_timer -= dt

        # Atalhos de teclado globais
        if pr.is_key_pressed(pr.KEY_TAB):
            # Alterna foco entre os três campos
            if foco is None:
                foco = "busca"
            elif foco == "busca":
                foco = "data_inicio"
            elif foco == "data_inicio":
                foco = "data_fim"
            else:
                foco = None
        if pr.is_key_down(pr.KEY_LEFT_CONTROL) or pr.is_key_down(pr.KEY_RIGHT_CONTROL):
            if pr.is_key_pressed(pr.KEY_L):
                # Ctrl+L: limpa tudo
                texto_busca = ""
                data_inicio_str = ""
                data_fim_str = ""
                atualizar_resultados()
            elif pr.is_key_pressed(pr.KEY_F):
                # Ctrl+F: foco na busca
                foco = "busca"
        if pr.is_key_pressed(pr.KEY_ESCAPE):
            pr.close_window()
            return
        # Ajuste de limite com +/-
        if pr.is_key_pressed(pr.KEY_KP_ADD) or pr.is_key_pressed(pr.KEY_EQUAL):
            limite_resultados = min(500, limite_resultados + 10)
            atualizar_resultados()
        elif pr.is_key_pressed(pr.KEY_KP_SUBTRACT) or pr.is_key_pressed(pr.KEY_MINUS):
            limite_resultados = max(10, limite_resultados - 10)
            atualizar_resultados()

        cores = get_colors()

        # Entrada de teclado para campo focado
        if foco:
            tecla = pr.get_char_pressed()
            while tecla > 0:
                if 32 <= tecla <= 125 or tecla >= 160:
                    if foco == "busca":
                        texto_busca += chr(tecla)
                        atualizar_resultados()
                    elif foco == "data_inicio":
                        data_inicio_str += chr(tecla)
                        atualizar_resultados()
                    elif foco == "data_fim":
                        data_fim_str += chr(tecla)
                        atualizar_resultados()
                tecla = pr.get_char_pressed()

            if pr.is_key_pressed(pr.KEY_BACKSPACE) or pr.is_key_pressed_repeat(pr.KEY_BACKSPACE):
                if foco == "busca" and texto_busca:
                    texto_busca = texto_busca[:-1]
                    atualizar_resultados()
                elif foco == "data_inicio" and data_inicio_str:
                    data_inicio_str = data_inicio_str[:-1]
                    atualizar_resultados()
                elif foco == "data_fim" and data_fim_str:
                    data_fim_str = data_fim_str[:-1]
                    atualizar_resultados()

        # Clique do mouse
        if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            if pr.check_collision_point_rec(mouse_pos, busca_rect):
                foco = "busca"
            elif pr.check_collision_point_rec(mouse_pos, data_inicio_rect):
                foco = "data_inicio"
            elif pr.check_collision_point_rec(mouse_pos, data_fim_rect):
                foco = "data_fim"
            elif pr.check_collision_point_rec(mouse_pos, btn_tema_rect):
                tema_claro = not tema_claro
            elif pr.check_collision_point_rec(mouse_pos, btn_busca_rect):
                atualizar_resultados()
                btn_click_timer = 0.2
            elif pr.check_collision_point_rec(mouse_pos, btn_data_busca_rect):
                atualizar_resultados()
                btn_click_timer = 0.2
            elif pr.check_collision_point_rec(mouse_pos, btn_limpar_rect):
                texto_busca = ""
                data_inicio_str = ""
                data_fim_str = ""
                atualizar_resultados()
                btn_click_timer = 0.2
            else:
                foco = None

        # Scroll da área de resultados
        scroll_amount = pr.get_mouse_wheel_move()
        if scroll_amount != 0 and pr.check_collision_point_rec(mouse_pos, area_resultados_rect):
            altura_item = 70
            max_scroll = max(0, len(resultados) - int(area_resultados_rect.height / altura_item))
            scroll_resultados -= int(scroll_amount * 2)
            scroll_resultados = max(0, min(scroll_resultados, max_scroll))

        # Desenho
        pr.begin_drawing()
        pr.clear_background(cores["bg"])

        # Cabeçalho
        pr.draw_rectangle(0, 0, pr.get_screen_width(), 60, cores["accent"])
        pr.draw_text("Explorador de Comentários do YouTube", 50, 15, 30, pr.WHITE)

        # Informação do limite
        limite_text = f"Limite: {limite_resultados} (+/-)"
        pr.draw_text(limite_text, pr.get_screen_width() - 120, 25, 14, pr.WHITE)

        # Botão tema
        icone_tema = "🌙" if tema_claro else "☀️"
        btn_tema_cor = cores["hover"] if pr.check_collision_point_rec(mouse_pos, btn_tema_rect) else cores["panel"]
        pr.draw_rectangle_rec(btn_tema_rect, btn_tema_cor)
        pr.draw_rectangle_lines_ex(btn_tema_rect, 2, cores["border"])
        pr.draw_text(icone_tema, int(btn_tema_rect.x) + 8, int(btn_tema_rect.y) + 5, 28, cores["text"])

        # Campo de busca
        pr.draw_text("Buscar por palavra‑chave (autor ou mensagem):", 50, 60, 16, cores["text"])
        desenhar_campo_texto(busca_rect, texto_busca, foco == "busca", "Digite a palavra‑chave...")
        # Botão BUSCAR
        cor_busca = cores["hover"] if pr.check_collision_point_rec(mouse_pos, btn_busca_rect) else cores["accent"]
        if btn_click_timer > 0 and pr.check_collision_point_rec(mouse_pos, btn_busca_rect):
            cor_busca = cores["success"]
        pr.draw_rectangle_rec(btn_busca_rect, cor_busca)
        pr.draw_text("BUSCAR", int(btn_busca_rect.x) + 20, int(btn_busca_rect.y) + 10, 20, pr.WHITE)

        # Botão DATA
        cor_data = cores["hover"] if pr.check_collision_point_rec(mouse_pos, btn_data_busca_rect) else cores["accent"]
        if btn_click_timer > 0 and pr.check_collision_point_rec(mouse_pos, btn_data_busca_rect):
            cor_data = cores["success"]
        pr.draw_rectangle_rec(btn_data_busca_rect, cor_data)
        pr.draw_text("DATA", int(btn_data_busca_rect.x) + 30, int(btn_data_busca_rect.y) + 10, 18, pr.WHITE)

        # Botão LIMPAR
        cor_limpar = cores["hover"] if pr.check_collision_point_rec(mouse_pos, btn_limpar_rect) else cores["error"]
        if btn_click_timer > 0 and pr.check_collision_point_rec(mouse_pos, btn_limpar_rect):
            cor_limpar = cores["success"]
        pr.draw_rectangle_rec(btn_limpar_rect, cor_limpar)
        pr.draw_text("LIMPAR", int(btn_limpar_rect.x) + 12, int(btn_limpar_rect.y) + 10, 18, pr.WHITE)

        # Campos de data
        desenhar_campo_texto(data_inicio_rect, data_inicio_str, foco == "data_inicio", "Início AAAA-MM-DD")
        desenhar_campo_texto(data_fim_rect, data_fim_str, foco == "data_fim", "Fim AAAA-MM-DD")

        # Área de resultados
        pr.draw_rectangle_rec(area_resultados_rect, cores["panel"])
        pr.draw_rectangle_lines_ex(area_resultados_rect, 2, cores["border"])
        titulo = f"Comentários ({len(resultados)} exibidos de {total_resultados})"
        pr.draw_text(titulo, int(area_resultados_rect.x) + 10, int(area_resultados_rect.y) - 25, 18, cores["accent"])

        if not resultados:
            msg = "Nenhum comentário encontrado." if (texto_busca or data_inicio_str or data_fim_str) else "Digite uma palavra‑chave ou use filtros de data."
            pr.draw_text(msg, int(area_resultados_rect.x) + 20, int(area_resultados_rect.y) + 30, 20, cores["text_bright"])
        else:
            idx_inicio = scroll_resultados
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
            pr.draw_text(mensagem_status, 50, pr.get_screen_height() - 30, 18, cor)

        pr.end_drawing()

    pr.close_window()

if __name__ == "__main__":
    main()

import pyray as pr
import sqlite3
import os

# --- Configuration ---
DB_PATH = os.path.join(os.path.dirname(__file__), "./db_rca/comments.db")
DB_NAME = DB_PATH
# DB_NAME = "comments.db"
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700

# --- Colors ---
BG_COLOR = pr.Color(245, 245, 245, 255)        # Soft light gray
PANEL_COLOR = pr.Color(255, 255, 255, 255)     # White
TEXT_COLOR = pr.Color(40, 40, 40, 255)         # Dark gray
SUBTEXT_COLOR = pr.Color(120, 120, 120, 255)   # Medium gray
PRIMARY_COLOR = pr.Color(66, 135, 245, 255)    # Friendly Blue
HOVER_COLOR = pr.Color(100, 160, 255, 255)     # Lighter Blue

def search_database(search_term):
    """Fetches up to 15 recent comments matching the search term in author or message."""
    if not search_term.strip():
        return []
        
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        query = f"%{search_term}%"
        
        # Searching both author and message columns
        cursor.execute("""
            SELECT author, message, timestamp_usec 
            FROM comments 
            WHERE author LIKE ? OR message LIKE ?
            ORDER BY timestamp_usec DESC
            LIMIT 12
        """, (query, query))
        
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Database Error: {e}")
        return []

def main():
    pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Comment Search Explorer")
    pr.set_target_fps(60)

    # UI State variables
    search_text = ""
    is_typing = False
    results = []
    
    # UI Elements Rectangles (x, y, width, height)
    search_box_rect = pr.Rectangle(50, 80, 600, 40)
    search_btn_rect = pr.Rectangle(670, 80, 180, 40)

    while not pr.window_should_close():
        mouse_pos = pr.get_mouse_position()
        
        # --- Logic & Interaction ---
        
        # Check if user clicked inside the text box to start typing
        if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            if pr.check_collision_point_rec(mouse_pos, search_box_rect):
                is_typing = True
            else:
                is_typing = False

        # Handle keyboard input for the search box
        if is_typing:
            # Get typed characters
            key = pr.get_char_pressed()
            while key > 0:
                # Add character if it's a valid printable ASCII/Unicode character
                if 32 <= key <= 125 or key >= 160:
                    search_text += chr(key)
                key = pr.get_char_pressed()

            # Handle Backspace
            if pr.is_key_pressed(pr.KEY_BACKSPACE) or pr.is_key_pressed_repeat(pr.KEY_BACKSPACE):
                search_text = search_text[:-1]

            # Handle Enter key to trigger search
            if pr.is_key_pressed(pr.KEY_ENTER):
                results = search_database(search_text)

        # Handle Search Button Click
        btn_hover = pr.check_collision_point_rec(mouse_pos, search_btn_rect)
        if btn_hover and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            results = search_database(search_text)

        # --- Drawing ---
        pr.begin_drawing()
        pr.clear_background(BG_COLOR)

        # Top Header
        pr.draw_rectangle(0, 0, SCREEN_WIDTH, 60, PRIMARY_COLOR)
        pr.draw_text("YouTube Comment Search", 50, 15, 30, pr.WHITE)

        # Instructions
        pr.draw_text("Type a username or keyword to search:", 50, 60, 16, SUBTEXT_COLOR)

        # Draw Search Box
        box_color = PRIMARY_COLOR if is_typing else pr.LIGHTGRAY
        pr.draw_rectangle_lines_ex(search_box_rect, 2, box_color)
        pr.draw_rectangle_rec(search_box_rect, PANEL_COLOR)
        
        # Draw Search Text (Add a blinking cursor if active)
        display_text = search_text
        if is_typing and int(pr.get_time() * 2) % 2 == 0:
            display_text += "|"
        pr.draw_text(display_text, int(search_box_rect.x) + 10, int(search_box_rect.y) + 10, 20, TEXT_COLOR)

        # Draw Search Button
        current_btn_color = HOVER_COLOR if btn_hover else PRIMARY_COLOR
        pr.draw_rectangle_rec(search_btn_rect, current_btn_color)
        pr.draw_text("SEARCH", int(search_btn_rect.x) + 50, int(search_btn_rect.y) + 10, 20, pr.WHITE)

        # Draw Results Area Background
        results_bg = pr.Rectangle(50, 150, 800, 500)
        pr.draw_rectangle_rec(results_bg, PANEL_COLOR)
        pr.draw_rectangle_lines_ex(results_bg, 1, pr.LIGHTGRAY)

        # Draw Results
        if len(results) == 0:
            if search_text != "":
                pr.draw_text("No results found. Try another keyword.", 70, 170, 20, SUBTEXT_COLOR)
            else:
                pr.draw_text("Results will appear here...", 70, 170, 20, SUBTEXT_COLOR)
        else:
            y_offset = 170
            for row in results:
                author, message, timestamp = row
                
                # Truncate message if it's too long for the screen
                display_msg = message if len(message) < 80 else message[:77] + "..."
                
                # Draw Author (Bold-ish/Blueish)
                pr.draw_text(author, 70, y_offset, 18, PRIMARY_COLOR)
                
                # Draw Message
                pr.draw_text(display_msg, 70, y_offset + 25, 18, TEXT_COLOR)
                
                # Draw separator line
                pr.draw_line(70, y_offset + 55, 830, y_offset + 55, pr.LIGHTGRAY)
                
                y_offset += 70

        pr.end_drawing()

    pr.close_window()

if __name__ == "__main__":
    main()

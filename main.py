import os
import pygame
import chess
import chess.engine

# Initialize pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 600, 600
square_size = WIDTH // 8
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Chess Game")

# Load chess engine (Stockfish)

# Get the directory where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load Stockfish engine from the "stockfish" folder
engine_path = os.path.join(script_dir, "stockfish", "stockfish-windows-x86-64-avx2.exe")

# Check if the Stockfish file exists
if not os.path.exists(engine_path):
    raise FileNotFoundError(f"Stockfish engine not found at {engine_path}. Make sure it's in the 'stockfish' folder.")

engine = chess.engine.SimpleEngine.popen_uci(engine_path)

# Load board
board = chess.Board()

# Colors
WHITE = (255, 255, 255)
DARK_BROWN = (150, 75, 0)
RED = (255, 0, 0)    # Highlight for king in check
YELLOW = (255, 255, 0)  # Highlight for selected piece
BLUE = (0, 191, 255)  # Highlight for last move
GREEN = (0, 200, 0)   # Play Again button
BLACK = (0, 0, 0)

# Load chess piece images
piece_names = {
    "P": "wp.png", "R": "wr.png", "N": "wn.png", "B": "wb.png", "Q": "wq.png", "K": "wk.png",
    "p": "bp.png", "r": "br.png", "n": "bn.png", "b": "bb.png", "q": "bq.png", "k": "bk.png",
}
piece_images = {}
for symbol, filename in piece_names.items():
    image_path = os.path.join(script_dir, "pieces", filename)  # Construct relative path
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Missing piece image: {image_path}. Ensure all chess pieces are in the 'pieces' folder.")

    piece_images[symbol] = pygame.image.load(image_path)
    piece_images[symbol] = pygame.transform.scale(piece_images[symbol], (square_size, square_size))

# Font setup
font_large = pygame.font.Font(None, 80)
font_small = pygame.font.Font(None, 40)

# Variables for game state
selected_square = None
last_move = None  # Stores last move's "from" and "to" squares
game_over = False
game_result = ""  # Stores "Checkmate!" or "Stalemate!"

# Function to draw the board and highlight important squares
def draw_board():
    colors = [WHITE, DARK_BROWN]
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(col * square_size, row * square_size, square_size, square_size))

    # Highlight last moved piece (blue)
    if last_move:
        from_square, to_square = last_move
        from_col, from_row = chess.square_file(from_square), 7 - chess.square_rank(from_square)
        to_col, to_row = chess.square_file(to_square), 7 - chess.square_rank(to_square)

        pygame.draw.rect(screen, BLUE, pygame.Rect(from_col * square_size, from_row * square_size, square_size, square_size), 5)
        pygame.draw.rect(screen, BLUE, pygame.Rect(to_col * square_size, to_row * square_size, square_size, square_size), 5)

    # Highlight selected piece (yellow)
    if selected_square is not None:
        col, row = chess.square_file(selected_square), 7 - chess.square_rank(selected_square)
        pygame.draw.rect(screen, YELLOW, pygame.Rect(col * square_size, row * square_size, square_size, square_size), 5)

    # Highlight the king if in check (red)
    if board.is_check():
        king_square = board.king(board.turn)
        if king_square is not None:
            king_col, king_row = chess.square_file(king_square), 7 - chess.square_rank(king_square)
            pygame.draw.rect(screen, RED, pygame.Rect(king_col * square_size, king_row * square_size, square_size, square_size), 5)

# Function to draw pieces on the board
def draw_pieces():
    for row in range(8):
        for col in range(8):
            piece = board.piece_at(chess.square(col, 7 - row))
            if piece:
                screen.blit(piece_images[piece.symbol()], (col * square_size, row * square_size))

# AI move function
def ai_move():
    global game_over, last_move, game_result
    if board.turn == chess.BLACK and not game_over:  
        result = engine.play(board, chess.engine.Limit(time=0.5))
        last_move = (result.move.from_square, result.move.to_square)  # Store AI's last move
        board.push(result.move)

    # Check for game-ending conditions
    check_game_state()

# Function to check for checkmate or stalemate
def check_game_state():
    global game_over, game_result
    if board.is_checkmate():
        game_result = "CHECKMATE!"
        game_over = True
    elif board.is_stalemate():
        game_result = "STALEMATE!"
        game_over = True

# Function to handle user moves
def handle_click(position):
    global selected_square, last_move

    if game_over:
        return  # Prevent moves if the game is over

    col = position[0] // square_size
    row = position[1] // square_size
    clicked_square = chess.square(col, 7 - row)  # Convert to chess square index

    if selected_square is None:
        # First click: Select a piece
        piece = board.piece_at(clicked_square)
        if piece and piece.color == chess.WHITE:  
            selected_square = clicked_square
    else:
        # Second click: Attempt to move
        move = chess.Move(selected_square, clicked_square)

        # Handle pawn promotions
        if board.piece_at(selected_square).piece_type == chess.PAWN:
            if chess.square_rank(clicked_square) in [0, 7]:  
                move = chess.Move(selected_square, clicked_square, promotion=chess.QUEEN)

        # Handle special moves
        if move not in board.legal_moves:
            for legal_move in board.legal_moves:
                if legal_move.from_square == selected_square and legal_move.to_square == clicked_square:
                    move = legal_move
                    break

        if move in board.legal_moves:
            board.push(move)
            last_move = (move.from_square, move.to_square)  # Store the last move

            # Check for game-ending conditions
            check_game_state()

            if not game_over:
                ai_move()

        selected_square = None  # Reset selection

# Function to display game result message
def display_game_result():
    text = font_large.render(game_result, True, RED)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(text, text_rect)

    # Draw "Play Again" button
    button_rect = pygame.Rect(WIDTH // 3, HEIGHT // 2, WIDTH // 3, 50)
    pygame.draw.rect(screen, GREEN, button_rect)
    pygame.draw.rect(screen, BLACK, button_rect, 3)  

    button_text = font_small.render("Play Again", True, WHITE)
    button_text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, button_text_rect)

    return button_rect  

# Function to reset the game
def reset_game():
    global board, selected_square, game_over, last_move, game_result
    board = chess.Board()  
    selected_square = None
    last_move = None
    game_result = ""
    game_over = False  

# Main loop
def main():
    running = True

    while running:
        draw_board()
        draw_pieces()

        if game_over:
            play_again_button = display_game_result()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    if play_again_button.collidepoint(event.pos):
                        reset_game()
                else:
                    handle_click(pygame.mouse.get_pos())

    engine.quit()
    pygame.quit()

if __name__ == "__main__":
    main()

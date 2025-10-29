"""
BeeWise - A Spelling Practice Application
"""

import pygame
import sys
import pyttsx3

# ============================================================================
# INITIALISATION
# ============================================================================

# Initialize pygame
pygame.init()
# Initialise pyttsx3
engine = pyttsx3.init()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Window dimensions
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Color palette (RGB values)
BACKGROUND_COLOR = (255, 252, 240)  # Warm cream/honey
PRIMARY_COLOR = (255, 193, 7)  # Bright golden yellow
ACCENT_COLOR = (255, 167, 38)  # Warm amber/orange
TEXT_COLOR = (51, 51, 51)  # Charcoal black
CORRECT_COLOR = (139, 195, 74)  # Fresh lime green
ERROR_COLOR = (244, 81, 30)  # Warm orange-red
INPUT_BOX_COLOR = (255, 248, 220)  # Light cream
HIGHLIGHT_COLOR = (255, 213, 79)  # Soft golden yellow

# Fonts
TITLE_FONT_SIZE = 48
WORD_FONT_SIZE = 56
INPUT_FONT_SIZE = 42
MESSAGE_FONT_SIZE = 32
BUTTON_FONT_SIZE = 32

# Text to voice
SPEAKING_RATE = 125

# word list for practice
WORD_LIST = [
    "python",
    "programming",
    "algorithm",
    "function",
    "variable",
    "computer",
    "keyboard",
    "beautiful",
]

# ============================================================================
# SETUP
# ============================================================================

# Create the game window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("BeeWise - Spelling Practice")

# Create font objects
title_font = pygame.font.SysFont(None, TITLE_FONT_SIZE)
word_font = pygame.font.Font(None, WORD_FONT_SIZE)
button_font = pygame.font.SysFont(None, BUTTON_FONT_SIZE)

input_font = pygame.font.Font(None, INPUT_FONT_SIZE)
message_font = pygame.font.Font(None, MESSAGE_FONT_SIZE)

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Speak rate
engine.setProperty("rate", SPEAKING_RATE)

# ============================================================================
# GAME STATE VARIABLES
# ============================================================================

current_word_index = 0  # Which word we're on
current_word = WORD_LIST[0]  # The word to spell
user_input = ""  # What the user has typed
game_state = "INPUT"  # Can be "INPUT" or "FEEDBACK"
is_correct = False  # Was the answer correct?
highlighted_differences = []  # Stores which letters are wrong
cursor_visible = True  # Is cursor currently visible?
cursor_blink_time = 500  # Milliseconds between blinks
last_cursor_toggle = 0  # Last time cursor visibility toggled

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def draw_text_centered(text, font, color, y_position):
    """Draw text centered horizontally at a given y position"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, y_position))
    screen.blit(text_surface, text_rect)


def compare_words(correct, user_answer):
    """
    Compare the correct word with user's answer.
    Returns a list of booleans indicating which characters are correct.
    """
    differences = []
    max_length = max(len(correct), len(user_answer))

    for i in range(max_length):
        if i < len(correct) and i < len(user_answer):
            # Both words have a character at this position
            differences.append(correct[i] == user_answer[i])
        else:
            # One word is longer than the other
            differences.append(False)

    return differences


def draw_highlighted_word(correct_word, user_word, y_position):
    """
    Draw the correct word with user's mistakes highlighted.
    Green for correct letters, red for incorrect ones.
    """
    differences = compare_words(correct_word, user_word)

    # Calculate starting x position to center the word
    char_width = input_font.size("M")[0]  # Approximate character width
    total_width = char_width * len(correct_word)
    x_position = (WINDOW_WIDTH - total_width) // 2

    # Draw each character with appropriate color
    for i, char in enumerate(correct_word):
        if i < len(user_word):
            color = CORRECT_COLOR if differences[i] else ERROR_COLOR
        else:
            color = ERROR_COLOR  # Missing characters are errors

        char_surface = input_font.render(char, True, color)
        screen.blit(char_surface, (x_position + i * char_width, y_position))

    # Show if user typed extra characters
    if len(user_word) > len(correct_word):
        extra_text = message_font.render("(extra characters typed)", True, ERROR_COLOR)
        extra_rect = extra_text.get_rect(center=(WINDOW_WIDTH // 2, y_position + 60))
        screen.blit(extra_text, extra_rect)


def play_word(word):
    # Play word
    engine.say(word)
    engine.runAndWait()
    print(f"Playing word: {word}")


def move_to_next_word():
    """Load the next word in the list"""
    global current_word_index, current_word, user_input, game_state
    global cursor_visible, last_cursor_toggle

    current_word_index = (current_word_index + 1) % len(WORD_LIST)
    current_word = WORD_LIST[current_word_index]
    user_input = ""
    game_state = "INPUT"

    # Reset cursor to visible state
    cursor_visible = True
    last_cursor_toggle = pygame.time.get_ticks()

    # Play word
    play_word(current_word)


# ============================================================================
# MAIN GAME LOOP
# ============================================================================

running = True
while running:
    # Toggle cursor visibility every 500ms
    current_time = pygame.time.get_ticks()
    if current_time - last_cursor_toggle > cursor_blink_time:
        cursor_visible = not cursor_visible
        last_cursor_toggle = current_time

    # ========================================================================
    # EVENT HANDLING - Process user input
    # ========================================================================

    for event in pygame.event.get():
        # Window close button clicked
        if event.type == pygame.QUIT:
            running = False

        # Mouse button clicked
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "INPUT":
                # Check if play button was clicked
                mouse_pos = pygame.mouse.get_pos()
                play_button_rect = pygame.Rect(300, 200, 200, 60)
                if play_button_rect.collidepoint(mouse_pos):
                    play_word(current_word)

        # Key pressed
        elif event.type == pygame.KEYDOWN:
            if game_state == "INPUT":
                # User is typing their answer
                if event.key == pygame.K_RETURN:
                    # Enter key: Check the answer
                    if user_input:  # Only check if something was typed
                        is_correct = user_input.lower() == current_word.lower()
                        game_state = "FEEDBACK"

                elif event.key == pygame.K_BACKSPACE:
                    # Delete last character
                    user_input = user_input[:-1]
                    # Show cursor immediately after typing
                    cursor_visible = True
                    last_cursor_toggle = pygame.time.get_ticks()

                else:
                    # Add character to input (letters only)
                    if event.unicode.isalpha():
                        user_input += event.unicode
                        # Show cursor immediately after typing
                        cursor_visible = True
                        last_cursor_toggle = pygame.time.get_ticks()

            elif game_state == "FEEDBACK":
                # User is viewing feedback, press any key to continue
                move_to_next_word()

    # ========================================================================
    # DRAWING - Render everything on screen
    # ========================================================================

    # Clear screen with background color
    screen.fill(BACKGROUND_COLOR)

    # Draw title
    draw_text_centered("BeeWise", title_font, ACCENT_COLOR, 60)

    if game_state == "INPUT":
        # ====================================================================
        # INPUT STATE - User is typing
        # ====================================================================

        # Show the word to spell
        prompt_text = "Listen and spell the word:"
        draw_text_centered(prompt_text, message_font, TEXT_COLOR, 160)

        # Play word button
        play_button_rect = pygame.Rect(300, 200, 200, 60)
        pygame.draw.rect(screen, PRIMARY_COLOR, play_button_rect, border_radius=10)
        play_button_text = button_font.render("Play Word", True, TEXT_COLOR)
        play_button_text_rect = play_button_text.get_rect(
            center=play_button_rect.center
        )
        screen.blit(play_button_text, play_button_text_rect)

        # Draw input box
        input_box_rect = pygame.Rect(200, 300, 400, 60)
        pygame.draw.rect(screen, INPUT_BOX_COLOR, input_box_rect, border_radius=10)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, input_box_rect, 3, border_radius=10)

        # Draw user's input
        if user_input:
            input_surface = input_font.render(user_input, True, TEXT_COLOR)
            input_rect = input_surface.get_rect(center=(WINDOW_WIDTH // 2, 330))
            screen.blit(input_surface, input_rect)

            # Draw cursor after the text
            if cursor_visible:
                cursor_x = input_rect.right + 2
                cursor_y_top = input_rect.top
                cursor_y_bottom = input_rect.bottom
                pygame.draw.line(
                    screen,
                    TEXT_COLOR,
                    (cursor_x, cursor_y_top),
                    (cursor_x, cursor_y_bottom),
                    2,
                )
        else:
            # Draw cursor at center when no text
            if cursor_visible:
                cursor_x = WINDOW_WIDTH // 2
                cursor_y_top = 330 - input_font.get_height() // 2
                cursor_y_bottom = 330 + input_font.get_height() // 2
                pygame.draw.line(
                    screen,
                    TEXT_COLOR,
                    (cursor_x, cursor_y_top),
                    (cursor_x, cursor_y_bottom),
                    2,
                )

        # Instructions
        instruction_text = "Type your answer and press ENTER"
        draw_text_centered(instruction_text, message_font, TEXT_COLOR, 410)

    else:
        # ====================================================================
        # FEEDBACK STATE - Showing results
        # ====================================================================

        if is_correct:
            # Correct answer!
            draw_text_centered("Excellent!", word_font, CORRECT_COLOR, 180)
            draw_text_centered(
                f"'{current_word}' is correct!", message_font, TEXT_COLOR, 260
            )

        else:
            # Incorrect answer
            draw_text_centered("Not quite right", word_font, ERROR_COLOR, 160)

            # Show what user typed
            user_label = message_font.render("You typed:", True, TEXT_COLOR)
            user_label_rect = user_label.get_rect(center=(WINDOW_WIDTH // 2, 240))
            screen.blit(user_label, user_label_rect)

            user_surface = input_font.render(user_input, True, ERROR_COLOR)
            user_rect = user_surface.get_rect(center=(WINDOW_WIDTH // 2, 290))
            screen.blit(user_surface, user_rect)

            # Show correct spelling with highlighting
            correct_label = message_font.render("Correct spelling:", True, TEXT_COLOR)
            correct_label_rect = correct_label.get_rect(center=(WINDOW_WIDTH // 2, 360))
            screen.blit(correct_label, correct_label_rect)

            draw_highlighted_word(current_word, user_input, 410)

        # Continue instruction
        continue_text = "Press any for next word"
        draw_text_centered(continue_text, message_font, PRIMARY_COLOR, 520)

    # Progress indicator
    progress_text = f"Word {current_word_index + 1} of {len(WORD_LIST)}"
    progress_surface = message_font.render(progress_text, True, TEXT_COLOR)
    screen.blit(progress_surface, (20, WINDOW_HEIGHT - 40))

    # ========================================================================
    # UPDATE DISPLAY
    # ========================================================================

    pygame.display.flip()
    clock.tick(60)  # 60 frames per second

# ============================================================================
# CLEANUP
# ============================================================================

pygame.quit()
sys.exit()

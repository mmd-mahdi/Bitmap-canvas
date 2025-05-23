import asyncio
import platform
import pygame
import pyperclip
import re
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import os

# Initialize Pygame and Tkinter
def setup():
    global screen, grid, cell_size, width, height, reset_button, copy_button, copy32_button, paste_button, upload_button, compare_button
    global diff_matrix, show_diff, last_matrices
    pygame.init()
    width, height = 320, 490  # Increased height to accommodate new button
    cell_size = 10
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("32x32 LED Matrix Editor")
    grid = [[0 for _ in range(32)] for _ in range(32)]  # Initialize 32x32 grid with zeros
    diff_matrix = None  # Store difference matrix
    show_diff = False  # Toggle for displaying difference
    last_matrices = []  # Store last two pasted matrices
    # Define button rectangles
    reset_button = pygame.Rect(10, 330, 60, 30)   # Reset button
    copy_button = pygame.Rect(80, 330, 60, 30)    # Copy button (uint8_t)
    copy32_button = pygame.Rect(150, 330, 60, 30) # Copy32 button (uint32_t)
    paste_button = pygame.Rect(220, 330, 60, 30)  # Paste button
    upload_button = pygame.Rect(60, 370, 90, 30)  # Upload Image button
    compare_button = pygame.Rect(160, 370, 90, 30)  # Compare button
    draw_grid()

# Draw the grid and buttons
def draw_grid():
    screen.fill((255, 255, 255))  # White background
    # Draw 32x32 grid
    for y in range(32):
        for x in range(32):
            if show_diff and diff_matrix is not None:
                # Display difference matrix: red for differences, white for same
                color = (255, 0, 0) if diff_matrix[y][x] == 1 else (255, 255, 255)
            else:
                # Display editing grid: black for 1, white for 0
                color = (0, 0, 0) if grid[y][x] == 1 else (255, 255, 255)
            pygame.draw.rect(screen, color, (x * cell_size, y * cell_size, cell_size, cell_size))
            pygame.draw.rect(screen, (200, 200, 200), (x * cell_size, y * cell_size, cell_size, cell_size), 1)
    # Draw buttons
    pygame.draw.rect(screen, (100, 100, 255), reset_button)
    pygame.draw.rect(screen, (100, 255, 100), copy_button)
    pygame.draw.rect(screen, (50, 200, 50), copy32_button)
    pygame.draw.rect(screen, (255, 100, 100), paste_button)
    pygame.draw.rect(screen, (255, 165, 0), upload_button)
    pygame.draw.rect(screen, (100, 100, 100), compare_button)
    font = pygame.font.SysFont('arial', 18)
    reset_text = font.render('Reset', True, (255, 255, 255))
    copy_text = font.render('Copy', True, (255, 255, 255))
    copy32_text = font.render('Copy32', True, (255, 255, 255))
    paste_text = font.render('Paste', True, (255, 255, 255))
    upload_text = font.render('Upload', True, (255, 255, 255))
    compare_text = font.render('Compare', True, (255, 255, 255))
    screen.blit(reset_text, (reset_button.x + 10, reset_button.y + 5))
    screen.blit(copy_text, (copy_button.x + 10, copy_button.y + 5))
    screen.blit(copy32_text, (copy32_button.x + 5, copy32_button.y + 5))
    screen.blit(paste_text, (paste_button.x + 10, paste_button.y + 5))
    screen.blit(upload_text, (upload_button.x + 15, upload_button.y + 5))
    screen.blit(compare_text, (compare_button.x + 10, compare_button.y + 5))
    pygame.display.flip()

# Generate C-style uint8_t array output
def generate_uint8_array(matrix):
    output = "const uint8_t customBitmap[32][32] = {\n"
    for row in matrix:
        output += "  {" + ", ".join(str(cell) for cell in row) + "},\n"
    output += "};\n"
    return output

# Generate C-style uint32_t array output
def generate_uint32_array(matrix):
    output = "const uint32_t customBitmap[32] = {\n"
    for row in matrix:
        # Convert row to uint32_t by treating it as a 32-bit binary number
        value = 0
        for bit in row:
            value = (value << 1) | bit  # Shift left and add bit
        output += f"  0x{value:08X},\n"  # Format as hexadecimal
    output += "};\n"
    return output

# Copy array to clipboard
def copy_to_clipboard(uint8=True):
    if show_diff and diff_matrix is not None:
        matrix = diff_matrix
    else:
        matrix = grid
    if uint8:
        output = generate_uint8_array(matrix)
    else:
        output = generate_uint32_array(matrix)
    pyperclip.copy(output)

# Paste array from clipboard
def paste_from_clipboard():
    global grid, last_matrices
    try:
        clipboard = pyperclip.paste()
        # Extract numbers from the C-style array using regex
        numbers = re.findall(r'\b[0-1]\b', clipboard)
        if len(numbers) != 32 * 32:  # Expect exactly 1024 values (32x32)
            return  # Invalid format, do nothing
        new_grid = [[0 for _ in range(32)] for _ in range(32)]
        index = 0
        for i in range(32):
            for j in range(32):
                new_grid[i][j] = int(numbers[index])
                index += 1
        grid = new_grid  # Update grid if parsing succeeds
        # Store the pasted matrix (deep copy)
        last_matrices.append([row[:] for row in new_grid])
        if len(last_matrices) > 2:
            last_matrices.pop(0)  # Keep only the last two
        draw_grid()
    except:
        pass  # Silently ignore invalid clipboard content

# Upload and process image
def upload_image():
    global grid
    try:
        # Initialize Tkinter for file dialog
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        root.destroy()
        if not file_path or not os.path.exists(file_path):
            return  # No file selected or invalid path
        # Load and process image
        image = Image.open(file_path)
        # Resize to 32x32
        image = image.resize((32, 32), Image.Resampling.LANCZOS)
        # Convert to grayscale
        image = image.convert('L')
        # Convert to binary (black and white) using a threshold
        threshold = 128  # Midpoint for 8-bit grayscale
        image = image.point(lambda p: 1 if p < threshold else 0, '1')  # 1 for black, 0 for white
        # Update grid
        new_grid = [[0 for _ in range(32)] for _ in range(32)]
        pixels = image.load()
        for i in range(32):
            for j in range(32):
                new_grid[i][j] = pixels[j, i]  # Note: PIL uses (x, y), grid uses [y][x]
        grid = new_grid
        draw_grid()
    except:
        pass  # Silently ignore errors (e.g., invalid image file)

# Reset the grid
def reset_grid():
    global grid, diff_matrix, show_diff
    grid = [[0 for _ in range(32)] for _ in range(32)]
    diff_matrix = None
    show_diff = False
    draw_grid()

# Compare the last two pasted matrices
def compare_matrices():
    global diff_matrix, show_diff
    if len(last_matrices) < 2:
        # Not enough matrices pasted
        return
    matrix1, matrix2 = last_matrices[-2], last_matrices[-1]
    # Compute difference: 1 where matrices differ, 0 where they are the same
    diff_matrix = [[0 for _ in range(32)] for _ in range(32)]
    for i in range(32):
        for j in range(32):
            diff_matrix[i][j] = 1 if matrix1[i][j] != matrix2[i][j] else 0
    show_diff = True
    draw_grid()

# Main update loop
def update_loop():
    global show_diff
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                grid_x = x // cell_size
                grid_y = y // cell_size
                if reset_button.collidepoint(x, y):
                    reset_grid()
                elif copy_button.collidepoint(x, y):
                    copy_to_clipboard(uint8=True)
                elif copy32_button.collidepoint(x, y):
                    copy_to_clipboard(uint8=False)
                elif paste_button.collidepoint(x, y):
                    paste_from_clipboard()
                elif upload_button.collidepoint(x, y):
                    upload_image()
                elif compare_button.collidepoint(x, y):
                    compare_matrices()
                elif 0 <= grid_x < 32 and 0 <= grid_y < 32 and not show_diff:
                    if event.button == 1:  # Left click to set pixel
                        grid[grid_y][grid_x] = 1
                        draw_grid()
                    elif event.button == 3:  # Right click to clear pixel
                        grid[grid_y][grid_x] = 0
                        draw_grid()
            elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0] and not show_diff:
                x, y = pygame.mouse.get_pos()
                grid_x = x // cell_size
                grid_y = y // cell_size
                if 0 <= grid_x < 32 and 0 <= grid_y < 32:
                    grid[grid_y][grid_x] = 1  # Set pixel to 1 (on) for left drag
                    draw_grid()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:  # Press 'C' to clear grid
                    reset_grid()
                elif event.key == pygame.K_s:  # Press 'S' to copy uint8_t
                    copy_to_clipboard(uint8=True)
                elif event.key == pygame.K_v:  # Press 'V' to paste
                    paste_from_clipboard()
                elif event.key == pygame.K_u:  # Press 'U' to upload image
                    upload_image()
                elif event.key == pygame.K_d:  # Press 'D' to toggle difference view
                    show_diff = False
                    draw_grid()
    pygame.quit()

# Run the game
async def main():
    setup()
    update_loop()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
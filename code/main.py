import pygame
import pyperclip
import re
from PIL import Image
import tkinter as tk
from tkinter import filedialog, Toplevel, Text, Button, messagebox
import os

# Global Tkinter root for reuse
tk_root = None

# Initialize Pygame and Tkinter
def setup():
    global screen, grid, cell_size, width, height, reset_button, copy_button, paste_button, upload_button, compare_button
    global diff_matrix, show_diff, tk_root
    pygame.init()
    tk_root = tk.Tk()
    tk_root.withdraw()  # Hide root window
    width, height = 320, 490  # Increased height for compare button
    cell_size = 10
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("32x32 LED Matrix Editor")
    grid = [[0 for _ in range(32)] for _ in range(32)]  # Initialize 32x32 grid with zeros
    diff_matrix = None  # Store difference matrix
    show_diff = False  # Toggle for displaying difference
    # Define button rectangles
    reset_button = pygame.Rect(10, 330, 90, 30)   # Reset button
    copy_button = pygame.Rect(110, 330, 90, 30)   # Copy button
    paste_button = pygame.Rect(210, 330, 90, 30)  # Paste button
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
    pygame.draw.rect(screen, (255, 100, 100), paste_button)
    pygame.draw.rect(screen, (255, 165, 0), upload_button)
    pygame.draw.rect(screen, (100, 100, 100), compare_button)
    font = pygame.font.SysFont('arial', 20)
    reset_text = font.render('Reset', True, (255, 255, 255))
    copy_text = font.render('Copy', True, (255, 255, 255))
    paste_text = font.render('Paste', True, (255, 255, 255))
    upload_text = font.render('Upload', True, (255, 255, 255))
    compare_text = font.render('Compare', True, (255, 255, 255))
    screen.blit(reset_text, (reset_button.x + 20, reset_button.y + 5))
    screen.blit(copy_text, (copy_button.x + 20, copy_button.y + 5))
    screen.blit(paste_text, (paste_button.x + 20, paste_button.y + 5))
    screen.blit(upload_text, (upload_button.x + 15, upload_button.y + 5))
    screen.blit(compare_text, (compare_button.x + 10, compare_button.y + 5))
    pygame.display.flip()

# Generate C-style array output
def generate_array(matrix):
    output = "const uint8_t customBitmap[32][32] = {\n"
    for row in matrix:
        output += "  {" + ", ".join(str(cell) for cell in row) + "},\n"
    output += "};\n"
    return output

# Copy array to clipboard
def copy_to_clipboard():
    if show_diff and diff_matrix is not None:
        output = generate_array(diff_matrix)
    else:
        output = generate_array(grid)
    pyperclip.copy(output)

# Parse matrix from text
def parse_matrix(text):
    try:
        numbers = re.findall(r'\b[0-1]\b', text)
        if len(numbers) != 32 * 32:  # Expect 1024 values
            return None
        matrix = [[0 for _ in range(32)] for _ in range(32)]
        index = 0
        for i in range(32):
            for j in range(32):
                matrix[i][j] = int(numbers[index])
                index += 1
        return matrix
    except:
        return None

# Paste array from clipboard
def paste_from_clipboard():
    global grid
    try:
        clipboard = pyperclip.paste()
        matrix = parse_matrix(clipboard)
        if matrix is not None:
            grid = matrix
            draw_grid()
    except:
        pass  # Silently ignore invalid clipboard content

# Upload and process image
def upload_image():
    global grid, tk_root
    try:
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")],
            parent=tk_root
        )
        if not file_path or not os.path.exists(file_path):
            return
        image = Image.open(file_path)
        image = image.resize((32, 32), Image.Resampling.LANCZOS)
        image = image.convert('L')
        threshold = 128
        image = image.point(lambda p: 1 if p < threshold else 0, '1')
        new_grid = [[0 for _ in range(32)] for _ in range(32)]
        pixels = image.load()
        for i in range(32):
            for j in range(32):
                new_grid[i][j] = pixels[j, i]
        grid = new_grid
        draw_grid()
    except:
        pass

# Reset the grid
def reset_grid():
    global grid, diff_matrix, show_diff
    grid = [[0 for _ in range(32)] for _ in range(32)]
    diff_matrix = None
    show_diff = False
    draw_grid()

# Open simplified comparison window
def open_compare_window():
    global diff_matrix, show_diff, tk_root
    compare_window = Toplevel(tk_root)
    compare_window.title("Compare Matrices")
    compare_window.geometry("600x400")

    # Matrix 1 placeholder
    tk.Label(compare_window, text="Paste Matrix 1 (C-style array):").pack(pady=5)
    text_matrix1 = Text(compare_window, height=10, width=50)
    text_matrix1.pack(pady=5)

    # Matrix 2 placeholder
    tk.Label(compare_window, text="Paste Matrix 2 (C-style array):").pack(pady=5)
    text_matrix2 = Text(compare_window, height=10, width=50)
    text_matrix2.pack(pady=5)

    # Submit button
    def submit_comparison():
        global diff_matrix, show_diff
        matrix1 = parse_matrix(text_matrix1.get("1.0", tk.END))
        matrix2 = parse_matrix(text_matrix2.get("1.0", tk.END))
        if matrix1 is None or matrix2 is None:
            messagebox.showerror("Error", "Invalid matrix format. Ensure both are 32x32 arrays of 0s and 1s.")
            return
        # Compute difference: 1 where matrices differ, 0 where they are the same
        diff_matrix = [[0 for _ in range(32)] for _ in range(32)]
        for i in range(32):
            for j in range(32):
                diff_matrix[i][j] = 1 if matrix1[i][j] != matrix2[i][j] else 0
        show_diff = True
        draw_grid()
        compare_window.destroy()

    tk.Button(compare_window, text="Submit", command=submit_comparison).pack(pady=10)

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
                    copy_to_clipboard()
                elif paste_button.collidepoint(x, y):
                    paste_from_clipboard()
                elif upload_button.collidepoint(x, y):
                    upload_image()
                elif compare_button.collidepoint(x, y):
                    open_compare_window()
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
                    grid[grid_y][grid_x] = 1
                    draw_grid()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    reset_grid()
                elif event.key == pygame.K_s:
                    copy_to_clipboard()
                elif event.key == pygame.K_v:
                    paste_from_clipboard()
                elif event.key == pygame.K_u:
                    upload_image()
                elif event.key == pygame.K_d:  # Press 'D' to toggle difference view
                    show_diff = False
                    draw_grid()
    tk_root.destroy()
    pygame.quit()

# Run the game
async def main():
    setup()
    update_loop()

if __name__ == "__main__":
    import asyncio
    import platform
    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())
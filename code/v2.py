import asyncio
import platform
import pygame
import pyperclip
import re
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import os


def setup():
    global screen, grid, cell_size, width, height, reset_button, copy_button, copy32_button, paste_button, upload_button, compare_button
    global diff_matrix, show_diff, last_matrices
    pygame.init()
    width, height = 320, 490
    cell_size = 10
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("32x32 LED Matrix Editor")
    grid = [[0 for _ in range(32)] for _ in range(32)]
    diff_matrix = None
    show_diff = False
    last_matrices = []

    reset_button = pygame.Rect(10, 330, 60, 30)
    copy_button = pygame.Rect(80, 330, 60, 30)
    copy32_button = pygame.Rect(150, 330, 60, 30)
    paste_button = pygame.Rect(220, 330, 60, 30)
    upload_button = pygame.Rect(60, 370, 90, 30)
    compare_button = pygame.Rect(160, 370, 90, 30)
    draw_grid()


def draw_grid():
    screen.fill((255, 255, 255))

    for y in range(32):
        for x in range(32):
            if show_diff and diff_matrix is not None:

                color = (255, 0, 0) if diff_matrix[y][x] == 1 else (255, 255, 255)
            else:

                color = (0, 0, 0) if grid[y][x] == 1 else (255, 255, 255)
            pygame.draw.rect(screen, color, (x * cell_size, y * cell_size, cell_size, cell_size))
            pygame.draw.rect(screen, (200, 200, 200), (x * cell_size, y * cell_size, cell_size, cell_size), 1)

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


def generate_uint8_array(matrix):
    output = "const uint8_t customBitmap[32][32] = {\n"
    for row in matrix:
        output += "  {" + ", ".join(str(cell) for cell in row) + "},\n"
    output += "};\n"
    return output


def generate_uint32_array(matrix):
    output = "const uint32_t customBitmap[32] = {\n"
    for row in matrix:

        value = 0
        for bit in row:
            value = (value << 1) | bit
        output += f"  0x{value:08X},\n"
    output += "};\n"
    return output


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


def paste_from_clipboard():
    global grid, last_matrices
    try:
        clipboard = pyperclip.paste()

        numbers = re.findall(r'\b[0-1]\b', clipboard)
        if len(numbers) != 32 * 32:
            return
        new_grid = [[0 for _ in range(32)] for _ in range(32)]
        index = 0
        for i in range(32):
            for j in range(32):
                new_grid[i][j] = int(numbers[index])
                index += 1
        grid = new_grid

        last_matrices.append([row[:] for row in new_grid])
        if len(last_matrices) > 2:
            last_matrices.pop(0)
        draw_grid()
    except:
        pass


def upload_image():
    global grid
    try:

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        root.destroy()
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


def reset_grid():
    global grid, diff_matrix, show_diff
    grid = [[0 for _ in range(32)] for _ in range(32)]
    diff_matrix = None
    show_diff = False
    draw_grid()


def compare_matrices():
    global diff_matrix, show_diff
    if len(last_matrices) < 2:

        return
    matrix1, matrix2 = last_matrices[-2], last_matrices[-1]

    diff_matrix = [[0 for _ in range(32)] for _ in range(32)]
    for i in range(32):
        for j in range(32):
            diff_matrix[i][j] = 1 if matrix1[i][j] != matrix2[i][j] else 0
    show_diff = True
    draw_grid()


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
                    if event.button == 1:
                        grid[grid_y][grid_x] = 1
                        draw_grid()
                    elif event.button == 3:
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
                    copy_to_clipboard(uint8=True)
                elif event.key == pygame.K_v:
                    paste_from_clipboard()
                elif event.key == pygame.K_u:
                    upload_image()
                elif event.key == pygame.K_d:
                    show_diff = False
                    draw_grid()
    pygame.quit()


async def main():
    setup()
    update_loop()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
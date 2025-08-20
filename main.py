import os
import subprocess
import textwrap
from math import ceil
from math import floor

from PIL import Image, ImageDraw, ImageFont

IMAGE_PADDING = 10
LINE_CHAR_LIMIT = 150
# The desired ratio of width to height (the number of "widths" for each "height").
TARGET_ASPECT_RATIO = 1
# 6 is a good default because it's small, but still readable (barely). If the program is taking a long time
# (~20+ seconds) to run, you probably need to reduce this - the image will be too big to reasonably load anyway.
FONT_SIZE = 6
MONOSPACE_FONT_PATH = "/usr/share/fonts/truetype/ubuntu/UbuntuMono[wght].ttf"


def main():
    if LINE_CHAR_LIMIT < 40:
        print("Error: Line character limit must be at least 40.")
        exit(1)

    print("Enter a path to the root of a repository to visualize:")
    path = input()

    repo_contents = assemble_repository_into_string(path)

    text_to_image(
        text=repo_contents,
        output_image_path="text_visualization.png",
        font_path=MONOSPACE_FONT_PATH
    )


def assemble_repository_into_string(repo_path: str) -> str:
    assembled_string = ""

    if not os.path.isdir(repo_path):
        print("Error: Path must be a directory.")
        exit(1)

    branch_name = run_command("git branch --show-current", repo_path)
    repo_filenames = run_command(f"git ls-tree -r {branch_name} --name-only", repo_path).split("\n")

    for repo_filename in repo_filenames:
        print(f'Reading {repo_filename}')

        if len(repo_filename) > LINE_CHAR_LIMIT:
            formatted_filename = repo_filename[:22] + '...' + repo_filename[-(LINE_CHAR_LIMIT - 25):]
        else:
            empty_space_length = floor((LINE_CHAR_LIMIT - len(repo_filename)) / 2)
            formatted_filename = '*' * empty_space_length + repo_filename + '*' * empty_space_length

        assembled_string += f"""

{formatted_filename}

"""

        try:
            with open(f'{repo_path}/{repo_filename}', 'r', encoding='utf-8') as repo_file:
                assembled_string += repo_file.read()
        except UnicodeDecodeError:
            assembled_string += '(Binary file)'
        except IsADirectoryError:
            assembled_string += '(Is a directory - possibly a submodule)'

    print('All files read.')

    return assembled_string


def run_command(command: str, cwd: str = None) -> str:
    process = subprocess.Popen(command.split(' '), cwd=cwd, stdout=subprocess.PIPE, text=True)
    return process.stdout.read().strip()


def text_to_image(text: str, output_image_path: str, font_path: str = None):
    # Load the font
    try:
        font = ImageFont.truetype(font_path or "error", FONT_SIZE)
    except IOError:
        print(
            "Font not found. Using default PIL font, but this is not a monospace font - things will not line up perfectly.")
        font = ImageFont.load_default()

    # Define the starting position and line height
    x_pos, y_pos = IMAGE_PADDING, IMAGE_PADDING
    # A reliable way to get line height + a little spacing
    line_height = font.getbbox("Tg")[3] + 2
    # Get the max line width - it should be the same regardless of the content if the font is monospaced
    line_width = font.getbbox("a" * LINE_CHAR_LIMIT)[2]

    original_lines = text.split('\n')

    # Count total lines after wrapping (including paragraph spacing as in drawing)
    wrapped_lines = []
    for line in original_lines:
        wrapped_line = [""] if line == "" else textwrap.wrap(line, width=LINE_CHAR_LIMIT)
        wrapped_lines += wrapped_line
    lines_count = len(wrapped_lines)

    columns = calculate_optimal_columns(line_width, line_height, lines_count)
    lines_per_column = ceil(lines_count / columns)

    # Create image and draw context now that we know the needed height and columns
    image_width = int(line_width * columns + IMAGE_PADDING * (columns + 1))
    image_height = int(lines_per_column * line_height + IMAGE_PADDING * 2)
    img = Image.new('RGB', (image_width, image_height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw the text using the same wrapping configuration
    current_line_num = 1
    for line in wrapped_lines:
        draw.text((x_pos, y_pos), line, fill='black', font=font)
        y_pos += line_height

        current_line_num += 1
        if current_line_num > lines_per_column:
            current_line_num = 1
            x_pos += line_width + IMAGE_PADDING
            y_pos = IMAGE_PADDING

    # Save the final image
    img.save(output_image_path)
    print(f"Image saved successfully to {output_image_path}")


def calculate_optimal_columns(line_width, line_height, lines_count):
    """
    Calculates the optimal number of columns to achieve a target aspect ratio.
    """

    if line_height <= 0 or line_width <= 0:
        print("Error: Line height and width must be positive values.")
        exit(1)

    # Initialize variables to track the best result
    best_columns = 0
    best_difference_from_target = float('inf')
    current_tested_columns = 0

    while True:
        current_tested_columns += 1

        total_width = current_tested_columns * line_width

        # The total number of lines must be an integer. Round up because lines use the full height even if they don't
        # use the full width.
        lines_per_column = ceil(lines_count / current_tested_columns)

        # Calculate the actual height based on the integer number of lines.
        total_height = lines_per_column * line_height

        # Calculate the actual aspect ratio for this number of columns.
        current_aspect_ratio = total_width / total_height

        # Calculate the absolute difference between the current ratio and the target.
        difference = abs(current_aspect_ratio - TARGET_ASPECT_RATIO)

        # If this difference is the smallest so far, we have a new best result.
        if difference < best_difference_from_target:
            best_difference_from_target = difference
            best_columns = current_tested_columns
        else:
            # We started at the minimum, so once it stops improving, we know we've found the best possible result.
            return best_columns


if __name__ == "__main__":
    main()

from PIL import Image, ImageDraw, ImageFont
import textwrap

IMAGE_PADDING = 10
LINE_CHAR_LIMIT = 150


def text_to_image(text_file_path, output_image_path, font_path=None):
    # Load the font
    try:
        font = ImageFont.truetype(font_path or "error", 12)
    except IOError:
        print(
            "Font not found. Using default PIL font, but this is not a monospace font - things will not line up perfectly.")
        font = ImageFont.load_default()

    # Read the text file
    with open(text_file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()

    # Define the starting position and line height
    x_pos, y_pos = IMAGE_PADDING, IMAGE_PADDING
    # A reliable way to get line height + a little spacing
    line_height = font.getbbox("Tg")[3] + 2
    # Get the max line width - it should be the same regardless of the content if the font is monospaced
    line_width = font.getbbox("a" * LINE_CHAR_LIMIT)[2]

    original_lines = text_content.split('\n')

    # Count total lines after wrapping (including paragraph spacing as in drawing)
    wrapped_lines = []
    for line in original_lines:
        wrapped_line = textwrap.wrap(line, width=LINE_CHAR_LIMIT)
        wrapped_lines += wrapped_line

    # Create image and draw context now that we know the needed height
    image_width = int(line_width + IMAGE_PADDING * 2)
    image_height = int(len(wrapped_lines) * line_height + IMAGE_PADDING * 2)
    img = Image.new('RGB', (image_width, image_height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw the text using the same wrapping configuration
    for line in wrapped_lines:
        draw.text((x_pos, y_pos), line, fill='black', font=font)
        y_pos += line_height

    # Save the final image
    img.save(output_image_path)
    print(f"Image saved successfully to {output_image_path}")


if __name__ == "__main__":
    # Create a dummy text file for testing
    with open("sample_text.txt", "w") as f:
        f.write("a" * 500 + "\n")
        f.write("This is a test paragraph with some text. This is a test paragraph with some text. " * 20 + "\n")
        f.write(
            "This is a second paragraph. " * 20 + "\n")
        f.write("And here is a third paragraph. The patterns of these paragraphs should be visible in the image. " * 20)

    # Run the function
    text_to_image(
        text_file_path="sample_text.txt",
        output_image_path="text_visualization.png",
        font_path="/usr/share/fonts/truetype/ubuntu/UbuntuMono[wght].ttf"
    )

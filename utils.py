import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCISSORS_PATH = "resources/scissors.png"
ARROW_PATH = "resources/arrow.png"
SCISSORS_ARROW_PATH = "resources/scissors_and_arrow.png"


def adjust_image_for_printing(image: np.ndarray):
    image = crop_image_to_square(image)
    image = sharpen_image(image)
    image = add_white_border(image, border_width=30)
    image = add_cutting_line(image, line_width=3)
    image, empty_area_yx = normalize_to_paper_size(image, desired_ratio=1.48)
    image = add_patch_into_empty_area(
        image, empty_area_yx, SCISSORS_ARROW_PATH, relative_yx=(0.2, 0.5), mirror=True
    )
    image = add_patch_into_empty_area(
        image, empty_area_yx, SCISSORS_ARROW_PATH, relative_yx=(0.8, 0.5), mirror=True
    )
    return image


def normalize_to_paper_size(image, desired_ratio: float):
    # Adjust aspect ratio to match desired one
    h, w, ch = image.shape
    desired_w = h * desired_ratio
    add_sides = int((desired_w - w) / 2)
    image = cv2.copyMakeBorder(
        image, None, None, add_sides, add_sides, cv2.BORDER_CONSTANT, None, (255, 255, 255)
    )
    added_area_size = (h, add_sides)
    return image, added_area_size


def add_cutting_line(image, line_width: int):
    # Add thin gray line for cutting
    image = cv2.copyMakeBorder(
        image,
        None,
        None,
        line_width,
        line_width,
        cv2.BORDER_CONSTANT,
        None,
        (100, 100, 100),
    )

    # Make the line dashed
    dash_line_size = 5
    indexes = np.arange(0, image.shape[0], dash_line_size * 2)
    for y in list(indexes)[1::2]:
        image[y : y + dash_line_size, 0:line_width, :] = 255
        image[y : y + dash_line_size, -line_width:, :] = 255

    return image


def add_patch_into_empty_area(
    image,
    empty_area_yx: tuple,
    patch: str | np.ndarray,
    relative_yx: tuple,
    mirror=False,
    side="Left",
):
    patch_image = cv2.imread(patch) if isinstance(patch, str) else patch
    h, w, _ = patch_image.shape
    start_y = int(empty_area_yx[0] * relative_yx[0] - h / 2)
    end_y = start_y + patch_image.shape[0]
    start_x = int(empty_area_yx[1] * relative_yx[1] - w / 2)
    end_x = start_x + patch_image.shape[1]

    if image.shape[2] == 4:
        patch_like = np.ones((h, w, 4), np.uint8) * 255
        patch_like[:, :, 0:3] = patch_image[:, :, ::-1]
        patch_image = patch_like

    x_range = (start_x, end_x)
    start_x = x_range[0] if side == "Left" else -x_range[1]
    end_x = x_range[1] if side == "Left" else -x_range[0]
    image[start_y:end_y, start_x:end_x] = patch_image
    if mirror:
        flipped_patch = cv2.flip(patch_image, 1)
        image[start_y:end_y, -end_x:-start_x] = flipped_patch
    return image


def add_white_border(image, border_width):
    image_with_border = cv2.copyMakeBorder(
        image,
        border_width + 35,
        border_width + 35,
        border_width,
        border_width,
        cv2.BORDER_CONSTANT,
        None,
        (255, 255, 255),
    )
    return image_with_border


def crop_image_to_square(image):
    h, w, ch = image.shape
    pixels_to_crop = w - h
    start_x = pixels_to_crop // 2
    end_x = w - (pixels_to_crop // 2)
    cropped_image = image[:, start_x:end_x, :]
    return cropped_image


def add_text_to_image(
    image_np,
    text,
    font_size,
    text_color=(255, 255, 255, 255),
    shadow_color=(0, 0, 0, 255),
    text_y: int = None,
):
    # Convert numpy array to PIL Image
    image = Image.fromarray(image_np)
    draw = ImageDraw.Draw(image)
    width, height = image.size
    font_path = "resources/Montserrat-Bold.ttf"
    font = ImageFont.truetype(font_path, font_size)

    # Calculate text size and position
    _, _, text_width, text_height = font.getbbox(text)
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2 if not text_y else text_y

    # Draw text shadow
    shadow_offset = 3
    shadow_position = (text_x + shadow_offset, text_y + shadow_offset)
    draw.text(shadow_position, text, font=font, fill=shadow_color)

    draw.text((text_x, text_y), text, font=font, fill=text_color)

    # Convert back to numpy array
    image_np_with_text = np.array(image)

    return image_np_with_text


def sharpen_image(image):
    # Define the sharpening kernel
    sharpening_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    # Apply the sharpening kernel to the input image
    sharpened_image = cv2.filter2D(image, -1, sharpening_kernel)
    mix = cv2.addWeighted(image, 0.9, sharpened_image, 0.2, 1)
    return mix


if __name__ == "__main__":
    filename = r"C:\Users\melni\Desktop\rpi_cam_tests2\20240504-231248.jpeg"
    filename = "captured_images/20240505-152058.jpeg"

    image = cv2.imread(filename)
    adjusted_image = adjust_image_for_printing(image)
    # cv2.imshow("original", image)
    cv2.imwrite("temp2.jpeg", adjusted_image)
    cv2.imshow("adjusted", adjusted_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

#!/usr/bin/python3
"""
Script is intended to run automatically after startup.



"""

import datetime
import re
import subprocess
import time
from sys import stdin
from termios import TCIOFLUSH, tcflush

import cv2
import numpy as np
from libcamera import controls, Transform
from picamera2 import Picamera2, Preview

import keyboard_conditions
import utils

SCREEN_SIZE = (1920, 1080)
PRINTER_NAME = "Canon_SELPHY_CP1500"
RESOURCES_VARIANT = "variant2"
CAPTURE_GUIDE = f"resources/{RESOURCES_VARIANT}/capture.png"
PRINT_OR_BACK_GUIDE = f"resources/{RESOURCES_VARIANT}/print_or_back.png"
FULL_GUIDE = f"resources/{RESOURCES_VARIANT}/guide.png"


def get_default_overlay(camera, reset=True):
    """Set default overlay for the preview screen.

    Default overlay blackens the sides of the screen to show only square crop out
    """
    # TODO consider setting manual overlay instead
    canvas = np.zeros((SCREEN_SIZE[1], SCREEN_SIZE[0], 4), np.uint8)
    canvas[:, :, 3] = 255
    canvas[:, 420:-420, 3] = 0
    if reset:
        camera.set_overlay(canvas)
    return canvas


def set_special_overlay(camera, image_base: np.ndarray, overlay: str):
    image_base = utils.add_patch_into_empty_area(
        image_base,
        (1080, 420),
        overlay,
        (0.5, 0.5),
    )
    image_base = utils.add_patch_into_empty_area(
        image_base, (1080, 420), FULL_GUIDE, (0.5, 0.5), side="RIGHT"
    )

    camera.set_overlay(image_base)


def preview_and_save_image(camera, image: np.ndarray):
    image2 = cv2.resize(image, (1920, 1080)) if image.shape[0] else np.copy(image)
    image2 = blacken_borders(image2)
    set_special_overlay(camera, image2, PRINT_OR_BACK_GUIDE)

    if image.shape[2] == 4:
        b, g, r, a = cv2.split(image)
        image_save = cv2.merge((r, g, b))
    else:
        image_save = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    filename = f"captured_images/{datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.jpeg"
    cv2.imwrite(filename, image_save)


def blacken_borders(image: np.ndarray):
    image[:, :+420, 0:3] = 0
    image[:, -420:, 0:3] = 0
    return image


def print_image(camera, image: np.ndarray, filename: str):
    # Set overlay
    image2 = utils.add_text_to_image(
        image,
        "PRINTING!",
        font_size=100,
    )
    image2 = blacken_borders(image2)
    camera.set_overlay(image2)

    # TODO implement error handling for printer jobs handling (empty tray, no colors.. etc).. by parsing stdout
    args = ["lp", filename]
    print_process = subprocess.run(args, capture_output=True, text=True)
    print(print_process)
    time.sleep(1)
    stdout = print_process.stdout
    job_id = re.findall(r"request id.+-(\d+)\b", stdout)[-1]
    print(f"Job ID is: {job_id}")
    jobs = check_print_job(camera, image2, job_id)
    print(jobs)


def check_print_job(camera, image, job_id: str):
    """Parse output of lpstat -l -o to check stat us of the print jobs"""
    # TODO make nice.. maybe use pycups?
    started = time.time()

    while True:
        print_stats_process = subprocess.run(["lpstat", "-l", "-o"], capture_output=True, text=True)
        stdout = print_stats_process.stdout
        jobs = re.split(rf"{PRINTER_NAME}-(?=\d+)", stdout.strip())[1:]
        jobs = {re.findall(r"^(\d+)", job)[0]: job for job in jobs}
        job_std_out = jobs.get(job_id)

        if not job_std_out:
            break
        message = job_std_out.splitlines()[-1].strip()
        alerts = re.findall("Alerts: (.+)", job_std_out)
        alerts = alerts[0] if alerts else "unknown"
        queued = re.findall("(queued .+)", job_std_out)

        status = re.findall("Status: (.+)", job_std_out)
        status = status[0] if status else "unknown"

        if alerts in ["job-printing", "none"]:
            alert_color = (20, 255, 20, 255)
        else:
            alert_color = (255, 20, 20, 255)

        image2 = np.copy(image)
        image2 = utils.add_text_to_image(image2, f"Status:{status}", font_size=25, text_y=600)
        image2 = utils.add_text_to_image(image2, f"Message:{message}", font_size=25, text_y=640)
        image2 = utils.add_text_to_image(
            image2, f"Alerts:{alerts}", font_size=25, text_y=680, text_color=alert_color
        )

        if alerts == "none" and not queued:
            break

        # TODO - check if releasing the job is needed
        # subprocess.run(["lp", "-H", job_id])
        elapsed = time.time() - started
        if not int(elapsed) % 10:
            enable_printer()

        if elapsed > 20 and alerts not in ["job-printing", "none"]:
            msg = "️Kontaktujte svědka (777 452 999)"
            image2 = utils.add_text_to_image(
                image2, msg, font_size=40, text_y=800, text_color=(230, 230, 0, 255)
            )
            # cancel_all_print_jobs()

        camera.set_overlay(image2)
        time.sleep(0.5)

    return None


def save_image_for_printing(image: np.ndarray):
    filename = f"printed_images/{datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.jpeg"
    if image.shape[2] == 4:
        b, g, r, a = cv2.split(image)
        image_save = cv2.merge((r, g, b))
    else:
        image_save = image
    image_save = utils.adjust_image_for_printing(image_save)
    cv2.imwrite(filename, image_save)
    print("Saved ", filename)
    return filename


def perform_countdown(camera):
    canvas = get_default_overlay(camera)
    font_size = 400
    text_color = (255, 255, 255, 100)
    white_canvas = np.copy(canvas)
    white_canvas[:, :, 0:3] = 200

    for text in ["3", "2", "1"]:
        start = time.time()
        image = utils.add_text_to_image(
            canvas,
            text,
            font_size,
            text_color,
            shadow_color=(0, 0, 0, 50),
        )
        camera.set_overlay(image)
        end = time.time()
        time.sleep(1 - (end - start))

    # TODO maybe add cheese instead?
    camera.set_overlay(white_canvas)
    time.sleep(0.2)


def wait_for_print_to_finish(camera, image):
    """
    Just hardcoded wait duration along with progress info (print time is stable)

    Timestamps
    - 10s busy
    - 10s yellow
    - 10s magenta
    - 10s cyan
    - 10s protective foil
    """

    ts_messages = {
        0: ((255, 255, 0, 255), "Yellow!"),
        10: ((255, 0, 255, 255), "Magenta!"),
        20: ((0, 255, 255, 255), "Cyan!"),
        30: ((255, 255, 255, 255), "Final touches :)"),
    }
    expected_duration = 40
    main_message = "PRINTING!"
    count_down_preview(camera, expected_duration, image, main_message, ts_messages)
    image2 = utils.add_text_to_image(
        np.copy(blacken_borders(image)),
        "PRINT DONE!",
        font_size=100,
    )
    camera.set_overlay(image2)
    time.sleep(1)
    set_special_overlay(camera, image, PRINT_OR_BACK_GUIDE)


def count_down_preview(camera, expected_duration, image, main_message, ts_messages):
    canvas = blacken_borders(image)
    started_ts = time.time()
    elapsed = 0
    while elapsed < expected_duration:
        color_selection = [
            message_color for message_color in ts_messages if elapsed >= message_color
        ][-1]
        color, action = ts_messages[color_selection]
        elapsed = time.time() - started_ts
        if elapsed >= expected_duration:
            break
        text = f"{expected_duration - elapsed:2.0f} s remaining ({action})"
        image2 = utils.add_text_to_image(
            np.copy(canvas),
            main_message,
            font_size=100,
            text_color=color,
        )
        image2 = utils.add_text_to_image(
            image2,
            text,
            font_size=40,
            text_color=color,
            text_y=600,
        )
        camera.set_overlay(image2)


def print_image_copies(camera, captured_image, filename, auto_exit_timeout=120, max_copies=8):
    """Continue printing image copies if the user keeps requesting it.

    Function returns none when in either of the following cases:
        - User presses return button
        - auto_exit_timeout (time between individual prints)
        - max_copies is reached
    """
    wait_started = time.time()
    copies = 0
    while True:
        waiting_duration = time.time() - wait_started
        if keyboard_conditions.print_image():
            print("Yes copies")
            print_image(camera, captured_image, filename)
            wait_for_print_to_finish(camera, captured_image)
            wait_started = time.time()
            copies += 1

        if (
            keyboard_conditions.return_back()
            or waiting_duration >= auto_exit_timeout
            or copies >= max_copies
        ):
            return None


def enable_printer():
    """Make sure printer is enabled in case of previous errors"""
    subprocess.run(["sudo", "cupsenable", PRINTER_NAME])


def cancel_all_print_jobs():
    subprocess.run(["cancel", "-a"])


def setup_camera():
    camera = Picamera2()
    camera.start_preview(Preview.DRM, x=0, y=0, width=SCREEN_SIZE[0], height=SCREEN_SIZE[1])
    preview_config = camera.create_preview_configuration(
        {"size": SCREEN_SIZE},
        transform=Transform(hflip=True),
    )
    camera.configure(preview_config)
    camera.start()
    camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    canvas = get_default_overlay(camera)
    set_special_overlay(camera, canvas, CAPTURE_GUIDE)
    return camera


if __name__ == "__main__":
    camera = setup_camera()
    enable_printer()
    cancel_all_print_jobs()
    captured_image = None

    try:
        while True:
            if keyboard_conditions.capture_image() and captured_image is None:
                perform_countdown(camera)
                captured_image = camera.capture_array("main")
                preview_and_save_image(camera, captured_image)
            if keyboard_conditions.print_image() and captured_image is not None:
                filename = save_image_for_printing(captured_image)
                print_image(camera, captured_image, filename)
                wait_for_print_to_finish(camera, captured_image)
                print_image_copies(camera, captured_image, filename)
                canvas = get_default_overlay(camera, reset=False)
                set_special_overlay(camera, canvas, CAPTURE_GUIDE)
                captured_image = None
            if keyboard_conditions.return_back():
                canvas = get_default_overlay(camera, reset=False)
                set_special_overlay(camera, canvas, CAPTURE_GUIDE)
                captured_image = None
            if keyboard_conditions.quit():
                print("Closing camera...")
                break

    finally:
        cancel_all_print_jobs()
        camera.stop_preview()
        camera.stop()
        camera.close()
        tcflush(stdin, TCIOFLUSH)

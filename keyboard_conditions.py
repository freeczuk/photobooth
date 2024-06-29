from keyboard import is_pressed


def print_image() -> bool:
    return is_pressed("8") or is_pressed("9")


def return_back() -> bool:
    return is_pressed("5") or is_pressed("6")


def capture_image():
    return is_pressed("2") or is_pressed("3")


def quit() -> bool:
    return is_pressed("0")

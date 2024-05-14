from base64 import b64encode as be


def encode_image_to_b64(image_path: str | bytes) -> str:
    if isinstance(image_path, str):
        with open(image_path, "rb") as image_file:
            return be(image_file.read()).decode("utf-8")
    return be(image_path).decode("utf-8")

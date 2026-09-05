from django.core.exceptions import ValidationError
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


def validate_avatar_size(img):
    max_size = 10*1024*1024

    if img.size > max_size:
        raise ValidationError(
            "The image must be smaller than 10 MB"
        )


def compress_image(image):
    img = Image.open(image)

    img.thumbnail((640, 640))

    buffer = BytesIO()

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(
        buffer,
        format="JPEG",
        quality=85,
        optimize=True,
    )

    return ContentFile(
        buffer.getvalue(),
        name="avatar.jpg",
    )

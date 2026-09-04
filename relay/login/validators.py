from django.core.exceptions import ValidationError

def validate_avater_size(img):
    max_size = 10*1024*1024

    if img.size > max_size:
        raise ValidationError(
            "The image must be smaller than 10 MB"
        )
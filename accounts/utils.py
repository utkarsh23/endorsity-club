from PIL import Image


def center_crop_and_square_image(image_path):
    im = Image.open(image_path).convert('RGB')
    width, height = im.size
    new_dimension = min(width, height)

    left = (width - new_dimension)/2
    top = (height - new_dimension)/2
    right = (width + new_dimension)/2
    bottom = (height + new_dimension)/2

    im = im.crop((left, top, right, bottom))
    im.save(image_path)


def resize_image(image_path):
    im = Image.open(image_path).convert('RGB')
    im.thumbnail((500, 500), Image.ANTIALIAS)
    im.save(image_path)

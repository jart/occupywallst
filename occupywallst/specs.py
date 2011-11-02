# myapp/specs.py

from imagekit.specs import ImageSpec
from imagekit import processors

# first we define our thumbnail resize processor
class ResizeThumb(processors.Resize):
    width = 100
    height = 75
    crop = True

# now we define a display size resize processor
class ResizeDisplay(processors.Resize):
    width = 600

# now let's create an adjustment processor to enhance the image at small sizes
class EnhanceThumb(processors.Adjustment):
    contrast = 1.2
    sharpness = 1.1

# now we can define our thumbnail spec
class Thumbnail(ImageSpec):
    quality = 90  # defaults to 70
    access_as = 'thumbnail_image'
    pre_cache = True
    processors = [ResizeThumb, EnhanceThumb]

# and our display spec
class Display(ImageSpec):
    quality = 90  # defaults to 70
    increment_count = True
    processors = [ResizeDisplay]

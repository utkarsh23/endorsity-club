import string
import random

from django import template

register = template.Library()

@register.simple_tag
def random_string():
    N = random.choice(range(8,16))
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

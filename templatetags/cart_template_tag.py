from django import template
from sw_cart.utils import get_cart


register = template.Library()


@register.filter
def cart_item_count(request):
  cart = get_cart(request)
  return cart.items.all().count()



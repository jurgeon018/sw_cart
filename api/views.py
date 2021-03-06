from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from sw_catalog.models import Item
from sw_cart.models import CartItem, FavourItem, Cart 
from sw_cart.utils import get_cart, get_cart_info
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json 
from .serializers import *

@api_view(['GET','POST'])
def check_if_item_with_attributes_is_in_cart(request):
  return Response(data={}, status=200)


@api_view(['GET','POST'])
def change_item_amount(request, id):
  get_cart(request).change_item_amount(id, request.data['quantity'])
  return Response(get_cart_info(request), status=203)


@api_view(['GET','POST','DELETE'])
def cart_items(request):
  cart       = get_cart(request)
  if request.method == 'GET':
    return Response(data=get_cart_info(request),status=200)
  if request.method == 'POST':
    query      = request.data
    quantity   = query.get('quantity', 1)
    item_id    = query['item_id']
    attributes = query.get('attributes', [])
    if attributes:
      attributes = json.loads(attributes)
    cart.add_item(item_id, quantity, attributes)
    return Response(data=get_cart_info(request), status=203)
  if request.method == 'DELETE':
    cart.clear()
    return Response(data=get_cart_info(request), status=204)


from sw_currency.models import Currency


@api_view(['GET','PATCH','DELETE'])
def cart_item(request, id):
  cart = get_cart(request)
  if request.method == 'GET':
    cart_item = CartItem.objects.get(id=id)
    return Response(data=CartItemSerializer(cart_item, context={'request':request}).data, status=200)
  elif request.method == 'PATCH':
    cart_item    = cart.change_cart_item_amount(id, request.data['quantity'])
    currency = None 
    currency_code = request.session.get('current_currency_code')
    if currency_code:
      currency = Currency.objects.get(code=currency_code)
    cart_item_total_price = cart_item.get_price(currency, 'total_price_with_discount_with_attributes')
    # cart_item_total_price = cart_item.total_price
    response     = {
      "cart_item_total_price":cart_item_total_price, 
    }
    response.update(get_cart_info(request))
    return Response(data=response, status=202)
  elif request.method == 'DELETE':
    get_cart(request).remove_cart_item(id)
    response = get_cart_info(request)
    return Response(response, status=200)


@api_view(['GET','POST','DELETE'])
def favour_items(request):
  cart = get_cart(request)
  if request.method == 'GET':
    favours  = FavourItem.objects.filter(cart=cart)
    response = FavourItemSerializer(favours, many=True).data
    return Response(response, status=200)
  if request.method == 'POST':
    item_id   = request.data['item_id']
    favour, _ = FavourItem.objects.get_or_create(
      cart=cart, 
      item=Item.objects.get(id=item_id)
    )
    return Response(status=202)
  if request.method == 'DELETE':
    FavourItem.objects.filter(cart=cart).delete()
    return Response(status=204)


@api_view(['GET','DELETE'])
def favour_item(request, id):
  cart = get_cart(request)
  if request.method == 'GET':
    favour_item = FavourItem.objects.get(id=id)
    response    = FavourItemSerializer(favour_item).data
    return Response(response, status=200)
  elif request.method == 'DELETE':
    FavourItem.objects.get(id=id).delete()
    return Response(status=204)


@api_view(['DELETE'])
def remove_favour_by_like(request, id):
  FavourItem.objects.get(cart=get_cart(request), item__id=id).delete()
  return Response(status=204)


@api_view(['POST'])
def add_favour_to_cart(request, id):
  favour_item = FavourItem.objects.get(id=id)
  cart_item, _ = CartItem.objects.get_or_create(
    cart=get_cart(request),
    item=favour_item.item,
    ordered=False,
  )
  if _: cart_item.quantity = 1
  if not _: cart_item.quantity += 1
  cart_item.save()
  favour_item.delete()
  return Response(status=202)


@api_view(['POST'])
def add_favours_to_cart(request):
  favours = FavourItem.objects.filter(cart=get_cart(request))
  for favour in favours:
    cart_item, _ = CartItem.objects.get_or_create(
      cart=get_cart(request),
      item=favour.item,
      ordered=False,
    )
    if _: cart_item.quantity = 1
    if not _: cart_item.quantity += 1
    cart_item.save()
    favour.delete()
  return Response(status=200)



@api_view(['GET'])
def get_favours_amount(request):
  favours = FavourItem.objects.filter(cart=get_cart(request))
  return HttpResponse(favours.count())


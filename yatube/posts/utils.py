from django.core.paginator import Paginator


def do_paginate(request, paginate_data, page_nums):
    paginator = Paginator(paginate_data, page_nums)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

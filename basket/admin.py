#coding: utf-8
from django.contrib import admin
from basket.models import Article, Basket


class ArticleAdmin(admin.ModelAdmin):
    model = Article
    search_fields = ['name', 'description']
    list_display = ('name', 'code', 'created_at', 'updated_at')


class BasketAdmin(admin.ModelAdmin):
    model = Basket

admin.site.register(Article, ArticleAdmin)
admin.site.register(Basket, BasketAdmin)

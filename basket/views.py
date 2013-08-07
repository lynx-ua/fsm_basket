# Create your views here.
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from basket.models import Article, Basket


class BasketArticleMixin(object):

    def get_articles(self):
        return Article.objects.all()

    def get_article(self, code):
        return Article.objects.get(code=code)

    def get_basket(self, key):
        try:
            return Basket.objects.get(key=key)
        except Basket.DoesNotExist:
            return Basket(key=key)


class IndexPage(TemplateView, BasketArticleMixin):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexPage, self).get_context_data()
        context.update({'basket': self.get_basket(self.request.session.session_key),
                        'articles': self.get_articles()})
        return context


class AddToBasket(View, BasketArticleMixin):

    def get(self, request, *args, **kwargs):
        self.get_basket(request.session.session_key).transition('ADD', article=self.get_article(kwargs['code']), **kwargs)
        return HttpResponseRedirect(reverse_lazy('index-page'))


class DeleteFromBasket(View, BasketArticleMixin):

    def get(self, request, *args, **kwargs):
        self.get_basket(request.session.session_key).transition('DELETE', article=self.get_article(kwargs['code']), **kwargs)
        return HttpResponseRedirect(reverse_lazy('index-page'))


class CleanBasket(View, BasketArticleMixin):

    url = reverse_lazy('index-page')

    def get(self, request, *args, **kwargs):
        self.get_basket(request.session.session_key).transition('CLEAN', **kwargs)
        return HttpResponseRedirect(reverse_lazy('index-page'))
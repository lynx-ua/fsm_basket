from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User


class InvalidSymbol(Exception):
    """Raise when a symbol is invalid or not defined"""


class InvalidTransition(Exception):
    """Raise when a transition is invalid or not allowed"""


class TransitionError(Exception):
    """Raise when a some internal error while transition"""

BASKET_TTL = 30      # Minutes
INITIAL_BASKET_STATE = u'EMPTY'

CURRENCY_CHOICES = (
    ('uah', 'UAH'),
)

"""
SYMBOL      STATE       CONDITION           NEXT STATE      ACTION
-----------------------------------------------------------------------
ADD         EMPTY                           FILLED          add_article
ADD         FILLED                          FILLED          add_article
DEL         FILLED      has_single_article  EMPTY           clean
DEL         FILLED                          FILLED          delete_article
CLEAN       *                               EMPTY           clean
EXPIRE      *                               EMPTY           clean
"""


STATES_MAP = {
    'EXPIRE': {
        '*': {
            'action': 'clean',
            'next_state': u'EMPTY'
        }
    },
    'CLEAN': {
        '*': {
            'action': 'clean',
            'next_state': u'EMPTY'
        }
    },
    'ADD': {
        u'EMPTY': {
            'action': 'add_article',
            'next_state': u'FILLED'
        },
        u'FILLED': {
            'action': 'add_article',
            'next_state': u'FILLED'
        },
    },
    u'DELETE': {
        # it is possible to have different next states by the same symbol and current state
        # in case of some conditions.
        u'FILLED': [
            {'action': 'clean',
             'next_state': u'EMPTY',
             'condition': 'has_single_article'},

            {'action': 'delete_article',
             'next_state': u'FILLED'}
        ]
    }
}


class Article(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=16, unique=True)
    price = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Basket(models.Model):
    key = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(User, null=True, blank=True)
    state = models.CharField(max_length=32, default=INITIAL_BASKET_STATE)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expire_at = models.DateTimeField(null=True, blank=True)

    def total_cost(self):
        return sum([a.article.price for a in self.articles.all()])

    def is_expired(self):
        return datetime.now() > self.expire_at if self.expire_at else False

    def is_empty(self):
        return not self.articles.exists()

    def reset_expire_at(self):
        self.expire_at = None

    def update_expire_at(self):
        self.expire_at = datetime.now() + timedelta(minutes=BASKET_TTL)

    # Conditions
    def has_single_article(self, **kwargs):
        return self.articles.count() == 1

    # Actions
    def add_article(self, **kwargs):
        self.articles.create(article=kwargs['article'])
        self.update_expire_at()

    def delete_article(self, **kwargs):
        self.articles.filter(article=kwargs['article'])[0].delete()
        self.update_expire_at()

    def clean(self, **kwargs):
        self.articles.all().delete()
        self.reset_expire_at()

    # transition
    def transition(self, symbol, **kwargs):
        # Some sanity check
        if not symbol or symbol not in STATES_MAP.keys():
            raise InvalidSymbol('Invalid symbol \'%s\'' % symbol)

        # Before any action check if basket is still active
        # if not, execute EXPIRE transitions than execute requested one
        if self.is_expired():
            self.execute_transition(STATES_MAP['EXPIRE'].get('*') or STATES_MAP['EXPIRE'].get(self.state))

        transition_data = STATES_MAP[symbol].get('*') or STATES_MAP[symbol].get(self.state)

        # it is possible to have different next states by the same symbol and current state
        # in this case we have list of states data with some conditions.
        if isinstance(transition_data, list):
            for _data in transition_data:
                if 'condition' in _data and hasattr(self, _data['condition']):
                    if getattr(self, _data['condition'])(**kwargs):
                        self.execute_transition(_data, **kwargs)
                        break
                else:
                    self.execute_transition(_data, **kwargs)
                    break
        else:
            self.execute_transition(transition_data, **kwargs)

    def execute_transition(self, transition_data, **kwargs):
        if not transition_data:
            raise InvalidTransition('Transition is not allowed')

        if not hasattr(self, transition_data['action']):
            raise InvalidTransition('Invalid transition action \'%s\'' % transition_data['action'])
        if not self.pk:
            self.save()

        getattr(self, transition_data['action'])(**kwargs)
        self.state = transition_data['next_state']
        self.save()


class BasketArticles(models.Model):
    class Meta:
        ordering = ('basket', 'article')

    basket = models.ForeignKey(Basket, related_name='articles')
    article = models.ForeignKey(Article)
    created_at = models.DateTimeField(auto_now_add=True)
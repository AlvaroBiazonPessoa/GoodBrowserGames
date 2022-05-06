from django.shortcuts import render, redirect
from django.db.models import Count, Avg

import datetime
import pytz

from django.views.generic.edit import CreateView

from .models import User
from games.models import BrowserGame, Categoria

from .forms import UserCreateForm

class CreateUserView(CreateView):
    
    model = User
    form_class = UserCreateForm

    template_name = 'registration/user_registration.html'
    success_url = '/auth/login'


class Relatorio:
    def __init__(self, start=0, stop=0, class_obj=BrowserGame, top=5):
        self.start = datetime.datetime(start.year, start.month, start.day, tzinfo=pytz.UTC) if start else start
        self.stop = datetime.datetime(stop.year, stop.month, stop.day, tzinfo=pytz.UTC) if stop else stop
        self.class_obj = class_obj
        self.top = top
        self.objects = self.compute_objects()

    def compute_objects(self):
        objs_grouped = self.class_obj.objects.annotate(av_count=Count('avaliacao__id'))

        objs_grouped = self.filter_date_objs(objs_grouped)

        values = [x for x in objs_grouped.order_by('-av_count')[:self.top].values('av_count', 'nome')]
        [values[x].update({'pos': x+1}) for x in range(len(values))]
        return values

    def filter_date_objs(self, objs):
        if self.start:
            objs.filter(avaliacao__create_date__gte=self.start)
        if self.stop:
            objs.filter(avaliacao__create_date__lte=self.stop)
        return objs

class RelatorioCategorias(Relatorio):
    def compute_objects(self):
        objs_grouped = self.class_obj.objects.annotate(
            av_count=Count('browsergame__avaliacao__id')
        )
        if self.start:
            objs_grouped.filter(browsergame__avaliacao__create_date__gte=self.start)
        if self.stop:
            objs_grouped.filter(browsergame__avaliacao__create_date__lte=self.stop)

        values = [x for x in objs_grouped.order_by('-av_count')[:self.top].values('av_count', 'nome')]
        [values[x].update({'pos': x+1}) for x in range(len(values))]

        return values

class RelatorioUsers(Relatorio):
    def compute_objects(self):
        objs_grouped = self.class_obj.objects.annotate(
            av_count=Count('avaliacao__id')
        )
        objs_grouped = self.filter_date_objs(objs_grouped)

        values = [x for x in objs_grouped.order_by('-av_count')[:self.top].values('av_count', 'username')]
        [values[x].update({'pos': x+1}) for x in range(len(values))]

        return values


class RelatorioMediaGames(Relatorio):
    def compute_objects(self):
        objs_grouped = self.class_obj.objects.annotate(
            av_media=Avg('avaliacao__rating'), 
            av_count=Count('avaliacao__id')
        ).filter(av_count__gte=4)

        objs_grouped = self.filter_date_objs(objs_grouped)

        values = [x for x in objs_grouped.order_by('-av_media')[:self.top].values('av_media', 'av_count', 'nome')]
        [values[x].update({'pos': x+1}) for x in range(len(values))]

        return values



def criar_relatorios(start=0, stop=0):
    dict_relatorios = {
        'games_mais_avaliados': Relatorio(start, stop),
        'usuarios_mais_avaliaram': RelatorioUsers(start, stop, User),
        'categorias_mais_avaliadas': RelatorioCategorias(start, stop, Categoria, 3),
        'games_maior_media': RelatorioMediaGames(start, stop)
    }
    return dict_relatorios


def relatorios(request, start=0, stop=0):
    user = request.user

    context = {
        'user': user,
        'relatorios': criar_relatorios(start, stop)
    }
    return render(request, 'relatorios.html', context)
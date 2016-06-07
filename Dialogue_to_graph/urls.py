from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index,name='index'),
    url(r'^evaluate/',views.evaluate_graph,name='evaluation'),
    url(r'^dialogues/get',views.get_dialogues,name='get_dialogues'),
    url(r'^dialogues/save-json/',views.save_dialogues_json,name='save_eval_dialogues')
]
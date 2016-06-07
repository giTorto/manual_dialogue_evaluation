import json

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.template import loader

from Dialogue_to_graph.graph_analysis_lib import DialogueNode, DialogueTreeBuilder
from .models import Post
from django.http import JsonResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt


def index(request):
    template = loader.get_template('post/index.html')
    q = Post.objects.values('did','content').filter(type='start_discussion').distinct()
    context = {
        'latest_post_list': q,
    }
    return HttpResponse(template.render(context,request))

def evaluate_graph(request):
    template = loader.get_template('post/evaluate_dialogues.html')
    context = {}
    return HttpResponse(template.render(context,request))

def get_dialogues(request):
    q = Post.objects.values('did').filter(evaluated=0).distinct()
    dids = [x['did'] for x in list(q)[:3]]
    rs = Post.objects.filter(did__in=dids)
    del dids

    data = serializers.serialize("json", list(rs.all()))
    #print data
    return HttpResponse(data)

def update_db(did_up):
    q = Post.objects.filter(did=did_up).update(evaluated=1)
    print 'Updated ', q, ' rows'
    return

def js_graph_to_std(json_data):
    json_graph = json_data['nodeDataArray']
    root_node = None
    # 1. create root node
    for element in json_graph:
        if element.get('pid') == '' and element.get('cid')== '':
            root_node = DialogueNode(element.get('key'),element.get('name'),element.get('content'),reachables=[])
    dlg_tree_bld = DialogueTreeBuilder(json_data.get('did'), root_node)

    for element in json_graph:
        if element.get('pid') != '':
            dlg_tree_bld.create_node(element.get('key'),element.get('name'),element.get('content'),
                                     element.get('time'),element.get('pid'),element.get('cid'),parent=[])
            print element.get('parent')
            dlg_tree_bld.add_parent(element.get('parent'),element.get('key'))

    dict_result = DialogueTreeBuilder.DialogueTreeEncoder().encode(dlg_tree_bld.get_dialogue_graph())
    with open('evaluated_graph.json','a') as out_file:
        json.dump((json_data.get('did'), dict_result),out_file)
        out_file.write('\n')

    return json_data.get('did'), dict_result


@csrf_exempt
def save_dialogues_json(request):
    result = None
    if request.is_ajax():
        if request.method == 'POST':
            result = json.loads(request.body)
    did,dict_res = js_graph_to_std(result)
    update_db(did)

    return HttpResponse("OK")

#TODO: transform to a graph compliant with the already existent one,or check tradeoff
#TODO: find a way to store it and update DB
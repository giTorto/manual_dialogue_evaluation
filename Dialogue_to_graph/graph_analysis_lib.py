import random
from json import JSONEncoder

import operator


class DialogueTreeBuilder:
    def __init__(self, nid, root_node):
        self.nid = nid
        self.root_node = root_node
        self.nodes = {}
        self.ids_added = [None]
        self.user_last_addition = {}
        self.user_last_addition[root_node.user] = root_node.node_id

    def add_neighbour(self, from_node, to_node_id):
        # adding parents
        node = self.nodes.get(from_node)
        if node is None:
            node = self.root_node
        if node.node_id != from_node:
            return False
        result = node.add_neighbour(to_node_id)
        if result:
            result = result and self.nodes.get(to_node_id).add_parent(from_node)
            if not result:
                raise Exception('Error adding node')
        return result

    def add_parent(self,parent,future_son):
        future_son_node = self.nodes.get(future_son)
        if future_son_node is None:
            print 'Issues getting the son node. It shouldn\'t be a root node'
            raise Exception('Trying to add a parent node to the root!')
        if future_son_node.node_id != future_son:
            return False

        parent_node = self.nodes.get(parent)
        if parent_node is None:
            print 'Getting the root node'
            parent_node = self.root_node
        if parent_node.node_id != parent:
            return False

        result = self.nodes.get(future_son).add_parent(parent)
        if result:
            result = result and parent_node.add_neighbour(future_son)
        if not result:
            raise Exception('Error adding node')
        return result


    def reachable(self, from_node, to_node_id):
        actual_node = self.nodes.get(from_node)
        if actual_node is None and from_node == self.root_node.node_id:
            actual_node = self.root_node
        elif actual_node is None:
            raise Exception("Starting node is not in the graph")
        neighbors = actual_node.reachable_nodes
        look_in_neighborhoods = []
        for neighbor in neighbors:
            if neighbor == to_node_id:
                return True
            else:
                look_in_neighborhoods.append(neighbor)

        for neighbor in look_in_neighborhoods:
            result = self.reachable(neighbor, to_node_id)
            if result:
                return True

        return False

    def create_node(self, node_id, user, content, timestamp=None, process_id=None, comment_id=None,parent=[]):
        if node_id not in self.nodes:
            if process_id == None:
                print "The node with id " + node_id + " has no Process ID"
            new_node = DialogueNode(node_id, user, content, timestamp=timestamp, process_id=process_id, reachables=[],
                                    comment_id=comment_id,parent=[])
            self.nodes[node_id] = new_node
            self.ids_added.append(node_id)
            self.user_last_addition[user] = node_id
            return True
        else:
            return False

    def add_node(self, node):
        if self.nodes.get(node.node_id) is not None:
            return False
        else:
            self.nodes[node.node_id] = node
            self.ids_added.append(node.node_id)
            self.user_last_addition[node.user] = node.node_id
            return True

    def get_node(self, node_id):
        node = self.nodes.get(node_id)
        if node is None:
            node = self.root_node
            if node.node_id == node_id:
                return node
            else:
                None
        return node

    def get_last_node_added(self):
        return self.nodes.get(self.ids_added[-1])

    def get_dialogue_graph(self):
        nodes = self.nodes
        return (self.root_node, nodes)

    class DialogueTreeEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__


class DialogueNode:
    def __init__(self, node_id, user, content, timestamp=0, process_id=0, comment_id=0, reachables=[],parent=[]):
        self.parents = parent
        self.user = user
        self.content = content
        self.id_comment = comment_id
        self.reachable_nodes = reachables
        self.node_id = node_id
        self.time = timestamp
        self.id_process = process_id

    def add_neighbour(self, dialogue_node_id):
        # cannot be in the reachable list already, otherwise there are duplicates
        # cannot be in the parent, otherwise there is a loop
        if (dialogue_node_id not in self.reachable_nodes) and not(dialogue_node_id in self.parents):
            self.reachable_nodes.append(dialogue_node_id)
            return True
        else:
            return False

    def add_parent(self,dialogue_node_id):
        # cannot be in the parent list already, otherwise there are duplicates
        # cannot be in the reachable list, otherwise there is a loop
        if dialogue_node_id not in self.reachable_nodes:
            self.parents.append(dialogue_node_id)
            return True
        else:
            return False

    def remove_neighbour(self,dialogue_node_id):
        if (dialogue_node_id in self.reachable_nodes):
            self.reachable_nodes.remove(dialogue_node_id)
            return True
        else:
            return False



def ensure_replies_to_users_linked(user_replied, user_replying, dialogue_tree, new_node_id,verbose=False):
    if user_replied == user_replying:
        return
    user_last_addition_id = dialogue_tree.user_last_addition.get(user_replied)
    # sometimes people tags someone to involve them in the conversation
    # without the hereunder check comments that will refer to comments in the middle of a
    # thread will be ignored, since they are not answering neither to the root nor to the starting
    # user, otherwise we can take it as answer to the reply an stop i
    #if len(dialogue_tree.nodes[user_last_addition_id].reachable_nodes) > 0:
    #    return
    if user_last_addition_id is None:
        if verbose:
            print 'the user hasn\'t already wrote'
        return
    # this is a shortcut, to perform better I should check all the comments posted by that user and
    # take the one with higher timestamp
    # if not dialogue_tree.reachable(user_last_addition_id,new_node_id):
    result = dialogue_tree.add_neighbour(user_last_addition_id, new_node_id)
    if verbose:
        print result
        last = dialogue_tree.get_last_node_added()

        print last.content,last.reachable_nodes,last.parents
    return


"""
Transform a dialogue element to a graph
"""
def extract_starting_user_info(dialogue):
    content = dialogue['post']
    user = dialogue['user']['name'].strip(' ')
    time = dialogue['timestamp']
    return content,user,time

def extract_user_info(post):
    new_node_id = str(post['pid']) + str(post['cid']) + str(post['time'])
    post_user = post['user']['name'].strip(' ')
    post_time = post['time']
    post_pid = post['pid']
    post_cid = post['cid']
    return new_node_id,post_user,post_time,post_pid,post_cid

def add_edges_given_user_references(replies,post_user,dialogue_tree,new_node_id,verbose):
    if isinstance(replies, list):
        set_user_names = set()
        if verbose:
            print 'Adding edge'
            print replies
        for reply in replies:
            if reply['name'][1:] != '' and (reply['name'] != reply['link'] or '@' in reply['name']):
                set_user_names.add(reply['name'][1:])
        for user_name in set_user_names:
            # can happen that people replies to itselves
            if verbose:
                print user_name,post_user,new_node_id
            ensure_replies_to_users_linked(user_name, post_user, dialogue_tree, new_node_id)
    else:
        user_replied = replies['name'][1:]
        if verbose:
            print 'Adding edge',user_replied,post_user

        ensure_replies_to_users_linked(user_replied, post_user, dialogue_tree, new_node_id,verbose)

"""
This function creates an edge between the new node and the last one or with the root node, if not considered
in the same diadic thread.
"""
def add_edge(dialogue_tree,post_user,pid_users,last_node_added,created_node,user,root,new_node_id):
    if post_user in pid_users:
        dialogue_tree.add_neighbour(last_node_added.node_id, created_node.node_id)
        #two cases to consider when the set is empty and when not
    else:
        pid_users.clear()
        pid_users.add(user)
        pid_users.add(post_user)
        if post_user != user:
            dialogue_tree.add_neighbour(root.node_id, new_node_id)

"""
With this function a new node is created and is attached to the best node
in the dataset considering the user that did it and the time in which happened.
"""
def add_node_and_edge(dialogue_tree,post,set_of_pids,pid_users, user, verbose=False):
    root = dialogue_tree.root_node
    new_node_id,post_user,post_time, post_pid, post_cid = extract_user_info(post)
    if verbose:
        print post_pid,post_cid,post_time
    # print post['pid'], post['time'], "These are a pid and time"
    post_content = post['content']
    if verbose:
        print post_content, post_user
    last_node_added = dialogue_tree.get_last_node_added()
    result = dialogue_tree.create_node(new_node_id, post_user, post_content, timestamp=post_time,
                                       process_id=post_pid, comment_id=post_cid)

    if verbose and not result:
        print "Node not added"
    created_node = dialogue_tree.get_last_node_added()
    if post_pid not in set_of_pids:
        if verbose:
            print post_user
        # we assume that we can  go from root to the same user only if it's the first post
        #   otherwise we assume it follows the path from a previous pid, given from a discussion is endend only when a
        #   user out of the pid comes in
        if len(set_of_pids) == 0:
            dialogue_tree.add_neighbour(root.node_id, new_node_id)
            pid_users.add(post_user)
            pid_users.add(user)
            set_of_pids.add(post['pid'])
            return

        set_of_pids.add(post['pid'])

        # since the pid is changed and posts are odered by group, this means that I'm in a leaf
        if last_node_added is not None:
            if last_node_added.time < created_node.time:
                if verbose:
                    print post_user, ' vs ',pid_users
                # needed to check if also the discussion is gone among two users and then a new one
                # starts a pid, it must be removed
                add_edge(dialogue_tree,post_user,pid_users,last_node_added,created_node,user,root,new_node_id)
            else:
                # if it happened before, behave like the user don't belong to this group
                if post_user in pid_users:
                    pid_users.remove(post_user)
                add_edge(dialogue_tree,post_user,pid_users,last_node_added,created_node,user,root,new_node_id)


    else:
        # dialogue_tree.add_neighbour(root_of_graph.node_id, new_node_id)
        pid_users.add(post_user)
        if created_node.id_process == last_node_added.id_process and created_node.time > last_node_added.time:
            dialogue_tree.add_neighbour(last_node_added.node_id, new_node_id)

    # if I have a replied_to I have to check that a node from the last post of that user to this is already linked
    # otherwise link it. In addition I have to check that it is a real link
    if post.get('replied_to') is not None:
        replies = post['replied_to']
        if verbose:
            print replies
        add_edges_given_user_references(replies,post_user,dialogue_tree,new_node_id,verbose)

"""
This function reduces indegree of each node, keeping as parent only the one with highest timestamp.
"""
def reduce_indegree_of_each_node(dialogue_tree):
    # removing to much parents
    for node_id in dialogue_tree.nodes:
        node = dialogue_tree.nodes.get(node_id)
        if len(node.parents)>1:
            # keep just the latest
            max_time = 0
            max_id = 0
            for parent in node.parents:
                parent_node = dialogue_tree.get_node(parent)
                parent_time = parent_node.time
                # higher time, more recent the post
                if parent_time> max_time:
                    max_id = parent_node.node_id
                    max_time = parent_time
            # other nodes disown this node
            disowning_parents = [x for x in node.parents if x!= max_id]
            for id in disowning_parents:
                dialogue_tree.get_node(id).remove_neighbour(node_id)
            # this node diwons other parents except the recent one
            dialogue_tree.nodes[node_id].parents = [x for x in dialogue_tree.nodes[node_id].parents if x==max_id]

def from_dialogue_to_graph(dialogue):
    root_of_graph = None

    # knowing for sure that data are not ordered by time
    content,user,time = extract_starting_user_info(dialogue)
    #create root of the graph
    root_of_graph = DialogueNode(time + '0', user, content, reachables=[])
    dialogue_tree = DialogueTreeBuilder(dialogue['nid'], root_of_graph)
    # sort answers according to pid and time, pid and cid will lead to the same thing
    # in many case works but I found a case in which not, sort pid by time
    posts = sorted(dialogue['answers'], key=operator.itemgetter('pid', 'time'))
    set_of_pids = set()
    pid_users = set()
    verbose = False
    #value = random.randrange(0,1000)
    #if dialogue['nid']=='74272':
    #    verbose = True
    #    print 'here I\'m'
    #TODO: nids that can be used in the presentation 58995, 132660,236671,248403,100636

    for post in posts:
        add_node_and_edge(dialogue_tree,post,set_of_pids,pid_users,user,verbose)

    # removing to much parents
    reduce_indegree_of_each_node(dialogue_tree)
    # removing to much parents
    for node_id in dialogue_tree.nodes:
        node = dialogue_tree.nodes.get(node_id)
        if len(node.parents)>1:
            print 'Error, parents not disowned'

    if verbose:
        print 'dialogue',dialogue['nid']
        print dialogue_tree.root_node.reachable_nodes, dialogue_tree.root_node.content,dialogue_tree.root_node.user
        for node in dialogue_tree.nodes:
            print dialogue_tree.nodes[node].reachable_nodes, dialogue_tree.nodes[node].content, dialogue_tree.nodes[
                node].user, dialogue_tree.nodes[node].id_process, dialogue_tree.nodes[node].node_id,'\n'

        exit(0)
    dict_result = DialogueTreeBuilder.DialogueTreeEncoder().encode(dialogue_tree.get_dialogue_graph())
    return dialogue['nid'], dict_result


def from_json(json_object):
    """ self.parents = parent
        self.user = user
        self.content = content
        self.id_comment = comment_id
        self.reachable_nodes = reachables
        self.node_id = node_id
        self.time = timestamp
        self.id_process = process_id"""
    if 'node_id' in json_object and \
                    'user' in json_object and \
                    'content' in json_object:
        if 'time' in json_object and 'id_process' in json_object and 'reachable_nodes' in json_object:
            return DialogueNode(json_object['node_id'], json_object['user'], json_object['content'],
                                json_object['time'], json_object['id_process'],  json_object['id_comment'],
                                json_object['reachable_nodes'],json_object['parents'])
        else:
            return DialogueNode(json_object['node_id'], json_object['user'], json_object['content'])


import requests
import simplejson as json
import networkx as nx

r = requests.get('http://occupywallst.org/api/safe/article_get/?article_slug=occupy-seattle-occupies-wal-mart')
j = json.loads(r.content)
article = j['results'][0]

r = requests.get('http://occupywallst.org/api/safe/article_get_comments/?article_slug=occupy-seattle-occupies-wal-mart')
j = json.loads(r.content)

G = nx.DiGraph()
G.add_node('original article', ups=0, downs=0, karma=0, **article)
G.users = set()


for c in j['results']:
    user = c.pop('user')
    G.users.add(user)

    id = c.pop('id')
    pid = c.pop('parent_id')
    # special case: reply to original article
    if pid == None:
        pid = 'original article'

    G.add_node(id, **c)

    G.add_edge(user, id, type='author')
    G.add_edge(id, pid, type='response')

# calculate average ups, downs
for u in G.users:
    G.node[u]['ups'] = sum([float(G.node[c]['ups']) for c in G[u]])
    G.node[u]['downs'] = sum([float(G.node[c]['downs']) for c in G[u]])
    G.node[u]['karma'] = (G.node[u]['ups'] - G.node[u]['downs']) / len(G[u])

# list the posts from the highest karma users
high_karma = [u for u in G.users if G.node[u]['karma'] >= 3.0]
for u in high_karma:
    print u
    for c in G[u]:
        print '#%d:'%c,
        print '(%d hr)' % ((G.node[c]['published'] - G.node['original article']['published'])/(1000*3600)),
        print G.node[c]['content']
        print


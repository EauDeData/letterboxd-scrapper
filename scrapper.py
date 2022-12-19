import requests as r
import networkx as nx
from bs4 import BeautifulSoup as BS

BeautifulSoup = lambda x: BS(x, features = 'lxml')

def film2actors(link):
    html = r.get(link).text
    soup = BeautifulSoup(html)
    actor_sou = soup.find_all(class_ = 'cast-list')
    actors = BeautifulSoup(str(actor_sou[0])).find_all('a')
    return [x.attrs['href'] for x in actors]

def film2directors(link):
    html = r.get(link).text
    soup = str('\n'.join([str(x) for x in BeautifulSoup(html).find_all(class_ = 'text-sluglist')]))
    crew = BeautifulSoup(soup).find_all('a')
    return [x.attrs['href'] for x in crew if 'director' in x.attrs['href']]

def actor2films(link):
    html = r.get(link).text
    soup = BeautifulSoup(html).find_all(class_ = 'poster-container')
    parsed = [BeautifulSoup(str(x)).find('div') for x in soup]
    return [x.attrs['data-target-link'] for x in parsed]

def director2films(link):
    html = r.get(link).text
    soup = BeautifulSoup(html).find_all(class_ = 'poster-container')
    parsed = [BeautifulSoup(str(x)).find('div') for x in soup]
    return [x.attrs['data-target-link'] for x in parsed]

def step_on_graph(graph, discovered, current_item, verb, target_queue, explored_set, discovered_type, current_type):
    
    clean = lambda x: x.split('/')[-2]
    current_item = clean(current_item)
    if not current_item in graph.nodes(): graph.add_node(current_item, kind = current_type)
    # TODO: What if someone is director AND actor

    for item in discovered:

        _item = clean(item)
        if not _item in graph.nodes(): graph.add_node(_item, kind = discovered_type)
        graph.add_edge(current_item, _item, kind = verb)
        

        if not item in explored_set and not item in target_queue: target_queue.append(item)
        
graph = nx.Graph()
directors_queue = ['/director/alejandro-amenabar']
actors_queue = []
films_queue = []

MAX_NODES = 15000

director_fstring = "https://letterboxd.com{}"
actor_fstring = "https://letterboxd.com{}"
film_fstring = "https://letterboxd.com{}"

explored_items = set()
errs = set()
while len(explored_items) < MAX_NODES and (len(directors_queue) or len(actors_queue) or len(films_queue)):
    
    print(f"Currently explored {len(explored_items)} items. {len(films_queue)} films, {len(actors_queue)} actors and {len(directors_queue)} directors queued. {len(errs)} errors found. \t",)
    
    if len(directors_queue):

        try:     
            current_director = directors_queue.pop(0)
            films = director2films(director_fstring.format(current_director))
            step_on_graph(graph, films, current_director, 'directed', films_queue, explored_items, 'film', 'director')
            explored_items.add(current_director)
        except:
            errs.add(current_director)
    
    if len(actors_queue):
        
        try:
            current_actor = actors_queue.pop(0)
            films = actor2films(actor_fstring.format(current_actor))
            step_on_graph(graph, films, current_actor, 'acted', films_queue, explored_items, 'film', 'actor')
            explored_items.add(current_actor)
        except:
            errs.add(current_actor)
        
    if len(films_queue):
        
        current_film = films_queue.pop(0)
        
        try:
            ### DIRECTOR DISCOVERY ###
            directors = film2directors(film_fstring.format(current_film))
            step_on_graph(graph, directors, current_film, 'directed', directors_queue, explored_items, 'director', 'film')
            
            
            ### ACTOR DISCOVERY ###
            actors = film2actors(film_fstring.format(current_film))
            step_on_graph(graph, actors, current_film, 'acted', actors_queue, explored_items, 'actor', 'film')
            
            explored_items.add(current_film)
        except:
            errs.add(current_film)
        
    if not (len(explored_items)%25):
        nx.write_gexf(graph, './graph.gexf')
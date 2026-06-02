
# solver.py
from typing import Optional, Callable, Tuple
import heapq
import time
from collections import deque
from node import Node
from rush_hour_puzzle import RushHourPuzzle
'''
Sur BFS : C’est une méthode exhaustive sans heuristique qui garantit la solution optimale (nombre minimal de mouvements), 
mais elle peut être lente à cause du grand nombre d’états explorés.

Sur h1 : C’est l’heuristique la plus simple, basée sur la distance à la sortie, sans considérer les voitures qui bloquent. 
Elle guide la recherche mais est moins précise.

Sur h2 : Elle améliore la précision en tenant compte aussi des voitures bloquantes, ce qui aide à éviter d’explorer des chemins 
qui n’avancent pas vers la sortie.

Sur h3 : C’est la plus avancée, qui ajoute une pénalité pondérée selon la difficulté de déplacer les voitures bloquantes,
ce qui améliore encore la qualité de la recherche en réduisant le nombre d’états visités.

Sur A* : C’est un algorithme meilleur que BFS grâce à l’heuristique, qui permet d’explorer beaucoup moins d’états en visant 
directement les plus prometteurs. Plus l’heuristique est précise, plus A* est efficace.
'''

def heuristic_h1(puzzle: RushHourPuzzle) -> int:
    """
    
    Elle mesure la distance directe de la voiture rouge (identifiée par 'X') à la sortie.

Comme la voiture rouge est horizontale, elle calcule 

largeur_board − (x+longueur), c'est-à-dire combien de cases il reste à la voiture rouge pour atteindre la sortie.

Cest une estimation simple et admissible (elle ne surestime jamais le coût).
  
    """
    red_car = next((v for v in puzzle.vehicles if v.id == 'X'), None)
    if not red_car or red_car.orientation != 'H':
        return 0
    return puzzle.board_width - (red_car.x + red_car.length)

def heuristic_h2(puzzle: RushHourPuzzle) -> int:
    """
    Cest h1 plus le nombre de véhicules qui bloquent le chemin direct de la voiture rouge vers la sortie.

Les véhicules bloquants sont ceux sur la même ligne que la sortie (généralement la ligne médiane) et situés à droite de la voiture 
rouge.

Cette heuristique prend donc en compte non seulement la distance mais aussi les obstacles.
    Les véhicules bloquants sont ceux dans la rangée de sortie (board_height//2 - 1) et à droite de la voiture rouge.
    """
    h1 = heuristic_h1(puzzle)
    red_car = next((v for v in puzzle.vehicles if v.id == 'X'), None)
    if not red_car:
        return h1
    exit_row = (puzzle.board_height // 2) - 1
    blocking_count = sum(1 for v in puzzle.vehicles if v.id != 'X' and v.y == exit_row and v.x > red_car.x)
    return h1 + blocking_count

def heuristic_h3(puzzle: RushHourPuzzle, red_car_init_pos: int) -> int:
    """
    Heuristique h3  : h2 + pénalité basée sur la mobilité des véhicules bloquants.
    Pour chaque véhicule bloquant, ajoute 1 / (mobilité + 1) pour estimer le coût de les déplacer.
    pour que 
    Cela rend h3 admissible (pas de surestimation) et plus efficace, réduisant les nœuds explorés et le temps.
    """
    h2 = heuristic_h2(puzzle)
    red_car = next((v for v in puzzle.vehicles if v.id == 'X'), None)
    if not red_car:
        return h2
    exit_row = (puzzle.board_height // 2) - 1
    blocking_vehicles = [v for v in puzzle.vehicles if v.id != 'X' and v.y == exit_row and v.x > red_car.x]
    
   
    penalty = sum(1 / (puzzle.estimate_mobility(v) + 1) for v in blocking_vehicles)
    
    return h2 + int(penalty)  

def bfs(initial: RushHourPuzzle) -> Tuple[Optional[Node], int, float]:
    """
    Algorithme BFS (Breadth-First Search)
BFS explore tous les nœuds à une profondeur donnée avant de passer à la suivante.

Il garantit de trouver la solution avec le nombre minimum de mouvements (le chemin le plus court en nombre d'étapes).

Fonctionnement :

On commence avec l'état initial dans une queue (frontière).

À chaque étape, on extrait le premier état et génère ses successeurs.

On ajoute à la frontière tous les successeurs non explorés.

On continue jusqu’à trouver l’état but (la voiture rouge a atteint la sortie).

BFS peut explorer beaucoup de nœuds, donc il peut être lent pour de gros puzzles.
    Algorithme BFS : Recherche en largeur d'abord pour trouver la solution avec le nombre minimal de mouvements.
    Retourne : (nœud solution, nombre de nœuds explorés, temps d'exécution en secondes)
    """
    start_time = time.time()
    initial_node = Node(initial)
    if initial.isGoal():
        return initial_node, 1, time.time() - start_time
    frontier = deque([initial_node])
    explored = set([initial_node])
    explored_count = 1  # Compte le nœud initial
    while frontier:
        node = frontier.popleft()
        for action, successor in node.state.successorFunction():
            child = Node(successor, node, action, node.g + 1)
            if child not in explored:
                explored_count += 1
                if successor.isGoal():
                    return child, explored_count, time.time() - start_time
                explored.add(child)
                frontier.append(child)
    return None, explored_count, time.time() - start_time

def astar(initial: RushHourPuzzle, heuristic: Callable[[RushHourPuzzle], int]) -> Tuple[Optional[Node], int, float]:
    """
    A* est une recherche informée qui combine le coût réel pour atteindre un état ''g'' et une estimation heuristique du coût restant
    ''h''.
Le score f = g + h mesure le "coût total estimé" d’un chemin passant par ce nœud.
A* utilise un tas (heap) pour toujours explorer le nœud avec le plus petit f en premier.
Il évite de revisiter les états déjà explorés pour éviter les boucles.
Le choix de l’heuristique influence fortement la performance : plus l’heuristique est informée 
(proche de la distance réelle tout en restant admissible), moins il faut explorer de nœuds.

    Algorithme A* ------------ Recherche avec heuristique pour trouver une solution optimale ou proche.
    Retourne  ----- nœud solution, nombre de nœuds explorés, temps d'exécution 
    """
    start_time = time.time()
    initial_node = Node(initial)
    initial_node.setF(heuristic(initial))
    frontier = []
    heapq.heappush(frontier, initial_node)
    explored = set()
    g_score = {initial_node: 0}
    explored_count = 0  
    while frontier:
        current = heapq.heappop(frontier)
        if current.state.isGoal():
            return current, explored_count, time.time() - start_time
        explored.add(current)
        explored_count += 1
        for action, successor in current.state.successorFunction():
            neighbor = Node(successor, current, action, current.g + 1)
            if neighbor in explored:
                continue
            tentative_g = current.g + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                g_score[neighbor] = tentative_g
                neighbor.setF(heuristic(successor))
                heapq.heappush(frontier, neighbor)
    return None, explored_count, time.time() - start_time
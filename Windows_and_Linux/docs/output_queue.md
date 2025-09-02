## Rôle principal du `output_queue`

Le `output_queue` est une **file d'attente qui accumule le texte de réponse de l'IA** au fur et à mesure qu'il arrive. C'est essentiel pour gérer les réponses qui peuvent arriver en plusieurs parties.

## Fonctionnement détaillé

### 1. **Initialisation et remise à zéro**
```python
def _setup_core_attributes(self) -> None:
    # ...
    self.output_queue = ""  # Initialisation comme chaîne vide
```

Le `output_queue` est remis à zéro à plusieurs moments :
- Au démarrage de l'application
- Chaque fois qu'on appuie sur le raccourci (`on_hotkey_pressed()`)

### 2. **Accumulation du texte**
Dans la méthode `replace_text()`, le texte est accumulé :
```python
def replace_text(self, new_text: str) -> None:
    # ...
    self.output_queue += new_text  # Accumulation du texte au fur et à mesure
```

### 3. **Traitement final**
Une fois le texte complet arrivé, il est traité :
```python
current_output = self.output_queue.strip()  # Nettoyage
# Puis remise à zéro : self.output_queue = ""
```

## Pourquoi cette approche ?

D'après l'analyse du fichier `aiprovider.py`, cela s'explique par le fait que **certains providers d'IA peuvent envoyer les réponses en "streaming"** (par petits morceaux successifs). Le `output_queue` :

1. **Accumule** tous les morceaux de texte au fur et à mesure qu'ils arrivent
2. **Attend** que la réponse soit complète avant de la traiter
3. **Gère** les erreurs en cours de route (comme `"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST"`)

## Exemple de flux typique

1. **Utilisateur** sélectionne du texte et appuie sur le raccourci
2. **Interface** détecte la sélection et crée une popup
3. **IA Provider** commence à générer la réponse
4. **Morceaux de texte** arrivent progressivement dans `replace_text()` et s'accumulent dans `output_queue`
5. **Une fois complet**, le texte final est remplacé dans l'application ou affiché dans une fenêtre

Cette approche permet de **gérer efficacement les réponses asynchrones** et de **s'assurer que le texte final est complet** avant de procéder au remplacement.

En résumé, `output_queue` est un **tampon essentiel** qui garantit l'intégrité des réponses de l'IA pendant leur réception asynchrone.
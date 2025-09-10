# Gestion des tâches asynchrones dans WritingTools

---

## **1. Rôle de `concurrent.futures`**
### **Pourquoi l'utiliser ?**
- **Gérer les requêtes API longues** (Gemini, OpenAI, etc.) **sans bloquer l'UI**.
- **Annuler proprement** l'attente des réponses (même si le LLM continue de son côté).
- **Centraliser la gestion des erreurs** (timeouts, rate limits, etc.).

### **Exemple clé dans le code**
```python
# Dans aiprovider.py
self.executor = ThreadPoolExecutor(max_workers=1)  # Pool de 1 thread réutilisable
self.current_future = self.executor.submit(self._get_response_impl, ...)  # Lance la tâche

# Annulation
def cancel(self):
    if self.current_future and not self.current_future.done():
        self.current_future.cancel()  # Interrompt l'attente
```

### **Avantages vs `threading.Thread`**
| **Critère**               | `Thread` seul                          | `ThreadPoolExecutor`                     |
|---------------------------|----------------------------------------|------------------------------------------|
| Annulation                | ❌ (flag manuel inefficace)            | ✅ (`future.cancel()`)                   |
| Réutilisation des threads | ❌ (nouveau thread à chaque requête)   | ✅ (pool de threads)                     |
| Gestion des erreurs       | ❌ (manuelle)                          | ✅ (centralisée via `future.result()`)   |
| Code maintenable          | ❌ (dupliqué par provider)              | ✅ (uniforme pour tous les providers)    |

---

## **2. Rôle du `threading.Thread` dans `WritingToolApp`**
### **Pourquoi ce thread existe ?**
- **Isoler la préparation des données** (lente) de l'UI :
  - Conversion d'images en base64.
  - Capture du texte sélectionné.
  - Construction des prompts.
- **Déléguer les requêtes API** à `ThreadPoolExecutor` (dans `AIProvider`).

### **Flux d'exécution**
```
UI (Thread principal)
│
├── Clic utilisateur → process_option()
│   │
│   └── Lance un thread pour process_option_thread()
│       │
│       ├── Prépare les données (prompt, image, etc.)
│       │
│       └── Appelle get_response() → ThreadPoolExecutor (API)
│           │
│           └── Retourne la réponse → output_ready_signal
│
└── UI reste réactive pendant tout le processus
```

### **Pourquoi `daemon=True` ?**
- Le thread s'arrête **automatiquement** quand l'application se ferme (évite les fuites).

---

## **3. Différence entre les deux approches**
| **Outil**               | **Rôle**                                  | **Exemple dans le code**                     |
|-------------------------|------------------------------------------|---------------------------------------------|
| `threading.Thread`      | Préparer les données (UI → prompt).      | `process_option_thread()` dans `WritingToolApp`. |
| `ThreadPoolExecutor`    | Exécuter la requête API (prompt → réponse). | `get_response()` dans `AIProvider`.         |

- **Complémentarité** :
  - Le `Thread` gère la **préparation** (rapide mais nécessaire pour ne pas bloquer l'UI).
  - Le `ThreadPoolExecutor` gère l'**exécution longue** (API + annulation).

---

## **4. Limites de l'annulation**
### **Ce qu'on peut annuler**
- **L'attente du résultat** côté client (via `future.cancel()`).
- **L'affichage de la réponse** (ignorer le résultat si l'utilisateur annule).
- **Les tâches de préparation** (avant l'envoi de la requête).

### **Ce qu'on ne peut pas annuler**
- **La génération côté LLM** :
  - Une fois la requête envoyée (`POST /generate`), le LLM continue de générer (comme une impression lancée).
  - **Analogie** : Tu ne peux pas arrêter une imprimante à distance une fois qu'elle a commencé.

### **Exemple avec `CancelledError`**
```python
try:
    response = self.current_future.result()  # Bloque jusqu'à la réponse
except CancelledError:
    logging.debug("Requête annulée par l'utilisateur")
    return ""  # Ignore la réponse
```

---

## **5. Pourquoi `asyncio` serait mieux (optionnel)**
### **Avantages**
- **Moins de threads** : Utilise une boucle d'événements au lieu de threads (meilleure performance).
- **Annulation plus fine** :
  ```python
  task = asyncio.create_task(fetch_response())
  task.cancel()  # Annule cette tâche spécifique
  ```
- **Code plus lisible** :
  ```python
  async def get_response():
      response = await call_api()  # Attend sans bloquer
  ```
- **Intégration avec le streaming** (si l'API le supporte) :
  ```python
  async for chunk in gemini.generate_content_async(prompt, stream=True):
      if cancelled:
          break  # Arrête de consommer les chunks
  ```

### **Comparaison**
| **Critère**               | `ThreadPoolExecutor`       | `asyncio`                     |
|---------------------------|---------------------------|-------------------------------|
| Threads                   | 1 par tâche               | 1 total (boucle d'événements) |
| Annulation                | ✅ (mais limitée)          | ✅ (plus fine)                |
| Streaming                 | ❌                        | ✅                            |
| Lisibilité                | Moyenne                   | ✅ (code explicite)           |

---

## **6. Schémas visuels**
### **Architecture actuelle**
```
UI (Thread principal)
│
├── Thread (préparation) → ThreadPoolExecutor (API) → Résultat
│
└── UI reste réactive
```

### **Flux d'annulation**
```
Utilisateur clique "Annuler"
│
├── future.cancel() → Interrompt l'attente
│
└── LLM continue (mais réponse ignorée)
```

---

## **7. Résumé des bonnes pratiques**
1. **Utiliser `ThreadPoolExecutor`** pour :
   - Les requêtes API longues.
   - L'annulation propre des tâches.

2. **Garder le `Thread` dans `WritingToolApp`** pour :
   - La préparation des données (sans bloquer l'UI).

3. **Passer à `asyncio`** si :
   - Tu veux optimiser les performances (moins de threads).
   - L'API supporte le streaming (ex: Gemini async).

4. **Ne pas essayer d'annuler le LLM** :
   - Une fois la requête envoyée, la génération continue côté serveur.

---

## **8. Exemple complet avec `asyncio` (optionnel)**
```python
# Dans AIProvider (version asyncio)
async def get_response(self, system_instruction, prompt):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json={"system_instruction": system_instruction, "prompt": prompt},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return await response.json()
    except asyncio.CancelledError:
        return ""  # Annulation propre
    except Exception as e:
        return f"Erreur: {str(e)}"
```

---
## **9. Conclusion**
- **`ThreadPoolExecutor`** :
  - Solution **robuste** pour les requêtes API avec annulation.
  - Déjà une **nette amélioration** par rapport à l'ancienne version.

- **`asyncio`** :
  - **Option d'optimisation** pour moins de threads et un code plus lisible.
  - À considérer si tu veux ajouter du streaming ou améliorer les performances.

- **Aucun outil ne peut** :
  - Arrêter un LLM en cours de génération (limite des APIs externes).
  - Mais tous permettent de **gérer proprement l'attente et les ressources locales**.

****  "custom_data": {
    "update_available": false,
    "providers": {
    ...
    ,
        "openai-compatible": {
        "api_key": "",
        "api_base": "https://api.groq.com/openai/v1",
        "api_organisation": "",
        "api_project": "",
        "api_model": "llama-3.3-70b-versatile",
        "has_vision": true,
        "recorded": {
          "openrouter.ai": {
            "api_key": "",
            "api_base": "https://openrouter.ai/api/v1",
            "api_model": "google/gemini-2.0-flash-exp:free",
            "api_organisation": "",
            "api_project": "",
            "has_vision": true
          },
          "api.groq.com": {
            "api_key": "",
            "api_base": "https://api.groq.com/openai/v1",
            "api_model": "llama-3.3-70b-versatile",
            "api_organisation": "",
            "api_project": "",
            "has_vision": true
          }
        }
      }
    }
  }

Quand on change la valeur du modèle Dans le drop down C'est cette fonction dans provider_ui_builder.py auto_save() qui met à jour cette valeur

"openai-compatible": {
    ...
    "api_model": "llama-3.3-70b-versatile",

Mais il faudrait aussi mettre à jour les api_model Plus bas dans le fournisseur sélectionné (groq). On va appeler ça le fournisseur (ah c'est appelé preset comme dropdown)

    "api.groq.com": {
            "api_key": "",
            "api_base": "https://api.groq.com/openai/v1",
            "api_model": "llama-3.3-70b-versatile",
            "api_organisation": "",
            "api_project": "",
            "has_vision": true
          }

Si on change la valeur du dropdown au début ça marche, après ça marche plus. Bref C'est bizarre comme comportement, ça va pas. Et en plus, ça devrait être au même endroit que la valeur du dessus Pour le changement. Par contre, quand on fait save C'est à dire de le bouton qui a en dessous du drop donne des fournisseurs. Immédiatement, cette valeur est bien mise à jour selon le fournisseur sélectionné Donc ça marche à cet endroit

Ligne 268-289 : La méthode _update_recorded_preset qui met à jour le preset "recorded" 


La référence exacte du code où la valeur du dropdown change quand on clique sur un autre modèle se trouve dans :

Fichier : Windows_and_Linux/src/aiprovider/settings.py


Le Dropdown de preset (fournisseur) se trouve dans provider_preset_manager.py (preset_dropdown)

Il y a aussi évidemment le dropdown des providers.


Quand on ouvre la fenêtre des settings, si le provider est sur openai-compatible et le preset est sur api.groq.com, alors le dropdown de preset (fournisseur) est initialisé avec la valeur par défaut la 1ère ou si une valeur est présente dans les settings, elle doit être utilisée. 

    "api.groq.com": {
            ...
            "api_model": "llama-3.3-70b-versatile",

Quand on passe d'un preset à l'autre pareil. Il faut vérifier la valeur par défaut qu'il y a Dans les settings Des fournisseurs s'ils existent
Quand on modifie le drop down des providers par exemple, on va de ollama À open AI compatible C'est pareil. 
Évidemment, en même temps, il faut que la valeur de api_model, dans  soit mise à jour
    "providers": {
    ...
    ,
        "openai-compatible": {
            "api_model": ...

Soit mis à jour.

Je répète pour l'instant, le problème c'est que dans les fournisseurs Quand on change les valeurs, ça n'est pas bien mis à jour. Par contre, ce qui est bizarre, c'est que si on fait save, alors ça marche immédiatement et bien.
_on_save_preset() dans provider_settings.py.
J'ai le fichier data ouvert donc je vois les résultats en direct.

c:\Users\dd200\Documents\Mes_projets\WritingTools Related\copy-new\Windows_and_Linux\src\aiprovider\settings.py:257-258
```
        # DISABLE WHEEL SCROLL
        self.dropdown.wheelEvent = lambda e: e.ignore()
```

# Processus de planification

## 1. Objectif → type

`classify_objective()` déduit le type (build / migrate / improve / investigate /
rollout / generic) par mots-clés, ou le prend tel que fourni. Le type oriente le
gabarit de tâches et les estimations.

## 2. Construire les tâches

`build_tasks()` combine :
- les **tâches fournies** (`given_tasks`) ;
- sinon un **gabarit canonique** (10 tâches, Cadrage → Clôture) ;
- les **enseignements Learning** validés → tâches « Appliquer la recommandation … » ;
- les **délibérations Reasoning** → tâches « Mettre en œuvre la décision … » ;
- (optionnel) des suggestions d'un LLM — jamais requises.

## 3. Estimer

`estimate()` ajuste complexité / priorité / risque / impact par règles de mots-clés
(migration/production → risque ↑ ; test/revue → priorité ↑ ; documentation →
priorité ↓), en respectant les valeurs déjà fournies, puis borne tout.

## 4. Prérequis, dépendances, ordonnancement, blocages

- `resolve_prerequisites()` : titres → identifiants ; **prérequis introuvable** →
  blocage.
- `topological_order()` : tri topologique **déterministe** (Kahn, départage par
  identifiant) ; **cycle** → blocage. Les blocages n'empêchent pas la production du
  plan : ils sont **signalés**, pas masqués.

## 5. Stratégies & sélection

`generate_strategies()` produit trois variantes (complète / essentielle / rapide),
`score_all()` les score (impact / risque / complexité / couverture), `select()`
retient la meilleure — mais le plan reste **proposé**.

## 6. Assemblage

`build_structure()` construit phases → étapes → tâches (ordre topologique) ;
`build_manifest()` produit le **manifeste exécutable** ordonné, chaque tâche
`execution_status = not_executed`.

## 7. Extension LLM (optionnelle)

Un fournisseur (`PlanningProvider`) pourra *enrichir* : suggérer des tâches, des
stratégies, critiquer un ordonnancement. Il n'est **jamais requis** (repli
déterministe garanti) et ne **valide ni n'exécute** rien.

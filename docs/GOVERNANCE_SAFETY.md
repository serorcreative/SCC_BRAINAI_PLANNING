# Gouvernance & sûreté de la planification

> **Principes cardinaux : aucune auto-modification ; aucune exécution automatique
> non validée ; aucune décision souveraine sans validation humaine.**

## 1. Le plan reste proposé

Tout plan produit est au statut **`proposed`**. La planification ne peut pas produire
un plan « validé » ni déclencher son exécution.

## 2. Aucune exécution ici

Le plan porte un **manifeste exécutable** destiné au **Kernel**, mais Planning
**n'exécute jamais** : chaque entrée du manifeste porte
`execution_status = not_executed`. L'exécution éventuelle relèvera du Kernel, après
validation humaine, et hors de cette couche.

## 3. Validation humaine obligatoire

Seule une **action humaine explicite** change le statut, via `HumanValidationPolicy` :

| Action | Transition | Exigence |
|--------|-----------|----------|
| `validate` | proposed → validated | approbateur **requis** |
| `reject` | proposed → rejected | approbateur requis |
| `revoke` | validated → revoked | approbateur requis |

Sans approbateur → refus. Transition illégale → refus. Chaque décision est tracée
(action, approbateur, motif, horodatage). Un plan validé structurant relèverait du
processus **ADR** (SCC-DOC-0009).

## 4. Aucune capacité d'auto-modification

Le `PlanningEngine` **n'importe aucune API d'écriture** d'une autre couche. Il lit
enseignements et délibérations (interfaces publiques) et n'écrit que dans son
registre de plans (`data/plans.jsonl`). Il est donc **structurellement incapable**
de modifier Learning, Reasoning, Memory, Kernel, le graphe, une doctrine ou du code.

## 5. Audit

`audit()` vérifie, pour chaque jeu de plans :
- **intégrité** : empreinte de chaque tâche = son contenu ;
- **traçabilité** : chaque tâche cite une source ; l'ordonnancement ne référence que
  des tâches existantes ;
- **sûreté** : tout plan non-proposé porte un **approbateur humain** ; aucune tâche du
  manifeste n'est marquée exécutée.

## 6. Alignement doctrinal

- **Traçabilité complète** ([[SCC-DOC-0016]]) : chaque tâche et le plan sont tracés.
- **Gouvernance avant extension** ([[SCC-DOC-0015]]) : rien n'est validé/exécuté sans humain.
- **ADR obligatoire** ([[SCC-DOC-0009]]) : un plan structurant validé passe par un ADR.
- **Intelligence lourde optionnelle et branchable** ([[SCC-DOC-0029]]) : le LLM est
  une capacité optionnelle, jamais un prérequis.

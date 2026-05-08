# JPIO Parser 🚀

[![Java Version](https://img.shields.io/badge/Java-21-orange.svg)](https://www.oracle.com/java/technologies/javase/jdk21-archive-downloads.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**JPIO Parser** est un outil CLI puissant et léger conçu pour analyser le code source Java et extraire des métadonnées structurées sous format JSON. Il permet de cartographier rapidement l'architecture d'un projet en identifiant les classes, les champs, les méthodes et leurs annotations.

---

## ✨ Fonctionnalités

- 🔍 **Analyse Récursive** : Parcourt tous les fichiers `.java` d'un répertoire donné.
- 📂 **Métadonnées Complètes** : Extrait les noms de classes, packages, héritages, implémentations, champs, méthodes et paramètres.
- 🏷️ **Support des Annotations** : Capture les annotations présentes sur les classes, champs et méthodes.
- 📄 **Sortie JSON** : Génère un flux JSON (standard ou formaté) facile à intégrer dans d'autres outils.
- ⚡ **Performance** : Basé sur [JavaParser](https://javaparser.org/), garantissant une analyse robuste et rapide.

---

## 🚀 Utilisation

Exécutez le parser en spécifiant le chemin source de votre projet Java :

```bash
java -jar target/jpio-parser.jar --source /chemin/vers/mon-projet
```

### Options CLI

| Option | Description | Valeur par défaut |
| :--- | :--- | :--- |
| `--source <path>` | **Requis**. Chemin vers le répertoire contenant les fichiers Java. | - |
| `--output <format>` | Format de sortie JSON (`json` ou `pretty`). | `json` |

### Exemple de commande avec sortie formatée

```bash
java -jar target/jpio-parser.jar --source ./src/main/java --output pretty
```

---

## 📊 Exemple de Sortie JSON

```json
{
  "classes": [
    {
      "name": "UserService",
      "packageName": "com.example.service",
      "classType": "CLASS",
      "isPublic": true,
      "annotations": ["@Service", "@Transactional"],
      "fields": [
        {
          "name": "userRepository",
          "type": "UserRepository",
          "typeSimple": "UserRepository",
          "visibility": "private",
          "annotations": ["@Autowired"],
          "isFinal": true,
          "isStatic": false
        }
      ],
      "methods": [
        {
          "name": "findUserById",
          "returnType": "User",
          "visibility": "public",
          "parameters": [
            { "name": "id", "type": "Long" }
          ],
          "annotations": ["@Override"]
        }
      ],
      "extendsList": ["BaseService"],
      "implementsList": ["IUserService"]
    }
  ]
}
```

---

## 🧰 Stack Technique

- **Langage** : Java 21
- **Moteur de parsing** : [JavaParser](https://javaparser.org/)
- **Sérialisation** : [Jackson Databind](https://github.com/FasterXML/jackson-databind)
- **Build Tool** : Maven

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

1. Forkez le projet.
2. Créez votre branche (`git checkout -b feature/AmazingFeature`).
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4. Pushez vers la branche (`git push origin feature/AmazingFeature`).
5. Ouvrez une Pull Request.

---

## 📄 Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.

---

*Développé avec ❤️ par l'équipe JPIO.*

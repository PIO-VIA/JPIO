"""
core/models.py
--------------
Dataclasses internes de JPIO.
Ces structures sont le contrat entre analyzer, generator et writer.
Tout passe par ces objets — rien n'est passé en dict brut entre les couches.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Types Java supportés pour les champs d'une entité
# ---------------------------------------------------------------------------

SUPPORTED_JAVA_TYPES = [
    "String",
    "Integer",
    "Long",
    "Double",
    "Float",
    "Boolean",
    "LocalDate",
    "LocalDateTime",
    "BigDecimal",
]

# Types qui nécessitent un import Java supplémentaire dans l'entité
JAVA_TYPE_IMPORTS = {
    "LocalDate":     "java.time.LocalDate",
    "LocalDateTime": "java.time.LocalDateTime",
    "BigDecimal":    "java.math.BigDecimal",
}

# Types de relations JPA supportés
SUPPORTED_RELATIONS = [
    "OneToMany",
    "ManyToOne",
    "ManyToMany",
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FolderMapping:
    """
    Mappe chaque couche logique du projet à un dossier réel sur le disque.
    Permet de s'adapter aux projets existants qui utilisent des noms
    différents (ex: 'model' au lieu d' 'entity').
    """
    entity:     str = "models/entity"
    dto:        str = "dto"
    mapper:     str = "mapper"
    repository: str = "repository"
    service:    str = "service"
    controller: str = "controller"
    exception:  str = "exception"
    config:     str = "config"

    @classmethod
    def from_dict(cls, data: dict) -> "FolderMapping":
        return cls(
            entity=data.get("entity", "models/entity"),
            dto=data.get("dto", "dto"),
            mapper=data.get("mapper", "mapper"),
            repository=data.get("repository", "repository"),
            service=data.get("service", "service"),
            controller=data.get("controller", "controller"),
            exception=data.get("exception", "exception"),
            config=data.get("config", "config")
        )

    def to_dict(self) -> dict:
        return {
            "entity": self.entity,
            "dto": self.dto,
            "mapper": self.mapper,
            "repository": self.repository,
            "service": self.service,
            "controller": self.controller,
            "exception": self.exception,
            "config": self.config
        }


@dataclass
class Enum:
    """Représente une énumération Java."""
    name: str
    values: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Enum":
        return cls(name=data["name"], values=data.get("values", []))

    def to_dict(self) -> dict:
        return {"name": self.name, "values": self.values}


@dataclass
class PomFeatures:
    """
    Résultat de l'analyse du pom.xml.
    Chaque attribut correspond à une dépendance Spring Boot détectée.
    """
    has_jpa:        bool = True   # spring-boot-starter-data-jpa
    has_lombok:     bool = True   # lombok
    has_swagger:    bool = True   # springdoc-openapi
    has_validation: bool = False  # spring-boot-starter-validation

    @classmethod
    def from_dict(cls, data: dict) -> "PomFeatures":
        return cls(
            has_jpa=data.get("has_jpa", True),
            has_lombok=data.get("has_lombok", True),
            has_swagger=data.get("has_swagger", True),
            has_validation=data.get("has_validation", False)
        )

    def to_dict(self) -> dict:
        return {
            "has_jpa": self.has_jpa,
            "has_lombok": self.has_lombok,
            "has_swagger": self.has_swagger,
            "has_validation": self.has_validation
        }


@dataclass
class Field:
    """
    Représente un champ d'une entité JPA.

    Exemple :
        Field(name="price", java_type="Double", nullable=True)
    """
    name: str
    java_type: str
    nullable: bool = True
    is_enum: bool = False

    @property
    def capitalized(self) -> str:
        """Retourne le nom du champ avec la première lettre en majuscule."""
        return self.name[0].upper() + self.name[1:]

    @classmethod
    def from_dict(cls, data: dict) -> "Field":
        return cls(
            name=data["name"],
            java_type=data["java_type"],
            nullable=data.get("nullable", True),
            is_enum=data.get("is_enum", False)
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "java_type": self.java_type,
            "nullable": self.nullable,
            "is_enum": self.is_enum
        }


@dataclass
class Relation:
    """
    Représente une relation JPA entre deux entités.

    Exemple :
        Relation(kind="ManyToMany", target="Category", mapped_by="products")

    Attributs :
        kind        : type JPA — OneToMany | ManyToOne | ManyToMany
        target      : nom de l'entité cible (ex: "Category")
        mapped_by   : nom du champ côté inverse (pour OneToMany / ManyToMany)
                      Vide si cette entité est le côté propriétaire (ManyToOne)
        owner       : True si cette entité possède la @JoinTable (côté propriétaire)
    """
    kind: str
    target: str
    mapped_by: str = ""
    owner: bool = True

    @property
    def target_lower(self) -> str:
        """Retourne le nom de la cible en minuscule (pour les noms de champs)."""
        return self.target[0].lower() + self.target[1:]

    @property
    def field_name(self) -> str:
        """
        Retourne le nom du champ Java pour cette relation.
        OneToMany / ManyToMany → liste plurielle  ex: categories
        ManyToOne              → singulier         ex: category
        """
        if self.kind in ("OneToMany", "ManyToMany"):
            base = self.target_lower
            return base + "s" if not base.endswith("s") else base
        return self.target_lower

    @classmethod
    def from_dict(cls, data: dict) -> "Relation":
        return cls(
            kind=data["kind"],
            target=data["target"],
            mapped_by=data.get("mapped_by", ""),
            owner=data.get("owner", True)
        )

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "target": self.target,
            "mapped_by": self.mapped_by,
            "owner": self.owner
        }


@dataclass
class Entity:
    """
    Représente une entité JPA complète avec ses champs et ses relations.

    Exemple :
        Entity(
            name="Product",
            fields=[Field("name", "String"), Field("price", "Double")],
            relations=[Relation("ManyToMany", "Category")]
        )
    """
    name: str
    fields: list[Field] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)

    @property
    def name_lower(self) -> str:
        """Retourne le nom de l'entité en camelCase minuscule (ex: product)."""
        return self.name[0].lower() + self.name[1:]

    @property
    def name_upper(self) -> str:
        """Retourne le nom de l'entité avec majuscule (ex: Product)."""
        return self.name[0].upper() + self.name[1:]

    @property
    def extra_imports(self) -> list[str]:
        """
        Retourne les imports Java supplémentaires nécessaires
        selon les types de champs utilisés.
        """
        imports = set()
        for f in self.fields:
            if f.java_type in JAVA_TYPE_IMPORTS:
                imports.add(JAVA_TYPE_IMPORTS[f.java_type])
        return sorted(imports)

    @classmethod
    def from_dict(cls, data: dict) -> "Entity":
        fields = [Field.from_dict(f) for f in data.get("fields", [])]
        relations = [Relation.from_dict(r) for r in data.get("relations", [])]
        return cls(name=data["name"], fields=fields, relations=relations)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "fields": [f.to_dict() for f in self.fields],
            "relations": [r.to_dict() for r in self.relations]
        }


@dataclass
class ProjectConfig:
    """
    Configuration globale du projet — produit par analyzer.py,
    consommé par generator.py.

    Attributs :
        base_package : package Java de base détecté ou saisi (ex: com.pio.ecommerce)
        api_prefix   : préfixe des routes REST (ex: /api/v1)
        entities     : liste de toutes les entités décrites par l'utilisateur
    """
    base_package: str
    api_prefix: str
    entities: list[Entity] = field(default_factory=list)
    enums: list[Enum] = field(default_factory=list)
    pom_features: PomFeatures = field(default_factory=PomFeatures)
    folder_mapping: FolderMapping = field(default_factory=FolderMapping)

    @property
    def package_path(self) -> str:
        """
        Convertit le package Java en chemin de dossier.
        ex: com.pio.ecommerce → com/pio/ecommerce
        """
        return self.base_package.replace(".", "/")

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        entities = [Entity.from_dict(e) for e in data.get("entities", [])]
        enums = [Enum.from_dict(e) for e in data.get("enums", [])]
        pom_features = PomFeatures.from_dict(data.get("pom_features", {}))
        folder_mapping = FolderMapping.from_dict(data.get("folder_mapping", {}))
        return cls(
            base_package=data["base_package"],
            api_prefix=data.get("api_prefix", "/api/v1"),
            entities=entities,
            enums=enums,
            pom_features=pom_features,
            folder_mapping=folder_mapping
        )

    def to_dict(self) -> dict:
        return {
            "base_package": self.base_package,
            "api_prefix": self.api_prefix,
            "entities": [e.to_dict() for e in self.entities],
            "enums": [e.to_dict() for e in self.enums],
            "pom_features": self.pom_features.to_dict(),
            "folder_mapping": self.folder_mapping.to_dict()
        }
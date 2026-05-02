"""
Internal JPIO Dataclasses.
These structures form the contract between analyzer, generator, and writer.
Everything passes through these objects — no raw dicts are passed between layers.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Supported Java types for entity fields
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

# Types requiring an additional Java import in the entity
JAVA_TYPE_IMPORTS = {
    "LocalDate":     "java.time.LocalDate",
    "LocalDateTime": "java.time.LocalDateTime",
    "BigDecimal":    "java.math.BigDecimal",
}

# Supported JPA relation types
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
    Maps each logical layer of the project to a real folder on disk.
    Allows adaptation to existing projects using different names
    (e.g., 'model' instead of 'entity').
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
    """Represents a Java enumeration."""
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
    Result of pom.xml analysis.
    Each attribute corresponds to a detected Spring Boot dependency.
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
    Represents a field in a JPA entity.

    Example:
        Field(name="price", java_type="Double", nullable=True)
    """
    name: str
    java_type: str
    nullable: bool = True
    is_enum: bool = False

    @property
    def capitalized(self) -> str:
        """Returns the field name with the first letter capitalized."""
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
    Represents a JPA relation between two entities.

    Example:
        Relation(kind="ManyToMany", target="Category", mapped_by="products")

    Attributes:
        kind        : JPA type — OneToMany | ManyToOne | ManyToMany
        target      : target entity name (e.g., "Category")
        mapped_by   : inverse side field name (for OneToMany / ManyToMany)
                      Empty if this entity is the owning side (ManyToOne)
        owner       : True if this entity has the @JoinTable (owning side)
    """
    kind: str
    target: str
    mapped_by: str = ""
    owner: bool = True

    @property
    def target_lower(self) -> str:
        """Returns the target name in lowercase (for field names)."""
        return self.target[0].lower() + self.target[1:]

    @property
    def field_name(self) -> str:
        """
        Returns the Java field name for this relation.
        OneToMany / ManyToMany → plural list    e.g., categories
        ManyToOne              → singular       e.g., category
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
    Represents a complete JPA entity with its fields and relations.

    Example:
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
        """Returns the entity name in lowercase camelCase (e.g., product)."""
        return self.name[0].lower() + self.name[1:]

    @property
    def name_upper(self) -> str:
        """Returns the entity name with uppercase (e.g., Product)."""
        return self.name[0].upper() + self.name[1:]

    @property
    def extra_imports(self) -> list[str]:
        """
        Returns additional Java imports required
        based on the field types used.
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
class SecurityConfig:
    """Security configuration collected by the security wizard."""
    username_field: str
    jwt_secret: str
    jwt_expiration_hours: int
    public_routes: list[str] = field(default_factory=list)
    existing_user_entity: str = ""
    extra_user_fields: list[Field] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "SecurityConfig":
        extra_fields = [Field.from_dict(f) for f in data.get("extra_user_fields", [])]
        return cls(
            username_field=data["username_field"],
            jwt_secret=data["jwt_secret"],
            jwt_expiration_hours=data["jwt_expiration_hours"],
            public_routes=data.get("public_routes", []),
            existing_user_entity=data.get("existing_user_entity", ""),
            extra_user_fields=extra_fields
        )

    def to_dict(self) -> dict:
        return {
            "username_field": self.username_field,
            "jwt_secret": self.jwt_secret,
            "jwt_expiration_hours": self.jwt_expiration_hours,
            "public_routes": self.public_routes,
            "existing_user_entity": self.existing_user_entity,
            "extra_user_fields": [f.to_dict() for f in self.extra_user_fields]
        }


@dataclass
class ProjectConfig:
    """
    Global project configuration — produced by analyzer.py,
    consumed by generator.py.

    Attributes:
        base_package : detected or entered base Java package (e.g., com.pio.ecommerce)
        api_prefix   : REST route prefix (e.g., /api/v1)
        entities     : list of all entities described by the user
    """
    base_package: str
    api_prefix: str
    entities: list[Entity] = field(default_factory=list)
    enums: list[Enum] = field(default_factory=list)
    pom_features: PomFeatures = field(default_factory=PomFeatures)
    folder_mapping: FolderMapping = field(default_factory=FolderMapping)
    security: Optional[SecurityConfig] = None

    @property
    def package_path(self) -> str:
        """
        Converts the Java package to a folder path.
        e.g., com.pio.ecommerce → com/pio/ecommerce
        """
        return self.base_package.replace(".", "/")

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        entities = [Entity.from_dict(e) for e in data.get("entities", [])]
        enums = [Enum.from_dict(e) for e in data.get("enums", [])]
        pom_features = PomFeatures.from_dict(data.get("pom_features", {}))
        folder_mapping = FolderMapping.from_dict(data.get("folder_mapping", {}))
        
        security = None
        if "security" in data and data["security"]:
            security = SecurityConfig.from_dict(data["security"])
            
        return cls(
            base_package=data["base_package"],
            api_prefix=data.get("api_prefix", "/api/v1"),
            entities=entities,
            enums=enums,
            pom_features=pom_features,
            folder_mapping=folder_mapping,
            security=security
        )

    def to_dict(self) -> dict:
        return {
            "base_package": self.base_package,
            "api_prefix": self.api_prefix,
            "entities": [e.to_dict() for e in self.entities],
            "enums": [e.to_dict() for e in self.enums],
            "pom_features": self.pom_features.to_dict(),
            "folder_mapping": self.folder_mapping.to_dict(),
            "security": self.security.to_dict() if self.security else None
        }
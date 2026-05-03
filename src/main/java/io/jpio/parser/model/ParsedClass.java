package io.jpio.parser.model;

import java.util.ArrayList;
import java.util.List;

public class ParsedClass {
    private String name;
    private String qualifiedName;
    private String packageName;
    private String classType; // "CLASS" | "INTERFACE" | "ENUM" | "RECORD" | "ANNOTATION"
    private List<String> annotations = new ArrayList<>();
    private List<String> implementsList = new ArrayList<>();
    private List<String> extendsList = new ArrayList<>();
    private List<String> imports = new ArrayList<>();
    private List<ParsedField> fields = new ArrayList<>();
    private List<ParsedMethod> methods = new ArrayList<>();
    private boolean isAbstract;
    private boolean isPublic;
    private String filePath;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getQualifiedName() { return qualifiedName; }
    public void setQualifiedName(String qualifiedName) { this.qualifiedName = qualifiedName; }

    public String getPackageName() { return packageName; }
    public void setPackageName(String packageName) { this.packageName = packageName; }

    public String getClassType() { return classType; }
    public void setClassType(String classType) { this.classType = classType; }

    public List<String> getAnnotations() { return annotations; }
    public void setAnnotations(List<String> annotations) { this.annotations = annotations; }

    public List<String> getImplementsList() { return implementsList; }
    public void setImplementsList(List<String> implementsList) { this.implementsList = implementsList; }

    public List<String> getExtendsList() { return extendsList; }
    public void setExtendsList(List<String> extendsList) { this.extendsList = extendsList; }

    public List<String> getImports() { return imports; }
    public void setImports(List<String> imports) { this.imports = imports; }

    public List<ParsedField> getFields() { return fields; }
    public void setFields(List<ParsedField> fields) { this.fields = fields; }

    public List<ParsedMethod> getMethods() { return methods; }
    public void setMethods(List<ParsedMethod> methods) { this.methods = methods; }

    public boolean isAbstract() { return isAbstract; }
    public void setAbstract(boolean anAbstract) { isAbstract = anAbstract; }

    public boolean isPublic() { return isPublic; }
    public void setPublic(boolean aPublic) { isPublic = aPublic; }

    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }
}

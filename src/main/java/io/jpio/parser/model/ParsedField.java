package io.jpio.parser.model;

import java.util.ArrayList;
import java.util.List;

public class ParsedField {
    private String name;
    private String type;
    private String typeSimple;
    private List<String> annotations = new ArrayList<>();
    private boolean isFinal;
    private boolean isStatic;
    private String visibility;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getTypeSimple() { return typeSimple; }
    public void setTypeSimple(String typeSimple) { this.typeSimple = typeSimple; }

    public List<String> getAnnotations() { return annotations; }
    public void setAnnotations(List<String> annotations) { this.annotations = annotations; }

    public boolean isFinal() { return isFinal; }
    public void setFinal(boolean aFinal) { isFinal = aFinal; }

    public boolean isStatic() { return isStatic; }
    public void setStatic(boolean aStatic) { isStatic = aStatic; }

    public String getVisibility() { return visibility; }
    public void setVisibility(String visibility) { this.visibility = visibility; }
}

package io.jpio.parser.model;

import java.util.ArrayList;
import java.util.List;

public class ParsedMethod {
    private String name;
    private String returnType;
    private String returnTypeSimple;
    private List<ParsedParameter> parameters = new ArrayList<>();
    private List<String> annotations = new ArrayList<>();
    private List<String> throwsList = new ArrayList<>();
    private boolean isPublic;
    private boolean isStatic;
    private boolean isOverride;
    private String visibility;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getReturnType() { return returnType; }
    public void setReturnType(String returnType) { this.returnType = returnType; }

    public String getReturnTypeSimple() { return returnTypeSimple; }
    public void setReturnTypeSimple(String returnTypeSimple) { this.returnTypeSimple = returnTypeSimple; }

    public List<ParsedParameter> getParameters() { return parameters; }
    public void setParameters(List<ParsedParameter> parameters) { this.parameters = parameters; }

    public List<String> getAnnotations() { return annotations; }
    public void setAnnotations(List<String> annotations) { this.annotations = annotations; }

    public List<String> getThrowsList() { return throwsList; }
    public void setThrowsList(List<String> throwsList) { this.throwsList = throwsList; }

    public boolean isPublic() { return isPublic; }
    public void setPublic(boolean aPublic) { isPublic = aPublic; }

    public boolean isStatic() { return isStatic; }
    public void setStatic(boolean aStatic) { isStatic = aStatic; }

    public boolean isOverride() { return isOverride; }
    public void setOverride(boolean override) { isOverride = override; }

    public String getVisibility() { return visibility; }
    public void setVisibility(String visibility) { this.visibility = visibility; }
}

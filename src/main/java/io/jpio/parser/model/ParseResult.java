package io.jpio.parser.model;

import java.util.ArrayList;
import java.util.List;

public class ParseResult {
    private List<ParsedClass> classes = new ArrayList<>();
    private int totalFiles;
    private int totalClasses;
    private List<String> errors = new ArrayList<>();
    private String parserVersion = "1.0.0";
    private String javaVersion;

    public List<ParsedClass> getClasses() { return classes; }
    public void setClasses(List<ParsedClass> classes) { this.classes = classes; }

    public int getTotalFiles() { return totalFiles; }
    public void setTotalFiles(int totalFiles) { this.totalFiles = totalFiles; }

    public int getTotalClasses() { return totalClasses; }
    public void setTotalClasses(int totalClasses) { this.totalClasses = totalClasses; }

    public List<String> getErrors() { return errors; }
    public void setErrors(List<String> errors) { this.errors = errors; }

    public String getParserVersion() { return parserVersion; }
    public void setParserVersion(String parserVersion) { this.parserVersion = parserVersion; }

    public String getJavaVersion() { return javaVersion; }
    public void setJavaVersion(String javaVersion) { this.javaVersion = javaVersion; }
}

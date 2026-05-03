package io.jpio.parser;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.Modifier;
import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.github.javaparser.symbolsolver.JavaSymbolSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.JavaParserTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.ReflectionTypeSolver;
import io.jpio.parser.model.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class JavaSourceParser {

    public static ParseResult parse(Path sourcePath) {
        ParseResult result = new ParseResult();
        result.setJavaVersion(System.getProperty("java.version"));

        // 1. Configure SymbolSolver
        CombinedTypeSolver solver = new CombinedTypeSolver();
        solver.add(new ReflectionTypeSolver());
        try {
            solver.add(new JavaParserTypeSolver(sourcePath));
        } catch (Exception e) {
            System.err.println("WARN: Could not initialize JavaParserTypeSolver for " + sourcePath + ": " + e.getMessage());
        }
        StaticJavaParser.getParserConfiguration()
                .setSymbolResolver(new JavaSymbolSolver(solver));

        // 2. Scan recursively for .java files
        List<Path> javaFiles = new ArrayList<>();
        try (Stream<Path> walk = Files.walk(sourcePath)) {
            javaFiles = walk.filter(p -> p.toString().endsWith(".java"))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            result.getErrors().add("Could not scan directory: " + e.getMessage());
            return result;
        }

        result.setTotalFiles(javaFiles.size());

        // 3. Parse each file
        for (Path file : javaFiles) {
            try {
                CompilationUnit cu = StaticJavaParser.parse(file);
                String relativePath = sourcePath.relativize(file).toString();
                
                List<String> fileImports = cu.getImports().stream()
                        .map(ImportDeclaration::getNameAsString)
                        .collect(Collectors.toList());

                for (TypeDeclaration<?> type : cu.findAll(TypeDeclaration.class)) {
                    ParsedClass pc = parseType(type, relativePath, fileImports);
                    result.getClasses().add(pc);
                }
            } catch (Exception e) {
                result.getErrors().add(file.toString() + ": " + e.getMessage());
            }
        }

        result.setTotalClasses(result.getClasses().size());
        return result;
    }

    private static ParsedClass parseType(TypeDeclaration<?> type, String relativePath, List<String> fileImports) {
        ParsedClass pc = new ParsedClass();
        pc.setName(type.getNameAsString());
        pc.setQualifiedName(type.getFullyQualifiedName().orElse(type.getNameAsString()));
        pc.setPackageName(pc.getQualifiedName().contains(".") ? 
                pc.getQualifiedName().substring(0, pc.getQualifiedName().lastIndexOf(".")) : "");
        
        pc.setClassType(determineClassType(type));
        pc.setAnnotations(extractAnnotations(type));
        pc.setImports(fileImports);
        pc.setFilePath(relativePath);
        pc.setPublic(type.isPublic());
        pc.setAbstract(type.getModifiers().stream().anyMatch(m -> m.getKeyword() == Modifier.Keyword.ABSTRACT));

        if (type instanceof ClassOrInterfaceDeclaration) {
            ClassOrInterfaceDeclaration cid = (ClassOrInterfaceDeclaration) type;
            pc.setImplementsList(cid.getImplementedTypes().stream()
                    .map(ClassOrInterfaceType::getNameAsString)
                    .collect(Collectors.toList()));
            pc.setExtendsList(cid.getExtendedTypes().stream()
                    .map(ClassOrInterfaceType::getNameAsString)
                    .collect(Collectors.toList()));
        }

        // Fields
        for (FieldDeclaration field : type.getFields()) {
            for (VariableDeclarator var : field.getVariables()) {
                ParsedField pf = new ParsedField();
                pf.setName(var.getNameAsString());
                pf.setType(var.getTypeAsString());
                pf.setTypeSimple(stripGenerics(var.getTypeAsString()));
                pf.setAnnotations(extractAnnotations(field));
                pf.setFinal(field.isFinal());
                pf.setStatic(field.isStatic());
                String visibility = field.getAccessSpecifier().asString();
                pf.setVisibility(visibility.isEmpty() ? "package" : visibility);
                pc.getFields().add(pf);
            }
        }

        // Methods
        for (MethodDeclaration method : type.getMethods()) {
            ParsedMethod pm = new ParsedMethod();
            pm.setName(method.getNameAsString());
            pm.setReturnType(method.getTypeAsString());
            pm.setReturnTypeSimple(stripGenerics(method.getTypeAsString()));
            pm.setAnnotations(extractAnnotations(method));
            pm.setThrowsList(method.getThrownExceptions().stream()
                    .map(com.github.javaparser.ast.type.ReferenceType::asString)
                    .collect(Collectors.toList()));
            pm.setPublic(method.isPublic());
            pm.setStatic(method.isStatic());
            pm.setOverride(method.getAnnotationByClass(Override.class).isPresent() || 
                           pm.getAnnotations().contains("Override"));
            String visibility = method.getAccessSpecifier().asString();
            pm.setVisibility(visibility.isEmpty() ? "package" : visibility);

            for (Parameter param : method.getParameters()) {
                pm.getParameters().add(new ParsedParameter(param.getNameAsString(), param.getTypeAsString()));
            }
            pc.getMethods().add(pm);
        }

        // Special handling for Records
        if (type instanceof RecordDeclaration) {
            RecordDeclaration rd = (RecordDeclaration) type;
            for (Parameter param : rd.getParameters()) {
                ParsedField pf = new ParsedField();
                pf.setName(param.getNameAsString());
                pf.setType(param.getTypeAsString());
                pf.setTypeSimple(stripGenerics(param.getTypeAsString()));
                pf.setAnnotations(extractAnnotations(param));
                pf.setFinal(true);
                pf.setStatic(false);
                pf.setVisibility("private");
                pc.getFields().add(pf);
            }
        }

        return pc;
    }

    private static String determineClassType(TypeDeclaration<?> type) {
        if (type instanceof ClassOrInterfaceDeclaration) {
            return ((ClassOrInterfaceDeclaration) type).isInterface() ? "INTERFACE" : "CLASS";
        } else if (type instanceof EnumDeclaration) {
            return "ENUM";
        } else if (type instanceof AnnotationDeclaration) {
            return "ANNOTATION";
        } else if (type instanceof RecordDeclaration) {
            return "RECORD";
        }
        return "CLASS";
    }

    private static List<String> extractAnnotations(com.github.javaparser.ast.nodeTypes.NodeWithAnnotations<?> node) {
        return node.getAnnotations().stream()
                .map(a -> a.getNameAsString())
                .collect(Collectors.toList());
    }

    private static String stripGenerics(String type) {
        if (type.contains("<")) {
            return type.substring(0, type.indexOf("<"));
        }
        return type;
    }
}

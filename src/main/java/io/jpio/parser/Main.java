package io.jpio.parser;

import io.jpio.parser.model.ParseResult;
import io.jpio.parser.util.JsonSerializer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class Main {
    public static void main(String[] args) {
        String sourcePathStr = null;
        String outputFormat = "json";

        for (int i = 0; i < args.length; i++) {
            if ("--source".equals(args[i]) && i + 1 < args.length) {
                sourcePathStr = args[++i];
            } else if ("--output".equals(args[i]) && i + 1 < args.length) {
                outputFormat = args[++i];
            }
        }

        if (sourcePathStr == null) {
            System.err.println("ERROR: --source <path> is required and must exist");
            System.exit(1);
        }

        Path sourcePath = Paths.get(sourcePathStr);
        if (!Files.exists(sourcePath) || !Files.isDirectory(sourcePath)) {
            System.err.println("ERROR: --source <path> is required and must exist");
            System.exit(1);
        }

        try {
            ParseResult result = JavaSourceParser.parse(sourcePath);
            
            String json;
            if ("pretty".equalsIgnoreCase(outputFormat)) {
                json = JsonSerializer.toPrettyJson(result);
            } else {
                json = JsonSerializer.toJson(result);
            }

            System.out.println(json);
            System.exit(0);

        } catch (Exception e) {
            System.err.println("ERROR: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(2);
        }
    }
}

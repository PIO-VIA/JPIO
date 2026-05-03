package io.jpio.parser.util;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import io.jpio.parser.model.ParseResult;

public class JsonSerializer {
    private static final ObjectMapper compactMapper = new ObjectMapper()
            .setSerializationInclusion(JsonInclude.Include.NON_NULL)
            .disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);

    private static final ObjectMapper prettyMapper = new ObjectMapper()
            .setSerializationInclusion(JsonInclude.Include.NON_NULL)
            .disable(SerializationFeature.FAIL_ON_EMPTY_BEANS)
            .enable(SerializationFeature.INDENT_OUTPUT);

    public static String toJson(ParseResult result) throws JsonProcessingException {
        return compactMapper.writeValueAsString(result);
    }

    public static String toPrettyJson(ParseResult result) throws JsonProcessingException {
        return prettyMapper.writeValueAsString(result);
    }
}

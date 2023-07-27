package ca.concordia;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;

public class FileUtil {

    public static String read(String filename) throws IOException {
        Path path = Paths.get(filename);
        try (Stream<String> lines = Files.lines(path)) {
            return lines.collect(Collectors.joining("\n"));
        }

    }

    public static void writeJsonFile(JsonObject Json, String folder_name, String filename){

        try {
            File folder = new File(folder_name);
            if (!folder.exists()) {
                boolean mkdir_result = folder.mkdirs();
                if (!mkdir_result) {
                    throw new IOException("Output directory creation failed.");
                }
            }

            FileWriter writer = new FileWriter(folder + File.separator + filename +".json");
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            gson.toJson(Json, writer);
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    public static String findFile(Path startPath, String fileName) throws IOException {
        FileFinder finder = new FileFinder(fileName);
        Files.walkFileTree(startPath, finder);

        Path foundFile = finder.getFoundPath();
        return foundFile == null ? null : foundFile.toAbsolutePath().toString();
    }

    private static class FileFinder extends SimpleFileVisitor<Path> {
        private final PathMatcher matcher;
        private Path foundPath;

        FileFinder(String fileName) {
            matcher = FileSystems.getDefault().getPathMatcher("glob:" + fileName);
        }

        Path getFoundPath() {
            return foundPath;
        }

        @Override
        public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
            if (matcher.matches(file.getFileName())) {
                foundPath = file;
                return FileVisitResult.TERMINATE;
            }
            return FileVisitResult.CONTINUE;
        }

        @Override
        public FileVisitResult visitFileFailed(Path file, IOException exc) {
            return FileVisitResult.CONTINUE;
        }
    }
}

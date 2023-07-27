package ca.concordia;

import com.google.gson.*;
import com.google.gson.reflect.TypeToken;


import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.NoSuchFileException;
import java.nio.file.Paths;
import java.util.*;

import java.lang.reflect.Type;

import static ca.concordia.FileUtil.findFile;
import static java.lang.Math.floor;


public class Application {

    static EnvPropertiesLoader envPropertiesLoader = new EnvPropertiesLoader();
    static String basePath = envPropertiesLoader.getSecret("base_path");
    static String data_file_path = Paths.get(basePath, "DeepDiveBugReportsWithLogs", "data", "bug_reports_with_stack_traces_details.json").toString();


    static Map<String, String> projectsList = new HashMap<>() {{
        put("Lang", Paths.get(basePath, "defects4j", "project_repos", "commons-lang.git").toString());
        put("Math", Paths.get(basePath, "defects4j", "project_repos", "commons-math.git").toString());
        put("Cli", Paths.get(basePath, "open_source_repos_being_studied", "commons-cli").toString());
        put("Closure", Paths.get(basePath, "open_source_repos_being_studied", "closure-compiler").toString());
        put("Codec", Paths.get(basePath, "open_source_repos_being_studied", "commons-codec").toString());
        put("Collections", Paths.get(basePath, "open_source_repos_being_studied", "commons-collections").toString());
        put("Compress", Paths.get(basePath, "open_source_repos_being_studied", "commons-compress").toString());
        put("Csv", Paths.get(basePath, "open_source_repos_being_studied", "commons-csv").toString());
        put("Gson", Paths.get(basePath, "open_source_repos_being_studied", "gson").toString());
        put("JacksonCore", Paths.get(basePath, "open_source_repos_being_studied", "jackson-core").toString());
        put("JacksonDatabind", Paths.get(basePath, "open_source_repos_being_studied", "jackson-databind").toString());
        put("Jsoup", Paths.get(basePath, "open_source_repos_being_studied", "jsoup").toString());
        put("JxPath", Paths.get(basePath, "open_source_repos_being_studied", "commons-jxpath").toString());
        put("Mockito", Paths.get(basePath, "open_source_repos_being_studied", "mockito").toString());
        put("Time", Paths.get(basePath, "open_source_repos_being_studied", "joda-time").toString());
        put("fastjson", Paths.get(basePath, "open_source_repos_being_studied", "fastjson").toString());
        put("junit4", Paths.get(basePath, "open_source_repos_being_studied", "junit4").toString());
    }};


    public static void main(String[] args){

        Gson gson = new GsonBuilder().create();




        try (FileReader reader = new FileReader(data_file_path)) {
            // Convert JSON to Java object
            Type type = new TypeToken<Map<String, Map<String, Object>>>() {}.getType();
            Map<String, Map<String, Object>> data = gson.fromJson(reader, type);

            // Access data from the object
            for (String project : data.keySet()) {
                if (project.equals("Lang") || project.equals("Math")){ //Skipping them for now since I can not run git checkout
                    System.out.println("Skipping the project "+ project);
                    continue;
                }
                System.out.println(project);
                String path_to_repo = projectsList.get(project);
                Map<String, Object> bugs = data.get(project);
                for (String bugID : bugs.keySet()) {
                    System.out.println(bugID);

                    Map<String, Object> bug = (Map<String, Object>) bugs.get(bugID);
                    String buggyCommit = (String) bug.get("buggy_commit");
                    String bugfixCommit = (String) bug.get("bugfix_commit");

                    // Checking the code
                    List<MethodData> addedLinesMethods;
                    List<MethodData> deletedLinesMethods;

                    Map<String,Map<String, Map<String, Integer>>> buggyMethods = new HashMap<>();
                    Map<String,Map<String, Map<String, Integer>>> newMethods = new HashMap<>();
                    Map<String, Map<String, Object>> modifiedCode = (Map<String, Map<String, Object>>) bug.get("modified_code");
                    for (String filePath : modifiedCode.keySet()) {
                        String filePathFixed = filePath;
                        if (filePath.startsWith("b/")) {
                            filePathFixed = filePath.substring(2);
                        }
                        String absolute_file_path = Paths.get(path_to_repo , filePath).toString();
                        Map<String, Object> fileInfo = modifiedCode.get(filePath);
                        List<Double> deletedLinesDouble = (List<Double>) fileInfo.get("deleted_lines");
                        deletedLinesMethods = get_touched_methods(buggyCommit, path_to_repo,deletedLinesDouble, absolute_file_path, filePathFixed, false);
                        List<Double> addedLinesDouble = (List<Double>) fileInfo.get("added_lines");
                        addedLinesMethods = get_touched_methods(bugfixCommit, path_to_repo,addedLinesDouble, absolute_file_path, filePathFixed, false);

                        for (MethodData md : deletedLinesMethods){
                            String fileName = filePathFixed;
                            String methodName = md.getMethodName();
                            buggyMethods= addNewMethod(buggyMethods, methodName, fileName, md);
                        }
                        List<Integer> addedLines = convertDoubleListIntoIntegers(addedLinesDouble);
                        // If a method was added in the bugfix commit, it is not a buggy method
                        GitHelper.checkoutCommit(path_to_repo, bugfixCommit);
                        for (MethodData md : addedLinesMethods){
                            String fileName = filePathFixed;
                            String methodName = md.getMethodName();
                            int aproxLineNumber = (int) floor((md.getEndLine() - md.getStartLine()) / 2);
                            GitHelper.checkoutCommit(path_to_repo, buggyCommit);
                            MethodData newMd = null;
                            try {
                                newMd = MethodFinderFromName.findMethodLines(absolute_file_path, aproxLineNumber, methodName);
                            } catch (NoSuchFileException exception){
                                // newMethod
                            }
                            GitHelper.checkoutCommit(path_to_repo, bugfixCommit);
                            if (newMd != null && !deletedLinesMethods.contains(newMd)){
                                boolean isNewMethod = CheckIfMethodWasCreatedFinder.checkIfMethodWasCreated(absolute_file_path, addedLines, methodName );
                                if (isNewMethod){
                                    newMethods= addNewMethod(newMethods, methodName, fileName, md);
                                } else{
                                    buggyMethods= addNewMethod(buggyMethods, methodName, fileName, newMd);
                                }
                            }
                        }
                    }

                    // Checking the tests
                    List<MethodData> addedLinesTests;
                    List<MethodData> deletedLinesTests;

                    Map<String,Map<String, Map<String, Integer>>> updatedTests = new HashMap<>();
                    Map<String,Map<String, Map<String, Integer>>> newTests = new HashMap<>();
                    Map<String, Map<String, Object>> modifiedTests = new HashMap<>();
                    if (bug.get("modified_tests") != null){
                        modifiedTests = (Map<String, Map<String, Object>>) bug.get("modified_tests");
                    }
                    for (String filePath : modifiedTests.keySet()) {
                        String filePathFixed = filePath;
                        if (filePath.startsWith("b/")) {
                            filePathFixed = filePath.substring(2);
                        }
                        String absolute_file_path = Paths.get(path_to_repo , filePath).toString();
                        Map<String, Object> fileInfo = modifiedTests.get(filePath);
                        String previousFilePath = "";
                        if(fileInfo.containsKey("previous_filename")) {
                            previousFilePath = (String) fileInfo.get("previous_filename");
                            if (previousFilePath.startsWith("b/")) {
                                previousFilePath = previousFilePath.substring(2);
                            }
                        }
                        List<Double> deletedLinesDouble = (List<Double>) fileInfo.get("deleted_lines");
                        String filePathForDeteled = filePathFixed;
                        String absoluteFilePathForDeteled = absolute_file_path;
                        if (previousFilePath!=""){
                            filePathForDeteled = previousFilePath;
                            absoluteFilePathForDeteled = Paths.get(path_to_repo , previousFilePath).toString();
                        }
                        deletedLinesTests = get_touched_methods(buggyCommit, path_to_repo, deletedLinesDouble, absoluteFilePathForDeteled, filePathForDeteled, true);
                        List<Double> addedLinesDouble = (List<Double>) fileInfo.get("added_lines");
                        addedLinesTests = get_touched_methods(bugfixCommit, path_to_repo, addedLinesDouble, absolute_file_path, filePathFixed, true);

                        for (MethodData md : deletedLinesTests){
                            String fileName = filePathFixed;
                            String testName = md.getMethodName();
                            updatedTests= addNewMethod(updatedTests, testName, fileName, md);
                        }
                        List<Integer> addedLines = convertDoubleListIntoIntegers(addedLinesDouble);
                        // If a method was added in the bugfix commit, it is not a buggy method
                        GitHelper.checkoutCommit(path_to_repo, bugfixCommit);
                        for (MethodData md : addedLinesTests) {
                            if (!deletedLinesTests.contains(md)) {
                                String fileName = filePathFixed;
                                String testName = md.getMethodName();
                                boolean newTest = CheckIfMethodWasCreatedFinder.checkIfMethodWasCreated(absolute_file_path, addedLines, testName);
                                if (newTest) {
                                    newTests= addNewMethod(newTests, testName, fileName, md);
                                } else {
                                    updatedTests= addNewMethod(updatedTests, testName, fileName, md);
                                }
                            }
                        }
                    }
                    List<String> st_files = (List<String>) bug.get("stack_trace_files");
                    List<String> st_methods = (List<String>) bug.get("stack_trace_methods");
                    List<String> st_lines = (List<String>) bug.get("stack_trace_lines");

                    Map<String,Map<String, Map<String, Integer>>> st_methods_details = new HashMap<>();
                    for (int i = 0; i < st_files.size(); i++) {
                        String fileName = st_files.get(i);
                        String method = st_methods.get(i);
                        String[] parts = method.split("\\.");
                        String methodName = parts[parts.length - 1].split("\\$")[0];
                        String line = st_lines.get(i);
                        if (line == "-1"){
                            continue;
                        }
                        GitHelper.checkoutCommit(path_to_repo, buggyCommit);
                        String absolute_st_file_path = null;
                        try {
                            absolute_st_file_path = findFile(Paths.get(path_to_repo), fileName);
                        } catch (IOException | NullPointerException e) {
                            // Not an internal file
                        }
                        MethodData md = null;
                        if (absolute_st_file_path != null) {
                            try {
                                md = MethodFinderFromName.findMethodLines(absolute_st_file_path, Integer.parseInt(line), methodName);
                            } catch (NoSuchFileException exception) {
                                // newMethod
                            }
                        }
                        if (md!=null){
                            st_methods_details= addNewMethod(st_methods_details, methodName, absolute_st_file_path, md);
                        }
                    }

                    bug.put("buggyMethods", buggyMethods);
                    bug.put("newMethods", newMethods);
                    bug.put("updatedTests", updatedTests);
                    bug.put("newTests", newTests);
                    bug.put("stackTraceMethodsDetails", st_methods_details);
                }
            }
            Gson gsonPretty = new GsonBuilder().setPrettyPrinting().create();
            String updatedJson = gsonPretty.toJson(data);

            // Write the updated JSON string to the file
            try (FileWriter writer = new FileWriter(data_file_path)) {
                writer.write(updatedJson);
                System.out.println("Json file data/merged_data_production_bug_reports.json update with the extract information: buggyMethods, newMethods, updatedTests and newTests");
            } catch (IOException e) {
                e.printStackTrace();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }


    }

    public static List<MethodData> get_touched_methods(String commit, String pathToRepo, List<Double> linesDouble, String absoluteFilePath, String filePath, boolean isTest) throws IOException {
        List<MethodData> touchedMethods = new ArrayList<>();
        GitHelper.checkoutCommit(pathToRepo, commit);
        List<Integer> lines = convertDoubleListIntoIntegers(linesDouble);
        if (linesDouble != null) {
            for (Integer line: lines){
                String methodName = MethodFinderFromLine.findMethodName(absoluteFilePath, line);
                MethodData methodData = MethodFinderFromLine.getmethodData();
                if (methodName != null && !touchedMethods.contains(filePath+ " - " +methodName)) {
                    touchedMethods.add(methodData);
                }
            }
        }
        return touchedMethods;
    }
    public static boolean contains(List<MethodData> methodDataList, MethodData target) {
        return methodDataList.contains(target);
    }

    public static List<Integer> convertDoubleListIntoIntegers(List<Double> linesDouble) {
        List<Integer> lines = new ArrayList<>();
        if (linesDouble != null) {
            for (Double d : linesDouble) {
                lines.add(d.intValue());
            }
        }
        return lines;
    }

    public static Map<String, Map<String, Map<String, Integer>>> addNewMethod(Map<String, Map<String, Map<String, Integer>>> methodsObject, String methodName, String fileName, MethodData methodData){
        if (!methodsObject.keySet().contains(fileName)) {
            methodsObject.put(fileName, new HashMap<>());
        }
        int startLine = methodData.getStartLine();
        int endLine = methodData.getEndLine();
        Map<String, Integer> methodInfo = new HashMap<>();
        methodInfo.put("startLine",startLine);
        methodInfo.put("endLine",endLine);
        Map<String, Map<String, Integer>> fileMethods = methodsObject.get(fileName);
        fileMethods.put(methodName, methodInfo);
        methodsObject.put(fileName, fileMethods);
        return methodsObject;
    }

}
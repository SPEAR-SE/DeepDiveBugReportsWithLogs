package ca.concordia;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;

public class GitHelper {

    public static void checkoutCommit(String projectPath, String commitHash) {
        try {
            ProcessBuilder processBuilder = new ProcessBuilder();
            processBuilder.directory(new File(projectPath));

            // Execute 'git checkout commit_hash'
            processBuilder.command("git", "checkout", commitHash);
            Process process = processBuilder.start();
            int exitCode = process.waitFor();

            if (exitCode != 0) {
                System.err.println("Error checking out commit " + commitHash);
                printErrorOutput(process);
            }
        } catch (IOException | InterruptedException e) {
            System.err.println("Error executing git command: " + e.getMessage());
        }
    }

    private static void printErrorOutput(Process process) {
        try (BufferedReader errorOutput = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
            String line;
            while ((line = errorOutput.readLine()) != null) {
                System.err.println(line);
            }
        } catch (IOException e) {
            System.err.println("Error reading error output: " + e.getMessage());
        }
    }

}

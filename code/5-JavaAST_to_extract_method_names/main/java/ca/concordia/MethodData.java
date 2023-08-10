package ca.concordia;

import java.util.Objects;

public class MethodData {
    private String methodName;
    private int startLine;
    private int endLine;

    private String path;

    public MethodData(String methodName, int startLine, int endLine, String path) {
        this.methodName = methodName;
        this.startLine = startLine;
        this.endLine = endLine;
        this.path = path;
    }


    public String getMethodName() {
        return methodName;
    }
    public int getStartLine() {
        return startLine;
    }
    public int getEndLine() {
        return endLine;
    }

    public String getPath() {
        return path;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        MethodData that = (MethodData) o;
        return startLine == that.startLine &&
                endLine == that.endLine &&
                Objects.equals(methodName, that.methodName);
    }

    @Override
    public int hashCode() {
        return Objects.hash(methodName, startLine, endLine);
    }
}

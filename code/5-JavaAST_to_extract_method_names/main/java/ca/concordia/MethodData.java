package ca.concordia;

import java.util.Objects;

public class MethodData {
    private String methodName;
    private int startLine;
    private int endLine;

    public MethodData(String methodName, int startLine, int endLine) {
        this.methodName = methodName;
        this.startLine = startLine;
        this.endLine = endLine;
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

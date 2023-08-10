package ca.concordia;

import org.eclipse.jdt.core.dom.*;


public class FindMethodFromLineVisitor extends ASTVisitor  {
    private final int lineNumber;
    private String methodName;
    
    private String path;
    private MethodData methodData;
    protected final CompilationUnit compilationUnit;

    public FindMethodFromLineVisitor(CompilationUnit compilationUnit, int lineNumber, String path) {
        this.compilationUnit = compilationUnit;
        this.lineNumber = lineNumber;
        this.path = path;
    }

    @Override
    public boolean visit(MethodDeclaration node) {
        int startPosition = node.getStartPosition();
        int endPosition = startPosition + node.getLength();
        int startLine = compilationUnit.getLineNumber(startPosition);
        int endLine = compilationUnit.getLineNumber(endPosition);

        if (lineNumber >= startLine && lineNumber <= endLine) {
            methodName = node.getName().toString();
            methodData = new MethodData(methodName, startLine, endLine, path);
            methodData = new MethodData(methodName, startLine, endLine, path);
        }

        return super.visit(node);
    }

    public String getMethodName() {
        if (methodData != null) {
            return methodData.getMethodName();
        }
        return null;
    }
    public MethodData getmethodData() {
        return methodData;
    }


}
package ca.concordia;

import org.eclipse.jdt.core.dom.ASTVisitor;
import org.eclipse.jdt.core.dom.CompilationUnit;
import org.eclipse.jdt.core.dom.MethodDeclaration;


public class FindMethodFromNameVisitor extends ASTVisitor  {
    private String methodName;

    private String path;
    private MethodData methodData;

    private int aproxLineNumber;

    protected final CompilationUnit compilationUnit;

    public FindMethodFromNameVisitor(CompilationUnit compilationUnit, String methodName, int aproxLineNumber, String path) {
        this.compilationUnit = compilationUnit;
        this.methodName = methodName;
        this.aproxLineNumber = aproxLineNumber;
        this.path = path;
    }

    @Override
    public boolean visit(MethodDeclaration node) {
        int startPosition = node.getStartPosition();
        int endPosition = startPosition + node.getLength();
        int startLine = compilationUnit.getLineNumber(startPosition);
        int endLine = compilationUnit.getLineNumber(endPosition);

        String nodeMethodName = node.getName().toString();
        if (methodName.equals(nodeMethodName)) {
            if (methodData != null){
                if (distFromAproxLine(aproxLineNumber, startLine, endLine) < distFromAproxLine(aproxLineNumber, methodData.getStartLine(), methodData.getEndLine())){
                    methodData = new MethodData(nodeMethodName, startLine, endLine, path);
                }
            } else{
                methodData = new MethodData(nodeMethodName, startLine, endLine, path);
            }
        }
        return super.visit(node);
    }

    public String getMethodName() {
        return methodName;
    }
    public MethodData getmethodData() {
        return methodData;
    }

    public int distFromAproxLine(int aproxLineNumber, int startLine, int endLine){
        if(aproxLineNumber<startLine){
            return startLine - aproxLineNumber;
        } else if (startLine <= aproxLineNumber && aproxLineNumber <= endLine){
            return 0;
        } else{
            return aproxLineNumber - endLine;
        }
    }


}
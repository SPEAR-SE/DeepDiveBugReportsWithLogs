package ca.concordia;

import org.eclipse.jdt.core.dom.ASTVisitor;
import org.eclipse.jdt.core.dom.CompilationUnit;
import org.eclipse.jdt.core.dom.MethodDeclaration;

import java.util.List;


public class CheckIfMethodWasCreatedVisitor extends ASTVisitor  {
    private final List<Integer> addedLines;
    private final String methodName;

    private boolean isANewMethod = false;
    protected final CompilationUnit compilationUnit;
    public CheckIfMethodWasCreatedVisitor(CompilationUnit compilationUnit, List<Integer> addedLines, String methodName) {
        this.compilationUnit = compilationUnit;
        this.addedLines = addedLines;
        this.methodName = methodName;
    }

    @Override
    public boolean visit(MethodDeclaration node) {
        String currentMethodName = node.getName().toString();
        if (currentMethodName.equals(this.methodName)){
            int startPosition = node.getStartPosition();
            int endPosition = startPosition + node.getLength();
            int startLine = compilationUnit.getLineNumber(startPosition);
            int endLine = compilationUnit.getLineNumber(endPosition);

            isANewMethod = true;
            for (int i = startLine; i <= endLine; i++) {
                if (!addedLines.contains(i)) {
                    isANewMethod = false;
                    return true;
                }
            }

        }
        return super.visit(node);
    }

    public Boolean getIsANewMethod() {
        return isANewMethod;
    }

}

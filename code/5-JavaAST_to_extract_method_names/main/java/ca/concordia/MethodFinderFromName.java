package ca.concordia;

import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.AST;
import org.eclipse.jdt.core.dom.ASTParser;
import org.eclipse.jdt.core.dom.CompilationUnit;

import java.io.IOException;
import java.util.Map;

class MethodFinderFromName {

  private static MethodData methodData;

  public static MethodData findMethodLines(String filename, int aproxlineNumber, String methodName) throws IOException {

    String source = FileUtil.read(filename);

    ASTParser parser = ASTParser.newParser(AST.getJLSLatest());

    Map<String, String> options = JavaCore.getOptions();
    JavaCore.setComplianceOptions(JavaCore.VERSION_11, options);
    parser.setCompilerOptions(options);

    parser.setSource(source.toCharArray());
    CompilationUnit compilationUnit = (CompilationUnit) parser.createAST(null);

    FindMethodFromNameVisitor visitor = new FindMethodFromNameVisitor(compilationUnit, methodName, aproxlineNumber);
    compilationUnit.accept(visitor);

    methodData = visitor.getmethodData();

    return methodData;
  }

  public static MethodData getmethodData() {
    return methodData;
  }
}
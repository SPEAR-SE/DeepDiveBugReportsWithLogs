package ca.concordia;

import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.AST;
import org.eclipse.jdt.core.dom.ASTParser;
import org.eclipse.jdt.core.dom.CompilationUnit;

import java.io.IOException;
import java.util.List;
import java.util.Map;

class CheckIfMethodWasCreatedFinder {

  public static boolean checkIfMethodWasCreated(String filename, List<Integer> addedLines, String methodName) throws IOException {

    FileResult result =FileUtil.read(filename);
    String source = result.content;

    ASTParser parser = ASTParser.newParser(AST.getJLSLatest());

    Map<String, String> options = JavaCore.getOptions();
    JavaCore.setComplianceOptions(JavaCore.VERSION_11, options);
    parser.setCompilerOptions(options);

    parser.setSource(source.toCharArray());
    CompilationUnit compilationUnit = (CompilationUnit) parser.createAST(null);

    CheckIfMethodWasCreatedVisitor visitor = new CheckIfMethodWasCreatedVisitor(compilationUnit, addedLines, methodName);
    compilationUnit.accept(visitor);


    return visitor.getIsANewMethod();
  }
}
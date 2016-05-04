package pimlico.caevo;

import caevo.SieveDocument;
import caevo.SieveDocuments;
import caevo.util.TreeOperator;
import caevo.util.WordNet;
import com.google.common.base.Joiner;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.trees.*;
import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import org.jdom.output.Format;
import org.jdom.output.XMLOutputter;
import pimlico.core.Py4JGatewayStarter;

import java.util.ArrayList;
import java.util.List;

/**
 * Wrapper around Nate Chambers' Caevo tool for event extraction to provide access to it via Py4J for Pimlico module.
 * Based closely on Caevo's Main class.
 */
public class CaevoGateway {
    public static WordNet wordnet;

    boolean debug = true;
    String seivePath;

    private final TreebankLanguagePack tlp;
    private final GrammaticalStructureFactory gsf;
    private final TreeFactory tf;
    private final Main main;
    private final XMLOutputter xout;

    public CaevoGateway(String seivePath) {
        this(seivePath, true);
    }

    public CaevoGateway(String sievePath, boolean debug) {
        this.debug = debug;
        xout = new XMLOutputter(Format.getPrettyFormat());

        // Initialize the dependency rulebase.
        tlp = new PennTreebankLanguagePack();
        gsf = tlp.grammaticalStructureFactory();
        tf = new LabeledScoredTreeFactory();

        // The sieve list is loaded according to this system property: override it to set the file it will be loaded from
        System.setProperty("sieves", sievePath);

        // Load a Caevo Main to do all the work
        main = new Main(new String[] {});
    }

    public String markupParsedDocument(String docName, List<String> sentences) {
        // Read in trees and produce deps, adding all to the doc's annotations
        SieveDocument doc = lexParsedToDeps(docName, sentences);
        SieveDocuments docs = new SieveDocuments();
        docs.addDocument(doc);

        // Annotate events and timexes on the doc
        main.markupAll(docs);
        main.runSieves(docs);

        return xout.outputString(docs.getDocuments().get(0).toXML());
    }

    private SieveDocument lexParsedToDeps(String docName, List<String> stringParses) {
        SieveDocument doc = new SieveDocument(docName);
        Joiner joiner = Joiner.on(' ');

        for( String strParse : stringParses ) {
            // Get deps, create infofile sentence.
            Tree parseTree = TreeOperator.stringToTree(strParse, tf);
            String strDeps = lexParseToDeps(parseTree, gsf);

            List<String> tokens = new ArrayList<String>();
            if( parseTree != null && parseTree.size() > 1 )
                tokens = TreeOperator.stringLeavesFromTree(parseTree);

            List<CoreLabel> cls = new ArrayList<CoreLabel>();
            for( String token : tokens ) {
                CoreLabel label = new CoreLabel();
                label.set(CoreAnnotations.BeforeAnnotation.class, "");
                label.set(CoreAnnotations.OriginalTextAnnotation.class, token);
                label.set(CoreAnnotations.AfterAnnotation.class, " "); // put a space after every token...
                cls.add(label);
            }

            if( cls.size() > 1 )
                cls.get(cls.size()-1).set(CoreAnnotations.AfterAnnotation.class, "\n\n"); // new lines after each sentence

            doc.addSentence(joiner.join(tokens), cls, strParse, strDeps, null, null);
        }

        return doc;
    }

    /**
     * DEP PARSE the sentence - CAUTION: DESTRUCTIVE to parse tree
     */
    private static String lexParseToDeps(Tree lexTree, GrammaticalStructureFactory gsf) {
        String depString = "";
        if( lexTree != null && lexTree.size() > 1 ) {
            try {
                GrammaticalStructure gs = gsf.newGrammaticalStructure(lexTree);
                if( gs != null ) {
                    List<TypedDependency> localdeps = gs.typedDependenciesCCprocessed(true);
                    if( localdeps != null )
                        for( TypedDependency dep : localdeps )
                            depString += dep + "\n";
                }
            } catch( Exception ex ) {
                System.out.println("ERROR: dependency tree creation failed...");
                ex.printStackTrace();
                System.exit(-1);
            }
        }
        return depString;
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("CAEVO Py4J gateway");
        argParser.description("Run CAEVO, providing access to it via Py4J");
        argParser.addArgument("seive_path").help("Path to the seive specification");
        argParser.addArgument("--port").type(Integer.class).help("Specify a port for gateway server to run on").setDefault(0);
        argParser.addArgument("--python-port").type(Integer.class).help("Specify a port for gateway server to use " +
                "to response to Python").setDefault(0);

        Namespace opts = null;
        try {
            opts = argParser.parseArgs(args);
        } catch (ArgumentParserException e) {
            System.err.println("Error in command-line arguments: " + e);
            System.exit(1);
        }

        try {
            // Load the gateway instance
            CaevoGateway entryPoint = new CaevoGateway(opts.getString("seive_path"));
            // Create a gateway server, using this as an entry point
            Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"), "PORT: ");
        } catch (Exception e) {
            System.err.println("Error starting up Caevo gateway");
            e.printStackTrace();
            System.exit(1);
        }
    }
}

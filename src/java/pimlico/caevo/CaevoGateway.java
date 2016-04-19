package pimlico.caevo;

import caevo.*;
import caevo.sieves.Sieve;
import caevo.tlink.TLink;
import caevo.tlink.TimeTimeLink;
import caevo.util.DCTHeursitics;
import caevo.util.SieveStats;
import caevo.util.WordNet;
import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import org.jdom.Document;
import org.jdom.output.Format;
import org.jdom.output.XMLOutputter;
import pimlico.core.Py4JGatewayStarter;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

/**
 * Wrapper around Nate Chambers' Caevo tool for event extraction to provide access to it via Py4J for Pimlico module.
 * Based closely on Caevo's Main class.
 */
public class CaevoGateway {
    private TextEventClassifier eventClassifier;
    private TimexClassifier timexClassifier;
    public static WordNet wordnet;

    Closure closure;
    boolean debug = true;
    boolean useClosure = true;
    String dctHeuristic = "none";
    String seivePath;

    // List the sieve class names in your desired order.
    private String[] sieveClasses;


    public CaevoGateway(String seivePath) {
        this(seivePath, true);
    }

    public CaevoGateway(String seivePath, boolean debug) {
        this.debug = debug;
        this.seivePath = seivePath;
        init();
    }

    private void init() {
        // Initialize the transitive closure code.
        try {
            closure = new Closure();
        } catch( IOException ex ) {
            System.out.println("ERROR: couldn't load Closure utility.");
            ex.printStackTrace();
            System.exit(1);
        }

        // Load WordNet for any and all sieves.
        wordnet = new WordNet();

        // Load the sieve list.
        sieveClasses = loadSieveList();
    }

    private String[] loadSieveList() {
        String filename = seivePath;
        if( filename == null ) filename = "default.sieves";

        System.out.println("Reading sieve list from: " + filename);

        List<String> sieveNames = new ArrayList<String>();
        try {
            BufferedReader reader = new BufferedReader(new FileReader(new File(filename)));
            String line;
            while( (line = reader.readLine()) != null ) {
                if( !line.matches("^\\s*$") && !line.matches("^\\s*//.*$") ) {
                    // Remove trailing comments if they exist.
                    if(line.contains("//"))
                        line = line.substring(0, line.indexOf("//"));
                    String name = line.trim();
                    sieveNames.add(name);
                }
            }
            reader.close();
        } catch( Exception ex ) {
            System.out.println("ERROR: no sieve list found");
            ex.printStackTrace();
            System.exit(1);
        }

        String[] arr = new String[sieveNames.size()];
        return sieveNames.toArray(arr);
    }

    public void markupAll(SieveDocuments docs) {
        markupEvents(docs);
        markupTimexes(docs);
        // Try to determine DCT based on relevant property settings
        // TODO: use reflection method parallel to how sieves are chosen to choose the right DCTHeuristic method
        if (dctHeuristic == "setFirstDateAsDCT") {
            for (SieveDocument doc : docs.getDocuments()) {
                DCTHeursitics.setFirstDateAsDCT(doc);;  // only if there isn't already a DCT specified!
            }
        }
        runSieves(docs);
    }

    /**
     * Assumes the SieveDocuments has its text parsed.
     */
    public void markupEvents(SieveDocuments info) {
        if( eventClassifier == null ) {
            eventClassifier = new TextEventClassifier(info, wordnet);
            eventClassifier.loadClassifiers();
        }
        eventClassifier.extractEvents();
    }

    /**
     * Assumes the SieveDocuments has its text parsed.
     */
    public void markupTimexes(SieveDocuments info) {
        if( timexClassifier == null )
            timexClassifier = new TimexClassifier(info);
        timexClassifier.markupTimex3();
    }

    /**
     * Run the sieve pipeline on the given documents.
     * Returns the resulting annotated documents as an XML doc.
     */
    public String runSieves(SieveDocuments thedocs) {
        // Remove all TLinks because we will add our own.
        thedocs.removeAllTLinks();

        // Start with zero links.
        List<TLink> currentTLinks = new ArrayList<TLink>();
        Map<String,TLink> currentTLinksHash = new HashMap<String,TLink>();

        // Create all the sieves first.
        Sieve sieves[] = createAllSieves(sieveClasses);

        // Statistics collection.
        SieveStats stats[] = new SieveStats[sieveClasses.length];
        Map<String, SieveStats> sieveNameToStats = new HashMap<String, SieveStats>();
        for( int i = 0; i < sieveClasses.length; i++ ) {
            stats[i] = new SieveStats(sieveClasses[i]);
            sieveNameToStats.put(sieveClasses[i], stats[i]);
        }

        // Do each file independently.
        for( SieveDocument doc : thedocs.getDocuments() ) {
            System.out.println("Processing " + doc.getDocname() + "...");

            // Loop over the sieves in order.
            for( int xx = 0; xx < sieves.length; xx++ ) {
                Sieve sieve = sieves[xx];
                if( sieve == null ) continue;
                System.out.println("\tSieve " + sieve.getClass().toString());

                // Run this sieve
                List<TLink> newLinks = sieve.annotate(doc, currentTLinks);
                if( debug ) System.out.println("\t\t" + newLinks.size() + " new links.");
                stats[xx].addProposedCount(newLinks.size());

                // Verify the links as non-conflicting.
                int numRemoved = removeConflicts(currentTLinksHash, newLinks);
                if( debug ) System.out.println("\t\tRemoved " + numRemoved + " proposed links.");
                stats[xx].addRemovedCount(numRemoved);

                if( newLinks.size() > 0 ) {
                    // Add the good links to our current list.
                    addProposedToCurrentList(sieveClasses[xx], newLinks, currentTLinks, currentTLinksHash);//currentTLinks.addAll(newLinks);

                    // Run Closure
                    if( useClosure ) {
                        List<TLink> closedLinks = closureExpand(sieveClasses[xx], currentTLinks, currentTLinksHash);
                        if( debug ) System.out.println("\t\tClosure produced " + closedLinks.size() + " links.");
                        //					if( debug ) System.out.println("\t\tclosed=" + closedLinks);
                        stats[xx].addClosureCount(closedLinks.size());
                    }
                }
                if( debug ) System.out.println("\t\tDoc now has " + currentTLinks.size() + " links.");
            }

            // Add links to InfoFile.
            doc.addTlinks(currentTLinks);
            currentTLinks.clear();
            currentTLinksHash.clear();
        }

        XMLOutputter op = new XMLOutputter(Format.getPrettyFormat());
        Document jdomDoc = thedocs.toXML();
        return op.outputString(jdomDoc);
    }

    /**
     * Turns a string class name into an actual Sieve Instance of the class.
     * @param sieveClass
     * @return
     */
    private Sieve createSieveInstance(String sieveClass) {
        try {
            Class<?> c = Class.forName("caevo.sieves." + sieveClass);
            Sieve sieve = (Sieve)c.newInstance();
            return sieve;
        } catch (InstantiationException e) {
            System.out.println("ERROR: couldn't load sieve: " + sieveClass);
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            System.out.println("ERROR: couldn't load sieve: " + sieveClass);
            e.printStackTrace();
        } catch (IllegalArgumentException e) {
            System.out.println("ERROR: couldn't load sieve: " + sieveClass);
            e.printStackTrace();
        } catch (ClassNotFoundException e) {
            System.out.println("ERROR: couldn't load sieve: " + sieveClass);
            e.printStackTrace();
        }
        return null;
    }

    private Sieve[] createAllSieves(String[] stringClasses) {
        Sieve sieves[] = new Sieve[stringClasses.length];
        for( int xx = 0; xx < stringClasses.length; xx++ ) {
            sieves[xx] = createSieveInstance(stringClasses[xx]);
            System.out.println("Added sieve: " + stringClasses[xx]);
        }
        return sieves;
    }

    private String getLinkDebugInfo(TLink link, List<SieveSentence> sents, SieveDocument doc) {
        StringBuilder builder = new StringBuilder();

        if (link instanceof TimeTimeLink) {
            TimeTimeLink ttLink = (TimeTimeLink)link;
            Timex t1 = doc.getTimexByTid(ttLink.getId1());
            Timex t2 = doc.getTimexByTid(ttLink.getId2());

            builder.append("Time-Time " + ttLink.getRelation() + "\t");
            builder.append(t1.getTid() + ": " + t1.getValue() + " (" + t1.getText() + ")\t");
            builder.append(t2.getTid() + ": " + t2.getValue() + " (" + t2.getText() + ")");
        } else {
            // complex code because Timex and TextEvent don't share a common parent or common APIs
            String id1 = link.getId1();
            Timex t1 = doc.getTimexByTid(id1);
            TextEvent e1 = doc.getEventByEiid(id1);
            String normId1 = t1 != null ? t1.getTid() : e1.getId();
            String text1 = t1 != null ? t1.getText() : e1.getString();
            int sid1 = t1 != null ? t1.getSid() : e1.getSid();
            String id2 = link.getId2();
            Timex t2 = doc.getTimexByTid(id2);
            TextEvent e2 = doc.getEventByEiid(id2);
            String normId2 = t2 != null ? t2.getTid() : e2.getId();
            String text2 = t2 != null ? t2.getText() : e2.getString();
            int sid2 = t2 != null ? t2.getSid() : e2.getSid();
            builder.append(String.format("%s(%s[%s],%s[%s])", link.getRelation(),
                    text1, normId1, text2, normId2));
            if (e1 != null && e2 != null) {
                TextEvent.Tense e1Tense = e1.getTense();
                TextEvent.Aspect e1Aspect = e1.getAspect();
                TextEvent.Class e1Class = e1.getTheClass();
                TextEvent.Tense e2Tense = e2.getTense();
                TextEvent.Aspect e2Aspect = e2.getAspect();
                TextEvent.Class e2Class = e2.getTheClass();
                // simple display of relation, anchor texts, and anchor ids.
                builder.append(String.format("\n%s[%s-%s-%s], %s[%s-%s-%s]",
                        normId1, e1Tense, e1Aspect, e1Class, normId2, e2Tense, e2Aspect, e2Class));
            }
            builder.append(String.format("\n%s\n%s", sents.get(sid1).sentence(), sents.get(sid2).sentence()));
        }

        return builder.toString();
    }

    private void addProposedToCurrentList(String sieveName, List<TLink> proposed, List<TLink> current, Map<String,TLink> currentHash) {
        for( TLink newlink : proposed ) {
            if( currentHash.containsKey(newlink.getId1()+newlink.getId2()) ) {
                System.out.println("MAIN WARNING: overwriting " + currentHash.get(newlink.getId1()+newlink.getId2()) + " with " + newlink);
            }
            current.add(newlink);
            currentHash.put(newlink.getId1()+newlink.getId2(), newlink);
            currentHash.put(newlink.getId2()+newlink.getId1(), newlink);
            newlink.setOrigin(sieveName);
        }
    }

    /**
     * DESTRUCTIVE FUNCTION (proposedLinks will be modified)
     * Remove a link from the given list if another link already exists in the list
     * and covers the same event or time pair.
     * @param proposedLinks A list of TLinks to check for duplicates.
     * @return The number of duplicates found.
     */
    private int removeDuplicatesAndInvalids(List<TLink> proposedLinks) {
        if( proposedLinks == null || proposedLinks.size() < 2 )
            return 0;

        List<TLink> removals = new ArrayList<TLink>();
        Set<String> seenNew = new HashSet<String>();

        for( TLink proposed : proposedLinks ) {
            // Make sure we have a valid link with 2 events!
            if( proposed.getId1() == null || proposed.getId2() == null ||
                    proposed.getId1().length() == 0 || proposed.getId2().length() == 0 ) {
                removals.add(proposed);
                System.out.println("WARNING (proposed an invalid link): " + proposed);
            }
            // Remove any proposed links that are duplicates of already proposed links.
            else if( seenNew.contains(proposed.getId1()+proposed.getId2()) ) {
                removals.add(proposed);
                System.out.println("WARNING (proposed the same link twice): " + proposed);
            }
            // Normal link. Keep it.
            else {
                seenNew.add(proposed.getId1()+proposed.getId2());
                seenNew.add(proposed.getId2()+proposed.getId1());
            }
        }

        for( TLink remove : removals )
            proposedLinks.remove(remove);

        return removals.size();
    }

    /**
     * DESTRUCTIVE FUNCTION (proposedLinks will be modified)
     * Removes any links from the proposed list that already have links between the same pairs in currentLinks.
     * @param currentLinksHash The list of current "good" links.
     * @param proposedLinks The list of proposed new links.
     * @return The number of links removed.
     */
    private int removeConflicts(Map<String,TLink> currentLinksHash, List<TLink> proposedLinks) {
        List<TLink> removals = new ArrayList<TLink>();

        // Remove duplicates.
        int duplicates = removeDuplicatesAndInvalids(proposedLinks);
        if( debug && duplicates > 0 ) System.out.println("\t\tRemoved " + duplicates + " duplicate proposed links.");

        for( TLink proposed : proposedLinks ) {
            // Look for a current link that conflicts with this proposed link.
            TLink current = currentLinksHash.get(proposed.getId1()+proposed.getId2());
            if( current != null && current.coversSamePair(proposed) )
                removals.add(proposed);
        }

        for( TLink remove : removals )
            proposedLinks.remove(remove);

        return removals.size() + duplicates;
    }

    /**
     * DESTRUCTIVE FUNCTION (links may have new TLink objects appended to it)
     * Run transitive closure and add any inferred links.
     * @param links The list of TLinks to expand with transitive closure.
     * @return The list of new links from closure (these are already added to the given lists)
     */
    private List<TLink> closureExpand(String sieveName, List<TLink> links, Map<String,TLink> linksHash) {
        List<TLink> newlinks = closure.computeClosure(links, false);
        addProposedToCurrentList(sieveName, newlinks, links, linksHash);
        return newlinks;
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Malt parser");
        argParser.description("Run the Malt parser, providing access to it via Py4J");
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
            Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
        } catch (Exception e) {
            System.err.println("Error starting up Caevo gateway");
            e.printStackTrace();
            System.exit(1);
        }
    }
}

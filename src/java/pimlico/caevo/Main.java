package pimlico.caevo;

import caevo.*;
import caevo.sieves.Sieve;
import caevo.tlink.TLink;
import caevo.util.*;
import edu.stanford.nlp.parser.lexparser.LexicalizedParser;
import edu.stanford.nlp.trees.GrammaticalStructureFactory;
import edu.stanford.nlp.trees.PennTreebankLanguagePack;
import edu.stanford.nlp.trees.TreebankLanguagePack;
import edu.stanford.nlp.util.StringUtils;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

/**
 * Almost exact copy of Main from Caevo. Minimally changed so we can run sieves without outputting to a file.
 *
 * @author chambers, markgw
 */
public class Main {
	public static WordNet wordnet;
	
	Closure closure;
	boolean debug = true;
	boolean useClosure = true;
	boolean force24hrDCT = true;
	String dctHeuristic = "none";
	
	// Which dataset do we load?
  	public static enum DatasetType { TRAIN, DEV, TEST, ALL };
  	DatasetType dataset = DatasetType.TRAIN;
	public static final String serializedGrammar = "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz";

	// List the sieve class names in your desired order.
	private String[] sieveClasses;

	private LexicalizedParser parser;
	private GrammaticalStructureFactory gsf;
	
	/**
	 * Constructor: give it the command-line arguments.
	 */
	public Main(String[] args) {
		Properties cmdlineProps = StringUtils.argsToProperties(args);

		// Read the properties from disk at the location specified by -Dprops=XXXXX
		try {
			CaevoProperties.load();
			// Overwrite these globals if they are in the properties file.
			debug = CaevoProperties.getBoolean("Main.debug", debug);
			useClosure = CaevoProperties.getBoolean("Main.closure", useClosure);
			dataset = DatasetType.valueOf(CaevoProperties.getString("Main.dataset", dataset.toString()).toUpperCase());
			force24hrDCT = CaevoProperties.getBoolean("Main.force24hrdct", force24hrDCT);
			dctHeuristic = CaevoProperties.getString("Main.dctHeuristic", dctHeuristic);
		} catch (IOException e) { e.printStackTrace(); }

		// -set on the command line?
		if( cmdlineProps.containsKey("set") ) {
			String type = cmdlineProps.getProperty("set");
			dataset = DatasetType.valueOf(type.toUpperCase());
		}
		
		init();
		
		System.out.println("Dataset:\t" + dataset);
		System.out.println("Using Closure:\t" + useClosure);
		System.out.println("Debug:\t\t" + debug);
	}
	
	/**
	 * Empty Constructor.
	 */
	public Main() {
		init();
	}
	
	private void init() {
		// Initialize a caevo Main, so all the global stuff is created
		caevo.Main main = new caevo.Main();
		
		// Load WordNet for any and all sieves.
		wordnet = caevo.Main.wordnet;

		// Load the sieve list.
		sieveClasses = loadSieveList();

		// Initialize the parser.
		parser = Ling.createParser(serializedGrammar);
		if( parser == null ) {
			System.out.println("Failed to create parser from " + serializedGrammar);
			System.exit(1);
		}
		TreebankLanguagePack tlp = new PennTreebankLanguagePack();
		gsf = tlp.grammaticalStructureFactory();

		// Initialize the transitive closure code
		try {
			closure = new Closure();
		} catch( IOException ex ) {
			System.out.println("ERROR: couldn't load Closure utility.");
			ex.printStackTrace();
			System.exit(1);
		}

		reset();
	}

	public void reset() {
	}


	private String[] loadSieveList() {
		String filename = System.getProperty("sieves");
		if( filename == null ) filename = "default.sieves";

		System.out.println("Reading sieve list from: " + filename);

		List<String> sieveNames = new ArrayList<String>();
		try {
			BufferedReader reader = new BufferedReader(new FileReader(new File(filename)));
			String line;
			while( (line = reader.readLine()) != null ) {
				if( !line.matches("^\\s*$") && !line.matches("^\\s*//.*$") ) {
					// Remove trailing comments if they exist.
					if( line.indexOf("//") > -1 )
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
		for (int xx = 0; xx < stringClasses.length; xx++) {
			sieves[xx] = createSieveInstance(stringClasses[xx]);
		}
		return sieves;
	}

	/**
	 * Run the sieve pipeline on the given documents.
	 * Modified so that it doesn't output to a file, but just puts all the annotation on thedocs.
	 */
	public void runSieves(SieveDocuments thedocs) {
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
		
		// Data
		SieveDocuments docs = getDataset(dataset, thedocs);
        
		// Do each file independently.
		for( SieveDocument doc : docs.getDocuments() ) {
			// Loop over the sieves in order.
			for( int xx = 0; xx < sieves.length; xx++ ) {
				Sieve sieve = sieves[xx];
				if( sieve == null ) continue;

				// Run this sieve
				List<TLink> newLinks = sieve.annotate(doc, currentTLinks);
				stats[xx].addProposedCount(newLinks.size());
				
				// Verify the links as non-conflicting.
				int numRemoved = removeConflicts(currentTLinksHash, newLinks);
				stats[xx].addRemovedCount(numRemoved);
				
				if( newLinks.size() > 0 ) {
					// Add the good links to our current list.
					addProposedToCurrentList(sieveClasses[xx], newLinks, currentTLinks, currentTLinksHash);//currentTLinks.addAll(newLinks);

					// Run Closure
					if( useClosure ) {
						List<TLink> closedLinks = closureExpand(sieveClasses[xx], currentTLinks, currentTLinksHash);
						stats[xx].addClosureCount(closedLinks.size());
					}
				}
			}
			
			// Add links to InfoFile.
			doc.addTlinks(currentTLinks);
			currentTLinks.clear();
			currentTLinksHash.clear();
		}
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

	/**
	 * Assumes the InfoFile has its text parsed.
	 */
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
		// Always load a new classifier, since it needs to be loaded for each new doc set
		TextEventClassifier eventClassifier = new TextEventClassifier(info, wordnet);
		eventClassifier.loadClassifiers();
		eventClassifier.extractEvents();
	}
	
	/**
	 * Assumes the SieveDocuments has its text parsed.
	 */
	public void markupTimexes(SieveDocuments info) {
		TimexClassifier timexClassifier = new TimexClassifier(info);
		timexClassifier.markupTimex3();
	}

	public SieveDocuments markupRawText(String filename, String text) {
		SieveDocuments docs = new SieveDocuments();

		// Parse the text
		SieveDocument doc = Tempeval3Parser.parseText(filename, text, parser, gsf);
		docs.addDocument(doc);

		// Markup events, times, and tlinks.
		markupAll(docs);

		return docs;
	}

	public SieveDocuments getDataset(DatasetType type, SieveDocuments docs) {
		SieveDocuments dataset;
		if( type == DatasetType.TRAIN )
			dataset = Evaluate.getTrainSet(docs);
		else if( type == DatasetType.DEV )
			dataset = Evaluate.getDevSet(docs);
		else if( type == DatasetType.TEST )
			dataset = Evaluate.getTestSet(docs);
		else // ALL
			dataset = docs;
		
		// Fix DCTs that aren't 24-hour days.
		if( force24hrDCT ) force24hrDCTs(docs);
		
		return dataset;
	}
	
	private void force24hrDCTs(SieveDocuments docs) {
		if( docs != null ) {
			for( SieveDocument doc : docs.getDocuments() ) {
				List<Timex> dcts = doc.getDocstamp();
				if( dcts != null ) {
					for( Timex dct : dcts )
						Util.force24hrTimex(dct);
				}
			}
		}
	}
}

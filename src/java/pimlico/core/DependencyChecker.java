package pimlico.core;

/**
 * Simple utility to try loading Java classes to see whether they're available.
 */
public class DependencyChecker {
    public static void main(String[] args) {
        if (args.length == 0) {
            // Allow this to be called with no arguments and return quietly, so we can check that this tool is available
            System.exit(0);
        }
        // Otherwise try loading the named class
        String className = args[0];
        try {
            Class.forName(className);
        } catch( ClassNotFoundException e ) {
            System.exit(1);
        }
    }
}
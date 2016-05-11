// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

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
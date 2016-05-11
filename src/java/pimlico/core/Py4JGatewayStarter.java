// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

package pimlico.core;

import py4j.GatewayServer;
import py4j.Py4JNetworkException;

import java.io.File;
import java.io.IOException;
import java.io.PrintStream;
import java.net.BindException;
import java.util.List;

/**
 * Convenience function for Py4J interfaces.
 */
public class Py4JGatewayStarter {
    public static void startGateway(Object entryPoint) {
        Py4JGatewayStarter.startGateway(entryPoint, 0, 0);
    }

    /**
     * Standard gateway starter, using particular ports (or finding a free one) and just outputting the
     * used port to stdout.
     *
     * @param entryPoint
     * @param port
     * @param pythonPort
     */
    public static void startGateway(Object entryPoint, int port, int pythonPort) {
        startGateway(entryPoint, port, pythonPort, null);
    }

    /**
     * Additionally specifies a prefix to output in front of the used port. This means that in cases where
     * the startup routine inevitably involves printing to stdout, so that we can't be sure the first output
     * line is the used port, we can detect where the used port is output.
     *
     * @param entryPoint
     * @param port
     * @param pythonPort
     * @param portOutputPrefix
     */
    public static void startGateway(Object entryPoint, int port, int pythonPort, String portOutputPrefix) {
        if (portOutputPrefix == null) portOutputPrefix = "";

        try {
            // Create a gateway server, using this as an entry point
            // GatewayServer has a constructor with no ports, which sets them to defaults
            // If ports aren't given, instead with set them to 0 to automatically allocated ports
            GatewayServer gatewayServer = new GatewayServer(entryPoint, port, pythonPort, 0, 0, (List) null);

            try {
                // Set the server running
                gatewayServer.start();
            } catch (Py4JNetworkException e) {
                // Catch the case of a port bind exception, since this is common, and output a useful message
                if (e.getCause() instanceof BindException) {
                    System.err.println(
                        "could not bind to port " + gatewayServer.getPort() + " (" + e.getCause() + "). " +
                        "Try connecting on a different port by setting py4j_port in local config file"
                    );
                    System.out.println("ERROR");
                    System.out.flush();
                    System.exit(1);
                } else throw e;
            }

            // Output the port to stdout
            int listening_port = gatewayServer.getListeningPort();
            System.out.println(portOutputPrefix + listening_port);
            System.out.flush();
        } catch (RuntimeException e) {
            // Write the full stack trace out to a file to help identify what went wrong
            try {
                PrintStream ps = new PrintStream(new File(System.getProperty("user.home") + "/py4jgateway.log"));
                e.printStackTrace(ps);
                ps.close();
            } catch (IOException e1) {
                e1.printStackTrace();
            }
            // If we have any errors starting the server, output them on stderr
            System.err.println("Error starting server: " + e);
            // Also output a line to stdout, so the caller isn't left hanging waiting for something
            System.out.println("ERROR");
            System.out.flush();
            System.exit(1);
        }
    }
}

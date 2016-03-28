package pimlico.core;

import py4j.GatewayServer;
import py4j.Py4JNetworkException;

import java.io.File;
import java.io.FileWriter;
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

    public static void startGateway(Object entryPoint, int port, int pythonPort) {
        try {
            // Create a gateway server, using this as an entry point
            GatewayServer gatewayServer;
            if (port != 0) {
                if (pythonPort == 0)
                    pythonPort = port + 1;

                gatewayServer = new GatewayServer(entryPoint, port, pythonPort, 0, 0, (List) null);
            } else
                gatewayServer = new GatewayServer(entryPoint);

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
            System.out.println("" + listening_port);
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

package pimlico.core;

import py4j.GatewayServer;

import java.util.List;

/**
 * Convenience function for Py4J interfaces.
 */
public class Py4JGatewayStarter {
    public static void startGateway(Object entryPoint) {
        Py4JGatewayStarter.startGateway(entryPoint, 0, 0);
    }

    public static void startGateway(Object entryPoint, int port, int pythonPort) {
        // Create a gateway server, using this as an entry point
        GatewayServer gatewayServer;
        if (port != 0) {
            if (pythonPort == 0)
                pythonPort = port + 1;

            gatewayServer = new GatewayServer(entryPoint, port, pythonPort, 0, 0, (List)null);
        } else
            gatewayServer = new GatewayServer(entryPoint);

        // Set the server running
        gatewayServer.start();
        // Output the port to stdout
        int listening_port = gatewayServer.getListeningPort();
        System.out.println("" + listening_port);
        System.out.flush();
    }
}

#!/usr/bin/env python3

"""
Simple emulation of a munin-node in Python.
Place some plugins in the plugins/ folder and ensure their shebangs are set correctly for the target platform
An example: '#!/usr/bin/env python'.

Author: Opbod
License: MIT
URL: https://github.com/opbod/munin-node-sim
"""

import subprocess
import os
import sys
import signal

# Configuration
node_name = "servername"  # Name of the node
version = "0.5"  # Version of the node

if __name__ == '__main__':

    # Avoid showing Traceback when ctrl+c is triggered
    signal.signal(signal.SIGINT, lambda x, y: sys.exit(1))

    def execute_plugin(plugin_name, config=""):

        plugin_name = os.path.basename(plugin_name)
        plugin_args = []

        if not plugin_name:
            print("# ERROR: Plugin name not provided.")
            return False

        try:
            # Plugin executable? Otherwise extract shebang.
            if os.access(plugin_name, os.X_OK):
                plugin_args.append("./" + plugin_name)
            else:
                interpreter = open(plugin_name).readline().replace("#!", "").strip().split()[-1]
                plugin_args.append(interpreter)  # The interpreter found in the plugin is the first argument
                plugin_args.append(plugin_name)  # The filename is the second argument to provide
        except FileNotFoundError:
            print("# ERROR: Plugin file not found in the plugins directory.")
            return False
        except IndexError:
            print("# ERROR: No valid Shebang found in the plugin.")
            return False
        except PermissionError:
            print("# ERROR: Not the right permissions.")
            return False

        # Pass the 'config' argument to the plugin if required as a third and final argument
        if config:
            plugin_args.append(config)

        try:
            # Run the process, capturing the stdout output (pipe) and outputting as string (universal_newlines)
            return subprocess.run(plugin_args, check=True, stdout=subprocess.PIPE, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print("# ERROR: Plugin returned non-zero exit status %d." % e.returncode)
            return False
        except OSError:
            print("# ERROR: Could not execute plugin. (Maybe missing shebang?)")
            return False

    # Verify the plugins/ directory exists
    try:
        os.chdir(os.path.dirname(os.path.realpath(__file__)) + "/plugins/")
    except FileNotFoundError:
        print("# ERROR: Plugins directory not found, exiting.")
        sys.exit(1)

    # Get all files in the plugins/ directory and consider them as Munin plugins
    plugins = [f for f in os.listdir() if os.path.isfile(f)]

    # Provide an interactive prompt, starting with the proper header text
    print("# munin node at %s\n" % node_name)
    while True:
        line = input()
        if not line:
            break
        line = line.strip()

        command = line.split(' ', 1)
        # If the command has an argument, consider it as the plugin name to use
        plugin = (len(command) > 1) and command[1] or None

        if command[0] == "list":
            print("%s\n" % " ".join(plugins))
        elif command[0] == "nodes":
            print("nodes\n%s\n.\n" % node_name)
        elif command[0] in ("fetch", "config"):
            config = (command[0] == "config") and "config" or ""
            completed_process = execute_plugin(plugin, config)
            if completed_process:
                print(completed_process.stdout)
            print(".\n")
        elif command[0] == "version":
            print("munins node on %s version: %s\n" % (node_name, version))
        elif command[0] == "cap":
            pass
            #print("cap multigraph dirtyconfig\n")
        elif command[0] == "quit" or command[0] == "exit":
            break
        else:
            print("# Unknown command. Try list, nodes, config, fetch, version or quit\n")

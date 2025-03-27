#!/usr/bin/env python3
import os
import sys
import re
import argparse
import configparser
from typing import Optional, Tuple, List

import vmup.gcp_utils as gcp_utils

class VMManager:
    """Manages SSH configuration file operations."""

    def __init__(self, config_file_path: str = None):
        """
        Initialize the SSH Config Manager.
        
        :param config_file_path: Path to the configuration file. 
                                  Defaults to user-specific paths if not provided.
        """
        # Default paths
        self.default_ssh_config = os.path.expanduser("~/.ssh/config")
        self.default_config_file = os.path.expanduser("vmup/vmup_config")
        self.ssh_dir = os.path.expanduser("~/.ssh/")

        # Use provided or default config file path
        self.config_file_path = config_file_path or self.default_config_file
        self.ssh_config_path = self._get_ssh_config_path()

    def _read_config(self) -> configparser.ConfigParser:
        """
        Read the configuration file.
        
        :return: Parsed configuration
        """
        config = configparser.ConfigParser()
        if os.path.isfile(self.config_file_path):
            config.read(self.config_file_path)
        return config

    def _get_ssh_config_path(self) -> str:
        """
        Retrieve the SSH config file location.
        
        :return: Path to SSH config file
        """
        config = self._read_config()
        return config.get("settings", "ssh_config", fallback=self.default_ssh_config)

    def get_ssh_user(self) -> str:
        """
        Retrieve the SSH user from configuration.
        
        :return: SSH username
        """
        config = self._read_config()
        return config.get("settings", "user", fallback="default_user")

    def get_project_and_zone(self) -> Tuple[str, str]:
        """
        Retrieve GCP project and zone from configuration.
        
        :return: Tuple of (project, zone)
        :raises SystemExit: If project or zone is not set
        """
        config = self._read_config()
        project = config.get("settings", "project", fallback=None)
        zone = config.get("settings", "zone", fallback=None)
        
        if not project or not zone:
            sys.exit("Error: Project and Zone must be set in the config file.")

        return project, zone

    def list_hostnames(self) -> List[str]:
        """
        List all hostnames from the SSH config file.
        
        :return: List of hostname entries
        """
        if not os.path.isfile(self.ssh_config_path):
            print(f"Error: Config file {self.ssh_config_path} not found!")
            return []

        with open(self.ssh_config_path, 'r') as f:
            lines = f.readlines()

        hostnames = []
        current_host = None

        for line in lines:
            host_match = re.match(r'^\s*Host\s+(.+)', line, re.IGNORECASE)
            if host_match:
                current_host = host_match.group(1)
            hostname_match = re.match(r'^\s*HostName\s+(.+)', line, re.IGNORECASE)
            if hostname_match and current_host:
                hostnames.append(f"{current_host} -> {hostname_match.group(1)}")

        return hostnames

    def update_hostname(self, host: str, new_ip: str) -> bool:
        """
        Update the SSH config file to change the HostName for a given host.
        
        :param host: Host to update
        :param new_ip: New IP address or hostname
        :return: True if update successful, False otherwise
        """
        if not os.path.isfile(self.ssh_config_path):
            print(f"Error: Config file {self.ssh_config_path} not found!")
            return False

        with open(self.ssh_config_path, 'r') as f:
            lines = f.readlines()

        host_found = False
        in_target_host_block = False
        modified_lines = []

        for line in lines:
            if re.match(r'^\s*Host\s+', line, re.IGNORECASE):
                in_target_host_block = bool(
                    re.match(r'^\s*Host\s+' + re.escape(host) + r'\s*$', line, re.IGNORECASE)
                )
                host_found |= in_target_host_block
            
            if in_target_host_block and re.match(r'^\s*HostName\s+', line, re.IGNORECASE):
                modified_line = re.sub(r'(^\s*HostName\s+).*', r'\g<1>' + new_ip, line)
                modified_lines.append(modified_line)
            else:
                modified_lines.append(line)

        if not host_found:
            print(f"Error: Host '{host}' not found in config file!")
            return False

        with open(self.ssh_config_path, 'w') as f:
            f.writelines(modified_lines)

        print(f"Successfully updated HostName for '{host}' to '{new_ip}' in {self.ssh_config_path}")
        return True

    def add_host(self, new_name: str) -> bool:
        """
        Add a new SSH host entry to the config file.
        
        :param new_name: Name of the new host to add
        :return: True if host added successfully, False otherwise
        """
        identity_file = os.path.join(self.ssh_dir, "google_compute_engine")
        known_hosts_file = os.path.join(self.ssh_dir, "google_compute_known_hosts")
        user = self.get_ssh_user()

        new_entry = f"""
Host {new_name}
    HostName 1.1.1.1
    IdentityFile {identity_file}
    UserKnownHostsFile={known_hosts_file}
    IdentitiesOnly=yes
    CheckHostIP=no
    User {user}
"""

        # Check if the host already exists
        with open(self.ssh_config_path, "r") as f:
            if any(re.match(rf'^\s*Host\s+{re.escape(new_name)}\s*$', line) for line in f):
                print(f"Error: Host '{new_name}' already exists in {self.ssh_config_path}!")
                return False

        with open(self.ssh_config_path, "a") as f:
            f.write(new_entry)

        print(f"Successfully added new host '{new_name}' to {self.ssh_config_path}")
        return True

    def start_vm(self, instance: str) -> bool:
        """
        Start a VM and update SSH config with its public IP.
        
        :param instance: Name of the VM instance
        :return: True if successful, False otherwise
        """
        try:
            project, zone = self.get_project_and_zone()
            print(f"Starting VM: {instance}...")
            
            start_result = gcp_utils.start_instance(instance, project, zone)
            print(start_result)
            
            if "Error" in start_result:
                print("Failed to start the VM.")
                return False
            
            print(f"Retrieving public IP for VM: {instance}...")
            public_ip = gcp_utils.get_public_ip(instance, project, zone)
            
            if "Error" in public_ip:
                print("Failed to retrieve the public IP.")
                return False
            
            print(f"Public IP obtained: {public_ip}")
            
            # Try to add the HostName (False if already exists)
            update_success = self.add_host(instance)
            update_success = self.update_hostname(instance, public_ip)

            if update_success:
                print(f"Successfully updated SSH config for {instance} with new IP: {public_ip}")
                return True
            
            return False
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return False


def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(description="Manage SSH HostName entries in the SSH config file.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List hostnames command
    subparsers.add_parser("list", help="List all configured SSH hosts")

    # Update hostname command
    update_parser = subparsers.add_parser("update", help="Update the HostName of a given SSH host")
    update_parser.add_argument("host", help="The SSH host to update")
    update_parser.add_argument("new_ip", help="The new IP address or hostname to set")

    # Add hostname command
    add_parser = subparsers.add_parser("add", help="Add a new SSH host entry")
    add_parser.add_argument("new_name", help="The new SSH host name to add")

    # Start VM command
    start_parser = subparsers.add_parser("start", help="Start a VM and update SSH config")
    start_parser.add_argument("instance", help="The name of the VM instance to start")

    args = parser.parse_args()
    config_manager = VMManager()

    try:
        if args.command == "list":
            hostnames = config_manager.list_hostnames()
            if hostnames:
                print("Configured Hosts:")
                for entry in hostnames:
                    print(entry)
            else:
                print("No hostnames found in the SSH config file.")
        
        elif args.command == "update":
            config_manager.update_hostname(args.host, args.new_ip)
        
        elif args.command == "add":
            config_manager.add_host(args.new_name)
        
        elif args.command == "start":
            config_manager.start_vm(args.instance)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
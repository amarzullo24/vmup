import argparse
import subprocess

def stop_instance(instance, project, zone):
    """Stops the Google Cloud VM instance."""
    command = [
        "gcloud", "compute", "instances", "stop", instance,
        "--project", project, "--zone", zone
    ]
    return run_command(command)

def get_public_ip(instance, project, zone):
    """Gets the external IP of the Google Cloud VM instance."""
    command = [
        "gcloud", "compute", "instances", "describe", instance,
        "--project", project, "--zone", zone,
        "--format=get(networkInterfaces[0].accessConfigs[0].natIP)"
    ]
    return run_command(command)

def start_instance(instance, project, zone):
    """Starts the Google Cloud VM instance."""
    command = [
        "gcloud", "compute", "instances", "start", instance,
        "--project", project, "--zone", zone
    ]
    return run_command(command)

def run_command(command):
    """Executes a shell command and returns the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Google Cloud Compute instances.")
    
    parser.add_argument("action", choices=["start", "stop", "ip"], help="Action to perform")
    parser.add_argument("--instance", help="Instance name")
    parser.add_argument("--project", help="Project ID")
    parser.add_argument("--zone", help="Zone (eg: us-central1-f)")

    args = parser.parse_args()

    if args.action == "stop":
        print(stop_instance(args.instance, args.project, args.zone))
    elif args.action == "describe":
        print(get_public_ip(args.instance, args.project, args.zone))
    elif args.action == "start":
        print(start_instance(args.instance, args.project, args.zone))

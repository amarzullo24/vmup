# **vmup**  

*A simple command-line tool to start a gcp vm and update SSH host IP addresses in your `~/.ssh/config` file.*  
## **🚀 Features**  
✅ Start a VM from the command line  
✅ Quickly update the IP address of a host in your SSH config  

---

## **📌 Installation**  
### **Using `pip`**
```sh
pip install git+https://github.com/amarzullo24/vmup.git
```

### **From Source**
```sh
git clone https://github.com/amarzullo24/vmup.git
cd vmup
pip install --editable .
```
## **gcp utils**
Ensure you have properly installed the GCP cli and authenitcate.

## **⚙ Custom SSH Config Path**
Set the default **SSH config file** path and your default username in the configuration file.
Set also the project and the region of the VM you want to start (only if you use the `start` argument)
```
[settings]
ssh_config = PATH_TO_SSH_CONFIG_FILE
user = VM_SSH_USER
project = PROJECT_ID
zone = VM_REGION
```
---

## **🛠 Usage**  
### **Basic Command**
```sh
vmup start <GCP_VM_NAME>
```
For example:  
```sh
vmup update vm_demo
```
This will automatically start `vm_demo` (ensure you have properly set the `project` and `zone` fields in the config file) and automatically update its `HostName` in `~/.ssh/config`.

```sh
vmup update <HOSTNAME> <NEW_IP>
```
For example:  
```sh
vmup update myserver 192.168.1.100
```
This will find `myserver` in `~/.ssh/config` and update its `HostName`.

You can also list the current hostnames and IPs as:
```sh
vmup list
```
You can also add a new hostname as:
```sh
vmup add <NEW_HOSTNAME>
```
By default the address of the new host is 1.1.1.1
Use vmup uodate `new_hostname new_ip` to change it.

---

## **📝 Example `.ssh/config` Before & After**  

### **Before**
```ini
Host myserver
    HostName 203.0.113.10
    User myuser
```

### **After Running `vmup myserver 192.168.1.100`**
```ini
Host myserver
    HostName 192.168.1.100
    User myuser
```

---

## **🔧 Uninstall**
To remove `vmup`, simply run:
```sh
pip uninstall vmup
```

---

## **📜 License**  
This project is licensed under the **MIT License**.  

import socket
import threading
import queue
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ===============================
# COMMON SERVICES DATABASE
# ===============================
COMMON_PORTS = {
    21:'FTP',22:'SSH',23:'Telnet',25:'SMTP',
    53:'DNS',80:'HTTP',110:'POP3',143:'IMAP',
    443:'HTTPS',3306:'MySQL',3389:'RDP',
    5900:'VNC',8080:'HTTP-Alt'
}

# ===============================
# PORT SCANNER ENGINE
# ===============================
class PortScanner:

    def __init__(self, gui, target, start_port, end_port):
        self.gui = gui
        self.target = target
        self.start_port = start_port
        self.end_port = end_port
        self.queue = queue.Queue()
        self.stop_flag = False

    def scan_port(self):
        while not self.queue.empty() and not self.stop_flag:
            port = self.queue.get()

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((self.target, port))

                if result == 0:
                    service = COMMON_PORTS.get(port, "Unknown")
                    self.gui.root.after(
                        0,
                        lambda p=port, s=service:
                        self.gui.append_output(f"[OPEN] Port {p} → {s}\n")
                    )

                sock.close()

            except:
                pass

            self.queue.task_done()

    def start_scan(self):

        self.gui.update_status("Scanning...")

        for port in range(self.start_port, self.end_port + 1):
            self.queue.put(port)

        total_ports = self.end_port - self.start_port + 1
        start_time = time.time()

        threads = []

        for _ in range(120):
            t = threading.Thread(target=self.scan_port, daemon=True)
            t.start()
            threads.append(t)

        while any(t.is_alive() for t in threads) and not self.stop_flag:

            time.sleep(0.05)

            scanned = total_ports - self.queue.qsize()
            progress = (scanned / total_ports) * 100
            elapsed = time.time() - start_time

            self.gui.root.after(
                0, lambda p=progress: self.gui.progress_bar.configure(value=p)
            )

            self.gui.root.after(
                0,
                lambda e=elapsed: self.gui.elapsed_label.config(
                    text=f"Elapsed: {e:.2f}s"
                )
            )

        self.gui.root.after(0, self.gui.scan_finished)

# ===============================
# GUI APPLICATION
# ===============================
class PortScannerGUI:

    def __init__(self, root):

        self.root = root
        self.root.title("Advanced Network Port Scanner")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # ----- Style -----
        style = ttk.Style()
        style.theme_use("clam")

        # GREEN STATIC PROGRESS BAR
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor="#cccccc",
            background="#00cc00",     # static green fill
            lightcolor="#00cc00",
            darkcolor="#009900",
            bordercolor="#cccccc"
        )

        main = ttk.Frame(root, padding=10)
        main.pack(fill="both", expand=True)

        # ---------- INPUT FRAME ----------
        frame = ttk.LabelFrame(main, text="Scan Settings", padding=10)
        frame.pack(fill="x")

        ttk.Label(frame,text="Target Host").grid(row=0,column=0,padx=5)
        self.target_entry = ttk.Entry(frame,width=30)
        self.target_entry.grid(row=0,column=1)

        ttk.Label(frame,text="Start Port").grid(row=0,column=2)
        self.start_entry = ttk.Entry(frame,width=10)
        self.start_entry.grid(row=0,column=3)

        ttk.Label(frame,text="End Port").grid(row=0,column=4)
        self.end_entry = ttk.Entry(frame,width=10)
        self.end_entry.grid(row=0,column=5)

        self.start_btn = ttk.Button(frame,text="Start Scan",command=self.start_scan)
        self.start_btn.grid(row=0,column=6,padx=5)

        self.stop_btn = ttk.Button(frame,text="Stop",command=self.stop_scan)
        self.stop_btn.grid(row=0,column=7)

        self.export_btn = ttk.Button(frame,text="Export Results",command=self.export_results)
        self.export_btn.grid(row=0,column=8,padx=5)

        # ---------- STATUS ----------
        status = ttk.LabelFrame(main,text="Status",padding=10)
        status.pack(fill="x",pady=10)

        self.status_label = ttk.Label(status,text="Idle")
        self.status_label.pack(anchor="w")

        # STATIC GREEN-FILL BAR
        self.progress_bar = ttk.Progressbar(
            status,
            length=600,
            style="Green.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x",pady=5)

        self.elapsed_label = ttk.Label(status,text="Elapsed: 0.00s")
        self.elapsed_label.pack(anchor="e")

        # ---------- OUTPUT ----------
        output = ttk.LabelFrame(main,text="Open Ports",padding=10)
        output.pack(fill="both",expand=True)

        self.result_box = tk.Text(output,font=("Consolas",10))
        self.result_box.pack(fill="both",expand=True)

    # ================= GUI FUNCTIONS =================

    def start_scan(self):

        try:
            target = self.target_entry.get().strip()
            target_ip = socket.gethostbyname(target)
        except:
            messagebox.showerror("Error","Invalid Hostname/IP")
            return

        try:
            start_port = int(self.start_entry.get())
            end_port = int(self.end_entry.get())
        except:
            messagebox.showerror("Error","Invalid Ports")
            return

        self.result_box.delete(1.0, tk.END)

        self.append_output(f"Target: {target} ({target_ip})\n")
        self.append_output(f"Port Range: {start_port}-{end_port}\n\n")

        self.start_btn.config(state="disabled")

        self.scanner = PortScanner(self,target_ip,start_port,end_port)

        threading.Thread(
            target=self.scanner.start_scan,
            daemon=True
        ).start()

    def stop_scan(self):
        if hasattr(self,'scanner'):
            self.scanner.stop_flag = True
        self.update_status("Stopped")

    def scan_finished(self):
        self.update_status("Completed")
        self.start_btn.config(state="normal")
        self.append_output("\nScan Completed Successfully\n")

    def append_output(self,text):
        self.result_box.insert(tk.END,text)
        self.result_box.see(tk.END)

    def update_status(self,text):
        self.status_label.config(text=text)

    # ---------- EXPORT ----------
    def export_results(self):
        file = filedialog.asksaveasfilename(defaultextension=".txt")
        if file:
            data = self.result_box.get(1.0, tk.END)
            with open(file,"w") as f:
                f.write(data)
            messagebox.showinfo("Saved","Results Exported")

# ===============================
# RUN PROGRAM
# ===============================
def main():
    root=tk.Tk()
    app=PortScannerGUI(root)
    root.mainloop()

if __name__=="__main__":
    main()
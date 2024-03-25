import os
import sys
import time
import subprocess
import logging

def execute_adb(adb_command):
    result = subprocess.run(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    print(f"Command execution failed: {adb_command}", "red")
    print(result.stderr, "red")
    return "ERROR"

def list_all_devices():
    adb_command = "adb devices"
    device_list = []
    result = execute_adb(adb_command)
    if result != "ERROR":
        devices = result.split("\n")[1:]
        for d in devices:
            device_list.append(d.split()[0])
    return device_list

class AndroidController:
    def __init__(self, device):
        self.device = device
        self.width, self.height = self.get_device_size()
        self.backslash = "\\"
        self.screenshot_dir = "/sdcard"
        self.xml_dir = "/sdcard"  # 
        os.system(f"adb -s {self.device} push yadb /sdcard")
        
    def get_device_size(self):
        adb_command = f"adb -s {self.device} shell wm size"
        result = execute_adb(adb_command)
        if result != "ERROR":
            return map(int, result.split(": ")[1].split("x"))
        return 0, 0

    def get_screenshot(self, prefix, save_dir):
        cap_command = f"adb -s {self.device} shell screencap -p " \
                      f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')}"
        pull_command = f"adb -s {self.device} pull " \
                       f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')} " \
                       f"{os.path.join(save_dir, prefix + '.png')}"
        result = execute_adb(cap_command)
        if result != "ERROR":
            result = execute_adb(pull_command)
            if result != "ERROR":
                return os.path.join(save_dir, prefix + ".png")
            return result
        return result

    def get_xml(self, prefix, save_dir):
        dump_command = f"adb -s {self.device} shell uiautomator dump " \
                       f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')}"
        pull_command = f"adb -s {self.device} pull " \
                       f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')} " \
                       f"{os.path.join(save_dir, prefix + '.xml')}"
        result = execute_adb(dump_command)
        if result != "ERROR":
            result = execute_adb(pull_command)
            if result != "ERROR":
                return os.path.join(save_dir, prefix+".xml")
            return result
        return result

    def get_activities(self, prefix, save_dir):
        command = f"adb -s {self.device} shell dumpsys activity activities"
        with open(os.path.join(save_dir, prefix + ".activities.log"), "w") as outfile:
            outfile.write(execute_adb(command))
            
    def text(self, input_str):
        adb_command = f"adb -s {self.device} shell app_process -Djava.class.path=/sdcard/yadb /sdcard com.ysbing.yadb.Main -keyboard \"{input_str}\""
        ret = execute_adb(adb_command)
        return ret

class UserInputMonitor(object):
    """
    A connection with the target device through `getevent`.
    `getevent` is able to get raw user input from device.
    """

    def __init__(self, device=None, output_fp=None):
        """
        initialize connection
        :param device: a Device instance
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.device = device
        self.connected = False
        self.process = None
        if output_fp is not None:
            self.out_file = output_fp
        else:
            self.out_file = "./user_input.txt"
            
        with open(self.out_file, "w") as outfile:
            pass

        self.x_pos = 0
        self.y_pos = 0
        self.pos_list = []
        self.step_ind = 1

    def connect(self):
        self.process = subprocess.Popen(["adb", "-s", self.device, "shell", "getevent", "-lt"],
                                        stdin=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE)
        import threading
        listen_thread = threading.Thread(target=self.handle_output)
        listen_thread.start()

    def disconnect(self):
        self.connected = False
        if self.process is not None:
            self.process.terminate()

    def check_connectivity(self):
        return self.connected

    def handle_output(self):
        self.connected = True

        while self.connected:
            if self.process is None:
                continue
            line = self.process.stdout.readline()
            if not isinstance(line, str):
                line = line.decode()    
            self.parse_line(line)
        print("[CONNECTION] %s is disconnected" % self.__class__.__name__)


    def write_input_action(self, input_str):
        with open(self.out_file, "a", encoding="utf-8") as outfile:
            outfile.write("Step {} : Input text \"{}\"\n".format(self.step_ind, input_str))
        self.step_ind += 1


    def write_complete_action(self):
        with open(self.out_file, "a", encoding="utf-8") as outfile:
            outfile.write("Step {} : Set spisode status as COMPLETE\n".format(self.step_ind))

    def parse_line(self, getevent_line):
        
        def print_and_write(outfile, str):
            print(str)
            outfile.write(str + "\n")
        
        if "BTN_TOUCH" in getevent_line:
            if "DOWN" in getevent_line:
                self.pos_list = []

            elif "UP" in getevent_line:
                if len(self.pos_list) == 1:
                    with open(self.out_file, "a", encoding="utf-8") as outfile:
                        print_and_write(outfile, "Step {} : Tap [{},{}]".format(self.step_ind, int(self.pos_list[0][0]), int(self.pos_list[0][1])))
                    self.step_ind += 1
                else:
                    with open(self.out_file, "a", encoding="utf-8") as outfile:
                        print_and_write(outfile, "Step {} : Move from [{},{}] to [{},{}]".format(self.step_ind,
                                int(self.pos_list[0][0]), int(self.pos_list[0][1]), 
                                int(self.pos_list[-1][0] - self.pos_list[0][0]), int(self.pos_list[-1][1] - self.pos_list[0][1])))
                    self.step_ind += 1

        elif "ABS_MT_POSITION_X" in getevent_line:
            pos = getevent_line.strip().split(" ")[-1]
            self.x_pos = float(int(pos, 16)) / 10.0
            
        elif "ABS_MT_POSITION_Y" in getevent_line:
            pos = getevent_line.strip().split(" ")[-1]
            self.y_pos = float(int(pos, 16)) / 10.0
            self.pos_list.append((self.x_pos, self.y_pos))


if __name__ == "__main__":
        
    task_id = "settings_4"
    task_description = "帮我打开省电模式"
    output_dir = "C:/Users/yznzh/OneDrive/文档/Agent/AAA_xiaomi_13"
    
    task_output_dir = os.path.join(output_dir, task_id)
    
    os.makedirs(task_output_dir, exist_ok=True)
    with open(os.path.join(task_output_dir, task_id + ".goal.txt"), "w", encoding="utf-8") as outfile:
        outfile.write(task_description)
        
    devices = list_all_devices()
    device = AndroidController(devices[0])
    input_monitor = UserInputMonitor(devices[0], output_fp=os.path.join(task_output_dir, "{}.action.txt".format(task_id)))
    input_monitor.connect()

    try:
        step = 1
        print("Start !")
        while True:
            device.get_xml("{}.step_{}".format(task_id, step), task_output_dir)
            device.get_screenshot("{}.step_{}".format(task_id, step), task_output_dir)
            device.get_activities("{}.step_{}".format(task_id, step), task_output_dir)
            input_str = input().strip()
            
            if input_str == "e" or input_str == "end":
                input_monitor.write_complete_action()
                break
            elif len(input_str) > 0:
                device.text(input_str)
                input_monitor.write_input_action(input_str)

            step += 1

    except KeyboardInterrupt:
        pass
    
    finally:
        input_monitor.disconnect()

import sys
import logging
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import xml.etree.ElementTree as ET
import csv
sys.path.append('..')

# ROBOT_HOST = '192.168.0.2'
ROBOT_HOST = '192.168.56.101'
ROBOT_PORT = 30004
config_filename = 'rtdeIO.xml'
RTDE_inputs = 'RTDE_Inputs.csv'
RTDE_outputs ='RTDE_Outputs.csv'


class RTDEConnect:
    _inputlist = RTDE_inputs
    _outputlist = RTDE_outputs

    def __init__(self, robotIP, fileName, inputlist=RTDE_inputs, outputlist=RTDE_outputs, frequency=500):
        self.robotIP = robotIP
        self.port = 30004
        self.con = rtde.RTDE(self.robotIP, self.port)
        self.keep_running = True
        self.config = fileName
        self.frequency = frequency
        self._rtdein = {}
        self._rtdeout = {}
        self._rtdein, self._rtdeout = RTDEConnect._rtdeIO(self._rtdein, self._rtdeout)
        self.programState = {
            0: 'Stopping',
            1: 'Stopped',
            2: 'Playing',
            3: 'Pausing',
            4: 'Paused',
            5: 'Resuming',
            6: 'Retracting'
        }
        self.initialize()
        # self.con._RTDE__input_config[1].speed_slider_mask = 1

    def initialize(self):
        conf = rtde_config.ConfigFile(self.config)
        self.con.connect()
        self.con.get_controller_version()
        x = rtde_config.Recipe
        tree = ET.parse(self.config)
        root = tree.getroot()
        recipes = [x.parse(r) for r in root.findall('recipe')]

        # Iterate through all the recipe keys.
        for i in range(len(recipes)):
            # Check if recipe key's variables all exist as RTDE Inputs. If so, send the key as an input setup.
            if all(item in list(self._rtdein.keys()) for item in recipes[i].names):
                self.con.send_input_setup(recipes[i].names, recipes[i].types)
            # Check if recipe key's variables all exist as RTDE Outputs. If so, send the key as an output setup.
            elif all(item in list(self._rtdeout.keys()) for item in recipes[i].names):
                self.con.send_output_setup(recipes[i].names, recipes[i].types)
            else:
                print(f'Error: {recipes[i].key} has a mix of inputs and outputs or has a variable that does not '
                      f'exist\nExiting...')
                sys.exit()

        if not self.con.send_start():
            print('Could not connect. Exiting...')
            sys.exit()

    def receive(self):
        return self.con.receive()

    def send(self, cmd):
        return self.con.send(cmd)

    def shutdown(self):
        self.con.send_pause()
        self.con.disconnect()


    @staticmethod
    def _csvparse(csvlist, parsedDict):
        empty_lines = 0
        with open(csvlist, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if not ''.join(row).strip():
                    empty_lines += 1
                    continue
                parsedDict[row[0]] = row[1]
        return parsedDict

    @classmethod
    def _rtdeIO(cls, inputDict, outputDict):
        inputs = cls._csvparse(cls._inputlist, inputDict)
        outputs = cls._csvparse(cls._outputlist, outputDict)
        return inputs, outputs


if __name__ == "__main__":
    state_monitor = RTDEConnect(ROBOT_HOST, config_filename)
    runtime_old = -1
    while state_monitor.keep_running:
        state = state_monitor.receive()

        if state is None:
            break

        if state.runtime_state != runtime_old:
            logging.info(f'Robot program is {state_monitor.programState.get(state.runtime_state)}')
            runtime_old = state.runtime_state

# rTest = RTDEConnect(ROBOT_HOST, config_filename)
# rTest._ioParse(RTDE_inputs, RTDE_outputs)
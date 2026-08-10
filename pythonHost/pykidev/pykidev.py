
import time, sys
from .pykiba import Pykiba


class PykiDev(Pykiba):
    """Extended version of Pykiba with auto-installation of Arduino commands.

    If the Arduino supports a 'help' command, this class dynamically binds all available
    commands as methods on the object.
    """
    def __init__(self, *args,  **kargs):
        """Constructor. Inherits Pykiba and installs commands.

        Parameters:
        ----------
        **kargs : dict
            Serial connection parameters (port, baudrate, etc.)
        """
        super().__init__(*args,  **kargs)
        self.install_arduino_commands()

    def install_arduino_commands(self):
        """Detects Arduino commands via 'help' and binds them as methods.

        Automatically creates Python methods matching the Arduino's serial command list.
        Very useful for dynamic, readable command execution.
        """  
        command_list = self.command("hlp")
        #command_list.append('hlp')
        for cmd in command_list:
            def function_template(*args, captured_name=cmd):
                return self.command(captured_name, *args)
            setattr(self, cmd, function_template)
            self.string_rep += cmd + '\n'
      
    def commands_list(self):
        """"Returns the commands inherited from Arduino.
            
        """
        return self.string_rep.strip().split("\n")[2:]
    
    def sleep(self, seconds):
        """Whait some time for TEST purposes!
           Parametes:
           ---------
                     seconds
           Returns:  
           --------  
                   "End"
        """
        time.sleep(seconds)
        return "End"

if __name__ == "__main__":
    ard = PykiDev('/dev/ttyACM0', baudrate = 115200) 

import os
import logging
import trace

from dagogo.eda_bridge.eda_bridge import EdaBridge

logger = logging.getLogger(__name__)


# Available attributes from Edatool
# 
#   - name (str): top vlnv name.
#   - toplevel (str): top-level design unit name.
#   - files (list): list of source files
#   - work_root (str): output scratch dir root: <build_root>/<flow>-<tool>/
#   - vpi_modules (list): List of VPI modules defined in .core files.
#   - hooks (dict): fusesoc-level coops. Don't use it.
#   - tool_options (dict): custom switches specified in .core files. Don't use it.
#   - parameters (dict): contain the following sub-dictionaries:
#       - vlogdefine (dict): Verilog defines for compiling all files 
#       - vlogparam (dict): Verilog parameters for compiling all files 
#       - plusarg (dict):Verilog plusargs for running all tests
#       - generic (dict): global VHDL generics for running all tests
#       - cmdlinearg (dict): command-line arguments for running all tests
# 
class Palladium(EdaBridge):

    # The HDL parameter types supported by this tool. Possible choices are:
    # End user can define such parameters in .core files, under the targets
    # section:
    #
    #  - vlogparam: Verilog parameters (compile-time option),
    #  - vlogdefine: Verilog defines (compile-time global symbol),
    #  - plusarg: Verilog plusargs (run-time option),
    #  - generic: VHDL generic (run-time option),
    #  - cmdlinearg: Command-line arguments (run-time option),
    #
    argtypes = ['plusarg', 'vlogdefine', 'vlogparam' ]

    # Wilson: Try not to use this if possible. Usually we don't want to
    #         package tool-specific settings with .core files. Users
    #         should specify tool-specific settings in tool or project
    #         .hjson files.
    @classmethod
    def get_doc(cls, api_ver):
        """Define attributes that can be specifed in .core files. These 
        attributes can be retried from self.tool_options (dict) inside
        configure_main().

        Args:
            cls (Class): This Palladium class.
            api_ver (int): Always 0 for now. Ignore it.

        Returns:
            (dict) Return a data structure that defines the supported
            attributes. There are two types of attributes:

               1. members: scalar attributes
               2. lists: attributes of list type.

            Each attribute definition includes three pieces of information:

               1. name: attribute name.
               2. type: entry data type. 'String' should be used here.
               3. desc: a brief description of this attribute.
        """
        return {'description' : "Palladium from Cadence Design System.",
                'members' : [
                    {'name' : 'hw_model',
                     'type' : 'String',
                     'desc' : 'Palladium accellerator model name.'},
                    ],
                'lists' : [
                    {'name' : 'vlan_opts',
                     'type' : 'String',
                     'desc' : 'Additional options for Palladium SV compilation.'},
                    {'name' : 'xrun_opts',
                     'type' : 'String',
                     'desc' : 'Additional options for Palladium elaboration.'},
                    ]}

    def _dump(self, I=""):
        """Show the Palladium object for debug purpose."""
        for k, v in sorted(self.__dict__.items(), key=lambda x: x[0]):
            if k.endswith('env'):
                continue
            if v is None:
                print(f'{I}- {k}: None')
            elif isinstance(v, dict):
                if len(v) == 0:
                    print(f'{I}- {k}: {{}}')
                else:
                    print(f'{I}- {k}:')
                    [print(f'{I}   - {k2}: {self._param_value_str(v2)}')
                        for k2, v2 in v.items()]
            elif isinstance(v, list):
                if len(v) == 0:
                    print(f'{I}- {k}: []')
                else:
                    print(f'{I}- {k}:')
                    [print(f'{I}   - {v2}') for v2 in v]
            else:
                print(f'{I}- {k}: {str(v)}')
        print('', flush=True)


    def configure_main(self):
        """This is the main method to generate all necessary data files for
        palladium build and run. For example:

            - file-list files
            - any additional configuration files for compile and elaboration
            - tcl files to initialize and run simulation
            - etc.

        All outputs should be generated under self.work_root.
        """
        self._dump()

        # TODO: the returned incdirs variable includes all include dirs, not
        #       separating the two compilations for simulator and accelerator.
        (src_files, incdirs) = self._get_fileset_files() 

        emu_filelist_file = os.path.join(self.work_root, self.name + '.emu.f')
        efh = open(emu_filelist_file, 'w')
        sim_filelist_file = os.path.join(self.work_root, self.name + '.sim.f')
        sfh = open(sim_filelist_file, 'w')

        for f in src_files:
            if f.file_type in ('verilogSource', 'systemVerilogSource'):
                # Skip included files.
                if hasattr(f, 'is_include_file'):
                    continue

                # Compose the line.
                args = []
                if f.file_type == 'systemVerilogSource':
                    args.append('-sv')
                if f.logical_name:
                    args.append(f'-lib {f.logical_name}')
                for k, v in self.vlogdefine.items():
                    args.append(f'+define+{k}={self._param_value_str(v)}')
                for k, v in self.vlogparam.items():
                    args.append(f'{k}={self._param_value_str(v)}')
                for v in incdirs:
                    args.append(f'+incdir+{v}')
                if self.tool_options.get('vlan_opts', ''):
                    args.append(' '.join(self.tool_options.get('vlan_opts')))
                args.append(f.name)

                if hasattr(f, 'partof') and (f.partof == 'dut'):
                    efh.write(' '.join(args) + '\n')
                else:
                    sfh.write(' '.join(args) + '\n')

        efh.close()
        sfh.close()
